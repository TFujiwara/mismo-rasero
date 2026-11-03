from app.services.presupuestos import comparativa_de

FILAS = {
    2023: {
        "gastos_1": 100_000, "gastos_2": 200_000,
        "gastos_total": 300_000, "ingresos_total": 310_000,
    },
    2024: {
        "gastos_1": 110_000, "gastos_2": 180_000,
        "gastos_total": 290_000, "ingresos_total": 295_000,
    },
}


def test_comparativa_basica():
    c = comparativa_de(FILAS, [2023, 2024])
    assert c["ano_anterior"] == 2023 and c["ano_ultimo"] == 2024
    tot = c["totales"]["gastos"]
    assert tot["importe_2023"] == 300_000 and tot["importe_2024"] == 290_000
    assert tot["delta_pct"] == -3.3
    assert c["totales"]["ingresos"]["delta_pct"] == round(
        100 * (295_000 - 310_000) / 310_000, 1
    )


def test_comparativa_por_capitulo():
    c = comparativa_de(FILAS, [2023, 2024])
    personal = next(f for f in c["por_capitulo"] if f["capitulo"] == "gastos_1")
    assert personal["nombre"] == "Gastos de personal"
    assert personal["delta_pct"] == 10.0
    bienes = next(f for f in c["por_capitulo"] if f["capitulo"] == "gastos_2")
    assert bienes["delta_pct"] == -10.0
    # total nunca aparece como capítulo (va en totales)
    assert all(f["capitulo"] != "gastos_total" for f in c["por_capitulo"])


def test_comparativa_sin_ano_previo():
    filas = {2024: FILAS[2024]}
    assert comparativa_de(filas, [2024]) is None
    assert comparativa_de({}, []) is None


def test_comparativa_capitulo_nuevo_sin_base():
    filas = {
        2023: {"gastos_total": 100_000},
        2024: {"gastos_total": 110_000, "gastos_1": 50_000},
    }
    c = comparativa_de(filas, [2023, 2024])
    nuevo = next(f for f in c["por_capitulo"] if f["capitulo"] == "gastos_1")
    assert nuevo["importe_2023"] == 0 and nuevo["delta_pct"] is None
