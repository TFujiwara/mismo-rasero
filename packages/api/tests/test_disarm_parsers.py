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
    assert f["fase"] is None  # la fase la resuelve seed_techniques con el mapa del sqlite
    assert f["url"].endswith("T0132")


FASES_STIX = {
    "plan strategy": "Plan", "plan objectives": "Plan",
    "target audience analysis": "Prepare", "develop narratives": "Prepare",
    "microtarget": "Prepare", "select channels and affordances": "Prepare",
    "conduct pump priming": "Execute", "deliver content": "Execute",
    "maximise exposure": "Execute", "drive offline activity": "Execute",
    "drive online harms": "Execute",
    "persist in the information environment": "Execute",
    "assess effectiveness": "Assess",
}


def test_mapa_tactica_fase_cubre_las_16(tmp_path):
    import sqlite3

    from disarm.importer import mapa_tactica_fase

    db = tmp_path / "DISARM.sqlite"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE phase (disarm_id TEXT, name TEXT)")
    conn.execute("CREATE TABLE tactic (disarm_id TEXT, name TEXT, phase_id TEXT)")
    for pid, nombre in (("P01", "Plan"), ("P02", "Prepare"), ("P03", "Execute"), ("P04", "Assess")):
        conn.execute("INSERT INTO phase VALUES (?, ?)", (pid, nombre))
    conn.execute("INSERT INTO tactic VALUES (1, 'TA06', 'P02', 'Develop Content')")
    conn.commit()
    conn.close()

    mapa = mapa_tactica_fase(db)
    # 16 tácticas del STIX, todas resueltas (13 por el fallback documentado,
    # la de Develop Content por el join real)
    for tactica in FASES_STIX:
        assert mapa.get(tactica) == FASES_STIX[tactica], tactica
    assert mapa["develop content"] == "Prepare"  # del sqlite real


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
