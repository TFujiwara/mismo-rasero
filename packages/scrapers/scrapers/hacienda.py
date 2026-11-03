"""Scraper del portal público de Presupuestos EELL (Hacienda, SGCIEF).

Verificado en vivo (oct. 2026) contra
https://serviciostelematicosext.hacienda.gob.es/sgcief/presupuestos/Publico

Flujo (todo con __RequestVerificationToken rotatorio):
  1. GET  /Publico                     → sesión + token
  2. POST /Framework/Ejercicio/CambioEjercicioPeriodo  (Continuar=True, EjercicioActivo=AÑO)
  3. POST /Publico/SeleccionConsultaPublico  (Comunidad, Provincia, CodigoTipoCorporacion)
     → lista de entidades con enlaces /SeleccionEntidad/{id}
  4. GET  /Publico/SeleccionConsultaPublico/SeleccionEntidad/{id}
     → código de entidad (17-12-135-AA-000) + enlace a formularios
  5. GET  /Ej{AÑO}/Entidades/AccesoFormulariosEntidad/{id}
  6. GET  /Ej{AÑO}/F_1_1_1/PintarFormulario → idFormulario
  7. GET  /Ej{AÑO}/Exportacion/ExportarXMLFormulario?idFormulario={id}&idTipoXML=1
     → XML con resumen de ingresos (capítulos 1-9) y gastos (1-9) en euros

El XML real (F.1.1.1) trae el resumen por capítulos del presupuesto inicial:
  ingresos → previsiones_iniciales (n_1..n_9, total_ingresos)
  gastos   → creditos_iniciales   (n_1..n_9, total_gastos)
"""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from decimal import Decimal

import httpx

BASE = "https://serviciostelematicosext.hacienda.gob.es/SGCIEF/Presupuestos"
DOMINIO = "https://serviciostelematicosext.hacienda.gob.es"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"

# tipos de corporación del portal
TIPO_DIPUTACIONES = "DD"
TIPO_AYUNTAMIENTOS_GRANDES = "A5"
TIPO_AYUNTAMIENTOS_PEQ = "AA"
TIPO_MANCOMUNIDADES = "MM"


@dataclass
class ResumenPresupuesto:
    codigo_entidad: str          # 17-12-135-AA-000
    nombre_entidad: str          # Vila-real
    ejercicio: int
    tipo_contabilidad: str | None
    ingresos: dict[str, Decimal] = field(default_factory=dict)   # "1".."9", "total"
    gastos: dict[str, Decimal] = field(default_factory=dict)
    fuente_url: str = ""


class SgciefScraper:
    def __init__(self, ejercicio: int, client: httpx.Client | None = None):
        self.ejercicio = ejercicio
        self.client = client or httpx.Client(
            headers={"User-Agent": UA}, follow_redirects=True, timeout=90
        )
        self._owned = client is None

    def close(self) -> None:
        if self._owned:
            self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _token(self, html: str) -> str:
        m = re.search(r'name="__RequestVerificationToken[^>]*value="([^"]+)"', html)
        if not m:
            raise RuntimeError("sin __RequestVerificationToken en la página")
        return m.group(1)

    def abrir_sesion(self, ccaa: str, provincia: str, tipo_entidad: str) -> list[dict]:
        """Ejercicio activo + selección → lista de entidades {id, nombre, codigo}."""
        r = self.client.get(f"{BASE}/Publico")
        r.raise_for_status()
        r = self.client.post(
            f"{BASE}/Framework/Ejercicio/CambioEjercicioPeriodo",
            data={
                "__RequestVerificationToken": self._token(r.text),
                "Continuar": "True",
                "EjercicioActivo": str(self.ejercicio),
            },
        )
        r.raise_for_status()
        r = self.client.post(
            f"{BASE}/Publico/SeleccionConsultaPublico",
            data={
                "__RequestVerificationToken": self._token(r.text),
                "Comunidad": ccaa,
                "Provincia": provincia,
                "CodigoTipoCorporacion": tipo_entidad,
            },
        )
        r.raise_for_status()
        entidades = []
        for m in re.finditer(
            r'href="(/SGCIEF/Presupuestos/Publico/SeleccionConsultaPublico/'
            r'SeleccionEntidad/(\d+))"[^>]*>(.{0,90}?)</a>', r.text, re.S
        ):
            nombre = html.unescape(
                re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(3))).strip()
            )
            # el href ya es absoluto desde la raíz del dominio — no sumar BASE
            entidades.append({"id": m.group(2), "url": DOMINIO + m.group(1),
                              "nombre": nombre})
        return entidades

    def resumen_de_entidad(self, entidad_id: str, nombre_sesion: str = "") -> ResumenPresupuesto:
        """Sigue la cadena de una entidad hasta su XML F.1.1.1 y lo parsea.
        nombre_sesion: el nombre limpio de la página de selección (preferente —
        la página de entidad lista también entidades dependientes y un regex
        puede pescar el nombre equivocado)."""
        r = self.client.get(
            f"{BASE}/Publico/SeleccionConsultaPublico/SeleccionEntidad/{entidad_id}"
        )
        r.raise_for_status()
        # el código real es '17-12-135-AA-000 — Vila-real' (sin ningún prefijo Ej)
        m = re.search(r"(\d{2}-\d{2}-\d{3}-[A-Z]{2}-\d{3})", r.text)
        if not m:
            raise RuntimeError(f"entidad {entidad_id}: sin código de entidad")
        codigo_entidad = m.group(1)
        nombre_entidad = nombre_sesion.strip() or codigo_entidad

        r = self.client.get(f"{BASE}/Ej{self.ejercicio}/Entidades/AccesoFormulariosEntidad/{entidad_id}")
        r.raise_for_status()
        r = self.client.get(f"{BASE}/Ej{self.ejercicio}/F_1_1_1/PintarFormulario")
        r.raise_for_status()
        m = re.search(r"idFormulario=(\d+)", r.text)
        if not m:
            raise RuntimeError(
                f"entidad {codigo_entidad}: sin formulario F.1.1.1 (¿sin presupuesto comunicado?)"
            )
        id_formulario = m.group(1)
        r = self.client.get(
            f"{BASE}/Ej{self.ejercicio}/Exportacion/ExportarXMLFormulario",
            params={"idFormulario": id_formulario, "idTipoXML": "1"},
        )
        r.raise_for_status()
        resumen = parse_xml_f111(r.content)
        resumen.codigo_entidad = codigo_entidad
        resumen.nombre_entidad = nombre_entidad
        resumen.ejercicio = self.ejercicio
        resumen.fuente_url = (
            f"{BASE}/Ej{self.ejercicio}/Entidades/AccesoFormulariosEntidad/{entidad_id}"
        )
        return resumen


def parse_xml_f111(xml_bytes: bytes) -> ResumenPresupuesto:
    """Parsea el XML del F.1.1.1 → capítulos de ingresos y gastos en euros."""
    root = ET.fromstring(xml_bytes)
    uri = root.tag.split("}")[0].lstrip("{") if "}" in root.tag else ""
    ns = {"p": uri} if uri else {}
    p = "p:" if uri else ""

    codigo = root.findtext(f".//{p}codigo_entidad", namespaces=ns) or ""
    nombre = root.findtext(f".//{p}nombre_entidad", namespaces=ns) or ""
    ejercicio_txt = root.findtext(f".//{p}periodo/{p}ejercicio", namespaces=ns) or ""
    tipo_cont = root.findtext(f".//{p}tipo_contabilidad", namespaces=ns)

    def _leer(ruta: str, destino: dict[str, Decimal]) -> None:
        cont = root.find(ruta, ns)
        if cont is None:
            return
        for hijo in cont:
            clave = hijo.tag.split("}")[-1]
            clave = re.sub(r"_(previsiones_iniciales|creditos_iniciales)$", "", clave)
            clave = re.sub(r"^n_", "", clave)
            # estructura real: <n_1><previsiones_iniciales>30899100</...></n_1>
            valor_el = next(iter(hijo), None)
            texto = (valor_el.text or "").strip() if valor_el is not None else ""
            if not texto:
                continue
            destino[{"total_ingresos": "total", "total_gastos": "total"}.get(clave, clave)
                    or "total"] = Decimal(texto)

    res = ResumenPresupuesto(
        codigo_entidad=codigo, nombre_entidad=nombre,
        ejercicio=int(ejercicio_txt) if ejercicio_txt.isdigit() else 0,
        tipo_contabilidad=tipo_cont,
    )
    _leer(f".//{p}resumen_clasificacion_economica_ingresos", res.ingresos)
    _leer(f".//{p}resumen_clasificacion_economica_gastos", res.gastos)
    return res
