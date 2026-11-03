"""Adaptador DOG — Diario Oficial de Galicia (xunta.gal).

Verificado en vivo (nov. 2026): el DOG publica RSS por secciones y un feed de
sumario con TODAS las disposiciones del día:
  https://www.xunta.gal/diario-oficial-galicia/rss/Sumario_es.rss  (castellano)
  .../rss/Sumario_gl.rss                                           (gallego)
Cada item: título oficial, enlace a la página del documento
(/dog/Publicados/.../AnuncioG..._es.html) y fecha. El PDF se extrae de la
página (segundo paso, como BOCM).

Solo cubre los días recientes — ingesta diaria (cron).
"""

from __future__ import annotations

import re
from datetime import date, datetime

import feedparser
import httpx

from scrapers.base import BoletinAdapter, DEFAULT_HEADERS, Documento

FEED_SUMARIO = "https://www.xunta.gal/diario-oficial-galicia/rss/Sumario_es.rss"
BASE = "https://www.xunta.gal"


class DogAdapter(BoletinAdapter):
    sigla = "DOG"
    rango = "DOG"

    def fetch_day(self, fecha: date) -> list[Documento]:
        docs: list[Documento] = []
        with httpx.Client(
            headers={**DEFAULT_HEADERS, "Accept": "application/rss+xml"},
            follow_redirects=True, timeout=60,
        ) as client:
            r = client.get(FEED_SUMARIO)
            r.raise_for_status()
            feed = feedparser.parse(r.text)

            for entry in feed.entries:
                enlace = getattr(entry, "link", "")
                pub = getattr(entry, "published", "") or ""
                m = re.search(r"\d{1,2} \w{3} \d{4}", pub)
                fecha_item = (
                    datetime.strptime(m.group(0), "%d %b %Y").date() if m else None
                )
                if fecha_item and fecha_item != fecha:
                    continue
                titulo = (getattr(entry, "title", "") or "").strip()
                if not enlace or not titulo:
                    continue

                # página del documento → enlace PDF
                r_pag = client.get(enlace)
                url_pdf = None
                if r_pag.status_code == 200:
                    mp = re.search(r'href="([^"]*\.pdf[^"]*)"', r_pag.text, re.I)
                    if mp:
                        url_pdf = mp.group(1)
                        if url_pdf.startswith("/"):
                            url_pdf = BASE + url_pdf
                identificador = enlace.rstrip("/").rsplit("/", 1)[-1].replace(
                    "_es.html", ""
                )
                docs.append(Documento(
                    identificador=identificador,
                    titulo=titulo,
                    fecha=fecha_item or fecha,
                    url_pdf=url_pdf or enlace,  # sin PDF en la página, la fuente citada es su página oficial
                    seccion="DOG",
                    extra={"pagina": enlace},
                ))
        return docs
