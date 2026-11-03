"""Pilar 3 — impuestos y reparto (§03): de cada 100 € que pagas, quién se queda qué.

Los tres impuestos canónicos del blueprint con sus cadenas y fuentes. El
reparto (split) no tiene columna en el DDL §19: el endpoint /fiscalidad lo
compone a partir de esta tabla + el mapa SPLIT de abajo (curado, con fuente).
"""

from app.models import Impuesto

IMPUESTOS: list[dict] = [
    {
        "nombre": "IRPF",
        "quien_legisla": "Estado (Ley 35/2006, tramo estatal) + Generalitat "
        "Valenciana (Ley 13/1997, tramo autonómico)",
        "quien_recauda": "AEAT (agencia estatal, recauda también el tramo "
        "autonómico salvo convenio)",
        "quien_decide_tipo": "Estado fija la escala general; la CCAA fija su "
        "tramo autonómico. El ayuntamiento no puede tocarlo.",
        "fuente_ley_url": "https://www.boe.es/buscar/act.php?id=BOE-A-2006-20764",
        "ordenanza_bop_url": None,
    },
    {
        "nombre": "IVA",
        "quien_legisla": "Estado (Ley 37/1992, LIVA) dentro del marco de la "
        "Directiva 2006/112/CE de la UE",
        "quien_recauda": "AEAT",
        "quien_decide_tipo": "Los tipos los fija el Estado (general 21%, "
        "reducidos 10% y 4%) — la CCAA no puede, el ayuntamiento tampoco.",
        "fuente_ley_url": "https://www.boe.es/buscar/act.php?id=BOE-A-1992-28925",
        "ordenanza_bop_url": None,
    },
    {
        "nombre": "IBI",
        "quien_legisla": "Estado (RDL 2/2004, TRLHL, art. 59-77)",
        "quien_recauda": "Tu ayuntamiento (100%)",
        "quien_decide_tipo": "El ayuntamiento fija el tipo dentro de la "
        "horquilla legal (art. 72) en su ordenanza fiscal, publicada en el BOP.",
        "fuente_ley_url": "https://www.boe.es/buscar/act.php?id=BOE-A-2004-4214",
        "ordenanza_bop_url": "https://bop.dipcas.es/",
    },
]

# reparto de cada 100 € (§03) — curado y con fuente legal en cada fila
SPLITS: dict[str, list[dict]] = {
    "IRPF": [
        {"destino": "Estado (PGE)", "porcentaje": 50,
         "por_que": "tramo estatal (Ley 35/2006)"},
        {"destino": "Comunidad autónoma", "porcentaje": 50,
         "por_que": "cesión del 50% (Ley 22/2009)"},
    ],
    "IVA": [
        {"destino": "Estado (PGE)", "porcentaje": 50,
         "por_que": "LIVA"},
        {"destino": "Comunidad autónoma", "porcentaje": 50,
         "por_que": "cesión del 50% de la recaudación (Ley 22/2009)"},
    ],
    "IBI": [
        {"destino": "Tu ayuntamiento", "porcentaje": 100,
         "por_que": "RDL 2/2004, art. 59 y ss."},
    ],
}


def seed_impuestos(session) -> int:
    # impuestos.nombre no tiene constraint UNIQUE en el DDL §19 — upsert manual
    existentes = {n for (n,) in session.query(Impuesto.nombre).all()}
    n = 0
    for i in IMPUESTOS:
        if i["nombre"] in existentes:
            continue
        session.add(Impuesto(**i))
        n += 1
    session.commit()
    return n


def fiscalidad(session) -> dict:
    """El desglose de §03: de cada 100 € que pagas de cada impuesto, quién se
    queda qué — con fuente."""
    filas = session.query(Impuesto).order_by(Impuesto.id).all()
    impuestos = []
    for i in filas:
        impuestos.append({
            "nombre": i.nombre,
            "quien_legisla": i.quien_legisla,
            "quien_recauda": i.quien_recauda,
            "quien_decide_tipo": i.quien_decide_tipo,
            "reparto_100_euros": SPLITS.get(i.nombre, []),
            "fuente_ley_url": i.fuente_ley_url,
            "ordenanza_bop_url": i.ordenanza_bop_url,
        })
    return {
        "titulo": "De cada 100 € que pagas, ¿quién se queda qué?",
        "impuestos": impuestos,
        "nota": "Repartos del blueprint §03, con la ley delante. La "
        "personalización por renta y municipio (¿cuánto te toca a ti?) llega "
        "con los presupuestos EELL de la Fase 3.",
    }
