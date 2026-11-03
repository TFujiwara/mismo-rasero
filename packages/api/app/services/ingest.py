"""Persistencia de ingestas — conecta los adaptadores (packages/scrapers) con las
tablas normas / administraciones. Los adaptadores son DB-agnósticos; este módulo
los une al esquema §19. En Fase 6+ las llamadas pasan a Celery; hoy es síncrono.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from scrapers.base import BoletinAdapter, Documento, ResumenIngesta, registrar_adapters
from scrapers.dir3 import Dir3Adapter

from app.models import Administracion, Boletin, Norma

logger = logging.getLogger(__name__)


def _persistir_documentos(
    session: Session,
    boletin: Boletin,
    adapter: BoletinAdapter,
    documentos: list[Documento],
    limit: int | None = None,
) -> ResumenIngesta:
    resumen = ResumenIngesta(sigla=boletin.sigla, fecha=documentos[0].fecha if documentos else date.today())
    total = documentos if limit is None else documentos[:limit]
    resumen.total = len(total)

    for doc in total:
        if not doc.url_pdf:
            # normas.url_pdf es NOT NULL — sin PDF no hay fila (BOE siempre lo trae)
            resumen.errores_pdf += 1
            continue
        try:
            hash_pdf = adapter.sha256_url(doc.url_pdf)
        except Exception as exc:  # noqa: BLE001 — un PDF roto no tumba la ingesta
            logger.warning("PDF %s falló: %s", doc.url_pdf, exc)
            resumen.errores_pdf += 1
            continue

        existe = session.execute(
            select(Norma.id).where(Norma.hash_sha256 == hash_pdf)
        ).scalar_one_or_none()
        if existe is not None:
            resumen.duplicados += 1
            continue

        session.add(Norma(
            titulo=doc.titulo,
            rango=adapter.rango or boletin.sigla,
            fecha_pub=doc.fecha,
            boletin_id=boletin.id,
            numero_boletin=doc.numero_boletin,
            url_pdf=doc.url_pdf,
            hash_sha256=hash_pdf,
        ))
        resumen.nuevos += 1

    boletin.ultimo_scrapeo = datetime.now(timezone.utc)
    session.commit()
    return resumen


def run_boletin(
    session: Session, sigla: str, fecha: date, limit: int | None = None
) -> ResumenIngesta:
    adapters = registrar_adapters()
    key = sigla.upper()
    if key not in adapters:
        raise ValueError(
            f"sin adaptador para {sigla}; disponibles: {sorted(adapters)}"
        )
    boletin = session.execute(
        select(Boletin).where(Boletin.sigla == key)
    ).scalar_one_or_none()
    if boletin is None:
        raise ValueError(f"el boletín {key} no existe en la tabla boletines — ejecuta el seed")

    adapter = adapters[key]()
    docs = adapter.fetch_day(fecha)
    return _persistir_documentos(session, boletin, adapter, docs, limit)


def run_dir3(session: Session, url: str | None = None) -> int:
    from app.config import settings

    url = url or settings().dir3_url
    unidades = Dir3Adapter(url).fetch()
    n = 0
    for u in unidades:
        existe = session.execute(
            select(Administracion.id).where(Administracion.nombre == u.nombre)
        ).scalar_one_or_none()
        if existe is not None:
            continue
        session.add(Administracion(
            nombre=u.nombre, tipo=u.tipo or "DIR3", nivel=u.nivel,
        ))
        n += 1
    session.commit()
    return n


def parse_boe_doc_xml(xml_text: str) -> dict:
    """Extrae metadatos del XML de un documento BOE
    (https://www.boe.es/diario_boe/xml.php?id=...)."""
    import xml.etree.ElementTree as ET

    root = ET.fromstring(xml_text)
    meta = root.find("metadatos")
    if meta is None:
        raise ValueError("BOE no devuelve metadatos")
    titulo = (meta.findtext("titulo") or "").strip()
    url_pdf = (meta.findtext("url_pdf") or "").strip()
    if not titulo or not url_pdf:
        raise ValueError("BOE sin titulo/url_pdf")
    fecha_pub = meta.findtext("fecha_publicacion") or ""
    return {
        "titulo": titulo,
        "url_pdf": url_pdf,
        "rango": (meta.findtext("rango") or "BOE").strip(),
        "diario_numero": meta.findtext("diario_numero") or None,
        "fecha_iso": (
            f"{fecha_pub[:4]}-{fecha_pub[4:6]}-{fecha_pub[6:8]}"
            if len(fecha_pub) == 8 else None
        ),
    }


def run_boe_norma(session: Session, identificador: str) -> dict:
    """Ingesta de una norma CONCRETA del BOE por identificador (ej. BOE-A-2022-5809).

    A diferencia del sumario diario, esto permite traer leyes específicas para
    los flujos normativos (Pilar 4) sin esperar al scrapeo cronológico.
    Fuente: https://www.boe.es/diario_boe/xml.php?id=<identificador>
    """
    import re

    import httpx
    from sqlalchemy import select

    from scrapers.base import DEFAULT_HEADERS

    identificador = identificador.strip().upper()
    if not re.fullmatch(r"BOE-[A-Z]-\d{4}-\d+", identificador):
        raise ValueError(f"identificador BOE no válido: {identificador}")

    with httpx.Client(
        headers={**DEFAULT_HEADERS, "Accept": "application/xml"},
        follow_redirects=True, timeout=60,
    ) as client:
        resp = client.get(
            f"https://www.boe.es/diario_boe/xml.php?id={identificador}"
        )
        resp.raise_for_status()
        doc = parse_boe_doc_xml(resp.text)

        resp_pdf = client.get(doc["url_pdf"])
        resp_pdf.raise_for_status()
        import hashlib

        hash_pdf = hashlib.sha256(resp_pdf.content).hexdigest()

    existe = session.execute(
        select(Norma.id).where(Norma.hash_sha256 == hash_pdf)
    ).scalar_one_or_none()
    if existe is not None:
        return {"identificador": identificador, "norma_id": existe, "nueva": False}

    from datetime import date as _date

    boletin = session.execute(
        select(Boletin).where(Boletin.sigla == "BOE")
    ).scalar_one_or_none()
    norma = Norma(
        titulo=doc["titulo"], rango=doc["rango"],
        fecha_pub=_date.fromisoformat(doc["fecha_iso"]) if doc["fecha_iso"] else None,
        boletin_id=boletin.id if boletin else None,
        numero_boletin=doc["diario_numero"], url_pdf=doc["url_pdf"],
        hash_sha256=hash_pdf,
    )
    session.add(norma)
    session.commit()
    return {
        "identificador": identificador, "norma_id": norma.id, "nueva": True,
        "titulo": doc["titulo"],
    }


def run_dir3_xlsx(session: Session, path: str) -> dict:
    """Ingesta del listado XLSX del CTT (Unidades EELL/CCAA/AGE).

    Upsert por codigo_dir3. Filas geocodificadas previamente (municipios sin
    código) no se tocan: solo se les rellena el código si coincide el nombre
    exacto 'Ayuntamiento de X'.
    """
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from scrapers.dir3 import parse_unidades_xlsx

    unidades = parse_unidades_xlsx(path)
    n = 0
    for u in unidades:
        stmt = (
            pg_insert(Administracion)
            .values(
                nombre=u.nombre, tipo=u.tipo or "DIR3", nivel=u.nivel,
                codigo_dir3=u.codigo, codigo_padre=u.padre,
                entidad_tipo=u.tipo, provincia=u.provincia,
            )
            .on_conflict_do_update(
                index_elements=[Administracion.codigo_dir3],
                set_={
                    "nombre": u.nombre, "tipo": u.tipo or "DIR3",
                    "nivel": u.nivel, "codigo_padre": u.padre,
                    "entidad_tipo": u.tipo, "provincia": u.provincia,
                },
            )
        )
        session.execute(stmt)
        n += 1
    session.commit()
    return {
        "fichero": path,
        "unidades_leidas": len(unidades),
        "upserts": n,
    }
