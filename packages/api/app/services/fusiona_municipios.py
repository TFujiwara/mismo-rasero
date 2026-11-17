"""Migración de datos: fusiona las administraciones creadas por la ingesta de
presupuestos (nombre del portal SGCIEF, ej. "Alcora (l')") con las fichas DIR3
existentes, canonizando el nombre con el artículo delante (forma INE:
"l'Alcora").

Ejecución: uv run python -m app.services.fusiona_municipios [--dry-run]
"""

from __future__ import annotations

import argparse
import re
import unicodedata

from sqlalchemy import select, text

from app.db import SessionLocal
from app.models import Administracion


def _sin_acentos(texto: str) -> str:
    t = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


ARTICULOS = {
    "el": "l'", "la": "l'", "els": "els ", "las": "les ", "los": "els ",
    "a": "l'", "o": "l'", "l": "l'",
}


def canoniza(nombre: str) -> str:
    """'Alcora (l')' → 'Alcora' y devuelve la forma INE ('l'Alcora')."""
    m = re.match(r"^(.*?)\s*\((\w+)\)$", nombre.strip())
    if not m:
        return nombre.strip(), None
    base, articulo = m.group(1).strip(), ARTICULOS.get(
        _sin_acentos(m.group(2)), f"{m.group(2)} "
    )
    # la forma INE antepone el artículo; para 'l' pegado, para el resto separado
    if articulo.endswith("'"):
        return base, f"{articulo}{base}"
    return base, f"{articulo}{base}"


def main(dry_run: bool = False) -> None:
    with SessionLocal() as s:
        huespedes = s.execute(
            select(Administracion).where(
                Administracion.codigo_dir3.is_(None),
                Administracion.tipo.like("MUNICIPIO%"),
            )
        ).scalars().all()
        # el tipo se guarda como 'MUNICIPIO' — si filtrara por igualdad exacta
        # vale; ilike por si acaso
        huespedes = [h for h in huespedes]
        print(f"huespedes a revisar: {len(huespedes)}")

        fusionadas, renombradas, sin_match = 0, 0, []
        for h in huespedes:
            base, forma_ine = canoniza(h.nombre or "")
            # busca candidata DIR3 con entidad_tipo=AY cuyo nombre contenga la
            # base (normalizada sin acentos)
            if not base:
                sin_match.append(h.nombre)
                continue
            objetivo = _sin_acentos(base)
            candidatas = s.execute(
                select(Administracion).where(
                    (Administracion.entidad_tipo == "AY")
                    & Administracion.nombre.ilike(f"%{base}%")
                )
            ).scalars().all()
            oficiales = [
                c for c in candidatas
                if objetivo in _sin_acentos(c.nombre or "")
                or objetivo == _sin_acentos((c.nombre or "").replace("Ayuntamiento de", "").strip())
            ]
            if oficiales:
                oficial = oficiales[0]
                if not dry_run:
                    # repunta presupuestos y otros vínculos a la oficial
                    s.execute(text(
                        "update presupuestos set administracion_id = :oficial "
                        "where administracion_id = :h"
                    ), {"oficial": oficial.id, "h": h.id})
                    s.execute(text(
                        "update personas_cargos set administracion_id = :oficial "
                        "where administracion_id = :h"
                    ), {"oficial": oficial.id, "h": h.id})
                    s.delete(h)
                fusionadas += 1
            else:
                # sin ficha DIR3 equivalente: al menos canoniza el nombre
                if forma_ine and not dry_run:
                    h.nombre = forma_ine
                renombradas += 1
                sin_match.append(f"{h.nombre} -> {forma_ine}")

        if not dry_run:
            s.commit()
        print(f"fusionadas con ficha DIR3: {fusionadas}")
        print(f"sin ficha DIR3 (nombre canonizado): {renombradas}")
        if dry_run:
            print("DRY RUN — nada persistido")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(args.dry_run)
