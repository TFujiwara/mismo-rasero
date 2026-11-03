from app.services.dinero import IMPUESTOS, SPLITS
from app.services.flujo import EJEMPLO, _hash_doue
from app.services.ingest import parse_boe_doc_xml

XML_REAL = """<?xml version="1.0" encoding="UTF-8"?>
<documento fecha_actualizacion="20261005085601">
  <metadatos>
    <identificador>BOE-A-2022-5809</identificador>
    <rango codigo="1300">Ley</rango>
    <titulo>Ley 7/2022, de 8 de abril, de residuos y suelos contaminados.</titulo>
    <fecha_publicacion>20220409</fecha_publicacion>
    <diario_numero>85</diario_numero>
    <url_pdf>https://www.boe.es/boe/dias/2022/04/09/pdfs/BOE-A-2022-5809.pdf</url_pdf>
  </metadatos>
  <analisis/>
  <texto/>
</documento>
"""


def test_parse_boe_doc_xml():
    doc = parse_boe_doc_xml(XML_REAL)
    assert doc["titulo"].startswith("Ley 7/2022")
    assert doc["rango"] == "Ley"
    assert doc["url_pdf"].endswith("BOE-A-2022-5809.pdf")
    assert doc["fecha_iso"] == "2022-04-09"
    assert doc["diario_numero"] == "85"


def test_parse_boe_doc_xml_sin_metadatos():
    import pytest

    with pytest.raises(ValueError):
        parse_boe_doc_xml("<documento/>")


def test_repartos_suman_100():
    for nombre, reparto in SPLITS.items():
        assert sum(r["porcentaje"] for r in reparto) == 100, nombre


def test_impuestos_tienen_fuente():
    for i in IMPUESTOS:
        assert i["fuente_ley_url"].startswith("https://www.boe.es/"), i["nombre"]


def test_hash_doue_estable():
    celex = EJEMPLO["doue"]["celex"]
    assert _hash_doue(celex) == _hash_doue(celex)
    assert _hash_doue(celex) != _hash_doue("OTRO")
