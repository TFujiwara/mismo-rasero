"""Adaptador DOE — Diario Oficial de Extremadura (juntaex.es).

Verificado en vivo (nov. 2026): el portal expone RSS por sección
(https://doe.juntaex.es/rss/rss.php?seccion=1..4) cuyos items traen el título
oficial, el PDF directo (http://doe.juntaex.es/pdfs/doe/...) y la fecha.
Solo cubre los documentos recientes — como DOGV, ingesta diaria.

Secciones: 1 Disposiciones generales-regionales, 2 Autoridades y personal,
3 Otras disposiciones, 4 Administración local (aprox. — el título del canal manda).
"""

from __future__ import annotations

import re
from datetime import date, datetime

import feedparser
import httpx

from scrapers.base import BoletinAdapter, DEFAULT_HEADERS, Documento

FEEDS = [f"https://doe.juntaex.es/rss/rss.php?seccion={i}" for i in range(1, 5)]


class DoeAdapter(BoletinAdapter):
    sigla = "DOE"
    rango = "DOE"

    def fetch_day(self, fecha: date) -> list[Documento]:
        docs: list[Documento] = []
        vistos: set[str] = set()
        with httpx.Client(
            headers={**DEFAULT_HEADERS, "Accept": "application/rss+xml"},
            follow_redirects=True, timeout=60,
        ) as client:
            for feed_url in FEEDS:
                resp = client.get(feed_url)
                resp.raise_for_status()
                feed = feedparser.parse(resp.text)
                seccion = feed.feed.get("title", "")
                for entry in feed.entries:
                    enlace = getattr(entry, "link", "")
                    if not enlace or enlace in vistos:
                        continue
                    pub = getattr(entry, "published", "") or ""
                    m = re.search(r"\d{4}-\d{2}-\d{2}", pub)
                    fecha_item = (
                        datetime.strptime(m.group(0), "%Y-%m-%d").date()
                        if m else None
                    )
                    # el feed trae lo reciente; filtra al día pedido
                    if fecha_item and fecha_item != fecha:
                        continue
                    vistos.add(enlace)
                    # identificador del PDF: .../pdfs/doe/2026/2110o/26040225.pdf
                    m_id = re.search(r"/(\d{6,12})\.pdf", enlace)
                    identificador = m_id.group(1) if m_id else enlace
                    titulo = (getattr(entry, "title", "") or "").strip()
                    if not titulo:
                        continue
                    docs.append(Documento(
                        identificador=identificador,
                        titulo=titulo,
                        fecha=fecha_item or fecha,
                        url_pdf=enlace,
                        seccion=seccion,
                        extra={"seccion_feed": feed_url},
                    ))
        return docs
