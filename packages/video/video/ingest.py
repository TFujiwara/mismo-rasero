"""Verificación de vídeo — blueprint §12.

REGLA DURA: este módulo analiza; nunca genera, publica ni redistribuye ningún
fragmento de vídeo. El fichero descargado se procesa en /tmp y se borra al
terminar (videos.borrado_en + estado DELETED). Solo texto se persiste.

Pipeline:
  1. Descarga (yt-dlp: YouTube/Atresplayer/Mitele/RTVE/TikTok; ffmpeg para m3u8 HLS)
  2. Transcripción (faster-whisper large-v3, word_timestamps, español)
  3. Diarización (pyannote: distingue voces, NO identifica personas)
  4. OCR de chyrons cada 2s (ffmpeg frames + EasyOCR)
  5. Detección de claims + verificación con el MISMO motor del texto (Fase 4)
  6. Borrado del original

Dependencias pesadas: uv sync --extra pipeline (ver pyproject).
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import sqlalchemy as sa

from app.db import SessionLocal
from app.models import Video, VideoTranscripcion, VideoVerificacion

logger = logging.getLogger(__name__)

TMP_DIR = Path(os.environ.get("VIDEO_TMP", "/tmp/blueprint-video"))
FPS_FRAMES = 0.5  # un frame cada 2s — §12

# Tipos de fuente reconocidos (videos.tipo)
TIPOS_URL = {
    "youtube.com": "YOUTUBE",
    "youtu.be": "YOUTUBE",
    "atresplayer.com": "ATRESPLAYER",
    "mitele.es": "MITELE",
    "rtve.es": "RTVE",
    "tiktok.com": "TIKTOK",
}


def detectar_tipo(url: str) -> str:
    if url.lower().endswith(".m3u8"):
        return "HLS"
    for dominio, tipo in TIPOS_URL.items():
        if dominio in url.lower():
            return tipo
    return "UPLOAD"


# ---------------------------------------------------------------------------
# 1. DESCARGA
# ---------------------------------------------------------------------------

def descargar(url: str) -> Path:
    """yt-dlp (sitios con extractor) / ffmpeg directo para m3u8 HLS."""
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    if url.lower().endswith(".m3u8"):
        destino = TMP_DIR / "hls_live.mp4"
        cmd = (
            f'ffmpeg -y -i "{url}" -c copy -f mp4 "{destino}"'
        )
        codigo = os.system(cmd)  # noqa: S605 — ffmpeg viene del sistema (§12)
        if codigo != 0:
            raise RuntimeError(f"ffmpeg falló descargando HLS: {url}")
        return destino

    import yt_dlp

    opts = {
        "format": "mp4/best",
        "outtmpl": str(TMP_DIR / "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        ruta = Path(ydl.prepare_filename(info))
    if not ruta.exists():
        raise RuntimeError(f"yt-dlp no dejó fichero en {ruta}")
    return ruta


# ---------------------------------------------------------------------------
# 2-3. TRANSCRIPCIÓN + DIARIZACIÓN
# ---------------------------------------------------------------------------

def transcribir(ruta_video: Path) -> list[dict]:
    from faster_whisper import WhisperModel

    model = WhisperModel("large-v3", device="auto", compute_type="auto")
    segments, info = model.transcribe(
        str(ruta_video), language="es", word_timestamps=True, vad_filter=True
    )
    out = []
    for seg in segments:
        out.append({
            "inicio": seg.start,
            "fin": seg.end,
            "texto": seg.text.strip(),
        })
    logger.info("transcripción: %s segmentos (%.1fs de audio)", len(out), info.duration)
    return out


def diarizar(ruta_video: Path) -> list[dict]:
    """pyannote — asigna 'voz_a'/'voz_b' a turnos de habla. NUNCA identifica personas."""
    from pyannote.audio import Pipeline

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=os.environ.get("HF_TOKEN"),
    )
    dia = pipeline(str(ruta_video))
    turnos = [
        {"inicio": turn.start, "fin": turn.end, "speaker": f"voz_{label:02d}"}
        for turn, _, label in dia.itertracks(yield_label=True)
    ]
    return turnos


def asignar_speakers(
    segmentos: list[dict], turnos: list[dict]
) -> list[dict]:
    """Por solapamiento temporal: el speaker con más intersección por segmento."""
    for seg in segmentos:
        mejor, max_inter = None, 0.0
        for t in turnos:
            inter = min(seg["fin"], t["fin"]) - max(seg["inicio"], t["inicio"])
            if inter > max_inter:
                mejor, max_inter = t["speaker"], inter
        seg["speaker"] = mejor
    return segmentos


# ---------------------------------------------------------------------------
# 4. OCR DE CHYRONS
# ---------------------------------------------------------------------------

def extraer_frames(ruta_video: Path) -> list[Path]:
    frames_dir = TMP_DIR / "frames"
    frames_dir.mkdir(exist_ok=True)
    cmd = (
        f'ffmpeg -y -i "{ruta_video}" -vf fps={FPS_FRAMES} '
        f'"{frames_dir / "frame_%04d.jpg"}"'
    )
    os.system(cmd)  # noqa: S605
    return sorted(frames_dir.glob("frame_*.jpg"))


def ocr_chyrons(ruta_video: Path) -> list[dict]:
    """Lee rótulos del informativo: 'ÚLTIMA HORA', 'DIRECTO', titulares."""
    import easyocr

    reader = easyocr.Reader(["es"], gpu=True)
    resultados = []
    for frame in extraer_frames(ruta_video):
        texto = " ".join(reader.readtext(str(frame), detail=0))
        if texto.strip():
            # timestamp aproximado por índice de frame
            idx = int(frame.stem.split("_")[1])
            resultados.append({
                "segundos": idx / FPS_FRAMES,
                "texto": texto.strip(),
            })
    return resultados


# ---------------------------------------------------------------------------
# 5. DETECCIÓN DE CLAIMS + VERIFICACIÓN
# ---------------------------------------------------------------------------

_RE_CLAIM = re.compile(
    r"\b(gobierno|ayuntamiento|generalitat|ministro|alcalde|president|"
    r"sub[íi]r[áa]|bajar[áa]|bajar[áa]n|subir[áa]n|prohibir[áa]|aprobar[áa]n?)\b",
    re.IGNORECASE,
)


def es_claim_verificable(texto: str) -> bool:
    return bool(_RE_CLAIM.search(texto))


def motor_verificacion() -> Callable[[str], dict] | None:
    """Seam hacia el motor de texto (Fase 4, §06). Mientras no exista,
    devuelve None y las claims quedan marcadas sin veredicto."""
    try:
        from app.services.verificar import verificar_competencial  # noqa: F401

        return verificar_competencial
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# 6. ORQUESTACIÓN + PERSISTENCIA + BORRADO
# ---------------------------------------------------------------------------

def procesar(url: str) -> str:
    """Pipeline completo para una URL. Devuelve el video_id."""
    with SessionLocal() as db:
        video = Video(url_original=url, tipo=detectar_tipo(url), estado="DOWNLOADING")
        db.add(video)
        db.flush()
        video_id = video.id
        db.commit()

    ruta: Path | None = None
    try:
        ruta = descargar(url)
        with SessionLocal() as db:
            db.execute(
                sa.update(Video).where(Video.id == video_id)
                .values(estado="TRANSCRIBING")
            )
            db.commit()

        segmentos = transcribir(ruta)
        try:
            segmentos = asignar_speakers(segmentos, diarizar(ruta))
        except Exception as exc:  # noqa: BLE001 — pyannote necesita HF_TOKEN; no es bloqueante
            logger.warning("diarización no disponible: %s", exc)
            for s in segmentos:
                s["speaker"] = None

        chyrons = ocr_chyrons(ruta)
        chyron_por_seg: dict[int, str] = {}
        for seg in segmentos:
            centro = (seg["inicio"] + seg["fin"]) / 2
            ch = min(chyrons, key=lambda c: abs(c["segundos"] - centro), default=None)
            if ch and abs(ch["segundos"] - centro) <= 2.0:
                chyron_por_seg[id(seg)] = ch["texto"]

        with SessionLocal() as db:
            db.execute(
                sa.update(Video).where(Video.id == video_id)
                .values(
                    estado="CLAIM_DETECTION",
                    duracion=int(segmentos[-1]["fin"]) if segmentos else 0,
                )
            )
            verificar = motor_verificacion()
            for seg in segmentos:
                claim = es_claim_verificable(seg["texto"])
                row = VideoTranscripcion(
                    video_id=video_id,
                    inicio=seg["inicio"], fin=seg["fin"], texto=seg["texto"],
                    speaker=seg.get("speaker"),
                    es_claim=claim,
                    claim_extraido=seg["texto"] if claim else None,
                    ocr_chyron=chyron_por_seg.get(id(seg)),
                )
                db.add(row)
                db.flush()
                if claim and verificar is not None:
                    resultado = verificar(seg["texto"])
                    db.add(VideoVerificacion(
                        transcripcion_id=row.id,
                        verificacion_json=resultado,
                        disarm_red_ttps=resultado.get("disarm_red"),
                        disarm_blue_counters=resultado.get("disarm_blue"),
                        veredicto=resultado.get("veredicto"),
                    ))
                elif claim:
                    logger.info("claim sin motor (Fase 4): %r", seg["texto"][:80])
            db.commit()
    finally:
        # 6. LIMPIEZA — el original se borra SIEMPRE, incluso si el pipeline falló
        if ruta is not None and ruta.exists():
            ruta.unlink(missing_ok=True)
            logger.info("vídeo original borrado: %s", ruta)

    with SessionLocal() as db:
        db.execute(
            sa.update(Video).where(Video.id == video_id)
            .values(estado="DELETED", borrado_en=datetime.now(timezone.utc))
        )
        db.commit()
    return str(video_id)


def main() -> None:
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Ingest de vídeo — solo verificación")
    parser.add_argument("url", help="URL (YouTube/Atresplayer/Mitele/RTVE/TikTok) o m3u8 HLS")
    args = parser.parse_args()
    video_id = procesar(args.url)
    print(f"video_id={video_id} — solo texto persistido; vídeo borrado")


if __name__ == "__main__":
    main()
