"""Adaptador DIR3 — Directorio Común de Unidades Orgánicas y Oficinas.

Dos modos:
  1. CSV de descarga masiva (URL configurable; la URL histórica del blueprint
     §01 murió con la reestructuración de administracion.gob.es).
  2. XLSX del CTT — "Listado Unidades EELL/CCAA" de
     https://administracionelectronica.gob.es/ctt/verPestanaDescargas.htm?idIniciativa=dir3
     El portal está tras F5 TrafficShield (challenge JS) y no permite descarga
     automatizada; los ficheros se obtienen del navegador o de instantáneas
     Wayback del CTT (declaradas como tal). Cabeceras reales verificadas:
     C_ID_UD_ORGANICA, C_DNM_UD_ORGANICA, C_ID_NIVEL_ADMON, C_ID_TIPO_ENT_PUBLICA,
     N_NIVEL_JERARQUICO, C_DESC_PROV, C_ID_DEP_UD_SUPERIOR, C_ID_ESTADO…
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from scrapers.base import DEFAULT_HEADERS

logger = logging.getLogger(__name__)

# candidatos de cabecera por campo (es/ca, mayúsculas/minúsculas, variantes)
HEADER_CODIGO = ("codigo_dir3", "código dir3", "codigo", "cod_unidad")
HEADER_NOMBRE = ("nombre_unidad", "denominacion", "denominación", "nombre", "unidad")
HEADER_NIVEL = ("nivel_jerarquico", "nivel jerárquico", "nivel", "nivel_jerarquico_dir3")
HEADER_PADRE = ("codigo_padre", "código padre", "unidad_superior", "codigo_unidad_superior")
HEADER_TIPO = ("tipo_unidad", "tipo", "nivel_administracion")


@dataclass
class UnidadDir3:
    codigo: str
    nombre: str
    nivel: int | None
    padre: str | None
    tipo: str | None


@dataclass
class UnidadDir3Rica(UnidadDir3):
    """Fila del listado XLSX del CTT (unidades EELL/CCAA/AGE)."""

    nivel_admon: int | None = None        # 1=AGE 2=CCAA 3=EELL
    provincia: str | None = None
    nombre_padre: str | None = None
    estado: str | None = None
    extra: dict = field(default_factory=dict)


# cabeceras reales verificadas en el fichero del CTT
_COLS_XLSX = (
    "C_ID_UD_ORGANICA", "C_DNM_UD_ORGANICA", "C_ID_NIVEL_ADMON",
    "C_ID_TIPO_ENT_PUBLICA", "N_NIVEL_JERARQUICO", "C_DESC_PROV",
    "C_ID_DEP_UD_SUPERIOR", "C_DNM_UD_ORGANICA_SUPERIOR", "C_ID_ESTADO",
)


def _fila_a_unidad(row: dict[str, object]) -> UnidadDir3Rica | None:
    codigo = (str(row.get("C_ID_UD_ORGANICA") or "")).strip()
    nombre = (str(row.get("C_DNM_UD_ORGANICA") or "")).strip()
    if not codigo or not nombre:
        return None
    nivel_jer = str(row.get("N_NIVEL_JERARQUICO") or "").strip()
    nivel_adm = str(row.get("C_ID_NIVEL_ADMON") or "").strip()

    def _int(v: str) -> int | None:
        return int(v) if v.isdigit() else None

    def _clean(v: object) -> str | None:
        s = str(v or "").strip()
        return s if s and s.lower() != "none" else None

    return UnidadDir3Rica(
        codigo=codigo,
        nombre=nombre,
        nivel=_int(nivel_jer),
        padre=_clean(row.get("C_ID_DEP_UD_SUPERIOR")),
        tipo=_clean(row.get("C_ID_TIPO_ENT_PUBLICA")),
        nivel_admon=_int(nivel_adm),
        provincia=_clean(row.get("C_DESC_PROV")),
        nombre_padre=_clean(row.get("C_DNM_UD_ORGANICA_SUPERIOR")),
        estado=_clean(row.get("C_ID_ESTADO")),
    )


def _parse_xlsx_xml(path: str | Path) -> list[UnidadDir3Rica]:
    """Parser OOXML directo (zip + iterparse).

    Necesario porque los XLSX que el CTT genera hoy dejan la hoja de datos
    HUÉRFANA del workbook (sheet5.xml de ~20 MB no declarada en workbook.xml):
    openpyxl solo ve las hojas registradas, que vienen vacías. Este parser
    recorre el zip, carga sharedStrings y busca la hoja con más <row> — la de
    datos — sin depender del manifiesto.
    """
    import io
    import zipfile
    import xml.etree.ElementTree as ET

    ns_strip = lambda tag: tag.rsplit("}", 1)[-1]  # noqa: E731

    with zipfile.ZipFile(path) as z:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            for evento, elem in ET.iterparse(
                io.BytesIO(z.read("xl/sharedStrings.xml")), events=("end",)
            ):
                if ns_strip(elem.tag) == "si":
                    texto = "".join(
                        t.text or "" for t in elem.iter() if ns_strip(t.tag) == "t"
                    )
                    shared.append(texto)
                    elem.clear()

        hojas = sorted(
            (n for n in z.namelist() if n.startswith("xl/worksheets/sheet")),
            key=lambda n: z.getinfo(n).file_size,
            reverse=True,
        )
        if not hojas:
            return []

        _letra_a_idx = lambda ref: sum(  # noqa: E731
            (ord(c) - 64) * 26**i for i, c in enumerate(reversed(ref))
        ) - 1

        filas: list[tuple[int, dict[str, object]]] = []
        with z.open(hojas[0]) as f:
            fila_actual: dict[str, object] | None = None
            for evento, elem in ET.iterparse(f, events=("start", "end")):
                tag = ns_strip(elem.tag)
                if evento == "start" and tag == "row":
                    fila_actual = {}
                elif evento == "end" and tag == "c" and fila_actual is not None:
                    ref = elem.attrib.get("r", "")
                    letras = "".join(c for c in ref if c.isalpha())
                    if not letras:
                        continue
                    tipo = elem.attrib.get("t")
                    valor: object = None
                    v = elem.find(
                        "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v"
                    )
                    if tipo == "s" and v is not None:
                        valor = shared[int(v.text)]
                    elif tipo == "inlineStr":
                        is_el = elem.find(
                            "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}is"
                        )
                        if is_el is not None:
                            valor = "".join(
                                t.text or ""
                                for t in is_el.iter()
                                if ns_strip(t.tag) == "t"
                            )
                    elif v is not None:
                        valor = v.text
                    if valor is not None:
                        fila_actual[_letra_a_idx(letras)] = valor
                    elem.clear()
                elif evento == "end" and tag == "row":
                    if fila_actual:
                        filas.append(
                            (len(filas), fila_actual)
                        )
                    fila_actual = None

    # localiza la fila de cabeceras y mapea columna → nombre de campo
    cab_idx = None
    for i, (_, fila) in enumerate(filas):
        valores = {str(v).strip() for v in fila.values()}
        if sum(1 for c in _COLS_XLSX[:3] if c in valores) == 3:
            cab_idx = i
            break
    if cab_idx is None:
        return []

    # el generador actual del CTT repite la cabecera C_DNM_UD_ORGANICA en las
    # columnas de "unidad superior" y "unidad principal": gana la primera
    col_a_nombre: dict[int, str] = {}
    for i, v in filas[cab_idx][1].items():
        nombre = str(v).strip()
        if nombre in _COLS_XLSX and nombre not in col_a_nombre.values():
            col_a_nombre[i] = nombre

    unidades: list[UnidadDir3Rica] = []
    for _, fila in filas[cab_idx + 1 :]:
        mapeada = {
            nombre: fila[i] for i, nombre in col_a_nombre.items() if i in fila
        }
        unidad = _fila_a_unidad(mapeada)
        if unidad and (unidad.estado in (None, "V")):
            unidades.append(unidad)
    return unidades


def parse_unidades_xlsx(path: str | Path) -> list[UnidadDir3Rica]:
    """Parsea un listado de unidades del CTT (EELL/CCAA/AGE). Solo unidades
    vigentes (C_ID_ESTADO = V)."""
    from openpyxl import load_workbook

    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    unidades: list[UnidadDir3Rica] = []
    cabeceras: dict[int, str] = {}
    for row in ws.iter_rows(values_only=True):
        if not cabeceras:
            presentes = {i: str(v).strip() for i, v in enumerate(row) if v}
            if all(c in presentes.values() for c in _COLS_XLSX[:3]):
                cabeceras = presentes
            continue
        fila = {cabeceras[i]: v for i, v in enumerate(row) if i in cabeceras}
        unidad = _fila_a_unidad(fila)
        if unidad and (unidad.estado in (None, "V")):
            unidades.append(unidad)
    wb.close()
    if unidades:
        return unidades
    # los XLSX del CTT (oct. 2026) dejan la hoja de datos huérfana del workbook:
    # openpyxl ve hojas vacías → parser OOXML directo
    return _parse_xlsx_xml(path)


def _col(row: dict, headers: tuple[str, ...]) -> str | None:
    for k, v in row.items():
        key = (k or "").strip().lower()
        if key in headers:
            return (v or "").strip() or None
    return None


class Dir3Adapter:
    def __init__(self, url: str, proxy: str | None = None):
        if not url:
            raise ValueError(
                "Falta la URL de descarga de DIR3 — pásala por --url o define DIR3_URL"
            )
        self.url = url
        self.proxy = proxy or None

    def fetch(self) -> list[UnidadDir3]:
        with httpx.Client(
            headers=DEFAULT_HEADERS, follow_redirects=True, timeout=300,
            proxy=self.proxy,
        ) as client:
            resp = client.get(self.url)
            resp.raise_for_status()
            content = resp.content

        text = None
        for enc in ("utf-8-sig", "cp1252", "latin-1"):
            try:
                text = content.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        if text is None:
            raise RuntimeError("No pude decodificar el fichero DIR3")

        sample = text[:8192]
        dialect = csv.Sniffer().sniff(
            sample, delimiters=";\t,",
        )
        reader = csv.DictReader(text.splitlines(), dialect=dialect)
        unidades: list[UnidadDir3] = []
        for row in reader:
            codigo = _col(row, HEADER_CODIGO)
            nombre = _col(row, HEADER_NOMBRE)
            if not codigo or not nombre:
                continue
            nivel_raw = _col(row, HEADER_NIVEL)
            unidades.append(UnidadDir3(
                codigo=codigo,
                nombre=nombre,
                nivel=int(nivel_raw) if nivel_raw and nivel_raw.isdigit() else None,
                padre=_col(row, HEADER_PADRE),
                tipo=_col(row, HEADER_TIPO),
            ))
        return unidades
