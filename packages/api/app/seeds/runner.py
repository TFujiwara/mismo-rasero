"""Seeds de arranque: boletines (§13+§14) y metanarrativas R2 (DDL §19).

Uso: uv run python -m app.seeds.runner all
"""

import argparse
import logging

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db import SessionLocal
from app.models import Boletin, MetanarrativaR2
from app.seeds.data_bops import BOPS, sigla_bop
from app.seeds.data_boletines import BOLETINES
from app.seeds.data_competencias import seed_competencias
from app.seeds.data_manual_accion import seed_manual_accion

logger = logging.getLogger(__name__)

# Las 12 metanarrativas fijas del §10, tal cual el INSERT del DDL §19.
METANARRATIVAS = [
    "Estado ladron", "Espana rota", "Casta", "Abandono territorial",
    "Invasion", "Decadencia moral", "Europa nos manda", "Sablazo fiscal",
    "Chiringuito", "Censura", "Colapso servicios", "Inseguridad",
]


def seed_boletines(session) -> int:
    """Upsert de los 20 boletines de §13 + DOUE, y los 43 BOPs de §14 como filas propias."""
    n = 0
    for b in BOLETINES:
        stmt = (
            pg_insert(Boletin)
            .values(**b)
            .on_conflict_do_update(index_elements=["sigla"], set_={
                "nombre": b["nombre"], "url_base": b["url_base"],
                "metodo": b["metodo"], "dificultad": b["dificultad"],
            })
        )
        session.execute(stmt)
        n += 1
    for provincia, url in BOPS:
        row = {
            "sigla": sigla_bop(provincia),
            "nombre": f"BOP {provincia}",
            "url_base": url,
            "metodo": "HTML",
            "dificultad": "media",
        }
        stmt = (
            pg_insert(Boletin)
            .values(**row)
            .on_conflict_do_update(index_elements=["sigla"], set_={
                "nombre": row["nombre"], "url_base": row["url_base"],
                "metodo": row["metodo"], "dificultad": row["dificultad"],
            })
        )
        session.execute(stmt)
        n += 1
    session.commit()
    return n


def seed_metanarrativas(session) -> int:
    n = 0
    for nombre in METANARRATIVAS:
        stmt = (
            pg_insert(MetanarrativaR2)
            .values(nombre=nombre)
            .on_conflict_do_nothing(index_elements=["nombre"])
        )
        session.execute(stmt)
        n += 1
    session.commit()
    return n


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Seeds del blueprint")
    parser.add_argument(
        "target",
        choices=["all", "boletines", "metanarrativas", "competencias", "accion"],
        nargs="?",
        default="all",
    )
    args = parser.parse_args()

    with SessionLocal() as session:
        if args.target in ("all", "boletines"):
            n = seed_boletines(session)
            total = session.execute(select(Boletin.id)).scalars().all()
            logger.info("boletines: %s upserts, %s filas en tabla", n, len(total))
        if args.target in ("all", "metanarrativas"):
            n = seed_metanarrativas(session)
            total = session.execute(select(MetanarrativaR2.id)).scalars().all()
            logger.info(
                "metanarrativas: %s upserts, %s filas en tabla", n, len(total)
            )
        if args.target in ("all", "competencias"):
            n = seed_competencias(session)
            from app.models import Competencia

            total = session.execute(select(Competencia.id)).scalars().all()
            logger.info("competencias: %s upserts, %s filas en tabla", n, len(total))
        if args.target in ("all", "accion"):
            n = seed_manual_accion(session)
            from app.models import ManualAccion

            total = session.execute(select(ManualAccion.id)).scalars().all()
            logger.info("manual_accion: %s nuevos, %s filas en tabla", n, len(total))


if __name__ == "__main__":
    main()
