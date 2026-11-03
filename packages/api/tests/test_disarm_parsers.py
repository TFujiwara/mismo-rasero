import json
import sqlite3

from disarm.importer import parse_counters_blue, parse_techniques_red

TACTIC = {
    "type": "x-mitre-tactic",
    "name": "Develop Narratives",
    "x_mitre_shortname": "develop-narratives",
}

TECH = {
    "type": "attack-pattern",
    "name": "Use fake experts",
    "description": "Utiliza personas presentadas como expertas.",
    "external_references": [
        {"source_name": "mitre-attack", "external_id": "T0132",
         "url": "https://example.org/T0132"},
    ],
    "kill_chain_phases": [{"kill_chain_name": "mitre-attack",
                           "phase_name": "develop-narratives"}],
}


def _mini_bundle() -> dict:
    return {"objects": [TACTIC, TECH, TECH]}


def test_parse_techniques_red_basico():
    filas = parse_techniques_red(_mini_bundle())
    assert len(filas) == 1  # dedup por external_id
    f = filas[0]
    assert f["id"] == "T0132"
    assert f["tipo"] == "RED"
    assert f["tactica"] == "Develop Narratives"
    assert f["fase"] is None  # sin fuente verificada de fase (documentado)
    assert f["url"].endswith("T0132")


def test_parse_techniques_red_sin_tactica():
    obj = dict(TECH)
    obj.pop("kill_chain_phases")
    bundle = {"objects": [TACTIC, obj]}
    filas = parse_techniques_red(bundle)
    assert filas[0]["tactica"] is None


def test_parse_counters_blue(tmp_path):
    db = tmp_path / "DISARM.sqlite"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE counter (disarm_id TEXT, name TEXT, summary TEXT)")
    conn.execute("INSERT INTO counter VALUES ('C001', 'Debunk', 'Desmonta la afirmación')")
    conn.execute("INSERT INTO counter VALUES (NULL, 'sin id', 'se descarta')")
    conn.commit()
    conn.close()

    filas = parse_counters_blue(db)
    assert len(filas) == 1
    assert filas[0]["id"] == "C001"
    assert filas[0]["nombre"] == "Debunk"


def test_bundle_real_estructura():
    """El bundle STIX real (si está cacheado en temp) debe dar 391 técnicas T."""
    import os
    from pathlib import Path

    cache = Path(os.environ.get("TEMP", "/tmp")) / "opencode" / "disarm" / "DISARM.json"
    if not cache.exists():
        return  # sin cache, sin test
    filas = parse_techniques_red(json.loads(cache.read_text(encoding="utf-8")))
    assert len(filas) == 391
    assert all(f["id"].startswith("T") for f in filas)
