"""API v1 — blueprint §17. Fase 1: health, boletines, normas, competencias,
disarm, auditoria/sesgo, ingest. Pilar 6 (motor LLM de verificación) llega en Fase 4.
"""

from __future__ import annotations

from datetime import date

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import (
    Boletin,
    Competencia,
    DeclaracionR0,
    DisarmCounter,
    DisarmTechnique,
    Norma,
)
from app.seeds.runner import (
    seed_boletines,
    seed_competencias,
    seed_manual_accion,
    seed_metanarrativas,
)
from app.services.ingest import run_boletin, run_dir3, run_dir3_xlsx

router = APIRouter(prefix="/api/v1")


@router.get("/health")
def health(db: Session = Depends(get_db)):
    import os
    import time

    db_ok = True
    try:
        db.execute(sa.text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_ok = False
    return {
        "status": "ok", "db": db_ok,
        "version": "0.1.0",
        "deploy_ts": os.environ.get("DEPLOY_TS") or str(int(time.time())),
    }


@router.get("/boletines")
def listar_boletines(q: str | None = None, db: Session = Depends(get_db)):
    stmt = sa.select(Boletin).order_by(Boletin.id)
    if q:
        stmt = stmt.where(Boletin.sigla.ilike(f"%{q}%") | Boletin.nombre.ilike(f"%{q}%"))
    rows = db.execute(stmt).scalars().all()
    return [
        {
            "id": b.id, "sigla": b.sigla, "nombre": b.nombre,
            "url_base": b.url_base, "metodo": b.metodo, "dificultad": b.dificultad,
            "ultimo_scrapeo": b.ultimo_scrapeo,
        }
        for b in rows
    ]


@router.get("/quien-manda")
def quien_manda(direccion: str = Query(..., min_length=4),
                db: Session = Depends(get_db)):
    """Pilar 1 (§01): geocodifica la dirección y devuelve el organigrama
    completo UE → Estado → CCAA → Diputación → Ayuntamiento, cada nivel con
    qué puede hacer, qué no y la fuente legal. La mancomunidad queda marcada
    como pendiente del seed DIR3."""
    from app.services.quien_manda import quien_manda as resolver

    return resolver(direccion, db)


@router.get("/normas")
def listar_normas(
    boletin: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    limit: int = Query(50, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    stmt = sa.select(Norma)
    if boletin:
        stmt = stmt.join(Boletin).where(Boletin.sigla == boletin.upper())
    if desde:
        stmt = stmt.where(Norma.fecha_pub >= desde)
    if hasta:
        stmt = stmt.where(Norma.fecha_pub <= hasta)
    total = db.execute(sa.select(sa.func.count()).select_from(stmt.subquery())).scalar()
    rows = db.execute(stmt.order_by(Norma.fecha_pub.desc(), Norma.id.desc()).limit(limit).offset(offset)).scalars().all()
    return {
        "total": total,
        "items": [
            {
                "id": n.id, "titulo": n.titulo, "rango": n.rango,
                "fecha_pub": n.fecha_pub, "numero_boletin": n.numero_boletin,
                "url_pdf": n.url_pdf, "hash_sha256": n.hash_sha256,
            }
            for n in rows
        ],
    }


@router.get("/normas/{norma_id}")
def detalle_norma(norma_id: int, db: Session = Depends(get_db)):
    n = db.get(Norma, norma_id)
    if n is None:
        raise HTTPException(404, "norma no encontrada")
    return {
        "id": n.id, "titulo": n.titulo, "rango": n.rango, "fecha_pub": n.fecha_pub,
        "numero_boletin": n.numero_boletin, "url_pdf": n.url_pdf,
        "hash_sha256": n.hash_sha256, "texto_consolidado": n.texto_consolidado,
    }


@router.get("/competencias")
def buscar_competencias(q: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    """Búsqueda por palabras_clave (GIN, §02) y por nombre — base del Pilar 6."""
    stmt = sa.select(Competencia).where(
        Competencia.palabras_clave.any(sa.func.lower(q))
        | Competencia.nombre.ilike(f"%{q}%")
    )
    rows = db.execute(stmt).scalars().all()
    return [
        {
            "id": c.id, "nombre": c.nombre, "slug": c.slug,
            "descripcion_llana": c.descripcion_llana,
            "articulo_legal": c.articulo_legal, "fuente_url": c.fuente_url,
            "administracion_id": c.administracion_id,
            "palabras_clave": c.palabras_clave,
        }
        for c in rows
    ]


@router.get("/accion")
def listar_accion(db: Session = Depends(get_db)):
    """Manual de acción §08: cómo reclamar cada cosa, con el artículo que ampara."""
    from app.models import ManualAccion

    rows = db.execute(sa.select(ManualAccion).order_by(ManualAccion.id)).scalars().all()
    return [
        {
            "id": m.id, "tramite": m.tramite, "donde": m.donde,
            "sede_url": m.sede_url, "articulo_ampara": m.articulo_ampara,
            "plazo_dias": m.plazo_dias,
        }
        for m in rows
    ]


@router.get("/verificar")
def verificar(texto: str = Query(..., min_length=4), db: Session = Depends(get_db)):
    """Pilar 6, versión determinista: match de la frase del usuario contra las
    palabras clave de cada competencia (lo que el LLM de Fase 4 sustituirá por
    extracción semántica). Devuelve explicación llana + cadena competencial
    (parseada de '->') + fuente citada. Sin LLM, sin veredicto especulativo."""
    from app.services.verificar import verificar_competencial

    return verificar_competencial(texto, session=db)


@router.get("/disarm/techniques")
def disarm_techniques(
    fase: str | None = None,
    tipo: str | None = Query(None, pattern="^(RED|BLUE)$"),
    q: str | None = None,
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
):
    stmt = sa.select(DisarmTechnique)
    if fase:
        stmt = stmt.where(DisarmTechnique.fase == fase.upper())
    if tipo:
        stmt = stmt.where(DisarmTechnique.tipo == tipo.upper())
    if q:
        stmt = stmt.where(DisarmTechnique.nombre.ilike(f"%{q}%") | DisarmTechnique.id.ilike(f"%{q}%"))
    rows = db.execute(stmt.limit(limit)).scalars().all()
    return [
        {
            "id": t.id, "fase": t.fase, "tactica": t.tactica, "nombre": t.nombre,
            "descripcion": t.descripcion, "url": t.url, "tipo": t.tipo,
        }
        for t in rows
    ]


@router.get("/disarm/counters")
def disarm_counters(q: str | None = None, limit: int = Query(200, le=1000),
                    db: Session = Depends(get_db)):
    stmt = sa.select(DisarmCounter)
    if q:
        stmt = stmt.where(DisarmCounter.nombre.ilike(f"%{q}%") | DisarmCounter.id.ilike(f"%{q}%"))
    rows = db.execute(stmt.limit(limit)).scalars().all()
    return [
        {"id": c.id, "nombre": c.nombre, "descripcion": c.descripcion}
        for c in rows
    ]


@router.get("/auditoria/sesgo")
def auditoria_sesgo(
    desde: date | None = None,
    hasta: date | None = None,
    db: Session = Depends(get_db),
):
    """§11 — panel público de sesgo, sin curación editorial.

    Nota honesta: el DDL §19 no incluye una tabla de veredictos ligada a
    declaraciones_r0 (los veredictos FALSO/VERDADERO se persisten en Fase 4 con
    el motor). Mientras tanto este endpoint devuelve el conteo de declaraciones
    por partido/rol y el % verificado; los pct_* de veredicto llegan con el motor.
    """
    stmt = sa.select(
        DeclaracionR0.partido,
        sa.func.count().label("total"),
        sa.func.sum(sa.case((DeclaracionR0.verificado.is_(True), 1), else_=0)).label("verificadas"),
    ).group_by(DeclaracionR0.partido)
    if desde:
        stmt = stmt.where(DeclaracionR0.fecha >= desde)
    if hasta:
        stmt = stmt.where(DeclaracionR0.fecha <= hasta)
    rows = db.execute(stmt).all()

    por_partido = []
    for partido, total, verificadas in rows:
        total = total or 0
        verificadas = verificadas or 0
        por_partido.append({
            "partido": partido,
            "total_verificaciones": total,
            "pct_falso": None,
            "pct_verdadero": None,
            "pct_parcial": None,
            "pct_verificado": round(100 * verificadas / total, 1) if total else 0.0,
        })

    return {
        "por_partido": por_partido,
        "nota": (
            "Publicado automáticamente, sin curación editorial. Los porcentajes de "
            "veredicto (FALSO/VERDADERO/PARCIAL) se activan en Fase 4 cuando el motor "
            "de verificación persista veredictos ligados a declaraciones; mientras "
            "tanto se expone el % de declaraciones verificadas por partido."
        ),
    }


@router.post("/ingest/boletin/{sigla}")
def ingest_boletin(
    sigla: str,
    fecha: date,
    limit: int | None = Query(None, le=2000),
    db: Session = Depends(get_db),
):
    """Ejecuta el adaptador del boletín para una fecha y persiste en normas."""
    try:
        resumen = run_boletin(db, sigla, fecha, limit)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"ingesta falló: {exc}") from exc
    return {
        "sigla": resumen.sigla, "fecha": resumen.fecha, "total": resumen.total,
        "nuevos": resumen.nuevos, "duplicados": resumen.duplicados,
        "errores_pdf": resumen.errores_pdf,
    }


@router.post("/ingest/dir3-xlsx")
def ingest_dir3_xlsx(path: str, db: Session = Depends(get_db)):
    """Ingesta del listado XLSX del CTT (unidades DIR3). path = fichero local
    en el servidor (ej. data/dir3/eell_full.xlsx)."""
    import os

    if not os.path.isfile(path):
        raise HTTPException(404, f"no existe {path}")
    try:
        return run_dir3_xlsx(db, path)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"ingesta DIR3 falló: {exc}") from exc


@router.post("/ingest/dir3")
def ingest_dir3(url: str | None = None, db: Session = Depends(get_db)):
    try:
        n = run_dir3(db, url)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"nuevas_administraciones": n}


@router.post("/ingest/presupuestos")
def ingest_presupuestos(
    ccaa: str = Query("17"),
    provincia: str = Query("12"),
    tipo: str = Query("A5"),
    ejercicio: int = Query(2024),
    max_entidades: int | None = Query(None, le=300),
    db: Session = Depends(get_db),
):
    """Pilar 3: scrapea el portal público SGCIEF de Hacienda e ingesta los
    presupuestos (F.1.1.1) de las entidades seleccionadas. Síncrono — usa
    max_entidades para pruebas (una entidad ≈ 7 peticiones)."""
    from scrapers.hacienda import SgciefScraper

    resultados, errores = [], []
    with SgciefScraper(ejercicio) as scraper:
        entidades = scraper.abrir_sesion(ccaa, provincia, tipo)
        if max_entidades:
            entidades = entidades[:max_entidades]
        for e in entidades:
            try:
                resumen = scraper.resumen_de_entidad(e["id"], nombre_sesion=e["nombre"])
                from app.services.presupuestos import ingresar_resumen

                resultados.append(ingresar_resumen(db, resumen, tipo))
            except Exception as exc:  # noqa: BLE001 — una entidad sin datos no tumba la ingesta
                errores.append({"entidad": e["nombre"], "error": str(exc)[:120]})
    return {"total_entidades": len(entidades), "ingestadas": len(resultados),
            "resultados": resultados, "errores": errores}


@router.get("/presupuestos/municipio/{nombre}")
def presupuestos_municipio(nombre: str, ano: int | None = None,
                           db: Session = Depends(get_db)):
    """Pilar 3 (§03): el desglose real por capítulos de un municipio, en euros
    y en % — con la fuente del portal de Hacienda."""
    from app.services.presupuestos import desglose_municipio

    resultado = desglose_municipio(db, nombre, ano)
    if resultado is None:
        raise HTTPException(404, f"sin presupuestos para {nombre} — ejecuta la ingesta")
    return resultado


@router.get("/fiscalidad")
def fiscalidad(db: Session = Depends(get_db)):
    """Pilar 3 (§03): de cada 100 € que pagas de IRPF/IVA/IBI, quién se queda
    qué — con la ley delante."""
    from app.services.dinero import fiscalidad as _fiscalidad

    return _fiscalidad(db)


@router.get("/norma/{norma_id}/flujo")
def flujo_de_norma(norma_id: int, db: Session = Depends(get_db)):
    """Pilar 4 (§04): el flujo DOUE → BOE → DOGV → BOP en el que participa
    una norma, con los pasos aún no localizados marcados como pendientes."""
    from app.services.flujo import timeline_de_norma

    resultado = timeline_de_norma(db, norma_id)
    if resultado is None:
        raise HTTPException(404, "esta norma no participa en ningún flujo indexado")
    return resultado


@router.post("/flujo/seed-ejemplo")
def flujo_seed_ejemplo(db: Session = Depends(get_db)):
    """Siembra el flujo canónico del §04: Directiva 2019/904 (plásticos)
    → Ley 7/2022 (residuos). DOGV y BOP quedan como pasos pendientes."""
    from app.services.flujo import seed_flujo_ejemplo

    return seed_flujo_ejemplo(db)


@router.post("/ingest/boe-norma/{identificador}")
def ingest_boe_norma(identificador: str, db: Session = Depends(get_db)):
    """Ingesta de una norma concreta del BOE por identificador (ej.
    BOE-A-2022-5809), sin esperar al scrapeo del sumario diario."""
    from app.services.ingest import run_boe_norma

    try:
        return run_boe_norma(db, identificador)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"ingesta falló: {exc}") from exc


@router.post("/seed")
def seed(target: str = Query(
    "all",
    pattern="^(all|boletines|metanarrativas|competencias|accion|impuestos)$",
),
         db: Session = Depends(get_db)):
    if target in ("all", "boletines"):
        seed_boletines(db)
    if target in ("all", "metanarrativas"):
        seed_metanarrativas(db)
    if target in ("all", "competencias"):
        seed_competencias(db)
    if target in ("all", "accion"):
        seed_manual_accion(db)
    if target in ("all", "impuestos"):
        from app.services.dinero import seed_impuestos

        seed_impuestos(db)
    return {"seed": target, "ok": True}
