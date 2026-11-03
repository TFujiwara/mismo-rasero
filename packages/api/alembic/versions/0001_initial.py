"""DDL completo del blueprint §19.

Todas las tablas: base (boletines, administraciones, competencias, impuestos, normas),
DISARM, R0R1R2, vídeo (solo verificación, sin campos de clip), presupuestos y pilares 5/7/8.
Extensiones: postgis + vector. Índices: GIN sobre competencias.palabras_clave,
(partido, rol) en declaraciones_r0 para /auditoria/sesgo, (boletin_id, fecha_pub) en normas.

Revision ID: 0001
Revises:
Create Date: 2026-10-26
"""

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql as pg

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # --- BOLETINES ---
    op.create_table(
        "boletines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sigla", sa.String(20), nullable=False, unique=True),
        sa.Column("nombre", sa.Text()),
        sa.Column("url_base", sa.Text()),
        sa.Column("metodo", sa.String(20)),
        sa.Column("dificultad", sa.String(20)),
        sa.Column("ultimo_scrapeo", sa.TIMESTAMP(timezone=True)),
    )

    op.create_table(
        "administraciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.Text()),
        sa.Column("tipo", sa.String(50)),
        sa.Column("nivel", sa.Integer()),
        sa.Column("geom", Geometry()),
        sa.Column("boletin_id", sa.Integer(), sa.ForeignKey("boletines.id")),
    )

    op.create_table(
        "competencias",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(200)),
        sa.Column("slug", sa.String(200), nullable=False, unique=True),
        sa.Column("descripcion_llana", sa.Text()),
        sa.Column("descripcion_tecnica", sa.Text()),
        sa.Column("articulo_legal", sa.String(200)),
        sa.Column("fuente_url", sa.Text()),
        sa.Column("fuente_csv", sa.String(100)),
        sa.Column(
            "administracion_id", sa.Integer(), sa.ForeignKey("administraciones.id")
        ),
        sa.Column("palabras_clave", pg.ARRAY(sa.Text())),
    )
    op.create_index(
        "ix_competencias_palabras_clave",
        "competencias",
        ["palabras_clave"],
        postgresql_using="gin",
    )

    op.create_table(
        "impuestos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(100)),
        sa.Column("quien_legisla", sa.Text()),
        sa.Column("quien_recauda", sa.Text()),
        sa.Column("quien_decide_tipo", sa.Text()),
        sa.Column("fuente_ley_url", sa.Text()),
        sa.Column("ordenanza_bop_url", sa.Text()),
    )

    op.create_table(
        "normas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("titulo", sa.Text()),
        sa.Column("rango", sa.String(50)),
        sa.Column("fecha_pub", sa.Date()),
        sa.Column("boletin_id", sa.Integer(), sa.ForeignKey("boletines.id")),
        sa.Column("numero_boletin", sa.String(50)),
        sa.Column("url_pdf", sa.Text(), nullable=False),
        sa.Column("hash_sha256", sa.String(100), nullable=False, unique=True),
        sa.Column("texto_consolidado", sa.Text()),
    )
    op.create_index(
        "ix_normas_boletin_fecha", "normas", ["boletin_id", "fecha_pub"]
    )

    # --- DISARM ---
    op.create_table(
        "disarm_techniques",
        sa.Column("id", sa.String(20), primary_key=True),
        sa.Column("fase", sa.String(20)),
        sa.Column("tactica", sa.String(100)),
        sa.Column("nombre", sa.Text()),
        sa.Column("descripcion", sa.Text()),
        sa.Column("url", sa.Text()),
        sa.Column("tipo", sa.String(10)),
    )
    op.create_index(
        "ix_disarm_techniques_fase_tipo", "disarm_techniques", ["fase", "tipo"]
    )

    op.create_table(
        "disarm_counters",
        sa.Column("id", sa.String(20), primary_key=True),
        sa.Column("nombre", sa.Text()),
        sa.Column("descripcion", sa.Text()),
    )

    # --- R0R1R2 ---
    op.create_table(
        "declaraciones_r0",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("texto_literal", sa.Text(), nullable=False),
        sa.Column("actor", sa.Text()),
        sa.Column("cargo", sa.Text()),
        sa.Column("partido", sa.String(100)),
        sa.Column("rol", sa.String(20)),  # GOBIERNO/OPOSICION/OTRO (§11)
        sa.Column("fecha", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("fuente_primaria_url", sa.Text(), nullable=False),
        sa.Column("disarm_red_ttps", pg.ARRAY(sa.Text())),
        sa.Column("disarm_blue_counters", pg.ARRAY(sa.Text())),
        sa.Column("disarm_confidence", sa.Float()),
        sa.Column("hash_video", sa.String(100)),
        sa.Column("verificado", sa.Boolean(), server_default="false"),
    )
    op.create_index(
        "ix_declaraciones_r0_partido_rol", "declaraciones_r0", ["partido", "rol"]
    )

    op.create_table(
        "marcos_r1",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "declaracion_id",
            sa.Integer(),
            sa.ForeignKey("declaraciones_r0.id"),
        ),
        sa.Column("marco_texto", sa.Text(), nullable=False),
        sa.Column("emocion", sa.String(50)),
        sa.Column("culpable", sa.Text()),
        sa.Column("victima", sa.Text()),
        sa.Column("canal", sa.Text()),
        sa.Column("disarm_tactic", sa.String(100)),
    )

    op.create_table(
        "metanarrativas_r2",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(100), nullable=False, unique=True),
        sa.Column("descripcion", sa.Text()),
    )

    # --- VÍDEO: solo verificación, sin generación/redistribución de clips (§12) ---
    op.create_table(
        "videos",
        sa.Column(
            "id", pg.UUID(as_uuid=True), primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("url_original", sa.Text()),
        sa.Column("tipo", sa.String(20)),
        sa.Column("estado", sa.String(20)),
        sa.Column("duracion", sa.Integer()),
        sa.Column("hash_perceptual", sa.String(100)),
        sa.Column("borrado_en", sa.TIMESTAMP(timezone=True)),
        sa.Column(
            "fecha_ingesta", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        # fuera de este esquema: s3_path, thumbnail_path — no se persiste el vídeo
    )

    op.create_table(
        "video_transcripciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "video_id", pg.UUID(as_uuid=True),
            sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("inicio", sa.Float(), nullable=False),
        sa.Column("fin", sa.Float(), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("speaker", sa.String(100)),
        sa.Column("speaker_confidence", sa.Float()),
        sa.Column("es_claim", sa.Boolean(), server_default="false"),
        sa.Column("claim_extraido", sa.Text()),
        sa.Column("ocr_chyron", sa.Text()),
    )
    op.create_index(
        "ix_video_transcripciones_video", "video_transcripciones", ["video_id"]
    )

    op.create_table(
        "video_verificaciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "transcripcion_id", sa.Integer(),
            sa.ForeignKey("video_transcripciones.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("verificacion_json", pg.JSONB()),
        sa.Column("disarm_red_ttps", pg.ARRAY(sa.Text())),
        sa.Column("disarm_blue_counters", pg.ARRAY(sa.Text())),
        sa.Column("veredicto", sa.String(20)),
    )

    op.create_table(
        "presupuestos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "administracion_id", sa.Integer(), sa.ForeignKey("administraciones.id")
        ),
        sa.Column("ano", sa.Integer()),
        sa.Column("capitulo", sa.Text()),
        sa.Column("importe", sa.BigInteger()),
        sa.Column("fuente_url", sa.Text()),
    )

    # --- PILARES 5, 7, 8 ---
    op.create_table(
        "programas_electorales",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("partido", sa.String(100)),
        sa.Column("ano", sa.Integer()),
        sa.Column("pdf_url", sa.Text()),
        sa.Column("promesa_texto", sa.Text()),
        sa.Column("competencia_id", sa.Integer(), sa.ForeignKey("competencias.id")),
        sa.Column("estado", sa.String(20)),
        sa.Column("norma_id", sa.Integer(), sa.ForeignKey("normas.id")),
    )

    op.create_table(
        "manual_accion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("competencia_id", sa.Integer(), sa.ForeignKey("competencias.id")),
        sa.Column("tramite", sa.String(100)),
        sa.Column("donde", sa.Text()),
        sa.Column("sede_url", sa.Text()),
        sa.Column("modelo_docx_url", sa.Text()),
        sa.Column("articulo_ampara", sa.Text()),
        sa.Column("plazo_dias", sa.Integer()),
        sa.Column("fuente_bop_url", sa.Text()),
    )

    op.create_table(
        "personas_cargos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.Text()),
        sa.Column("cargo", sa.Text()),
        sa.Column(
            "administracion_id", sa.Integer(), sa.ForeignKey("administraciones.id")
        ),
        sa.Column("codigo_dir3", sa.String(20)),
        sa.Column("sueldo_anual", sa.Integer()),
        sa.Column("patrimonio_url", sa.Text()),
        sa.Column("agenda_json", pg.JSONB()),
        sa.Column("fecha_inicio", sa.Date()),
        sa.Column("fuente_nombramiento_url", sa.Text()),
    )

    op.create_table(
        "flujo_normativo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("doue_url", sa.Text()),
        sa.Column("boe_transposicion_id", sa.Integer(), sa.ForeignKey("normas.id")),
        sa.Column("dogv_desarrollo_id", sa.Integer(), sa.ForeignKey("normas.id")),
        sa.Column("bop_ordenanza_id", sa.Integer(), sa.ForeignKey("normas.id")),
        sa.Column("timeline_json", pg.JSONB()),
    )


def downgrade() -> None:
    op.drop_table("flujo_normativo")
    op.drop_table("personas_cargos")
    op.drop_table("manual_accion")
    op.drop_table("programas_electorales")
    op.drop_table("presupuestos")
    op.drop_table("video_verificaciones")
    op.drop_index("ix_video_transcripciones_video", table_name="video_transcripciones")
    op.drop_table("video_transcripciones")
    op.drop_table("videos")
    op.drop_table("metanarrativas_r2")
    op.drop_table("marcos_r1")
    op.drop_index("ix_declaraciones_r0_partido_rol", table_name="declaraciones_r0")
    op.drop_table("declaraciones_r0")
    op.drop_index("ix_disarm_techniques_fase_tipo", table_name="disarm_techniques")
    op.drop_table("disarm_counters")
    op.drop_table("disarm_techniques")
    op.drop_index("ix_normas_boletin_fecha", table_name="normas")
    op.drop_table("normas")
    op.drop_table("impuestos")
    op.drop_index("ix_competencias_palabras_clave", table_name="competencias")
    op.drop_table("competencias")
    op.drop_table("administraciones")
    op.drop_table("boletines")
    op.execute("DROP EXTENSION IF EXISTS vector")
    op.execute("DROP EXTENSION IF EXISTS postgis")
