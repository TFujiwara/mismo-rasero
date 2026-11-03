from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Competencia(Base):
    __tablename__ = "competencias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str | None] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(200), unique=True)
    descripcion_llana: Mapped[str | None] = mapped_column(Text)
    descripcion_tecnica: Mapped[str | None] = mapped_column(Text)
    articulo_legal: Mapped[str | None] = mapped_column(String(200))
    fuente_url: Mapped[str | None] = mapped_column(Text)
    fuente_csv: Mapped[str | None] = mapped_column(String(100))
    administracion_id: Mapped[int | None] = mapped_column(
        ForeignKey("administraciones.id")
    )
    palabras_clave: Mapped[list[str] | None] = mapped_column(ARRAY(Text))


class Impuesto(Base):
    __tablename__ = "impuestos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str | None] = mapped_column(String(100))
    quien_legisla: Mapped[str | None] = mapped_column(Text)
    quien_recauda: Mapped[str | None] = mapped_column(Text)
    quien_decide_tipo: Mapped[str | None] = mapped_column(Text)
    fuente_ley_url: Mapped[str | None] = mapped_column(Text)
    ordenanza_bop_url: Mapped[str | None] = mapped_column(Text)
