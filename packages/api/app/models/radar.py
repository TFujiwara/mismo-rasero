from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class DeclaracionR0(Base):
    """Hecho literal (R0). rol alimenta el panel público de auditoría de sesgo (§11)."""

    __tablename__ = "declaraciones_r0"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    texto_literal: Mapped[str] = mapped_column(Text, nullable=False)
    actor: Mapped[str | None] = mapped_column(Text)
    cargo: Mapped[str | None] = mapped_column(Text)
    partido: Mapped[str | None] = mapped_column(String(100))
    # GOBIERNO | OPOSICION | OTRO
    rol: Mapped[str | None] = mapped_column(String(20))
    fecha: Mapped[datetime] = mapped_column(nullable=False)
    fuente_primaria_url: Mapped[str] = mapped_column(Text, nullable=False)
    disarm_red_ttps: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    disarm_blue_counters: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    disarm_confidence: Mapped[float | None] = mapped_column(Float)
    hash_video: Mapped[str | None] = mapped_column(String(100))
    verificado: Mapped[bool | None] = mapped_column(Boolean, server_default="false")


class MarcoR1(Base):
    __tablename__ = "marcos_r1"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    declaracion_id: Mapped[int | None] = mapped_column(
        ForeignKey("declaraciones_r0.id")
    )
    marco_texto: Mapped[str] = mapped_column(Text, nullable=False)
    emocion: Mapped[str | None] = mapped_column(String(50))
    culpable: Mapped[str | None] = mapped_column(Text)
    victima: Mapped[str | None] = mapped_column(Text)
    canal: Mapped[str | None] = mapped_column(Text)
    disarm_tactic: Mapped[str | None] = mapped_column(String(100))


class MetanarrativaR2(Base):
    """Las 12 metanarrativas fijas del blueprint (§10)."""

    __tablename__ = "metanarrativas_r2"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
