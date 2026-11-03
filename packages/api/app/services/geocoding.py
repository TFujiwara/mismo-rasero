"""Geocodificación — resolución dirección → municipio/provincia/CCAA.

Realidad verificada (oct. 2026): la API REST clásica de CartoCiudad
(/geocoder/api/geocoder/find) responde 500 server-side y el callejero REST del
Catastro (OVCCallejero/CallejeroGC.svc) responde 404 — ambas movidas/rotas.
El servicio usa Nominatim (OpenStreetMap) en modo ESTRUCTURADO (calle y
municipio separados), que evita el fuzzy matching que manda "Carrer del Mig 2,
Valencia" a Alicante. La provincia se extrae del display_name contra una lista
estática de las 50 provincias + Ceuta/Melilla (los nombres duales
"Castelló / Castellón" se resuelven con alias normalizados).

Fuente de los datos geográficos: OpenStreetMap/Nominatim — no cartografía
oficial del CNIG. Documentado en /metodologia.
"""

from __future__ import annotations

import re
from typing import Any

import httpx

from app.services.verificar import normaliza

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# política de uso de Nominatim: UA identificativo + ≤1 req/s
_HEADERS = {"User-Agent": "quien-manda/0.1 (open source; geocoding de direcciones ES)"}

# 50 provincias + Ceuta + Melilla — nombres oficiales con alias bilingües
# frecuentes en OSM (Castelló/Castellón, Alacant/Alicante, Araba/Álava…)
PROVINCIAS: dict[str, list[str]] = {
    "A Coruña": ["a coruna", "la coruna"],
    "Albacete": ["albacete"],
    "Alicante": ["alicante", "alacant"],
    "Almería": ["almeria"],
    "Araba/Álava": ["araba", "alava"],
    "Ávila": ["avila"],
    "Badajoz": ["badajoz"],
    "Barcelona": ["barcelona"],
    "Bizkaia": ["bizkaia", "vizcaya"],
    "Burgos": ["burgos"],
    "Cáceres": ["caceres"],
    "Cádiz": ["cadiz"],
    "Castellón": ["castellon", "castello"],
    "Ceuta": ["ceuta"],
    "Ciudad Real": ["ciudad real"],
    "Córdoba": ["cordoba"],
    "Cuenca": ["cuenca"],
    "Girona": ["girona", "gerona"],
    "Granada": ["granada"],
    "Guadalajara": ["guadalajara"],
    "Gipuzkoa": ["gipuzkoa", "guipuzcoa"],
    "Huelva": ["huelva"],
    "Huesca": ["huesca"],
    "Jaén": ["jaen"],
    "León": ["leon"],
    "Lleida": ["lleida", "lerida"],
    "La Rioja": ["la rioja", "rioja"],
    "Lugo": ["lugo"],
    "Madrid": ["madrid"],
    "Málaga": ["malaga"],
    "Melilla": ["melilla"],
    "Murcia": ["murcia"],
    "Navarra": ["navarra", "nafarroa"],
    "Ourense": ["ourense", "orense"],
    "Palencia": ["palencia"],
    "Las Palmas": ["las palmas", "palmas"],
    "Pontevedra": ["pontevedra"],
    "Salamanca": ["salamanca"],
    "Santa Cruz de Tenerife": ["santa cruz de tenerife", "santa cruz"],
    "Segovia": ["segovia"],
    "Sevilla": ["sevilla"],
    "Soria": ["soria"],
    "Tarragona": ["tarragona"],
    "Teruel": ["teruel"],
    "Toledo": ["toledo"],
    "Valencia": ["valencia", "valencia castello", "valencia valencia"],
    "Valladolid": ["valladolid"],
    "Zamora": ["zamora"],
    "Zaragoza": ["zaragoza"],
}

_ALIAS_A_PROVINCIA: dict[str, str] = {
    alias: prov for prov, aliases in PROVINCIAS.items() for alias in aliases
}


def parse_direccion(direccion: str) -> dict[str, str]:
    """Divide 'Carrer Ermita 12, 12540 Vila-real' en street y city.

    Heurística honesta: primer tramo = calle, último tramo = municipio (quitando
    un posible código postal pegado). Si solo hay un tramo, se trata como
    búsqueda de municipio (city-level) — nunca free-text fuzzy.
    """
    partes = [p.strip() for p in direccion.split(",") if p.strip()]
    if len(partes) >= 2:
        city = re.sub(r"^\d{4,5}\s+", "", partes[-1])
        return {"street": partes[0], "city": city}
    return {"city": direccion.strip()}


def provincia_de_display(display_name: str) -> str | None:
    """Busca la provincia en los segmentos del display_name de Nominatim.

    'Carrer Ermita, Vila-real, la Plana Baixa, Castelló / Castellón,
    Comunitat Valenciana, 12540, España' → 'Castellón'
    """
    for segmento in display_name.split(","):
        for mitad in segmento.split("/"):
            clave = normaliza(mitad)
            if clave in _ALIAS_A_PROVINCIA:
                return _ALIAS_A_PROVINCIA[clave]
    return None


def geocode(direccion: str) -> dict[str, Any] | None:
    """Resuelve una dirección. Devuelve None si Nominatim no la encuentra."""
    params = parse_direccion(direccion)
    query = {
        **params,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
        "countrycodes": "es",
    }
    with httpx.Client(headers=_HEADERS, follow_redirects=True, timeout=30) as client:
        resp = client.get(NOMINATIM_URL, params=query)
        resp.raise_for_status()
        resultados = resp.json()

    if not resultados:
        return None
    r = resultados[0]
    addr = r.get("address", {})
    municipio = (
        addr.get("city") or addr.get("town") or addr.get("village")
        or addr.get("municipality")
    )
    if not municipio:
        return None
    return {
        "direccion_original": direccion,
        "municipio": municipio,
        "provincia": addr.get("province") or provincia_de_display(r["display_name"]),
        "ccaa": addr.get("state"),
        "lat": float(r["lat"]),
        "lon": float(r["lon"]),
        "fuente": "OpenStreetMap / Nominatim",
        "display_name": r["display_name"],
    }
