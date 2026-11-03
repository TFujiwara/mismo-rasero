from app.models.boletines import Administracion, Boletin
from app.models.competencias import Competencia, Impuesto
from app.models.disarm import DisarmCounter, DisarmTechnique
from app.models.normas import FlujoNormativo, Norma
from app.models.pilares import (
    ManualAccion,
    PersonaCargo,
    Presupuesto,
    ProgramaElectoral,
)
from app.models.radar import DeclaracionR0, MarcoR1, MetanarrativaR2
from app.models.video import Video, VideoTranscripcion, VideoVerificacion

__all__ = [
    "Administracion",
    "Boletin",
    "Competencia",
    "DeclaracionR0",
    "DisarmCounter",
    "DisarmTechnique",
    "FlujoNormativo",
    "Impuesto",
    "ManualAccion",
    "MarcoR1",
    "MetanarrativaR2",
    "Norma",
    "PersonaCargo",
    "Presupuesto",
    "ProgramaElectoral",
    "Video",
    "VideoTranscripcion",
    "VideoVerificacion",
]
