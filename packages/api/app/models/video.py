import uuid
from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Video(Base):
    """Solo verificación: el fichero de vídeo nunca se persiste (§12)."""

    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    url_original: Mapped[str | None] = mapped_column(Text)
    # YOUTUBE | ATRESPLAYER | MITELE | RTVE | TIKTOK | UPLOAD | HLS
    tipo: Mapped[str | None] = mapped_column(String(20))
    # DOWNLOADING | TRANSCRIBING | CLAIM_DETECTION | VERIFIED | READY | ERROR | DELETED
    estado: Mapped[str | None] = mapped_column(String(20))
    duracion: Mapped[int | None] = mapped_column(Integer)
    hash_perceptual: Mapped[str | None] = mapped_column(String(100))
    # cuando se elimina el fichero original tras el análisis
    borrado_en: Mapped[datetime | None] = mapped_column()
    fecha_ingesta: Mapped[datetime | None] = mapped_column(server_default=text("NOW()"))


class VideoTranscripcion(Base):
    __tablename__ = "video_transcripciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"), nullable=False
    )
    inicio: Mapped[float] = mapped_column(Float, nullable=False)
    fin: Mapped[float] = mapped_column(Float, nullable=False)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    # diarización: "voz_a", "voz_b"… — NO identificación biométrica (§12)
    speaker: Mapped[str | None] = mapped_column(String(100))
    speaker_confidence: Mapped[float | None] = mapped_column(Float)
    es_claim: Mapped[bool | None] = mapped_column(Boolean, server_default="false")
    claim_extraido: Mapped[str | None] = mapped_column(Text)
    ocr_chyron: Mapped[str | None] = mapped_column(Text)


class VideoVerificacion(Base):
    __tablename__ = "video_verificaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transcripcion_id: Mapped[int] = mapped_column(
        ForeignKey("video_transcripciones.id", ondelete="CASCADE"), nullable=False
    )
    verificacion_json: Mapped[dict | None] = mapped_column(JSONB)
    disarm_red_ttps: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    disarm_blue_counters: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    veredicto: Mapped[str | None] = mapped_column(String(20))
