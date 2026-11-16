"""Backfill histórico del BOPV por meses (la API permite /{year}/{month}).

El cron diario trae los días recientes con margen de 2 días (la API va un día
por detrás). Este módulo rellena meses pasados: pagina el mes completo e
ingesta todos los actos con PDF, deduplicando por hash SHA-256 como la ingesta
normal. Reanudable: un mes ya ingerido se salta si la bandera existe.
"""

from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy import select

from app.db import SessionLocal
from app.models import Boletin, Norma
from scrapers.base import DEFAULT_HEADERS
from scrapers.bopv import API, ITEMS_POR_PAGINA

logger = logging.getLogger("bopv_backfill")

MADRID = ZoneInfo("Europe/Madrid")


def _ingestar_mes(session, boletin, year: int, month: int, sleep_s: float) -> dict:
    stats = {"leidos": 0, "nuevos": 0, "duplicados": 0, "sin_pdf": 0, "errores": 0}
    page = 1
    total_pages = 1
    with httpx.Client(
        headers={**DEFAULT_HEADERS, "Accept": "application/json"},
        follow_redirects=True, timeout=90,
    ) as client:
        while page <= total_pages:
            r = client.get(
                f"{API}/{year}/{month}",
                params={"lang": "SPANISH", "itemsOfPage": ITEMS_POR_PAGINA,
                        "currentPage": page},
            )
            if r.status_code in (401, 406):
                raise RuntimeError(f"WAF {r.status_code}")
            r.raise_for_status()
            data = r.json()
            total_pages = int(data.get("totalPages") or 1)
            for item in data.get("items", []):
                stats["leidos"] += 1
                nombre = (item.get("name") or "").strip()
                url_pdf = None
                for d in item.get("downloadable") or []:
                    u = (d.get("url") or "").strip()
                    if u.lower().endswith(".pdf") or (d.get("format") or "").lower() == "pdf":
                        url_pdf = u
                        break
                if not nombre or not url_pdf:
                    stats["sin_pdf"] += 1
                    continue
                try:
                    rp = client.get(url_pdf)
                    rp.raise_for_status()
                    import hashlib

                    hash_pdf = hashlib.sha256(rp.content).hexdigest()
                except Exception as exc:  # noqa: BLE001
                    stats["errores"] += 1
                    logger.warning("  PDF falló (%s): %s", item.get("id"), str(exc)[:80])
                    time.sleep(sleep_s)
                    continue

                existe = session.execute(
                    select(Norma.id).where(Norma.hash_sha256 == hash_pdf)
                ).scalar_one_or_none()
                if existe is not None:
                    stats["duplicados"] += 1
                else:
                    publish = (item.get("publishDate") or "").strip()
                    fecha_pub = None
                    if publish:
                        try:
                            dt = datetime.fromisoformat(publish.replace("Z", "+00:00"))
                            fecha_pub = dt.astimezone(MADRID).date()
                        except ValueError:
                            pass
                    session.add(Norma(
                        titulo=nombre,
                        rango="BOPV",
                        fecha_pub=fecha_pub,
                        boletin_id=boletin.id,
                        numero_boletin=str(item.get("numBulletin") or ""),
                        url_pdf=url_pdf,
                        hash_sha256=hash_pdf,
                    ))
                    stats["nuevos"] += 1
                time.sleep(sleep_s)
            page += 1
    session.commit()
    return stats


def run(year: int, desde_mes: int, hasta_mes: int, sleep_s: float) -> dict:
    total = {"leidos": 0, "nuevos": 0, "duplicados": 0, "sin_pdf": 0, "errores": 0}
    with SessionLocal() as session:
        boletin = session.execute(
            select(Boletin).where(Boletin.sigla == "BOPV")
        ).scalar_one_or_none()
        for month in range(desde_mes, hasta_mes + 1):
            try:
                s = _ingestar_mes(session, boletin, year, month, sleep_s)
                logger.info("mes %s-%02d: %s", year, month, s)
                for k in total:
                    total[k] += s[k]
            except Exception as exc:  # noqa: BLE001
                logger.warning("mes %s-%02d falló: %s", year, month, str(exc)[:120])
            time.sleep(sleep_s)
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill BOPV por meses")
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--desde", type=int, default=1)
    parser.add_argument("--hasta", type=int, default=11)
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--log", default="bopv_backfill.log")
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(args.log, encoding="utf-8"), logging.StreamHandler()],
    )
    stats = run(args.year, args.desde, args.hasta, args.sleep)
    logger.info("FIN: %s", stats)


if __name__ == "__main__":
    main()
