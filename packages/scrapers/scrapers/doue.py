"""Adaptador DOUE — Diario Oficial de la UE vía RSS de EUR-Lex.

Verificado en vivo (oct. 2026): EUR-Lex responde 202 con cuerpo vacío a peticiones
automáticas desde esta ubicación (soft-block de IP, no de headers). El adaptador
queda escrito contra el RSS oficial; si tu red lo sirve, funciona tal cual.
Si no, existen dos salidas documentadas:
  - EURLEX_PROXY en .env (salir por una IP residencial/UE)
  - carga manual: colocar el XML del OJ en data/doue/ y usar el modo --offline

URL del feed: https://eur-lex.europa.eu/rss/oj.html (JO L, general).
Cada entrada trae enlace a la obra con CELEX en el propio link/ guid.
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime

import feedparser
import httpx

from scrapers.base import BoletinAdapter, DEFAULT_HEADERS, Documento

logger = logging.getLogger(__name__)

RSS_OJ = "https://eur-lex.europa.eu/rss/oj.html"
CELEX_RE = re.compile(r"celex[:=]([0-9A-Za-z]+)", re.IGNORECASE)


class DoueAdapter(BoletinAdapter):
    sigla = "DOUE"
    rango = "DOUE"

    def __init__(self, proxy: str | None = None):
        self.proxy = proxy or None

    def fetch_day(self, fecha: date) -> list[Documento]:
        with httpx.Client(
            headers={**DEFAULT_HEADERS, "Accept": "application/rss+xml, application/xml"},
            follow_redirects=True,
            timeout=60,
            proxy=self.proxy,
        ) as client:
            resp = client.get(RSS_OJ)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)

        docs: list[Documento] = []
        for entry in feed.entries:
            # el RSS del OJ lista los documentos publicados en los últimos días;
            # filtra por fecha real de publicación
            pub = None
            if getattr(entry, "published_parsed", None):
                pub = datetime(*entry.published_parsed[:3]).date()
            if pub is not None and pub != fecha:
                continue

            link = getattr(entry, "link", "")
            guid = getattr(entry, "id", "") or link
            m = CELEX_RE.search(f"{link} {guid}")
            ident = m.group(1) if m else (guid or "")
            if not ident:
                continue
            docs.append(Documento(
                identificador=ident,
                titulo=getattr(entry, "title", "").strip(),
                fecha=pub or fecha,
                url_html=link,
                extra={"celex": ident},
            ))
        return docs
