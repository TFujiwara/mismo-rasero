from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Norma(Base):
    __tablename__ = "normas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    titulo: Mapped[str | None] = mapped_column(Text)
    # nivel del boletín: DOUE | BOE | <sigla CCAA> | <sigla BOP> (§04)
    rango: Mapped[str | None] = mapped_column(String(50))
    fecha_pub: Mapped[date | None] = mapped_column(Date)
    boletin_id: Mapped[int | None] = mapped_column(ForeignKey("boletines.id"))
    numero_boletin: Mapped[str | None] = mapped_column(String(50))
    url_pdf: Mapped[str] = mapped_column(Text, nullable=False)
    hash_sha256: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    texto_consolidado: Mapped[str | None] = mapped_column(Text)


class FlujoNormativo(Base):
    __tablename__ = "flujo_normativo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doue_url: Mapped[str | None] = mapped_column(Text)
    boe_transposicion_id: Mapped[int | None] = mapped_column(ForeignKey("normas.id"))
    dogv_desarrollo_id: Mapped[int | None] = mapped_column(ForeignKey("normas.id"))
    bop_ordenanza_id: Mapped[int | None] = mapped_column(ForeignKey("normas.id"))
    timeline_json: Mapped[dict | None] = mapped_column(JSONB)
