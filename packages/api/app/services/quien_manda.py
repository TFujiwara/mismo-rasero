"""Pilar 1 — ¿Quién manda? Construye el organigrama completo sobre una dirección.

Geocodifica (Nominatim estructurada, ver services/geocoding.py) y compone la
cadena UE → Estado → CCAA → Diputación → Ayuntamiento, cada nivel con qué
puede hacer, qué NO puede y la fuente legal. La mancomunidad queda como
tarjeta "pendiente" hasta que el seed DIR3/Censo EELL esté disponible — se
declara, no se inventa.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.services.geocoding import geocode
from app.services.verificar import normaliza

if TYPE_CHECKING:  # pragma: no cover
    from sqlalchemy.orm import Session

LBRL = ("Ley 7/1985, de Bases de Régimen Local (LBRL)",
        "https://www.boe.es/buscar/act.php?id=BOE-A-1985-11672")
CE = ("Constitución Española, art. 149",
      "https://www.boe.es/buscar/act.php?id=BOE-A-1978-31229")
ESTATUT_CV = ("Estatut d'Autonomia de la Comunitat Valenciana, art. 54 y 57",
              "https://dogv.gva.es/es/estatut")
BOLETTINS_CCAA = ("Boletines oficiales de las CCAA (índice)",
                  "https://administracion.gob.es/pag_Home/espanaAdmon/boletinesYLegislacion/BO_CCAA.html")
DOUE = ("Diario Oficial de la Unión Europea",
        "https://eur-lex.europa.eu/oj/direct-access.html")

# CCAA multiprovinciales (tienen diputación). Uniprovinciales sin BOP ni
# diputación: Asturias, Cantabria, Madrid, Murcia, Navarra, La Rioja, Baleares.
MULTIPROVINCIALES = {
    "andalucia", "aragon", "castilla y leon", "castilla la mancha",
    "comunitat valenciana", "comunidad valenciana", "cataluna", "catalunya",
    "canarias", "pais vasco", "euskadi", "extremadura", "galicia",
}


def _normaliza_simple(texto: str) -> str:
    return normaliza(texto or "")


def _nivel(
    nivel: str, nombre: str, puede: list[str], no_puede: list[str],
    fuente: tuple[str, str], pendiente: bool = False,
) -> dict[str, Any]:
    return {
        "nivel": nivel, "nombre": nombre,
        "puede": puede, "no_puede": no_puede,
        "fuente_texto": fuente[0], "fuente_url": fuente[1],
        "pendiente": pendiente,
    }


def construir_organigrama(
    geo: dict[str, Any],
    diputacion_row: Any | None = None,
    mancomunidades: list[str] | None = None,
    municipio_row: Any | None = None,
) -> list[dict[str, Any]]:
    """Función pura: geocodificación (+ filas DIR3 resueltas) → tarjetas.
    Testeable sin BD pasando los rows como None o objetos con los atributos
    que se usan (nombre, codigo_dir3, provincia)."""
    niveles: list[dict[str, Any]] = []

    niveles.append(_nivel(
        "UE", "Unión Europea",
        ["Reglamentos y directivas que llegan a tu día a día (etiquetado, medio "
         "ambiente, agricultura, IVA)"],
        ["Tu IBI, tus ordenanzas municipales, el IRPF"],
        DOUE,
    ))

    niveles.append(_nivel(
        "Estado", "Administración General del Estado",
        ["IRPF, SMI y pensiones", "defensa y política exterior",
         "legislación laboral y mercantil"],
        ["urbanismo y ordenanzas de tu calle",
         "sanidad y educación (en la mayoría de comunidades)"],
        CE,
    ))

    ccaa = geo.get("ccaa")
    if ccaa:
        if _normaliza_simple(ccaa) in (
            "comunitat valenciana", "comunidad valenciana",
        ):
            niveles.append(_nivel(
                "CCAA", "Generalitat Valenciana",
                ["sanidad y hospitales", "educación pública",
                 "tramo autonómico del IRPF", "carreteras CV y policía autonómica"],
                ["moneda o defensa", "el IBI de tu casa (es municipal)"],
                ESTATUT_CV,
            ))
        else:
            niveles.append(_nivel(
                "CCAA", f"Comunidad autónoma: {ccaa}",
                ["sanidad y hospitales", "educación pública",
                 "tramo autonómico del IRPF"],
                ["moneda, defensa, aduanas", "el IBI de tu casa (es municipal)"],
                BOLETTINS_CCAA,
            ))

    provincia = geo.get("provincia")
    if provincia and ccaa and _normaliza_simple(ccaa) in MULTIPROVINCIALES:
        nombre_dipu = (
            diputacion_row.nombre
            if diputacion_row is not None and diputacion_row.nombre
            else f"Diputación Provincial de {provincia}"
        )
        codigo_dipu = (
            f" · DIR3 {diputacion_row.codigo_dir3}"
            if diputacion_row is not None and diputacion_row.codigo_dir3
            else ""
        )
        niveles.append(_nivel(
            "Provincia", f"{nombre_dipu}{codigo_dipu}",
            ["carreteras provinciales",
             "asistencia técnica a municipios de menos de 20.000 habitantes",
             "recaudación colaborativa de impuestos locales"],
            ["ordenanzas fiscales de tu municipio", "sanidad ni educación"],
            ("LBRL art. 31-36 · registro DIR3", LBRL[1]),
        ))

    municipio = geo["municipio"]
    codigo_ayto = (
        f" · DIR3 {municipio_row.codigo_dir3}"
        if municipio_row is not None and municipio_row.codigo_dir3
        else ""
    )
    niveles.append(_nivel(
        "Local", f"Ayuntamiento de {municipio}{codigo_ayto}",
        ["urbanismo y licencias de obra", "IBI, IVTM, plusvalía y tasas (basura, agua)",
         "baches, farolas, parques, limpieza y policía local"],
        ["IRPF ni SMI", "hospitales ni colegios (salvo delegación expresa)"],
        ("LBRL art. 25.2 · registro DIR3", LBRL[1]),
    ))

    fuente_dir3 = (
        "Directorio Común DIR3 (CTT)",
        "https://administracionelectronica.gob.es/ctt/verPestanaDescargas.htm?idIniciativa=dir3",
    )
    if mancomunidades:
        niveles.append({
            "nivel": "Supramunicipal",
            "nombre": f"Mancomunidades registradas en {provincia}",
            "mancomunidades": mancomunidades,
            "afiliacion": "pendiente",
            "puede": [], "no_puede": [],
            "fuente_texto": f"{fuente_dir3[0]} — afiliación exacta por municipio "
                "pendiente (Censo de Entes Locales)",
            "fuente_url": fuente_dir3[1],
            "pendiente": False,
        })
    else:
        niveles.append(_nivel(
            "Supramunicipal", "Mancomunidades, consorcios y entes locales menores",
            [],
            [],
            fuente_dir3,
            pendiente=True,
        ))

    return niveles


def quien_manda(direccion: str, session: "Session") -> dict[str, Any]:
    """Endpoint service: geocodifica, construye organigrama y registra el
    municipio en administraciones (acumulación de datos reales)."""
    from sqlalchemy import select

    from app.models import Administracion
    from app.services.verificar import normaliza

    geo = geocode(direccion)
    if geo is None:
        return {
            "direccion": direccion, "resuelta": False,
            "nota": "No se ha podido resolver la dirección. Prueba con el formato "
            "'calle número, municipio' (ej.: 'Carrer Ermita 12, Vila-real').",
            "organigrama": [],
        }

    municipio_row = _busca_municipio(session, geo["municipio"])
    diputacion_row = _busca_diputacion(session, geo.get("provincia"))
    mancomunidades = _busca_mancomunidades(session, geo.get("provincia"))

    existe = session.execute(
        select(Administracion.id).where(
            (Administracion.nombre == geo["municipio"])
            & (Administracion.tipo == "MUNICIPIO")
        )
    ).scalar_one_or_none()
    if existe is None and municipio_row is None:
        session.add(Administracion(
            nombre=geo["municipio"], tipo="MUNICIPIO", nivel=5,
        ))
        session.commit()

    return {
        "direccion": direccion,
        "resuelta": True,
        "municipio": geo["municipio"],
        "provincia": geo["provincia"],
        "ccaa": geo["ccaa"],
        "coordenadas": {"lat": geo["lat"], "lon": geo["lon"]},
        "fuente_geocoder": geo["fuente"],
        "display_name": geo["display_name"],
        "organigrama": construir_organigrama(
            geo,
            diputacion_row=diputacion_row,
            mancomunidades=mancomunidades,
            municipio_row=municipio_row,
        ),
    }


def _misma_provincia(a: str | None, b: str | None) -> bool:
    """Compara provincias tolerando el formato bilingüe de DIR3
    ('Castelló/Castellón' vs 'Castellón')."""
    if not a or not b:
        return False
    na, nb = normaliza(a), normaliza(b)
    partes_a = {p.strip() for p in na.split() if p and p not in ("y", "e", "la", "las", "los", "de", "del")}
    # el nombre DIR3 puede unir las dos lenguas: 'castello castellon'
    for palabra in nb.split():
        if palabra in partes_a or palabra in na:
            return True
    return False


def _busca_municipio(session: "Session", municipio: str):
    from sqlalchemy import select

    from app.models import Administracion

    if not municipio:
        return None
    filas = session.execute(
        select(Administracion).where(
            (Administracion.entidad_tipo == "AY")
            & Administracion.nombre.ilike(f"Ayuntamiento de {municipio}%")
        )
    ).scalars().all()
    objetivo = normaliza(municipio)
    for f in filas:
        nombre = normaliza((f.nombre or "").replace("Ayuntamiento de", ""))
        if nombre == objetivo or objetivo in nombre:
            return f
    return None


def _busca_diputacion(session: "Session", provincia: str | None):
    from sqlalchemy import select

    from app.models import Administracion

    if not provincia:
        return None
    filas = session.execute(
        select(Administracion).where(
            (Administracion.entidad_tipo == "DP") & (Administracion.nivel == 1)
        )
    ).scalars().all()
    for f in filas:
        if _misma_provincia(f.provincia, provincia):
            return f
    return None


def _busca_mancomunidades(session: "Session", provincia: str | None, limite: int = 8):
    from sqlalchemy import select

    from app.models import Administracion

    if not provincia:
        return []
    filas = session.execute(
        select(Administracion).where(
            (Administracion.entidad_tipo == "MC") & (Administracion.nivel == 1)
        )
    ).scalars().all()
    nombres = [f.nombre for f in filas if _misma_provincia(f.provincia, provincia)]
    return sorted(nombres)[:limite]
