"""Legislación vasca vía SPARQL (grafo ELI de api.euskadi.eus).

El endpoint corre en api.euskadi.eus — el host NO bloqueado de la red vasca.
Consulta del operador (adaptada de los ejemplos oficiales): leyes desde 2020
con su página oficial en Legegunea (texto consolidado). v1: alcance "Ley…"
por prefijo de título — aproximación declarada (un decreto que menciona una
ley no entra; alguna ley con título raro podría escaparse).

Las normas se guardan con hash SHA-256 del identificador ELI/página como clave
estable: no hay PDF que descargar, la fuente citada es la página oficial de
Legegunea.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime

import httpx
from sqlalchemy import select

from app.models import Boletin, Norma

ENDPOINT = "https://api.euskadi.eus/sparql/"
GRAFO = "bopv-european-legislation-identifier-eli"

QUERY = """
PREFIX schema: <https://schema.org/>
PREFIX eli: <https://data.europa.eu/eli/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX graph: <https://id.euskadi.eus/graph/>

SELECT DISTINCT ?datePub ?url ?title
WHERE {
  GRAPH graph:{grafo} {
    ?legalresource eli:date_publication ?datePub .
    ?legalresource eli:is_realized_by ?expr .
    ?expr eli:title ?title .
    ?format eli:embodies ?expr .
    ?format schema:mainEntityOfPage ?url .
  }
  FILTER (?datePub >= "{desde}"^^xsd:date)
  FILTER regex(str(?title), "^Ley", "i")
}
ORDER BY DESC(?datePub)
"""


def _consulta(desde: str) -> list[dict]:
    """Ejecuta la consulta SPARQL y devuelve bindings normalizados.
    (replace en vez de format: el SPARQL tiene llaves literales.)"""
    query = QUERY.replace("{grafo}", GRAFO).replace("{desde}", desde)
    with httpx.Client(timeout=120) as client:
        r = client.get(
            ENDPOINT,
            params={"query": query},
            headers={
                "Accept": "application/sparql-results+json",
                "User-Agent": "Mismo Rasero/0.1",
            },
        )
        r.raise_for_status()
        data = r.json()
    return [
        {
            "date_pub": b.get("datePub", {}).get("value", ""),
            "url": b.get("url", {}).get("value", ""),
            "title": b.get("title", {}).get("value", "").strip(),
        }
        for b in data.get("results", {}).get("bindings", [])
    ]


def _fecha_iso(texto: str) -> date | None:
    try:
        return datetime.fromisoformat(texto).date()
    except ValueError:
        return None


def _hash_estable(url: str) -> str:
    """Clave única declarada para normas sin fichero descargable (misma
    convención que el nodo DOUE del flujo normativo)."""
    return hashlib.sha256(f"LEGVASCA:{url}".encode()).hexdigest()


def ingestar_legislacion_vasca(session, desde: str = "2020-01-01") -> dict:
    bopv = session.execute(select(Boletin).where(Boletin.sigla == "BOPV")).scalar_one_or_none()
    bindings = _consulta(desde)
    nuevos, existentes = 0, 0
    for b in bindings:
        url, titulo = b["url"], b["title"]
        if not url or not titulo:
            continue
        hash_clave = _hash_estable(url)
        existe = session.execute(
            select(Norma.id).where(Norma.hash_sha256 == hash_clave)
        ).scalar_one_or_none()
        if existe is not None:
            existentes += 1
            continue
        session.add(Norma(
            titulo=titulo,
            rango="Ley",
            fecha_pub=_fecha_iso(b["date_pub"]),
            boletin_id=bopv.id if bopv else None,
            numero_boletin=None,
            url_pdf=url,  # página oficial consolidada en Legegunea
            hash_sha256=hash_clave,
        ))
        nuevos += 1
    session.commit()
    return {"desde": desde, "leyes_encontradas": len(bindings),
            "nuevas": nuevos, "ya_ingestadas": existentes}
