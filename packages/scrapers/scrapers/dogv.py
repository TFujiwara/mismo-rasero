"""Adaptador DOGV — API interna del portal (sin Playwright).

Verificado en vivo (oct. 2026): el portal del DOGV es una SPA Angular cuya
config declara el backend en https://dogv.gva.es/dogv-portal. Endpoints
reales (extraídos del bundle de la SPA y probados):

  GET /dogv-portal/dogv/latest?lang=es_es
      → sumario completo: cabecera (numeroDogv, fecha) + disposiciones
        (id, titulo, seccion, organismo, codigoInsercion, urlPdf relativa)
  GET /dogv-portal/dogv/calendar?startDate=YYYY-MM-DD&endDate=YYYY-MM-DD
      → días publicados (esBis = bis)
  PDF de cada disposición: https://dogv.gva.es{urlPdf}
      (patrón /datos/YYYY/MM/DD/pdf/YYYY_NNNNNN_es.pdf, confirmado en robots.txt)

Limitación: la API solo expone el ÚLTIMO número (el parámetro fecha se
ignora) — para fechas pasadas sirve el cron diario. Requiere la cabecera
Referer del propio portal o responde 403.
"""

from __future__ import annotations

import logging
from datetime import date

import httpx

from scrapers.base import BoletinAdapter, DEFAULT_HEADERS, Documento

logger = logging.getLogger(__name__)

API_LATEST = "https://dogv.gva.es/dogv-portal/dogv/latest?lang=es_es"
REFERER = "https://dogv.gva.es/dogv-portal-frontend/es"
BASE_PDF = "https://dogv.gva.es"


class DogvAdapter(BoletinAdapter):
    sigla = "DOGV"
    rango = "DOGV"

    def _cabecera_y_disposiciones(self) -> tuple[dict, list[dict]]:
        with httpx.Client(
            headers={
                **DEFAULT_HEADERS,
                "Accept": "application/json",
                "Referer": REFERER,
            },
            follow_redirects=True,
            timeout=60,
        ) as client:
            resp = client.get(API_LATEST)
            resp.raise_for_status()
            data = resp.json()
        return data.get("cabecera", {}), data.get("disposiciones", [])

    def fetch_day(self, fecha: date) -> list[Documento]:
        cabecera, disposiciones = self._cabecera_y_disposiciones()

        # la API solo expone el último número: verificamos que el día pedido
        # sea el del último DOGV y, si no, error claro (no datos equivocados)
        fecha_num = self._parse_fecha_cabecera(cabecera.get("fecha", ""))
        if fecha_num and fecha_num != fecha:
            raise RuntimeError(
                f"la API del DOGV solo expone el último número ({fecha_num}); "
                f"pediste {fecha}. Ejecuta la ingesta diaria del último DOGV."
            )

        docs: list[Documento] = []
        for disp in disposiciones:
            url_pdf_rel = disp.get("urlPdf") or ""
            if not url_pdf_rel:
                continue
            docs.append(Documento(
                identificador=str(disp.get("codigoInsercion") or disp["id"]),
                titulo=(disp.get("titulo") or "").strip(),
                fecha=fecha,
                url_pdf=BASE_PDF + url_pdf_rel,
                seccion=(disp.get("seccion") or {}).get("descripcion"),
                departamento=disp.get("organismo"),
                numero_boletin=str(cabecera.get("numeroDogv") or ""),
                extra={"id_dogv": disp.get("id")},
            ))
        return docs

    @staticmethod
    def _parse_fecha_cabecera(texto: str) -> date | None:
        # 'Miércoles, 28 de octubre de 2026' → 2026-10-28
        MESES = {
            "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5,
            "junio": 6, "julio": 7, "agosto": 8, "septiembre": 9,
            "octubre": 10, "noviembre": 11, "diciembre": 12,
        }
        partes = (texto or "").lower().replace("de ", " ").split()
        numeros = [p for p in partes if p.isdigit()]
        meses = [MESES[p] for p in partes if p in MESES]
        if len(numeros) >= 2 and meses:
            return date(int(numeros[1]), meses[0], int(numeros[0]))
        return None
