"""Adaptador BOJA — API pública de la Junta de Andalucía (datos.juntadeandalucia.es).

Verificado en vivo (nov. 2026) contra la especificación OpenAPI oficial:
  https://datos.juntadeandalucia.es/api/v0/boja/openapi.json

Flujo:
  1. GET /get/calendar?year=AÑO        → pares (número, fecha) publicados;
     los números 5xx/200xxx+ son especiales/anexos — el número diario es el menor.
  2. GET /get/bulletin?year=AÑO&number=N → todas las disposiciones del número,
     con título (summaryNoHtml), sección, organismo y PDF (pdf[0].publicUrl).

Descubierta vía el buscador de APIs de datosabiertos: el blueprint §13 daba
RSS, la realidad es una API tabular mucho mejor.
"""

from __future__ import annotations

import logging
from datetime import date

import httpx

from scrapers.base import BoletinAdapter, DEFAULT_HEADERS, Documento

logger = logging.getLogger(__name__)

API = "https://datos.juntadeandalucia.es/api/v0/boja"


class BojaAdapter(BoletinAdapter):
    sigla = "BOJA"
    rango = "BOJA"

    def __init__(self):
        self.client = httpx.Client(
            headers={**DEFAULT_HEADERS, "Accept": "application/json"},
            follow_redirects=True,
            timeout=120,
        )

    def close(self) -> None:
        if getattr(self, "client", None):
            self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _get(self, ruta: str, params: dict) -> dict:
        resp = self.client.get(f"{API}/{ruta}", params=params)
        resp.raise_for_status()
        return resp.json()

    def fetch_day(self, fecha: date) -> list[Documento]:
        with self:
            cal = self._get("get/calendar", {"year": fecha.year})
            por_fecha: dict[str, list[int]] = {}
            for num, f in cal.get("rows", []):
                por_fecha.setdefault(f, []).append(int(num))
            destino = fecha.strftime("%d/%m/%Y")
            numeros = por_fecha.get(destino, [])
            if not numeros:
                return []  # día sin publicación
            numero = min(numeros)  # el menor = número diario regular

            data = self._get("get/bulletin",
                             {"year": fecha.year, "number": numero})

        docs: list[Documento] = []
        for fila in data.get("results", []):
            pdfs = fila.get("pdf") or []
            url_pdf = pdfs[0].get("publicUrl") if pdfs else None
            titulo = (fila.get("summaryNoHtml") or "").strip()
            if not url_pdf or not titulo:
                continue
            docs.append(Documento(
                identificador=str(fila.get("id") or ""),
                titulo=titulo,
                fecha=fecha,
                url_pdf=url_pdf,
                seccion=fila.get("titleSec"),
                departamento=fila.get("organisation"),
                numero_boletin=str(fila.get("number") or numero),
                extra={"tipo": fila.get("type"),
                       "disposicion": fila.get("dispositionNumber")},
            ))
        return docs
