"""Base de los adaptadores de boletines.

Cada boletín (20 de §13 + 43 BOPs de §14) exige un método distinto:
API JSON (BOE, BOPV), RSS (BOJA, DOGC…), HTML estático (BOPA, BORM…),
PDF plano (BOCCE, BOME) o HTML con JS (DOGV → Playwright).

Esta capa es DB-agnóstica: solo fetch + parse. La persistencia en `normas`
vive en app.services.ingest (packages/api), para no crear dependencias cruzadas.
"""

from __future__ import annotations

import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date

import httpx

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    # solo ASCII — los headers HTTP no admiten no-ASCII (httpx lo exige)
    "User-Agent": (
        "blueprint-transparencia/0.1 (+open source; uso: consulta de "
        "boletines oficiales de dominio publico, art. 13 LPI)"
    )
}


@dataclass
class Documento:
    """Un documento dentro del sumario diario de un boletín."""

    identificador: str            # ej. BOE-A-2024-87, o número de doc DOGV
    titulo: str
    fecha: date
    url_pdf: str | None = None
    url_html: str | None = None
    seccion: str | None = None
    departamento: str | None = None
    numero_boletin: str | None = None
    extra: dict = field(default_factory=dict)


@dataclass
class ResumenIngesta:
    sigla: str
    fecha: date
    total: int = 0
    nuevos: int = 0
    duplicados: int = 0
    errores_pdf: int = 0


class BoletinAdapter(ABC):
    """Contrato común: dado un día, devuelve la lista de documentos publicados."""

    sigla: str = ""
    rango: str = ""  # valor para normas.rango (DOUE/BOE/DOGV/BOP-…)

    @abstractmethod
    def fetch_day(self, fecha: date) -> list[Documento]:
        ...

    def sha256_url(self, url: str, client: httpx.Client | None = None) -> str:
        """Hash SHA-256 del PDF — campo obligatorio y único en normas (§19)."""
        close = False
        if client is None:
            client = httpx.Client(
                headers=DEFAULT_HEADERS, follow_redirects=True, timeout=60
            )
            close = True
        try:
            resp = client.get(url)
            resp.raise_for_status()
            return hashlib.sha256(resp.content).hexdigest()
        finally:
            if close:
                client.close()


def registrar_adapters() -> dict[str, type[BoletinAdapter]]:
    from scrapers.bocm import BocmAdapter
    from scrapers.boe import BoeAdapter
    from scrapers.boja import BojaAdapter
    from scrapers.bopv import BopvAdapter
    from scrapers.doe import DoeAdapter
    from scrapers.dog import DogAdapter
    from scrapers.dogv import DogvAdapter
    from scrapers.doue import DoueAdapter

    return {
        "BOE": BoeAdapter,
        "BOJA": BojaAdapter,
        "BOCM": BocmAdapter,
        "BOPV": BopvAdapter,
        "DOE": DoeAdapter,
        "DOG": DogAdapter,
        "DOGV": DogvAdapter,
        "DOUE": DoueAdapter,
    }
