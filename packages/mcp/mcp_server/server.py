"""Servidor MCP de ¿Quién manda? — blueprint técnico v2.5.

Expone los datos de transparencia como herramientas para clientes LLM
(Claude Desktop, opencode, …). Mismo motor que la API web — sin ramas por
actor (§11). Transporte stdio por defecto; streamable-http opcional para
servirlo en red local.

Arranque:
  uv run blueprint-mcp                        # stdio (config de cliente LLM)
  uv run blueprint-mcp --transport streamable-http --port 8620

Config de cliente (ejemplo):
  {
    "mcpServers": {
      "mismo-rasero": {
        "command": "uv",
        "args": ["--directory", "/ruta/al/repo", "run", "blueprint-mcp"],
        "env": {"DATABASE_URL": "postgresql+psycopg://blueprint:blueprint@localhost:5432/blueprint"}
      }
    }
  }
"""

from __future__ import annotations

import argparse
from datetime import date

import sqlalchemy as sa
from mcp.server.mcpserver import MCPServer

from app.db import SessionLocal
from app.models import (
    Boletin,
    Competencia,
    DeclaracionR0,
    DisarmCounter,
    DisarmTechnique,
    ManualAccion,
    Norma,
)
from app.services.verificar import verificar_competencial

mcp = MCPServer(
    "mismo-rasero",
    instructions=(
        "Datos de transparencia administrativa española con fuente citada. "
        "Usa verificar_frase para cualquier '¿puede X hacer Y?' o '¿es verdad "
        "que…?': devuelve la cadena competencial (UE → Estado → CCAA → Local) "
        "con artículo y fuente BOE. Cita SIEMPRE la fuente que devuelven las "
        "herramientas — no inventes normativa."
    ),
)


def _sesion():
    return SessionLocal()


@mcp.tool()
def verificar_frase(texto: str) -> dict:
    """Comprueba si una frase es competencialmente posible y qué administración
    decide (ej.: '¿puede el ayuntamiento bajar el IRPF?'). Devuelve veredicto
    (FALSO/VERDADERO COMPETENCIAL o informativo), explicación llana, cadena
    competencial completa, artículo legal y fuente oficial. Úsalo SIEMPRE para
    preguntas de 'quién puede hacer qué' y cita la fuente que devuelve."""
    with _sesion() as db:
        return verificar_competencial(texto, session=db)


@mcp.tool()
def buscar_competencias(consulta: str) -> list[dict]:
    """Busca en el índice de competencias por palabra clave o nombre (ej.:
    'ibí', 'hospital', 'basura'). Útil para explorar qué temas están
    cubiertos y quién es responsable de cada uno."""
    with _sesion() as db:
        stmt = sa.select(Competencia).where(
            Competencia.nombre.ilike(f"%{consulta}%")
            | Competencia.slug.ilike(f"%{consulta}%")
        )
        rows = db.execute(stmt).scalars().all()
        return [
            {
                "id": c.id, "nombre": c.nombre, "slug": c.slug,
                "descripcion_llana": c.descripcion_llana,
                "cadena": [
                    t.strip()
                    for t in (c.descripcion_tecnica or "").split("->") if t.strip()
                ],
                "articulo_legal": c.articulo_legal,
                "fuente_url": c.fuente_url,
                "palabras_clave": c.palabras_clave,
            }
            for c in rows
        ]


@mcp.tool()
def listar_boletines(filtro: str | None = None) -> list[dict]:
    """Lista los boletines oficiales indexados (BOE, DOGV, BOPs provinciales…)
    con su URL y método de acceso. filtro opcional por sigla o nombre
    (ej.: 'valencia', 'BOE')."""
    with _sesion() as db:
        stmt = sa.select(Boletin).order_by(Boletin.id)
        if filtro:
            stmt = stmt.where(
                Boletin.sigla.ilike(f"%{filtro}%") | Boletin.nombre.ilike(f"%{filtro}%")
            )
        rows = db.execute(stmt).scalars().all()
        return [
            {
                "sigla": b.sigla, "nombre": b.nombre, "url_base": b.url_base,
                "metodo": b.metodo, "dificultad": b.dificultad,
                "ultimo_scrapeo": str(b.ultimo_scrapeo) if b.ultimo_scrapeo else None,
            }
            for b in rows
        ]


@mcp.tool()
def buscar_normas(
    boletin: str | None = None,
    desde: str | None = None,
    hasta: str | None = None,
    limite: int = 20,
) -> list[dict]:
    """Busca normas publicadas en boletines oficiales, con hash SHA-256 y URL
    al PDF original. Filtros: boletin (sigla, ej. 'BOE'), desde/hasta
    ('YYYY-MM-DD'), limite (máx 200)."""
    desde_d = date.fromisoformat(desde) if desde else None
    hasta_d = date.fromisoformat(hasta) if hasta else None
    with _sesion() as db:
        stmt = sa.select(Norma)
        if boletin:
            stmt = stmt.join(Boletin).where(Boletin.sigla == boletin.upper())
        if desde_d:
            stmt = stmt.where(Norma.fecha_pub >= desde_d)
        if hasta_d:
            stmt = stmt.where(Norma.fecha_pub <= hasta_d)
        rows = db.execute(
            stmt.order_by(Norma.fecha_pub.desc(), Norma.id.desc())
            .limit(min(limite, 200))
        ).scalars().all()
        return [
            {
                "id": n.id, "titulo": n.titulo, "rango": n.rango,
                "fecha_pub": str(n.fecha_pub), "url_pdf": n.url_pdf,
                "hash_sha256": n.hash_sha256,
            }
            for n in rows
        ]


@mcp.tool()
def como_reclamar() -> list[dict]:
    """Devuelve los trámites de acción ciudadana disponibles: alegaciones,
    instancias, queja al Síndic de Greuges, reclamación patrimonial y acceso
    a información pública — cada uno con dónde presentarlo y el artículo que
    ampara. Úsalo cuando el usuario quiera saber cómo reclamar o denunciar."""
    with _sesion() as db:
        rows = db.execute(sa.select(ManualAccion).order_by(ManualAccion.id)).scalars().all()
        return [
            {
                "tramite": m.tramite, "donde": m.donde, "sede_url": m.sede_url,
                "articulo_ampara": m.articulo_ampara, "plazo_dias": m.plazo_dias,
            }
            for m in rows
        ]


@mcp.tool()
def disarm(
    tipo: str = "RED",
    consulta: str | None = None,
    fase: str | None = None,
    limite: int = 30,
) -> list[dict]:
    """Explora el framework DISARM de patrones de desinformación. tipo='RED'
    devuelve técnicas del atacante (T-codes: cómo se manipula el discurso);
    tipo='BLUE' devuelve contramedidas (C-codes). fase opcional
    (Plan/Prepare/Execute/Assess), consulta por texto (ej. 'narrativa')."""
    with _sesion() as db:
        if tipo.upper() == "BLUE":
            stmt = sa.select(DisarmCounter)
            if consulta:
                stmt = stmt.where(DisarmCounter.nombre.ilike(f"%{consulta}%"))
            rows = db.execute(stmt.limit(min(limite, 200))).scalars().all()
            return [
                {"id": c.id, "nombre": c.nombre, "descripcion": c.descripcion}
                for c in rows
            ]
        stmt = sa.select(DisarmTechnique).where(DisarmTechnique.tipo == "RED")
        if consulta:
            stmt = stmt.where(
                DisarmTechnique.nombre.ilike(f"%{consulta}%")
                | DisarmTechnique.id.ilike(f"%{consulta}%")
            )
        if fase:
            stmt = stmt.where(DisarmTechnique.fase == fase.title())
        rows = db.execute(stmt.limit(min(limite, 200))).scalars().all()
        return [
            {
                "id": t.id, "tactica": t.tactica, "fase": t.fase,
                "nombre": t.nombre, "descripcion": t.descripcion, "url": t.url,
            }
            for t in rows
        ]


@mcp.tool()
def auditoria_sesgo(desde: str | None = None, hasta: str | None = None) -> dict:
    """Panel público de auditoría de sesgo (§11): declaraciones indexadas por
    partido, sin curación editorial. Prueba de neutralidad: el mismo rasero
    para gobierno y oposición."""
    desde_d = date.fromisoformat(desde) if desde else None
    hasta_d = date.fromisoformat(hasta) if hasta else None
    with _sesion() as db:
        stmt = sa.select(
            DeclaracionR0.partido,
            DeclaracionR0.rol,
            sa.func.count().label("total"),
            sa.func.sum(sa.case((DeclaracionR0.verificado.is_(True), 1), else_=0))
            .label("verificadas"),
        ).group_by(DeclaracionR0.partido, DeclaracionR0.rol)
        if desde_d:
            stmt = stmt.where(DeclaracionR0.fecha >= desde_d)
        if hasta_d:
            stmt = stmt.where(DeclaracionR0.fecha <= hasta_d)
        rows = db.execute(stmt).all()
        return {
            "por_partido_rol": [
                {
                    "partido": p, "rol": r, "total": t,
                    "verificadas": v or 0,
                }
                for p, r, t, v in rows
            ],
            "nota": "Sin curación editorial. Los veredictos por partido se "
            "activan en Fase 4 con el motor completo.",
        }


@mcp.tool()
def estado_sistema() -> dict:
    """Estado del sistema: cuántas filas hay en cada tabla. Úsalo primero para
    saber qué datos están disponibles y calibrar las respuestas."""
    with _sesion() as db:
        def _count(model) -> int:
            return db.execute(sa.select(sa.func.count()).select_from(model)).scalar()

        return {
            "boletines": _count(Boletin),
            "competencias": _count(Competencia),
            "normas": _count(Norma),
            "trámites_accion": _count(ManualAccion),
            "disarm_techniques": _count(DisarmTechnique),
            "disarm_counters": _count(DisarmCounter),
            "declaraciones_r0": _count(DeclaracionR0),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor MCP ¿Quién manda?")
    parser.add_argument("--transport", choices=["stdio", "streamable-http"],
                        default="stdio")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8620)
    args = parser.parse_args()

    if args.transport == "streamable-http":
        mcp.run(transport=args.transport, host=args.host, port=args.port)
    else:
        mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
