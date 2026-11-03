from app.services.niveles import detectar_nivel, veredicto_competencial


def test_detectar_nivel_ayuntamiento():
    assert "Local" in detectar_nivel("El Ayuntamiento de Vila-real bajará el IRPF")


def test_detectar_nivel_estado():
    assert "Estado" in detectar_nivel("El gobierno central ha subido el IVA")


def test_detectar_nivel_ccaa():
    assert "CCAA" in detectar_nivel("La Generalitat construirá hospitales")


def test_detectar_nivel_nada():
    assert detectar_nivel("Buenos días, hace buen tiempo") == []


def test_veredicto_falso_competencial():
    """El ejemplo canónico del §06: ayuntamiento + IRPF = FALSO."""
    v = veredicto_competencial("irpf", "El Ayuntamiento de Vila-real bajará el IRPF")
    assert v["veredicto"] == "FALSO COMPETENCIAL"
    assert "ayuntamiento" in v["razon"]


def test_veredicto_verdadero_competencial():
    v = veredicto_competencial("irpf", "El gobierno central subirá el IRPF")
    assert v["veredicto"] == "VERDADERO COMPETENCIAL"


def test_veredicto_sin_sujeto():
    v = veredicto_competencial("ibi", "Me han subido mucho el recibo")
    assert v["veredicto"] == "SIN SUJETO CLARO"


def test_veredicto_con_override_llm():
    """La salida del LLM entra por la MISMA regla (nunca decide el modelo)."""
    v = veredicto_competencial(
        "irpf", "frase ambigua", niveles_override=["Estado"]
    )
    assert v["veredicto"] == "VERDADERO COMPETENCIAL"
    v2 = veredicto_competencial("irpf", "frase ambigua", niveles_override=["Local"])
    assert v2["veredicto"] == "FALSO COMPETENCIAL"


def test_via_publica_admite_dos_niveles():
    assert veredicto_competencial("via-publica", "El ayuntamiento arreglará los baches")[
        "veredicto"
    ] == "VERDADERO COMPETENCIAL"
    assert veredicto_competencial("via-publica", "La Diputación arreglará la carretera")[
        "veredicto"
    ] == "VERDADERO COMPETENCIAL"
