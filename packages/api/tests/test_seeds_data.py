from app.seeds.data_bops import BOPS, sigla_bop
from app.seeds.data_boletines import BOLETINES
from app.seeds.runner import METANARRATIVAS


def test_boletines_siglas_unicas_y_cortas():
    siglas = [b["sigla"] for b in BOLETINES]
    assert len(siglas) == len(set(siglas)), "siglas duplicadas"
    assert all(len(s) <= 20 for s in siglas), "sigla > VARCHAR(20)"
    assert all(b["metodo"] in {"API_JSON", "RSS", "HTML", "PDF"} for b in BOLETINES)


def test_boletines_blueprint_13_estan_todos():
    esperados = {
        "BOE", "BOJA", "BOA", "BOPA", "BOIB", "BOC-CANARIAS", "BOC-CANTABRIA",
        "BOCyL", "DOCM", "DOGC", "DOE", "DOG", "BOCM", "BORM", "BON", "BOPV",
        "BOR", "DOGV", "BOCCE", "BOME",
    }
    assert esperados <= {b["sigla"] for b in BOLETINES}
    assert "DOUE" in {b["sigla"] for b in BOLETINES}  # añadido para el Pilar 4


def test_bops_43_provincias():
    assert len(BOPS) == 43
    assert len({p for p, _ in BOPS}) == 43
    # uniprovinciales no deben tener BOP (§14)
    excluidas = {"Asturias", "Cantabria", "Madrid", "Murcia", "Navarra",
                 "La Rioja", "Baleares", "Ceuta", "Melilla"}
    assert not excluidas & {p for p, _ in BOPS}


def test_sigla_bop_normaliza():
    assert sigla_bop("Castellón") == "BOP-CASTELLON"
    assert sigla_bop("Araba/Álava") == "BOP-ARABA-ALAVA"
    assert sigla_bop("A Coruña") == "BOP-A-CORUNA"


def test_metanarrativas_son_12_y_coinciden_con_ddl():
    ddl = ["Estado ladron", "Espana rota", "Casta", "Abandono territorial",
           "Invasion", "Decadencia moral", "Europa nos manda", "Sablazo fiscal",
           "Chiringuito", "Censura", "Colapso servicios", "Inseguridad"]
    assert METANARRATIVAS == ddl
