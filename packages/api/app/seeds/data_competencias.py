"""Competencias semilla — los ejemplos canónicos del blueprint §02 y §06.

Cada fila lleva la cadena competencial completa y fuente citada. administracion_id
queda NULL hasta que el seed DIR3 de Fase 2 puebla administraciones; la cadena va
en descripcion_tecnica. La búsqueda GIN (palabras_clave) es la base del Pilar 6.
"""

from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models import Competencia

# (nombre, slug, descripcion_llana, descripcion_tecnica [cadena completa], articulo_legal,
#  fuente_url, palabras_clave)
COMPETENCIAS: list[dict] = [
    {
        "nombre": "Salario Mínimo Interprofesional (SMI)",
        "slug": "salario-minimo",
        "descripcion_llana": "Lo fija el Gobierno del Estado por Real Decreto cada año. "
        "Ni las CCAA ni los ayuntamientos pueden tocarlo.",
        "descripcion_tecnica": "UE (Carta Social Europea, directrices) -> Estado fija SMI por RD, "
        "publicado en BOE (ej. RD 99/2023) -> CCAA NO tiene competencia -> Ayuntamiento NO tiene "
        "competencia.",
        "articulo_legal": "Art. 149.1.7 CE + Estatuto de los Trabajadores Art. 27",
        "fuente_url": "https://www.boe.es/buscar/act.php?id=BOE-A-1995-7770",
        "palabras_clave": ["salario minimo", "smi", "salario", "retribucion minima",
                           "subida del smi", "bajada del smi"],
    },
    {
        "nombre": "Sanidad — hospitales y plazas sanitarias",
        "slug": "sanidad-plazas",
        "descripcion_llana": "Las plazas de médicos y la organización de los hospitales son de tu "
        "Comunidad Autónoma. El dinero sale en parte del Estado (cesión IRPF/IVA). El ayuntamiento "
        "no decide cuántos médicos hay en tu hospital.",
        "descripcion_tecnica": "UE (directivas de personal sanitario) -> Estado Ley 55/2003 + Ley "
        "16/2003 de cohesión -> Generalitat Valenciana organiza plazas MIR/OPE (Estatut art. 54 "
        "Sanidad). Dinero: Estado cede tramo IRPF+IVA (Ley 22/2009) -> Generalitat presupuesta -> "
        "Ayuntamiento NO decide médicos.",
        "articulo_legal": "Estatut d'Autonomia Art. 54 + Ley 16/2003",
        "fuente_url": "https://www.boe.es/buscar/act.php?id=BOE-A-2003-10715",
        "palabras_clave": ["hospital", "medicos", "sanidad", "plazas medicas", "mir",
                           "ambulatorio", "centro de salud", "urgencias", "cita previa"],
    },
    {
        "nombre": "Vía pública urbana — baches, farolas, aceras",
        "slug": "via-publica",
        "descripcion_llana": "El mantenimiento de las calles es del Ayuntamiento. Si el bache está "
        "en una carretera provincial, es de la Diputación; si es una CV, de la Generalitat.",
        "descripcion_tecnica": "UE no interviene -> Estado LBRL Art. 25.2.d (vía pública) -> "
        "Ayuntamiento: calles urbanas -> Diputación: carreteras provinciales -> Generalitat: "
        "carreteras CV (ej. CV-20).",
        "articulo_legal": "LBRL Art. 25.2.d",
        "fuente_url": "https://www.boe.es/buscar/act.php?id=BOE-A-1985-11672",
        "palabras_clave": ["bache", "farola", "acera", "asfalto", "via publica", "alcantarilla",
                           "señal de trafico", "calzada", "farola fundida", "socavón"],
    },
    {
        "nombre": "IBI — Impuesto sobre Bienes Inmuebles",
        "slug": "ibi",
        "descripcion_llana": "El Estado regula el impuesto y fija la horquilla; tu ayuntamiento "
        "decide el tipo exacto dentro de esa horquilla en su ordenanza fiscal (BOP) y recauda el "
        "100%.",
        "descripcion_tecnica": "Estado RDL 2/2004 (TRLHL) Art. 59-77 regula -> Ayuntamiento fija el "
        "tipo dentro de la horquilla (Art. 72) en ordenanza fiscal publicada en BOP -> "
        "Ayuntamiento recauda el 100%.",
        "articulo_legal": "RDL 2/2004 Art. 59-77",
        "fuente_url": "https://www.boe.es/buscar/act.php?id=BOE-A-2004-4214",
        "palabras_clave": ["ibi", "impuesto bienes inmuebles", "catastro", "recibo del ibi",
                           "tipo ibi", "subida del ibi", "bajada del ibi"],
    },
    {
        "nombre": "IRPF — Impuesto sobre la Renta",
        "slug": "irpf",
        "descripcion_llana": "Mitad Estado, mitad Comunidad Autónoma (tramo autonómico). El "
        "ayuntamiento NO puede bajar el IRPF — gestiona IBI, IVTM, Plusvalía y tasas.",
        "descripcion_tecnica": "UE no interviene en el tipo -> Estado Ley 35/2006 (tramo estatal) + "
        "Ley 22/2009 (cesión 50% a CCAA) -> Generalitat Ley 13/1997 (tramo autonómico) -> "
        "Ayuntamiento NO tiene competencia en IRPF (LBRL Art. 25); solo IBI, IVTM, IAE, Plusvalía, "
        "tasas (RDL 2/2004 Art. 59).",
        "articulo_legal": "Ley 35/2006 + Ley 22/2009",
        "fuente_url": "https://www.boe.es/buscar/act.php?id=BOE-A-2006-20764",
        "palabras_clave": ["irpf", "renta", "tramo autonómico", "declaracion de la renta",
                           "bajar el irpf", "subir el irpf"],
    },
]


def seed_competencias(session) -> int:
    n = 0
    for c in COMPETENCIAS:
        stmt = (
            pg_insert(Competencia)
            .values(**c)
            .on_conflict_do_update(index_elements=["slug"], set_={
                "nombre": c["nombre"], "descripcion_llana": c["descripcion_llana"],
                "descripcion_tecnica": c["descripcion_tecnica"],
                "articulo_legal": c["articulo_legal"], "fuente_url": c["fuente_url"],
                "palabras_clave": c["palabras_clave"],
            })
        )
        session.execute(stmt)
        n += 1
    session.commit()
    return n
