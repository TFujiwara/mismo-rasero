"""Adaptador BOCM — Boletín Oficial de la Comunidad de Madrid.

Verificado en vivo (nov. 2026): el portal expone RSS real
(https://www.bocm.es/ultimo-boletin.xml — órdenes del último boletín) y cada
documento tiene un XML espejo con los metadatos completos (mismo patrón que
el BOE): /boletin/CM_*/YYYY/MM/DD/BOCM-YYYYMMDD-N.xml con titulo, departamento,
seccion, url_pdf.

Solo el ÚLTIMO boletín (como DOGV) — ingesta diaria. ~96 documentos/número,
4 peticiones por documento (feed → página → XML → PDF).
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import date, datetime

import feedparser
import httpx

from scrapers.base import BoletinAdapter, DEFAULT_HEADERS, Documento

FEED_ULTIMO = "https://www.bocm.es/ultimo-boletin.xml"


class BocmAdapter(BoletinAdapter):
    sigla = "BOCM"
    rango = "BOCM"

    def __init__(self):
        self.client = httpx.Client(
            headers={**DEFAULT_HEADERS, "Accept": "application/rss+xml, application/xml"},
            follow_redirects=True,
            timeout=60,
        )

    def close(self) -> None:
        if getattr(self, "client", None):
            self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def fetch_day(self, fecha: date) -> list[Documento]:
        with self:
            resp = self.client.get(FEED_ULTIMO)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)

            # fecha del último boletín: la del primer item
            if not feed.entries:
                return []
            pub = feed.entries[0].get("published", "")
            m = re.search(r"\d{2} \w{3} \d{4}", pub)
            fecha_boletin = (
                datetime.strptime(m.group(0), "%d %b %Y").date() if m else None
            )
            if fecha_boletin and fecha_boletin != fecha:
                raise RuntimeError(
                    f"el BOCM solo expone el último boletín ({fecha_boletin}); "
                    f"pediste {fecha}. Ejecuta la ingesta diaria."
                )

            docs: list[Documento] = []
            for entry in feed.entries:
                enlace = getattr(entry, "link", "")
                if not enlace:
                    continue
                doc = self._documento_de_pagina(enlace, fecha)
                if doc:
                    docs.append(doc)
        return docs

    def _documento_de_pagina(self, url_pagina: str, fecha: date) -> Documento | None:
        r = self.client.get(url_pagina)
        if r.status_code != 200:
            return None
        m = re.search(r'href="(/boletin/[^"]*\.xml)"', r.text)
        if not m:
            return None
        r_xml = self.client.get("https://www.bocm.es" + m.group(1))
        if r_xml.status_code != 200:
            return None
        try:
            root = ET.fromstring(r_xml.content)
        except ET.ParseError:
            return None
        meta = root.find("metadatos")
        if meta is None:
            return None

        def _t(campo: str) -> str:
            return (meta.findtext(campo) or "").strip()

        titulo = _t("titulo")
        url_pdf = _t("url_pdf")
        if not titulo or not url_pdf:
            return None
        fecha_pub = _t("fecha_publicacion")
        try:
            fecha_doc = (
                datetime.strptime(fecha_pub, "%Y/%m/%d").date()
                if fecha_pub else fecha
            )
        except ValueError:
            fecha_doc = fecha

        return Documento(
            identificador=_t("identificador") or url_pagina.rsplit("-", 1)[-1],
            titulo=titulo,
            fecha=fecha_doc,
            url_pdf=url_pdf,
            seccion=_t("seccion"),
            departamento=_t("departamento"),
            numero_boletin=_t("diario_numero"),
            extra={"origen": _t("origen_legislativo")},
        )
