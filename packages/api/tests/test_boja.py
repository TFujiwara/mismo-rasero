from datetime import date

from scrapers.boja import BojaAdapter

CAL = {"rows": [["200101", "02/01/2026"], [1, "02/01/2026"], [2, "05/01/2026"],
                [501, "05/01/2026"], [168, "31/08/2026"], [216801, "31/08/2026"]]}

BULLETIN = {
    "results": [
        {"id": "disposition.2026.2.1",
         "summaryNoHtml": "Orden de 3 de enero de 2026, de la Consejería X.",
         "titleSec": "1. Disposiciones generales",
         "organisation": "Consejería X", "number": 2,
         "pdf": [{"publicUrl": "https://juntadeandalucia.es/eboja/2026/2/X.pdf"}]},
        {"id": "disposition.2026.2.2",
         "summaryNoHtml": "Resolución de 2 de enero de 2026, sin PDF.",
         "pdf": []},
    ]
}


class FalsoBoja(BojaAdapter):
    def __init__(self):
        self.llamadas = []

    def _get(self, ruta, params):
        self.llamadas.append((ruta, dict(params)))
        return CAL if ruta == "get/calendar" else BULLETIN


def test_seleccion_numero_regular_minimo():
    """El 05/01 tiene números [2, 501] — el diario es el 2, no el especial 501."""
    a = FalsoBoja()
    docs = a.fetch_day(date(2026, 1, 5))
    calendario = a.llamadas[0]
    assert calendario == ("get/calendar", {"year": 2026})
    assert a.llamadas[1] == ("get/bulletin", {"year": 2026, "number": 2})
    # la disposición sin PDF se descarta (url_pdf es NOT NULL en normas)
    assert len(docs) == 1
    assert docs[0].identificador == "disposition.2026.2.1"
    assert docs[0].titulo.startswith("Orden de 3 de enero")
    assert docs[0].url_pdf.endswith(".pdf")
    assert docs[0].numero_boletin == "2"


def test_dia_sin_publicacion_devuelve_vacio():
    a = FalsoBoja()
    assert a.fetch_day(date(2026, 3, 15)) == []
