"""Adaptador BOE — API de datos abiertos, verificada en vivo (blueprint §13).

GET https://www.boe.es/datosabiertos/api/boe/sumario/YYYYMMDD
con cabecera `Accept: application/xml` (sin ella responde 400).

Estructura: response > data > sumario > diario[numero] > seccion[nombre]
> departamento[nombre] > epigrafe[nombre] > item{identificador, titulo,
url_pdf, url_html, url_xml}.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from datetime import date

import httpx

from scrapers.base import BoletinAdapter, DEFAULT_HEADERS, Documento

logger = logging.getLogger(__name__)

SUMARIO_URL = "https://www.boe.es/datosabiertos/api/boe/sumario/{fecha:%Y%m%d}"


class BoeAdapter(BoletinAdapter):
    sigla = "BOE"
    rango = "BOE"

    def fetch_day(self, fecha: date) -> list[Documento]:
        docs: list[Documento] = []
        with httpx.Client(
            headers={**DEFAULT_HEADERS, "Accept": "application/xml"},
            follow_redirects=True,
            timeout=60,
        ) as client:
            resp = client.get(SUMARIO_URL.format(fecha=fecha))
            if resp.status_code == 404:
                # día sin publicación (fines de semana/festivos)
                return []
            resp.raise_for_status()
            root = ET.fromstring(resp.text)

            status = root.findtext("status/code")
            if status != "200":
                raise RuntimeError(f"BOE API status {status}: {resp.text[:200]}")

            diario = root.find("data/sumario/diario")
            if diario is None:
                return []
            numero_diario = diario.attrib.get("numero")

            for seccion in diario.iter("seccion"):
                sec_nombre = seccion.attrib.get("nombre")
                for departamento in seccion.iter("departamento"):
                    dep_nombre = departamento.attrib.get("nombre")
                    for epigrafe in departamento.iter("epigrafe"):
                        ep_nombre = epigrafe.attrib.get("nombre")
                        for item in epigrafe.findall("item"):
                            ident = item.findtext("identificador")
                            titulo = item.findtext("titulo")
                            if not ident or not titulo:
                                continue
                            docs.append(Documento(
                                identificador=ident,
                                titulo=titulo.strip(),
                                fecha=fecha,
                                url_pdf=item.findtext("url_pdf"),
                                url_html=item.findtext("url_html"),
                                seccion=sec_nombre,
                                departamento=dep_nombre,
                                numero_boletin=numero_diario,
                                extra={
                                    "epigrafe": ep_nombre,
                                    "url_xml": item.findtext("url_xml"),
                                },
                            ))
        return docs
