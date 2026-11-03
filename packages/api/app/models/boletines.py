from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Boletin(Base):
    __tablename__ = "boletines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sigla: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str | None] = mapped_column(Text)
    url_base: Mapped[str | None] = mapped_column(Text)
    # API_JSON | RSS | HTML | PDF — método de scraping (§13)
    metodo: Mapped[str | None] = mapped_column(String(20))
    # baja | media-baja | media | alta — dificultad de scraping (§13)
    dificultad: Mapped[str | None] = mapped_column(String(20))
    ultimo_scrapeo: Mapped[datetime | None] = mapped_column()


class Administracion(Base):
    __tablename__ = "administraciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str | None] = mapped_column(Text)
    tipo: Mapped[str | None] = mapped_column(String(50))
    nivel: Mapped[int | None] = mapped_column(Integer)
    geom: Mapped[bytes | None] = mapped_column(Geometry())
    boletin_id: Mapped[int | None] = mapped_column(ForeignKey("boletines.id"))
    # DIR3 (migración 0002) — código, jerarquía y provincia del Directorio Común
    codigo_dir3: Mapped[str | None] = mapped_column(String(20), unique=True)
    codigo_padre: Mapped[str | None] = mapped_column(String(20))
    # código de tipo de entidad pública DIR3: AY, DP, MC, EM, OA, CI…
    entidad_tipo: Mapped[str | None] = mapped_column(String(10), index=True)
    provincia: Mapped[str | None] = mapped_column(String(60))
