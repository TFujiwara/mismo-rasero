"""Pilar 3 — ingesta de presupuestos EELL reales (Hacienda, portal SGCIEF público).

Convierte los resúmenes F.1.1.1 (XML) en filas de `presupuestos`:
  capitulo = ingresos_1..ingresos_9 | gastos_1..gastos_9 | ingresos_total | gastos_total
El enlace con administraciones se hace por nombre normalizado ("Vila-real" →
"Ayuntamiento de Vila-real" del seed DIR3); si no existe, se crea.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from app.models import Administracion, Presupuesto
from app.services.verificar import normaliza

if TYPE_CHECKING:  # pragma: no cover
    from sqlalchemy.orm import Session


def _mejor_administracion(candidatos: list[Administracion], nombre: str) -> Administracion | None:
    """'Almassora' debe caer en 'Ayuntamiento de Almassora', NO en 'Correos
    Almassora-Almazora' (ambas existen en el seed DIR3). Prioridad:
    1) 'Ayuntamiento de {nombre}' exacto, 2) candidatas tipo AY que contengan
    el nombre — la más corta, 3) match exacto a secas, 4) la más corta."""
    objetivo = normaliza(nombre)
    objetivo_ayto = normaliza(f"Ayuntamiento de {nombre}")
    for c in candidatos:
        if normaliza(c.nombre or "") == objetivo_ayto:
            return c
    ays = [c for c in candidatos if c.entidad_tipo == "AY" and objetivo in normaliza(c.nombre or "")]
    if ays:
        return min(ays, key=lambda c: len(normaliza(c.nombre or "")))
    for c in candidatos:
        if normaliza(c.nombre or "") == objetivo:
            return c
    validos = [c for c in candidatos if objetivo in normaliza(c.nombre or "")]
    if validos:
        return min(validos, key=lambda c: len(normaliza(c.nombre or "")))
    return None


def _busca_o_crea_administracion(session: "Session", nombre: str, tipo: str) -> Administracion:
    """Encuentra la administración por nombre normalizado; si no hay match
    claro, la crea (los códigos INE del portal SGCIEF no están en el DDL)."""
    candidatos = session.execute(
        select(Administracion).where(Administracion.nombre.ilike(f"%{nombre}%"))
    ).scalars().all()
    mejor = _mejor_administracion(candidatos, nombre)
    if mejor is not None:
        return mejor

    prefijo = {"AY": "Ayuntamiento de", "DD": "Diputación Provincial de",
               "MM": "Mancomunidad de"}.get(tipo, "")
    nueva = Administracion(nombre=f"{prefijo}{nombre}".strip(), tipo="MUNICIPIO", nivel=5)
    session.add(nueva)
    session.flush()
    return nueva


def ingresar_resumen(
    session: "Session", resumen, tipo_entidad: str
) -> dict:
    """Persiste un ResumenPresupuesto en presupuestos (borrado previo del
    ejercicio para idempotencia)."""
    admin = _busca_o_crea_administracion(session, resumen.nombre_entidad, tipo_entidad)
    session.query(Presupuesto).filter(
        (Presupuesto.administracion_id == admin.id)
        & (Presupuesto.ano == resumen.ejercicio)
        & (Presupuesto.fuente_url == resumen.fuente_url)
    ).delete()

    n = 0
    for clave, importe in sorted(resumen.ingresos.items()):
        session.add(Presupuesto(
            administracion_id=admin.id, ano=resumen.ejercicio,
            capitulo=f"ingresos_{clave}", importe=int(round(importe)),
            fuente_url=resumen.fuente_url,
        ))
        n += 1
    for clave, importe in sorted(resumen.gastos.items()):
        session.add(Presupuesto(
            administracion_id=admin.id, ano=resumen.ejercicio,
            capitulo=f"gastos_{clave}", importe=int(round(importe)),
            fuente_url=resumen.fuente_url,
        ))
        n += 1
    session.commit()
    return {"administracion": admin.nombre, "ejercicio": resumen.ejercicio, "filas": n}


CAPITULO_NOMBRES = {
    "gastos_1": "Gastos de personal",
    "gastos_2": "Bienes y servicios",
    "gastos_3": "Gastos financieros",
    "gastos_4": "Transferencias corrientes",
    "gastos_5": "Fondo de contingencia",
    "gastos_6": "Inversiones reales",
    "gastos_7": "Transferencias de capital",
    "gastos_8": "Activos financieros",
    "gastos_9": "Pasivos financieros (amortización deuda)",
    "gastos_total": "TOTAL GASTOS",
    "ingresos_total": "TOTAL INGRESOS",
}


def comparativa_de(
    filas_por_ano: dict[int, dict[str, int]], anos: list[int]
) -> dict | None:
    """Comparación interanual pura: filas por año (capitulo → importe) y los
    dos años a comparar → capítulos con delta %. Testeable sin BD.
    El orden de `anos` da igual: se ordena dentro (anterior = penúltimo)."""
    if len(anos) < 2:
        return None
    anos_ord = sorted(anos)
    prev, ult = anos_ord[-2], anos_ord[-1]
    capitulos = sorted(
        set(filas_por_ano.get(prev, {})) | set(filas_por_ano.get(ult, {}))
    )
    filas = []
    for cap in capitulos:
        if cap in ("ingresos_total", "gastos_total"):
            continue
        a_prev = filas_por_ano.get(prev, {}).get(cap, 0)
        a_ult = filas_por_ano.get(ult, {}).get(cap, 0)
        delta = round(100 * (a_ult - a_prev) / a_prev, 1) if a_prev else None
        filas.append({
            "capitulo": cap,
            "nombre": CAPITULO_NOMBRES.get(cap, cap),
            f"importe_{prev}": a_prev,
            f"importe_{ult}": a_ult,
            "delta_pct": delta,
        })
    tot = {}
    for cap, destino in (("ingresos_total", "ingresos"), ("gastos_total", "gastos")):
        a_prev = filas_por_ano.get(prev, {}).get(cap, 0)
        a_ult = filas_por_ano.get(ult, {}).get(cap, 0)
        delta = round(100 * (a_ult - a_prev) / a_prev, 1) if a_prev else None
        tot[destino] = {
            f"importe_{prev}": a_prev, f"importe_{ult}": a_ult, "delta_pct": delta,
        }
    return {"ano_anterior": prev, "ano_ultimo": ult,
            "totales": tot, "por_capitulo": filas}


def desglose_municipio(session: "Session", nombre: str, ano: int | None = None) -> dict | None:
    """El desglose real de un municipio: capítulos en % y euros del último
    ejercicio disponible, más la comparación con el año anterior si hay datos."""
    candidatos = session.execute(
        select(Administracion).where(Administracion.nombre.ilike(f"%{nombre}%"))
    ).scalars().all()
    admin = _mejor_administracion(candidatos, nombre)
    if admin is None:
        return None

    filas = session.execute(
        select(Presupuesto).where(Presupuesto.administracion_id == admin.id)
    ).scalars().all()
    if not filas:
        return None

    anos_disponibles = sorted({f.ano for f in filas}, reverse=True)
    ano_real = anos_disponibles[0] if ano is None else ano
    if ano_real not in anos_disponibles:
        return None
    de_este_ano = [f for f in filas if f.ano == ano_real]
    ingresos_total = next(
        (f.importe for f in de_este_ano if f.capitulo == "ingresos_total"), 0
    )
    gastos_total = next(
        (f.importe for f in de_este_ano if f.capitulo == "gastos_total"), 0
    )
    gastos = []
    for f in sorted(de_este_ano, key=lambda x: x.capitulo):
        if not f.capitulo.startswith("gastos_") or f.capitulo == "gastos_total":
            continue
        pct = round(100 * f.importe / gastos_total, 1) if gastos_total else 0
        gastos.append({
            "capitulo": f.capitulo,
            "nombre": CAPITULO_NOMBRES.get(f.capitulo, f.capitulo),
            "importe_euros": f.importe, "pct": pct,
        })

    filas_por_ano: dict[int, dict[str, int]] = {}
    for f in filas:
        filas_por_ano.setdefault(f.ano, {})[f.capitulo] = f.importe
    comparativa = comparativa_de(filas_por_ano, anos_disponibles)

    return {
        "administracion": admin.nombre,
        "ejercicio": ano_real,
        "ingresos_total_euros": ingresos_total,
        "gastos_total_euros": gastos_total,
        "gastos_por_capitulo": gastos,
        "comparativa": comparativa,
        "fuente_url": de_este_ano[0].fuente_url,
        "fuente": "Ministerio de Hacienda — portal público de presupuestos EELL (SGCIEF)",
    }
