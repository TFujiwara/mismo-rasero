from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class DisarmTechnique(Base):
    """Técnicas RED del framework DISARM (seed desde DISARM.json STIX)."""

    __tablename__ = "disarm_techniques"

    # T-código DISARM, ej. T0085
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    # P01-P04: Plan / Prepare / Execute / Assess (§15)
    fase: Mapped[str | None] = mapped_column(String(20))
    # táctica a la que pertenece, ej. "Develop Narratives"
    tactica: Mapped[str | None] = mapped_column(String(100))
    nombre: Mapped[str | None] = mapped_column(Text)
    descripcion: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    # RED | BLUE
    tipo: Mapped[str | None] = mapped_column(String(10))


class DisarmCounter(Base):
    """Contramedidas BLUE del framework DISARM (seed desde DISARM_database.sqlite)."""

    __tablename__ = "disarm_counters"

    # C-código DISARM, ej. C001
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    nombre: Mapped[str | None] = mapped_column(Text)
    descripcion: Mapped[str | None] = mapped_column(Text)
