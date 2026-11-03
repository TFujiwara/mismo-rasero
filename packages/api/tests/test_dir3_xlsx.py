from openpyxl import Workbook

from scrapers.dir3 import parse_unidades_xlsx


def _xlsx_con(rows: list[list[object]], tmp_path, nombre="test.xlsx"):
    wb = Workbook()
    ws = wb.active
    ws.title = "Unidades EELL"
    ws.append([])  # fila vacía, como el fichero real
    ws.append([""] + rows[0])  # el fichero real deja una col vacía a la izquierda
    for r in rows[1:]:
        ws.append([""] + r)
    path = tmp_path / nombre
    wb.save(path)
    return str(path)


def test_parse_unidades_xlsx_solo_vigentes(tmp_path):
    path = _xlsx_con([
        ["C_ID_UD_ORGANICA", "C_DNM_UD_ORGANICA", "C_ID_NIVEL_ADMON",
         "C_ID_TIPO_ENT_PUBLICA", "N_NIVEL_JERARQUICO", "C_DESC_PROV",
         "C_ID_DEP_UD_SUPERIOR", "C_DNM_UD_ORGANICA_SUPERIOR", "C_ID_ESTADO"],
        ["L02000012", "Diputació de Castelló", "3", "DP", "1",
         "Castelló/Castellón", "LA9999999", "Entidades Locales", "V"],
        ["LA0006005", "O.A.L. Escuela", "3", "DP", "2",
         "Castelló/Castellón", "L02000012", "Diputació de Castelló", "A"],
        ["L12047024", "Ayuntamiento de Vila-real", "3", "AY", "1",
         "Castelló/Castellón", "LA9999999", "Entidades Locales", "V"],
    ], tmp_path)

    unidades = parse_unidades_xlsx(path)
    assert len(unidades) == 2  # la anulada (A) se descarta
    dipu = next(u for u in unidades if u.codigo == "L02000012")
    assert dipu.tipo == "DP" and dipu.nivel == 1
    assert dipu.provincia == "Castelló/Castellón"
    assert dipu.padre == "LA9999999"
    ayto = next(u for u in unidades if u.codigo == "L12047024")
    assert ayto.nombre == "Ayuntamiento de Vila-real"


def test_parse_unidades_xlsx_filas_vacias(tmp_path):
    path = _xlsx_con([
        ["C_ID_UD_ORGANICA", "C_DNM_UD_ORGANICA", "C_ID_NIVEL_ADMON",
         "C_ID_TIPO_ENT_PUBLICA", "N_NIVEL_JERARQUICO", "C_DESC_PROV",
         "C_ID_DEP_UD_SUPERIOR", "C_DNM_UD_ORGANICA_SUPERIOR", "C_ID_ESTADO"],
        [None, None, None, None, None, None, None, None, None],
        ["L01010014", "Ayuntamiento de Alegría-Dulantzi", "3", "AY", "1",
         "Araba/Álava", "LA9999999", "Entidades Locales", "V"],
    ], tmp_path)
    unidades = parse_unidades_xlsx(path)
    assert len(unidades) == 1
