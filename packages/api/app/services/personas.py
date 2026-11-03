"""Pilar 5 — personas: diputados del Congreso vía datos abiertos.

Verificado en vivo (nov. 2026): el Congreso publica a diario en
https://www.congreso.es/opendata/diputados los listados:
  DiputadosActivos__*.json, Diputadas__*.json, DiputadosDeBaja__*.json
  (cada registro: NOMBRE, CIRCUNSCRIPCION, FORMACIONELECTORAL, FECHAALTA,
   GRUPOPARLAMENTARIO, BIOGRAFIA)

Las URLs llevan timestamp de generación — se descubren raspando la página
/opendata/diputados (los tres ficheros, cualquier formato; se prefiere JSON).
"""

from __future__ import annotations

import re
from datetime import datetime

import httpx
from sqlalchemy import select

from app.models import Administracion, PersonaCargo

BASE_OD = "https://www.congreso.es/webpublica/opendata/diputados"
PAGINA = "https://www.congreso.es/opendata/diputados"
FUENTE = "https://www.congreso.es/opendata/diputados"


def _ficheros(session_http: httpx.Client) -> list[str]:
    r = session_http.get(PAGINA)
    r.raise_for_status()
    urls = re.findall(r'href="(/webpublica/opendata/diputados/[^"]*\.json)"', r.text)
    return [f"https://www.congreso.es{u}" for u in urls]


def _valor(registro: dict, campo: str) -> str:
    return (registro.get(campo) or "").strip()


def _fecha(texto: str):
    try:
        return datetime.strptime(texto.strip(), "%d/%m/%Y").date()
    except (ValueError, AttributeError):
        return None


def _admin_congreso(session) -> Administracion:
    admin = session.execute(
        select(Administracion).where(Administracion.nombre == "Congreso de los Diputados")
    ).scalar_one_or_none()
    if admin is None:
        admin = Administracion(
            nombre="Congreso de los Diputados", tipo="CONGRESO", nivel=2,
            entidad_tipo="CA",
        )
        session.add(admin)
        session.flush()
    return admin


def _cargo(nombre_formacion: str) -> str:
    return f"Diputado/a — {nombre_formacion}".strip(" —")


def ingestar_congreso(session) -> dict:
    """Baja los tres listados JSON y refresca personas_cargos para el Congreso.
    Idempotente: borra antes las filas de esta fuente y repuebla."""
    with httpx.Client(
        headers={"User-Agent": "Mismo Rasero/0.1"}, follow_redirects=True, timeout=90
    ) as client:
        urls = _ficheros(client)
        if not urls:
            raise RuntimeError("no se han encontrado ficheros JSON de diputados")
        registros = []
        for url in urls:
            r = client.get(url)
            r.raise_for_status()
            data = r.json()
            registros.extend(data if isinstance(data, list) else [])
            fuente_url = url

    admin = _admin_congreso(session)

    # idempotencia por fuente: se repuebla el bloque del Congreso
    session.query(PersonaCargo).filter(
        PersonaCargo.fuente_nombramiento_url.like(f"{FUENTE}%")
    ).delete(synchronize_session=False)

    vistos: set[tuple[str, str]] = set()
    n = 0
    for registro in registros:
        nombre = _valor(registro, "NOMBRE")
        grupo = _valor(registro, "GRUPOPARLAMENTARIO")
        if not nombre or (nombre, grupo) in vistos:
            continue
        vistos.add((nombre, grupo))
        session.add(PersonaCargo(
            nombre=nombre,
            cargo=_cargo(grupo),
            administracion_id=admin.id,
            sueldo_anual=None,
            agenda_json={
                "circunscripcion": _valor(registro, "CIRCUNSCRIPCION"),
                "formacion_electoral": _valor(registro, "FORMACIONELECTORAL"),
                "grupo_parlamentario": grupo,
                "fecha_alta": _valor(registro, "FECHAALTA"),
                "fecha_condicion_plena": _valor(registro, "FECHACONDICIONPLENA"),
                "biografia": _valor(registro, "BIOGRAFIA"),
                "lista_origen": url.split("/")[-1],
            },
            fecha_inicio=_fecha(registro.get("FECHAALTA")),
            fuente_nombramiento_url=fuente_url,
        ))
        n += 1
    session.commit()
    return {"registros_leidos": len(registros), "personas_insertadas": n,
            "fuente": fuente_url}


def buscar_personas(session, nombre: str, limite: int = 25) -> list[dict]:
    from app.services.verificar import normaliza

    objetivo = normaliza(nombre)
    filas = session.execute(
        select(PersonaCargo, Administracion.nombre)
        .join(Administracion,
              PersonaCargo.administracion_id == Administracion.id, isouter=True)
    ).all()

    # el Congreso guarda nombres con acentos variables ("Sánchez"/"Sanchez"):
    # filtrado por normalizado en memoria — la tabla es pequeña
    resultado = []
    for p, admin_nombre in filas:
        if objetivo not in normaliza(p.nombre or ""):
            continue
        extra = p.agenda_json or {}
        resultado.append({
            "id": p.id, "nombre": p.nombre, "cargo": p.cargo,
            "admin": admin_nombre,
            "fecha_inicio": str(p.fecha_inicio) if p.fecha_inicio else None,
            "circunscripcion": extra.get("circunscripcion"),
            "grupo": extra.get("grupo_parlamentario"),
            "biografia": extra.get("biografia"),
            "fuente_url": p.fuente_nombramiento_url,
        })
    # completos primero (con grupo), dentro por alta más reciente
    resultado.sort(key=lambda p: (
        bool(p["grupo"]),
        p["fecha_inicio"] or "",
    ), reverse=True)
    return resultado[:limite]
