"""Pilar 4 — flujo normativo DOUE → BOE → DOGV → BOP (§04).

El ejemplo canónico del blueprint: Directiva (UE) 2019/904 (plásticos de un
solo uso) → Ley 7/2022 (residuos) → desarrollo DOGV → ordenanza BOP. Los nodos
que aún no estén localizados quedan NULL en flujo_normativo y el timeline los
muestra como "pendiente" — se declara, no se inventa.

Nota sobre el hash del nodo DOUE: si EUR-Lex bloquea la descarga del PDF
(soft-block 202 verificado), se almacena sha256("DOUE:<celex>") como clave
estable y timeline_json lo declara explícitamente.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from sqlalchemy import select

from app.models import FlujoNormativo, Norma

if TYPE_CHECKING:  # pragma: no cover
    from sqlalchemy.orm import Session

EJEMPLO = {
    "doue": {
        "celex": "32019L0904",
        "titulo": "Directiva (UE) 2019/904, sobre plásticos de un solo uso",
        "url": "https://eur-lex.europa.eu/eli/dir/2019/904/oj",
        "fecha": "2019-06-05",
    },
    "boe": "BOE-A-2022-5809",
    "descripcion": "Plásticos de un solo uso: la directiva que acabará en la "
    "tasa de basura de tu municipio",
}


def _hash_doue(celex: str) -> str:
    return hashlib.sha256(f"DOUE:{celex}".encode()).hexdigest()


def seed_flujo_ejemplo(session: "Session") -> dict:
    """Crea (si no existen) las normas DOUE + BOE del ejemplo canónico y las
    enlaza en flujo_normativo. DOGV y BOP quedan pendientes de localizar."""
    from datetime import date

    doue_hash = _hash_doue(EJEMPLO["doue"]["celex"])
    doue = session.execute(
        select(Norma).where(Norma.hash_sha256 == doue_hash)
    ).scalar_one_or_none()
    if doue is None:
        doue = Norma(
            titulo=EJEMPLO["doue"]["titulo"],
            rango="DOUE",
            fecha_pub=date.fromisoformat(EJEMPLO["doue"]["fecha"]),
            url_pdf=EJEMPLO["doue"]["url"],
            hash_sha256=doue_hash,
        )
        session.add(doue)
        session.flush()

    from app.services.ingest import run_boe_norma

    resultado_boe = run_boe_norma(session, EJEMPLO["boe"])
    boe_norma = session.get(Norma, resultado_boe["norma_id"])

    flujo = session.execute(
        select(FlujoNormativo).where(
            (FlujoNormativo.doue_url == EJEMPLO["doue"]["url"])
            & (FlujoNormativo.boe_transposicion_id == boe_norma.id)
        )
    ).scalar_one_or_none()
    if flujo is None:
        flujo = FlujoNormativo(
            doue_url=EJEMPLO["doue"]["url"],
            boe_transposicion_id=boe_norma.id,
            dogv_desarrollo_id=None,
            bop_ordenanza_id=None,
            timeline_json={
                "tema": EJEMPLO["descripcion"],
                "nodos": [
                    {"paso": "DOUE", "estado": "ok",
                     "nota": "Directiva (UE) 2019/904 — hash declarado como "
                     "sha256('DOUE:celex'); EUR-Lex bloquea la descarga "
                     "automatizada de PDFs (soft-block 202)"},
                    {"paso": "BOE", "estado": "ok",
                     "nota": f"Transposición: {boe_norma.titulo}"},
                    {"paso": "DOGV", "estado": "pendiente",
                     "nota": "Desarrollo autonómico por localizar (requiere "
                     "búsqueda en el índice DOGV con Playwright)"},
                    {"paso": "BOP", "estado": "pendiente",
                     "nota": "Ordenanza municipal (tasa de basura) por "
                     "localizar en los BOPs de la provincia"},
                ],
                "anos_transcurridos": "2019 → 2022+ : por eso tarda 3-5 años (§04)",
            },
        )
        session.add(flujo)
    session.commit()
    return {
        "flujo_id": flujo.id,
        "doue_norma_id": doue.id,
        "boe_norma_id": boe_norma.id,
        "boe_nuevo": resultado_boe["nueva"],
    }


def timeline_de_norma(session: "Session", norma_id: int) -> dict | None:
    """Devuelve el flujo normativo en el que participa una norma, con su
    timeline completo (los 4 pasos, ok o pendiente)."""
    from sqlalchemy import or_

    flujo = session.execute(
        select(FlujoNormativo).where(
            or_(
                FlujoNormativo.boe_transposicion_id == norma_id,
                FlujoNormativo.dogv_desarrollo_id == norma_id,
                FlujoNormativo.bop_ordenanza_id == norma_id,
            )
        )
    ).scalar_one_or_none()
    if flujo is None:
        return None

    nodos = []
    for paso, norma_id_en_flujo, url in (
        ("DOUE", None, flujo.doue_url),
        ("BOE", flujo.boe_transposicion_id, None),
        ("DOGV", flujo.dogv_desarrollo_id, None),
        ("BOP", flujo.bop_ordenanza_id, None),
    ):
        if paso == "DOUE":
            nodos.append({"paso": paso, "estado": "ok" if url else "pendiente",
                          "norma_id": None, "url": url})
        else:
            nodos.append({
                "paso": paso,
                "estado": "ok" if norma_id_en_flujo else "pendiente",
                "norma_id": norma_id_en_flujo, "url": None,
            })

    return {
        "flujo_id": flujo.id,
        "tema": (flujo.timeline_json or {}).get("tema"),
        "nodos": nodos,
        "timeline": flujo.timeline_json,
    }
