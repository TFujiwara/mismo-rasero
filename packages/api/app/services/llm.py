"""Seam LLM para la extracción del SUJETO de una frase (Fase 4).

REGLA DURA (§06/§11): el LLM nunca emite el veredicto — solo ayuda a extraer
qué nivel administrativo menciona la frase cuando la detección regex no llega.
Su salida entra en la MISMA regla de veredicto que la detección determinista.
Sin LLM_API_KEY configurado, el motor funciona 100% determinista.

Interfaz OpenAI-compatible (chat/completions): OpenAI, Groq, Together,
Ollama (con /v1), vLLM, LM Studio…
"""

from __future__ import annotations

import json
import logging

import httpx

from app.config import settings
from app.services.niveles import NOMBRE_NIVEL, UE, ESTADO, CCAA, PROVINCIA, LOCAL
from app.services.verificar import normaliza

logger = logging.getLogger(__name__)

VALIDOS = {normaliza(k): k for k in (UE, ESTADO, CCAA, PROVINCIA, LOCAL)}

PROMPT = (
    "¿Qué niveles de la administración española menciona o implica esta frase? "
    "Niveles posibles: UE, Estado, CCAA, Provincia, Local. "
    "Responde SOLO con una lista JSON, ej: [\"Estado\"]. Frase: {texto}"
)


def llm_disponible() -> bool:
    return bool(settings().llm_base_url and settings().llm_api_key)


def extraer_niveles_con_llm(texto: str) -> list[str] | None:
    """Niveles detectados por el LLM, validados contra el catálogo. Cualquier
    fallo → None (el motor determinista sigue)."""
    if not llm_disponible():
        return None
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{settings().llm_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {settings().llm_api_key}"},
                json={
                    "model": settings().llm_model or "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "Eres un extractor de datos. "
                         "Responde exclusivamente JSON válido."},
                        {"role": "user", "content": PROMPT.format(texto=texto)},
                    ],
                    "temperature": 0,
                },
            )
            resp.raise_for_status()
            contenido = resp.json()["choices"][0]["message"]["content"]

        lista = json.loads(re_search_json(contenido))
        niveles = [VALIDOS[normaliza(str(x))] for x in lista
                   if normaliza(str(x)) in VALIDOS]
        return niveles or None
    except Exception as exc:  # noqa: BLE001 — el LLM es opcional, nunca bloquea
        logger.warning("LLM extractor falló (se continúa determinista): %s", exc)
        return None


def re_search_json(texto: str) -> str:
    """Extrae la primera lista JSON de una respuesta (tolera ```json fences)."""
    import re

    m = re.search(r"\[.*\]", texto, re.S)
    return m.group(0) if m else texto
