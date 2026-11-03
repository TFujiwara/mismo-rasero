"""Añade los campos DIR3 a administraciones.

El DDL §19 no traía código DIR3 ni jerarquía en administraciones; el seed real
del Directorio Común (CTT, Listado Unidades EELL/CCAA) los necesita para
resolver el organigrama por código (quien_manda) en vez de por nombre.

Fuente: https://administracionelectronica.gob.es/ctt/verPestanaDescargas.htm?idIniciativa=dir3
instantáneas Wayback del 2023-01-10 (el portal CTT está tras F5 TrafficShield
y no permite descarga automatizada).

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-27
"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("administraciones", sa.Column("codigo_dir3", sa.String(20)))
    op.add_column("administraciones", sa.Column("codigo_padre", sa.String(20)))
    op.add_column("administraciones", sa.Column("entidad_tipo", sa.String(10)))
    op.add_column("administraciones", sa.Column("provincia", sa.String(60)))
    op.create_index(
        "ix_administraciones_codigo_dir3",
        "administraciones",
        ["codigo_dir3"],
        unique=True,
    )
    op.create_index(
        "ix_administraciones_entidad_tipo", "administraciones", ["entidad_tipo"]
    )


def downgrade() -> None:
    op.drop_index("ix_administraciones_entidad_tipo", table_name="administraciones")
    op.drop_index("ix_administraciones_codigo_dir3", table_name="administraciones")
    for col in ("provincia", "entidad_tipo", "codigo_padre", "codigo_dir3"):
        op.drop_column("administraciones", col)
