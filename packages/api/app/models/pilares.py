from datetime import date

from sqlalchemy import BigInteger, Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Presupuesto(Base):
    __tablename__ = "presupuestos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    administracion_id: Mapped[int | None] = mapped_column(
        ForeignKey("administraciones.id")
    )
    ano: Mapped[int | None] = mapped_column(Integer)
    capitulo: Mapped[str | None] = mapped_column(Text)
    importe: Mapped[int | None] = mapped_column(BigInteger)
    fuente_url: Mapped[str | None] = mapped_column(Text)


class ProgramaElectoral(Base):
    __tablename__ = "programas_electorales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    partido: Mapped[str | None] = mapped_column(String(100))
    ano: Mapped[int | None] = mapped_column(Integer)
    pdf_url: Mapped[str | None] = mapped_column(Text)
    promesa_texto: Mapped[str | None] = mapped_column(Text)
    competencia_id: Mapped[int | None] = mapped_column(ForeignKey("competencias.id"))
    # POSIBLE | IMPOSIBLE | CUMPLIDO | PENDIENTE…
    estado: Mapped[str | None] = mapped_column(String(20))
    norma_id: Mapped[int | None] = mapped_column(ForeignKey("normas.id"))


class ManualAccion(Base):
    __tablename__ = "manual_accion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competencia_id: Mapped[int | None] = mapped_column(ForeignKey("competencias.id"))
    tramite: Mapped[str | None] = mapped_column(String(100))
    donde: Mapped[str | None] = mapped_column(Text)
    sede_url: Mapped[str | None] = mapped_column(Text)
    modelo_docx_url: Mapped[str | None] = mapped_column(Text)
    articulo_ampara: Mapped[str | None] = mapped_column(Text)
    plazo_dias: Mapped[int | None] = mapped_column(Integer)
    fuente_bop_url: Mapped[str | None] = mapped_column(Text)


class PersonaCargo(Base):
    __tablename__ = "personas_cargos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str | None] = mapped_column(Text)
    cargo: Mapped[str | None] = mapped_column(Text)
    administracion_id: Mapped[int | None] = mapped_column(
        ForeignKey("administraciones.id")
    )
    codigo_dir3: Mapped[str | None] = mapped_column(String(20))
    sueldo_anual: Mapped[int | None] = mapped_column(Integer)
    patrimonio_url: Mapped[str | None] = mapped_column(Text)
    agenda_json: Mapped[dict | None] = mapped_column(JSONB)
    fecha_inicio: Mapped[date | None] = mapped_column(Date)
    fuente_nombramiento_url: Mapped[str | None] = mapped_column(Text)
