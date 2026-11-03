"""Ingesta por lotes de presupuestos EELL para TODA España (Fase 3 a escala).

Recorre la matriz completa del portal SGCIEF: 19 CCAA × provincias INE × 8
tipos de entidad. Diseñado para correr en background (~20-30 h a ritmo
respetuoso) con:
  - reanudación: salta entidades cuyo fuente_url ya tiene filas en presupuestos
  - sesión nueva por combo (provincia+tipo) — sesiones largas caducan
  - rate limit entre peticiones
  - log de progreso a fichero; errores por entidad no abortan el lote

Uso:
  uv run python -m app.services.presupuestos_batch --ejercicio 2024 \
      --tipos A5,AA,DD,MM --sleep 0.3 --log ~/blueprint/data/logs/presu.log
"""

from __future__ import annotations

import argparse
import logging
import time

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Presupuesto
from app.services.presupuestos import ingresar_resumen
from scrapers.hacienda import (
    SgciefScraper,
    TIPO_AYUNTAMIENTOS_GRANDES,
    TIPO_AYUNTAMIENTOS_PEQ,
    TIPO_DIPUTACIONES,
    TIPO_MANCOMUNIDADES,
)

logger = logging.getLogger("presupuestos_batch")

# provincias INE por CCAA (código CCAA del portal → códigos de provincia)
CCAA_PROVINCIAS: dict[str, list[str]] = {
    "01": ["04", "11", "14", "18", "21", "23", "29", "41"],          # Andalucía
    "02": ["22", "44", "50"],                                        # Aragón
    "03": ["33"],                                                    # Asturias
    "04": ["07"],                                                    # Illes Balears
    "05": ["35", "38"],                                              # Canarias
    "06": ["39"],                                                    # Cantabria
    "07": ["05", "09", "24", "34", "37", "40", "42", "47", "49"],    # Castilla y León
    "08": ["02", "13", "16", "19", "45"],                            # Castilla-La Mancha
    "09": ["08", "17", "25", "43"],                                  # Cataluña
    "10": ["06", "10"],                                              # Extremadura
    "11": ["15", "27", "32", "36"],                                  # Galicia
    "12": ["28"],                                                    # Comunidad de Madrid
    "13": ["30"],                                                    # Región de Murcia
    "14": ["31"],                                                    # Navarra
    "15": ["01", "20", "48"],                                        # País Vasco
    "16": ["26"],                                                    # La Rioja
    "17": ["03", "12", "46"],                                        # Comunitat Valenciana
    "18": [""],                                                      # Ceuta (sin provincia)
    "19": [""],                                                      # Melilla
}

TODOS_LOS_TIPOS = [
    TIPO_DIPUTACIONES,
    TIPO_AYUNTAMIENTOS_GRANDES,
    TIPO_AYUNTAMIENTOS_PEQ,
    TIPO_MANCOMUNIDADES,
    "GG",  # agrupación de municipios
    "RR",  # comarcas
    "TT",  # áreas metropolitanas
    "AE",  # EATIM
]


def _ya_ingestada(session, entidad_id: str, ejercicio: int) -> bool:
    fuente = f"AccesoFormulariosEntidad/{entidad_id}"
    existe = session.execute(
        select(Presupuesto.id).where(
            (Presupuesto.fuente_url.like(f"%{fuente}%"))
            & (Presupuesto.ano == ejercicio)
        )
    ).first()
    return existe is not None


def run(
    ejercicio: int,
    tipos: list[str],
    sleep_s: float,
    solo_ccaa: list[str] | None = None,
) -> dict:
    stats = {"combos": 0, "entidades": 0, "omitidas": 0, "ingestadas": 0,
             "errores": 0}
    for ccaa, provincias in CCAA_PROVINCIAS.items():
        if solo_ccaa and ccaa not in solo_ccaa:
            continue
        for provincia in provincias:
            for tipo in tipos:
                stats["combos"] += 1
                try:
                    with SgciefScraper(ejercicio) as scraper:
                        entidades = scraper.abrir_sesion(ccaa, provincia, tipo)
                        logger.info("combo %s-%s-%s: %d entidades", ccaa,
                                    provincia, tipo, len(entidades))
                        with SessionLocal() as session:
                            for e in entidades:
                                stats["entidades"] += 1
                                try:
                                    if _ya_ingestada(session, e["id"], ejercicio):
                                        stats["omitidas"] += 1
                                        continue
                                    resumen = scraper.resumen_de_entidad(
                                        e["id"], nombre_sesion=e["nombre"]
                                    )
                                    resultado = ingresar_resumen(session, resumen, tipo)
                                    stats["ingestadas"] += 1
                                    logger.info("  ✓ %s (%s filas)",
                                                resultado["administracion"],
                                                resultado["filas"])
                                except Exception as exc:  # noqa: BLE001
                                    stats["errores"] += 1
                                    logger.warning("  ✗ %s: %s", e["nombre"],
                                                   str(exc)[:120])
                                time.sleep(sleep_s)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("combo %s-%s-%s falló: %s", ccaa, provincia,
                                   tipo, str(exc)[:120])
                    stats["errores"] += 1
                    time.sleep(sleep_s)
                    continue
                logger.info("STATS %s", stats)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingesta EELL toda España")
    parser.add_argument("--ejercicio", type=int, default=2024)
    parser.add_argument("--tipos", default="A5,AA,DD,MM,GG,RR,TT,AE")
    parser.add_argument("--ccaa", default="", help="filtrar por códigos CCAA, ej. 17,12")
    parser.add_argument("--sleep", type=float, default=0.3)
    parser.add_argument("--log", default="presupuestos_batch.log")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(args.log, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    tipos = [t.strip() for t in args.tipos.split(",") if t.strip()]
    solo = [c.strip() for c in args.ccaa.split(",") if c.strip()] or None
    logger.info("inicio: ejercicio=%s tipos=%s ccaa=%s sleep=%s",
                args.ejercicio, tipos, solo, args.sleep)
    stats = run(args.ejercicio, tipos, args.sleep, solo)
    logger.info("FIN: %s", stats)


if __name__ == "__main__":
    main()
