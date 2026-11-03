from types import SimpleNamespace

from app.services.geocoding import parse_direccion, provincia_de_display
from app.services.quien_manda import _misma_provincia, construir_organigrama


def test_parse_direccion_calle_y_municipio():
    p = parse_direccion("Carrer Ermita 12, Vila-real")
    assert p == {"street": "Carrer Ermita 12", "city": "Vila-real"}


def test_parse_direccion_con_cp():
    p = parse_direccion("Carrer Ermita 12, 12540 Vila-real")
    assert p["city"] == "Vila-real"


def test_parse_direccion_solo_municipio():
    assert parse_direccion("Vila-real") == {"city": "Vila-real"}


def test_provincia_display_name_bilingue():
    display = ("Carrer Ermita, Vila-real, la Plana Baixa, "
               "Castelló / Castellón, Comunitat Valenciana, 12540, España")
    assert provincia_de_display(display) == "Castellón"


def test_provincia_display_name_alicante():
    assert provincia_de_display("x, Alacant / Alicante, Comunitat Valenciana") == "Alicante"


def test_provincia_no_encontrada():
    assert provincia_de_display("Nowhere, Somewhere, Portugal") is None


def _geo(municipio="Vila-real", provincia="Castellón", ccaa="Comunitat Valenciana"):
    return {"municipio": municipio, "provincia": provincia, "ccaa": ccaa}


def test_organigrama_cv_completo():
    niveles = construir_organigrama(_geo())
    nombres = [n["nivel"] for n in niveles]
    assert nombres == ["UE", "Estado", "CCAA", "Provincia", "Local", "Supramunicipal"]
    cv = next(n for n in niveles if n["nivel"] == "CCAA")
    assert cv["nombre"] == "Generalitat Valenciana"
    assert "sanidad y hospitales" in cv["puede"]
    dipu = next(n for n in niveles if n["nivel"] == "Provincia")
    assert "Castellón" in dipu["nombre"]
    ayto = next(n for n in niveles if n["nivel"] == "Local")
    assert "IBI" in " ".join(ayto["puede"])
    manco = next(n for n in niveles if n["nivel"] == "Supramunicipal")
    assert manco["pendiente"] is True


def test_organigrama_uniprovincial_sin_diputacion():
    niveles = construir_organigrama(_geo(municipio="Madrid", provincia="Madrid",
                                         ccaa="Madrid"))
    assert all(n["nivel"] != "Provincia" for n in niveles)


def test_organigrama_ccaa_desconocida_generica():
    niveles = construir_organigrama(_geo(municipio="Jaca", provincia="Huesca",
                                         ccaa="Aragón"))
    ccaa = next(n for n in niveles if n["nivel"] == "CCAA")
    assert "Aragón" in ccaa["nombre"]
    assert any(n["nivel"] == "Provincia" for n in niveles)


def test_organigrama_fuentes_presentes():
    for n in construir_organigrama(_geo()):
        if not n["pendiente"]:
            assert n["fuente_url"].startswith("http")


def test_misma_provincia_bilingue():
    assert _misma_provincia("Castelló/Castellón", "Castellón")
    assert _misma_provincia("Alacant / Alicante", "Alicante")
    assert not _misma_provincia("Castelló/Castellón", "Valencia")
    assert not _misma_provincia(None, "Castellón")


def test_organigrama_con_filas_dir3():
    dipu = SimpleNamespace(
        nombre="Diputació de Castelló", codigo_dir3="L02000012",
        provincia="Castelló/Castellón",
    )
    ayto = SimpleNamespace(codigo_dir3="L12047024")
    mancos = ["Mancomunitat de la Plana Baixa", "Mancomunitat Espadà-Millars"]
    niveles = construir_organigrama(
        _geo(), diputacion_row=dipu, mancomunidades=mancos,
        municipio_row=ayto,
    )
    dip = next(n for n in niveles if n["nivel"] == "Provincia")
    assert "L02000012" in dip["nombre"] and "Diputació de Castelló" in dip["nombre"]
    local = next(n for n in niveles if n["nivel"] == "Local")
    assert "L12047024" in local["nombre"]
    sup = next(n for n in niveles if n["nivel"] == "Supramunicipal")
    assert sup["mancomunidades"] == mancos
    assert sup["pendiente"] is False
    assert "Censo" in sup["fuente_texto"]  # afiliación declarada pendiente
