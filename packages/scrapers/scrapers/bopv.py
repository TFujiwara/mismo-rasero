"""Adaptador BOPV — API REST oficial de Euskadi (api.euskadi.eus).

Documentación: OpenAPI v0.0.1 (spec proporcionada por el operador, nov. 2026):
  https://api.euskadi.eus/bopv/administrative-acts[/{year}[/{month}[/{numOrder}]]]
  params: lang=SPANISH|BASQUE, itemsOfPage (def. 10 — subir), currentPage (1-based)

Trampas conocidas (documentadas por el operador):
  - {month} SIN cero a la izquierda (10 ok, 5 no 05).
  - startDate/endDate NO funcionan: se ignoran y devuelven 2003 — filtrar por
    año/mes en la ruta y por publishDate en memoria.
  - La API va un día por detrás del portal: para el cron, ingesta de AYER.
  - 401/406 posibles por WAF.

Campos del item: id ("2026/10/4272"), name, numBulletin, publishDate, section,
department/issuingBody, downloadable[] (PDF por format o url .pdf), state,
isErrorCorrection, _links.
"""

from __future__ import annotations

import logging
from datetime import date

import httpx

from scrapers.base import BoletinAdapter, DEFAULT_HEADERS, Documento

logger = logging.getLogger(__name__)

API = "https://api.euskadi.eus/bopv/administrative-acts"
ITEMS_POR_PAGINA = 100


class BopvAdapter(BoletinAdapter):
    sigla = "BOPV"
    rango = "BOPV"

    def fetch_day(self, fecha: date) -> list[Documento]:
        # mes SIN cero a la izquierda — la spec lo exige así
        year, month = fecha.year, fecha.month
        docs: list[Documento] = []
        page = 1
        total_pages = 1

        with httpx.Client(
            headers={**DEFAULT_HEADERS, "Accept": "application/json"},
            follow_redirects=True, timeout=90,
        ) as client:
            while page <= total_pages:
                resp = client.get(
                    f"{API}/{year}/{month}",
                    params={
                        "lang": "SPANISH",
                        "itemsOfPage": ITEMS_POR_PAGINA,
                        "currentPage": page,
                    },
                )
                if resp.status_code in (401, 406):
                    raise RuntimeError(
                        f"BOPV devolvió {resp.status_code} (WAF) — reintentar más tarde"
                    )
                resp.raise_for_status()
                data = resp.json()
                total_pages = int(data.get("totalPages") or 1)
                for item in data.get("items", []):
                    doc = self._a_documento(item, fecha)
                    if doc:
                        docs.append(doc)
                page += 1

        # la API cubre el mes completo: filtra al día pedido
        return [d for d in docs if d.fecha == fecha]

    def _a_documento(self, item: dict, fecha: date) -> Documento | None:
        nombre = (item.get("name") or "").strip()
        if not nombre:
            return None
        # PDF: downloadable[] — el que acabe en .pdf (o format lo indique)
        url_pdf = None
        for descarga in item.get("downloadable") or []:
            url = (descarga.get("url") or "").strip()
            if url.lower().endswith(".pdf") or (descarga.get("format") or "").lower() == "pdf":
                url_pdf = url
                break
        if not url_pdf:
            return None
        if url_pdf.startswith("/"):
            url_pdf = "https://api.euskadi.eus" + url_pdf

        # publishDate viene en UTC ('2026-09-30T22:00:00Z' = 1 de octubre en
        # España) — convertir a hora peninsular o el filtro de día come datos
        publish = (item.get("publishDate") or "").strip()
        fecha_pub = fecha
        if publish:
            try:
                from datetime import datetime, timezone
                from zoneinfo import ZoneInfo

                dt = datetime.fromisoformat(publish.replace("Z", "+00:00"))
                fecha_pub = dt.astimezone(ZoneInfo("Europe/Madrid")).date()
            except ValueError:
                pass

        return Documento(
            identificador=str(item.get("id") or ""),
            titulo=nombre,
            fecha=fecha_pub,
            url_pdf=url_pdf,
            seccion=item.get("section"),
            departamento=item.get("department") or item.get("issuingBody"),
            numero_boletin=str(item.get("numBulletin") or ""),
            extra={"state": item.get("state"),
                   "es_correccion": item.get("isErrorCorrection")},
        )
