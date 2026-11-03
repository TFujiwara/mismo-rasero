"""Manual de acción — los 5 trámites del blueprint §08.

Cómo reclamar cada cosa, con el artículo que te ampara. modelo_docx_url y
fuente_bop_url quedan NULL hasta Fase 5 (generación de documentos).
"""

from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models import ManualAccion

TRAMITES: list[dict] = [
    {
        "tramite": "Alegación al planeamiento urbanístico (PGOU)",
        "donde": "Sede electrónica de tu ayuntamiento o registro presencial, "
        "durante el periodo de exposición pública que se anuncia en el BOP.",
        "sede_url": None,
        "articulo_ampara": "Art. 83 Ley 39/2015 (trámite de audiencia) + Art. 21.1.g "
        "Ley 5/2014 (LOTUP)",
        "plazo_dias": None,
    },
    {
        "tramite": "Instancia por bache, farola fundida o vía pública deteriorada",
        "donde": "Sede electrónica del ayuntamiento (o la app que use tu municipio, "
        "como Línea Verde). Si el ayuntamiento no responde, puedes reclamar por el "
        "daño que el mal estado te cause.",
        "sede_url": None,
        "articulo_ampara": "Art. 25.2.d LBRL + Art. 32 Ley 40/2015 (si hay daño)",
        "plazo_dias": None,
    },
    {
        "tramite": "Queja ante el Síndic de Greuges (Comunitat Valenciana)",
        "donde": "elsindic.com — para cuando una administración no responde o actúa "
        "mal, aunque no sea un conflicto legal formal.",
        "sede_url": "https://www.elsindic.com/",
        "articulo_ampara": "Art. 29 Estatut d'Autonomia + Ley 11/1988",
        "plazo_dias": None,
    },
    {
        "tramite": "Reclamación de responsabilidad patrimonial",
        "donde": "Al ayuntamiento si el daño es por vías urbanas; a la diputación si "
        "es por una carretera provincial. Es gratis: se presenta por escrito ante la "
        "administración que causó el daño.",
        "sede_url": None,
        "articulo_ampara": "Art. 32-35 Ley 40/2015",
        "plazo_dias": 365,
    },
    {
        "tramite": "Solicitud de acceso a información pública",
        "donde": "Portal de Transparencia de la administración. Si no te contestan o "
        "te niegan el acceso, puedes reclamar al Consejo de Transparencia.",
        "sede_url": "https://transparencia.gva.es/",
        "articulo_ampara": "Art. 17 Ley 19/2013 + Ley 2/2015 (GV)",
        "plazo_dias": None,
    },
]


def seed_manual_accion(session) -> int:
    n = 0
    # key de upsert: tramite — pero la tabla no lo tiene UNIQUE. Idempotencia manual:
    existentes = {
        t for (t,) in session.query(ManualAccion.tramite).all()
    }
    for t in TRAMITES:
        if t["tramite"] in existentes:
            continue
        session.add(ManualAccion(**t))
        n += 1
    session.commit()
    return n
