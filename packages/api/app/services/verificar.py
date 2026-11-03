"""Motor de verificación competencial — Pilar 6, versión determinista.

Match de la frase del usuario contra palabras_clave de competencias (GIN en la
API, mismo criterio aquí). El LLM de Fase 4 sustituirá el matching por
extracción semántica; el contrato de salida no cambia:
  {texto, matches: [{nombre, descripcion_llana, cadena, articulo_legal,
   fuente_url, palabra_disparadora}], nota}

Este módulo es el seam que el paquete de vídeo importa (video.ingest) y que
el servidor MCP reutiliza — un solo motor, sin ramas por actor (§11).
"""

from __future__ import annotations

import re
import unicodedata
from typing import TYPE_CHECKING, Iterable

import sqlalchemy as sa

if TYPE_CHECKING:  # pragma: no cover
    from sqlalchemy.orm import Session

    from app.models import Competencia


def normaliza(texto: str) -> str:
    """Minúsculas sin tildes ni símbolos — 'socavón' == 'socavon' == 'SOCAVON'."""
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def match_competencias(
    texto: str, competencias: Iterable["Competencia"]
) -> list[dict]:
    """Matching puro (sin BD) — testeable."""
    texto_norm = normaliza(texto)
    matches = []
    for c in competencias:
        disparador = None
        for kw in (c.palabras_clave or []):
            kw_norm = normaliza(kw)
            if kw_norm and kw_norm in texto_norm:
                if disparador is None or len(kw) > len(disparador):
                    disparador = kw
        if disparador is None and c.nombre and normaliza(c.nombre) in texto_norm:
            disparador = c.nombre
        if disparador:
            cadena = [
                tramo.strip()
                for tramo in (c.descripcion_tecnica or "").split("->")
                if tramo.strip()
            ]
            matches.append({
                "id": c.id, "nombre": c.nombre, "slug": c.slug,
                "descripcion_llana": c.descripcion_llana,
                "cadena": cadena,
                "articulo_legal": c.articulo_legal,
                "fuente_url": c.fuente_url,
                "palabra_disparadora": disparador,
            })
    # el término más específico primero (más largo = más concreto)
    matches.sort(key=lambda m: -len(m["palabra_disparadora"]))
    return matches


NOTA_CON_MATCH = (
    "El veredicto lo decide una regla contra la cadena competencial (§06) — no "
    "un modelo. La detección del sujeto es determinista y, si hay LLM "
    "configurado, asistida para frases difíciles."
)

NOTA_SIN_MATCH = (
    "No encuentro ese tema en el índice de competencias todavía. El índice "
    "crece con la Fase 2 (competencias completas UE → Estado → CCAA → Local)."
)


def verificar_competencial(texto: str, session: "Session | None" = None) -> dict:
    """Verifica una frase contra el índice de competencias.

    session es opcional: sin ella abre su propia sesión (seam para el paquete
    de vídeo, que llama con un solo argumento).
    """
    if session is None:
        from app.db import SessionLocal

        with SessionLocal() as own:
            return verificar_competencial(texto, session=own)

    from app.models import Competencia
    from app.services.niveles import (
        NIVELES_COMPETENTES,
        detectar_nivel,
        veredicto_competencial,
    )

    rows = session.execute(sa.select(Competencia)).scalars().all()
    matches = match_competencias(texto, rows)

    # el sujeto de la frase: regex primero; LLM (si está configurado) de apoyo
    mencionados = detectar_nivel(texto)
    via_llm = False
    if not mencionados:
        from app.services.llm import extraer_niveles_con_llm

        niveles_llm = extraer_niveles_con_llm(texto)
        if niveles_llm:
            mencionados, via_llm = niveles_llm, True

    for m in matches:
        v = veredicto_competencial(m["slug"], texto, niveles_override=mencionados)
        m["veredicto"] = v["veredicto"]
        m["razon"] = v["razon"]
        m["niveles_competentes"] = NIVELES_COMPETENTES.get(m["slug"], [])
        m["nivel_mencionado"] = mencionados
    if matches and via_llm:
        for m in matches:
            m["sujeto_via"] = "llm"

    return {
        "texto": texto,
        "matches": matches,
        "nota": NOTA_CON_MATCH if matches else NOTA_SIN_MATCH,
    }
