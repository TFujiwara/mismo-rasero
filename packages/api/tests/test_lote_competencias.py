"""Las 18 competencias sembradas: coherencia de fuentes y niveles.

Las fuentes se verificaron contra el BOE vía ELI (boe.es/eli/es/...) o son ids
de los tablas del blueprint ya verificados. Si un test falla, el id está mal —
corregir en data_competencias, no en el test.
"""

from app.seeds.data_competencias import COMPETENCIAS
from app.services.niveles import NIVELES_COMPETENTES


def test_lote_competencias_cuenta():
    slugs = {c["slug"] for c in COMPETENCIAS}
    assert len(slugs) == len(COMPETENCIAS) == 18
    assert NIVELES_COMPETENTES.keys() == slugs


def test_fuentes_verificadas():
    for c in COMPETENCIAS:
        url = c["fuente_url"]
        assert url.startswith((
            "https://www.boe.es/eli/",
            "https://dogv.gva.es",
            "https://www.boe.es/buscar/act.php?id=BOE-A-",
        )), f"{c['slug']}: fuente no verificada: {url}"
        assert c["articulo_legal"], c["slug"]


def test_cadena_competencial_parseable():
    for c in COMPETENCIAS:
        cadena = [t.strip() for t in c["descripcion_tecnica"].split("->") if t.strip()]
        assert len(cadena) >= 2, c["slug"]
        assert c["palabras_clave"], c["slug"]


def test_niveles_valores_validos():
    for slug, niveles in NIVELES_COMPETENTES.items():
        assert niveles, slug
        assert set(niveles) <= {"UE", "Estado", "CCAA", "Provincia", "Local"}, slug
