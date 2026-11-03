"""Tests del matching del Pilar 6 — función pura, sin BD.

Los "competencias" falsos replican el contrato del modelo: id, nombre, slug,
descripcion_llana, descripcion_tecnica (cadena con '->'), articulo_legal,
fuente_url, palabras_clave.
"""

from dataclasses import dataclass, field

from app.services.verificar import match_competencias, normaliza


@dataclass
class FakeCompetencia:
    id: int
    nombre: str
    slug: str
    descripcion_tecnica: str
    palabras_clave: list[str] = field(default_factory=list)
    descripcion_llana: str | None = None
    articulo_legal: str | None = None
    fuente_url: str | None = None


IRPF = FakeCompetencia(
    id=5,
    nombre="IRPF — Impuesto sobre la Renta",
    slug="irpf",
    descripcion_tecnica="Estado Ley 35/2006 (tramo estatal) -> Generalitat Ley 13/1997 "
    "(tramo autonómico) -> Ayuntamiento NO tiene competencia en IRPF",
    palabras_clave=["irpf", "renta", "bajar el irpf", "subir el irpf"],
    descripcion_llana="Mitad Estado, mitad CCAA. El ayuntamiento NO puede.",
    articulo_legal="Ley 35/2006 + Ley 22/2009",
    fuente_url="https://www.boe.es/buscar/act.php?id=BOE-A-2006-20764",
)

VIA = FakeCompetencia(
    id=3,
    nombre="Vía pública urbana",
    slug="via-publica",
    descripcion_tecnica="Ayuntamiento: calles urbanas -> Diputación: carreteras provinciales",
    palabras_clave=["bache", "farola fundida", "socavón"],
)


def test_normaliza_quita_tildes_y_mayusculas():
    assert normaliza("SOCAVÓN") == normaliza("socavon")
    assert normaliza("¿Puede el AYUNTAMIENTO bajar el IRPF?") == (
        "puede el ayuntamiento bajar el irpf"
    )


def test_match_por_palabra_clave():
    res = match_competencias("El ayuntamiento bajará el IRPF", [IRPF, VIA])
    assert len(res) == 1
    assert res[0]["slug"] == "irpf"
    assert res[0]["palabra_disparadora"] in ("irpf", "bajará el IRPF", "bajar el irpf")


def test_match_sin_tildes():
    res = match_competencias("hay un socavon en la acera", [VIA])
    assert len(res) == 1 and res[0]["slug"] == "via-publica"


def test_sin_match_devuelve_vacio():
    assert match_competencias("el precio del café", [IRPF, VIA]) == []


def test_cadena_parseada_y_mas_especifico_primero():
    res = match_competencias("van a bajar el irpf y además hay un bache", [VIA, IRPF])
    assert [m["slug"] for m in res] == ["irpf", "via-publica"]  # 'bajar el irpf' > 'bache'
    assert "->" not in res[0]["cadena"][0]
    assert len(res[0]["cadena"]) == 3
    assert res[0]["cadena"][-1].startswith("Ayuntamiento NO")


def test_match_por_nombre_si_no_hay_keywords():
    c = FakeCompetencia(
        id=9, nombre="Impuesto de Basuras", slug="basuras",
        descripcion_tecnica="Ayuntamiento -> ordenanza BOP",
        palabras_clave=[],
    )
    res = match_competencias("la tasa de impuesto de basuras sube", [c])
    assert len(res) == 1 and res[0]["slug"] == "basuras"
