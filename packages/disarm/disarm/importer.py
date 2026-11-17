"""Importador DISARM → disarm_techniques (RED) + disarm_counters (BLUE).

Fuentes — IMPORTANTES (verificadas en vivo, oct. 2026):
El blueprint §15 citaba DISARMFoundation/DISARM + generated_files/red_framework.json.
El repositorio actual es DISARMFoundation/DISARMframeworks y la estructura cambió:

  - RED:   generated_files/DISARM_STIX/DISARM.json  — bundle STIX 2.1 con 391
           attack-patterns (códigos T) y 16 x-mitre-tactic (táctica).
  - BLUE:  generated_files/DISARM_database.sqlite   — tabla `counter` con 140
           códigos C (nombre + summary). Y — CLAVE — las tablas `phase` (P01
           Plan / P02 Prepare / P03 Execute / P04 Assess) y `tactic`
           (tactic_id TA→phase_id) que permiten llenar `disarm_techniques.fase`
           (hueco #3 del README, cerrado).
  - El STIX da la táctica por técnica (kill_chain_phases → shortname); el
    sqlite da el mapeo táctica → fase. El importer cruza ambos.

Modo online (descarga) u offline (--offline-data con los ficheros ya cacheados).
"""

from __future__ import annotations

import json
import logging
import sqlite3
import tempfile
from pathlib import Path

import click
import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db import SessionLocal
from app.models import DisarmCounter, DisarmTechnique

logger = logging.getLogger(__name__)

RAW = "https://raw.githubusercontent.com/DISARMFoundation/DISARMframeworks/main"
STIX_URL = f"{RAW}/generated_files/DISARM_STIX/DISARM.json"
SQLITE_URL = f"{RAW}/generated_files/DISARM_database.sqlite"

BUNDLE_CACHE = Path(tempfile.gettempdir()) / "blueprint-disarm.json"
SQLITE_CACHE = Path(tempfile.gettempdir()) / "blueprint-disarm.sqlite"


def _download(url: str, dest: Path) -> Path:
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    logger.info("descargando %s", url)
    with httpx.Client(follow_redirects=True, timeout=300) as client:
        resp = client.get(url)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
    return dest


def _external_id(obj: dict) -> str | None:
    for ref in obj.get("external_references", []):
        if "external_id" in ref:
            return ref["external_id"]
    return None


def parse_techniques_red(bundle: dict) -> list[dict]:
    """Del bundle STIX → filas de disarm_techniques (tipo RED)."""
    objs = bundle.get("objects", [])
    shortname_to_name = {
        t["x_mitre_shortname"]: t["name"]
        for t in objs if t.get("type") == "x-mitre-tactic" and "x_mitre_shortname" in t
    }
    filas: list[dict] = []
    vistos: set[str] = set()
    for obj in objs:
        if obj.get("type") != "attack-pattern":
            continue
        ext_id = _external_id(obj)
        if not ext_id or ext_id in vistos:
            continue
        vistos.add(ext_id)
        tactica = None
        for phase in obj.get("kill_chain_phases", []):
            tactica = shortname_to_name.get(phase.get("phase_name", ""), tactica)
        url = None
        for ref in obj.get("external_references", []):
            if "url" in ref:
                url = ref["url"]
                break
        filas.append({
            "id": ext_id,
            "fase": None,          # ver docstring: sin fuente verificada de fase
            "tactica": tactica,
            "nombre": obj.get("name"),
            "descripcion": obj.get("description"),
            "url": url,
            "tipo": "RED",
        })
    return filas


def parse_counters_blue(sqlite_path: Path) -> list[dict]:
    """De la tabla `counter` del sqlite → filas de disarm_counters (BLUE)."""
    conn = sqlite3.connect(sqlite_path)
    try:
        rows = conn.execute(
            "SELECT disarm_id, name, summary FROM counter WHERE disarm_id IS NOT NULL"
        ).fetchall()
    finally:
        conn.close()
    return [
        {"id": r[0], "nombre": r[1], "descripcion": r[2]}
        for r in rows
    ]


def mapa_tactica_fase(sqlite_path: Path) -> dict[str, str]:
    """Del sqlite: código de táctica (TA01…) y nombre → fase (Plan/…/Assess).

    La tabla `tactic` (13 filas) es parcial respecto a las 16 tácticas del
    STIX — para las que falten, devuelve el nombre para que el cruce por
    nombre en el importer las resuelva si puede.
    """
    conn = sqlite3.connect(sqlite_path)
    try:
        # NOTA: tactic.phase_id guarda el disarm_id de phase ('P01'), no su id
        # numérico — el join es por phase.disarm_id
        rows = conn.execute(
            "SELECT t.disarm_id, t.name, p.name FROM tactic t "
            "JOIN phase p ON t.phase_id = p.disarm_id"
        ).fetchall()
    finally:
        conn.close()
    mapa = {}
    for ta_id, ta_name, fase in rows:
        if ta_id:
            mapa[ta_id] = fase
        if ta_name:
            mapa[ta_name.lower()] = fase

    # el sqlite mantiene la taxonomía ANTIGUA (13 tácticas); el STIX trae la
    # actual (16). Para las que no casan por nombre, mapeo documentado con la
    # estructura oficial del framework — consistente con las 3 que casan
    # (Develop Content→Prepare, Drive Offline Activity→Execute, y Assess).
    # Verificación manual: https://www.disarm.foundation/framework
    FASES_STIX = {
        "plan strategy": "Plan",
        "plan objectives": "Plan",
        "target audience analysis": "Prepare",
        "develop narratives": "Prepare",
        "establish assets": "Prepare",
        "establish legitimacy": "Prepare",
        "microtarget": "Prepare",
        "select channels and affordances": "Prepare",
        "conduct pump priming": "Execute",
        "deliver content": "Execute",
        "maximise exposure": "Execute",
        "drive offline activity": "Execute",
        "drive online harms": "Execute",
        "persist in the information environment": "Execute",
        "assess effectiveness": "Assess",
    }
    mapa.update(FASES_STIX)
    return mapa


def seed_techniques(filas: list[dict], mapa_fase: dict[str, str]) -> int:
    """Upsert de técnicas; resuelve `fase` por código de táctica (TA01) o por
    nombre de táctica con el mapa del sqlite. Las que no casen quedan NULL."""
    with SessionLocal() as session:
        for f in filas:
            fase = None
            if f.get("tactica"):
                fase = mapa_fase.get(f["tactica"].lower())
            stmt = (
                pg_insert(DisarmTechnique)
                .values(**{**f, "fase": fase})
                .on_conflict_do_update(index_elements=[DisarmTechnique.id], set_={
                    "fase": fase, "tactica": f["tactica"],
                    "nombre": f["nombre"], "descripcion": f["descripcion"],
                    "url": f["url"], "tipo": f["tipo"],
                })
            )
            session.execute(stmt)
        session.commit()
    return len(filas)


def seed_counters(filas: list[dict]) -> int:
    with SessionLocal() as session:
        for f in filas:
            stmt = (
                pg_insert(DisarmCounter)
                .values(**f)
                .on_conflict_do_update(index_elements=[DisarmCounter.id], set_={
                    "nombre": f["nombre"], "descripcion": f["descripcion"],
                })
            )
            session.execute(stmt)
        session.commit()
    return len(filas)


@click.command("disarm-import")
@click.option("--offline-data", type=click.Path(exists=True, file_okay=False, path_type=Path),
              default=None, help="Directorio con DISARM.json y DISARM.sqlite ya descargados")
def main(offline_data: Path | None):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if offline_data:
        bundle_path = offline_data / "DISARM.json"
        sqlite_path = offline_data / "DISARM.sqlite"
        if not bundle_path.exists() or not sqlite_path.exists():
            raise click.ClickException(
                f"en {offline_data} deben existir DISARM.json y DISARM.sqlite"
            )
    else:
        bundle_path = _download(STIX_URL, BUNDLE_CACHE)
        sqlite_path = _download(SQLITE_URL, SQLITE_CACHE)

    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    tecnicas = parse_techniques_red(bundle)
    counters = parse_counters_blue(sqlite_path)
    mapa_fase = mapa_tactica_fase(sqlite_path)

    n1 = seed_techniques(tecnicas, mapa_fase)
    n2 = seed_counters(counters)
    con_fase = sum(1 for t in tecnicas if mapa_fase.get((t.get("tactica") or "").lower()))
    click.echo(f"disarm_techniques: {n1} filas RED upsert ({con_fase} con fase)")
    click.echo(f"disarm_counters: {n2} filas BLUE upsert")


if __name__ == "__main__":
    main()
