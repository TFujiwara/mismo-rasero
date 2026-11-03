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
    {
        "nombre": "Educación pública — colegios y plazas escolares",
        "slug": "educacion-publica",
        "descripcion_llana": "Colegios, plazas escolares y profesorado son de tu "
        "Comunidad Autónoma. El ayuntamiento mantiene los edificios en algunos "
        "municipios (convenio), pero no decide el profesorado ni las plazas.",
        "descripcion_tecnica": "UE (no interviene en el servicio ordinario) -> Estado "
        "regula el marco (LOE, Ley Orgánica 2/2006) -> Comunidad Autónoma crea y "
        "organiza centros, plazas y profesorado (Estatut art. 57 educación) -> "
        "Ayuntamiento: conservación de edificios si hay convenio (LBRL art. 25.2.h) "
        "y suelo escolar.",
        "articulo_legal": "LOE (LO 2/2006) + Estatut art. 57",
        "fuente_url": "https://www.boe.es/buscar/act.php?id=BOE-A-2006-7899",
        "palabras_clave": ["colegio", "colegios", "educación", "escuela", "plazas escolares",
                           "profesores", "instituto", "guardería pública"],
    },
    {
        "nombre": "Basuras — recogida y tasa de basura",
        "slug": "basuras",
        "descripcion_llana": "La recogida de basuras es del ayuntamiento (o de la "
        "mancomunidad si está agrupado), que financia el servicio con la tasa de "
        "basuras, no con tus impuestos generales.",
        "descripcion_tecnica": "UE (directivas de residuos: Ley 7/2022 las transpone) -> "
        "Estado marco de residuos (Ley 7/2022) -> Ayuntamiento: servicio obligatorio "
        "(LBRL art. 25.2.a, D) y tasa por ordenanza en BOP (RDL 2/2004 art. 20.4) -> "
        "Mancomunidad si el municipio está agrupado.",
        "articulo_legal": "LBRL art. 25.2.a + RDL 2/2004 art. 20.4",
        "fuente_url": "https://www.boe.es/buscar/act.php?id=BOE-A-1985-11672",
        "palabras_clave": ["basura", "basuras", "tasa de basuras", "residuos",
                           "contenedores", "recogida de basura", "punto limpio"],
    },
    {
        "nombre": "Agua — abastecimiento y suministro",
        "slug": "agua-abastecimiento",
        "descripcion_llana": "El agua que sale de tu grifo la gestiona el ayuntamiento "
        "o una mancomunidad/sociedad mixta. Los cortes, la factura municipal y la "
        "calidad del servicio son competencia local. Los embalses no.",
        "descripcion_tecnica": "Estado: recurso y cuenca (TRLA, RDL 1/2001, "
        "Confederaciones Hidrográficas) -> Comunidad Autónoma: sanidad del agua de "
        "consumo -> Ayuntamiento o Mancomunidad: abastecimiento, distribución y "
        "saneamiento (LBRL art. 25.2.a y D; RDL 2/2004 tasa).",
        "articulo_legal": "LBRL art. 25.2 + TRLA (RDLeg 1/2001)",
        "fuente_url": "https://www.boe.es/eli/es/rdlg/2001/07/20/1",
        "palabras_clave": ["agua", "abastecimiento de agua", "cortes de agua",
                           "factura del agua", "saneamiento", "fuga de agua"],
    },
    {
        "nombre": "Carreteras — según la titularidad",
        "slug": "carreteras",
        "descripcion_llana": "Quién arregla una carretera depende de de quién es: las "
        "calles son del ayuntamiento, las carreteras provinciales de la diputación, "
        "las autonómicas (CV, A-) de la Comunidad y las nacionales (N-) del Estado.",
        "descripcion_tecnica": "Ayuntamiento: vía urbana (LBRL art. 25.2) -> Diputación: "
        "carreteras provinciales (LBRL art. 36.1.b) -> Comunidad Autónoma: red "
        "autonómica -> Estado: red nacional (N-) y interestatal. La matrícula de la "
        "vía (CV-, N-, A-) indica el titular.",
        "articulo_legal": "LBRL art. 25.2 y 36.1.b",
        "fuente_url": "https://www.boe.es/buscar/act.php?id=BOE-A-1985-11672",
        "palabras_clave": ["carretera", "carreteras", "conservera", "autovía",
                           "comarcal", "nacional", "vía interurbana"],
    },
    {
        "nombre": "Policía local",
        "slug": "policia-local",
        "descripcion_llana": "La policía local depende del ayuntamiento: tráfico "
        "urbano, seguridad en el municipio y ordenanzas. No es la Policía Nacional "
        "ni la Guardia Civil.",
        "descripcion_tecnica": "Ayuntamiento: policía local (LBRL art. 25.2.f; LO "
        "2/1986 regula las policías locales) -> Estado: Policía Nacional y Guardia "
        "Civil (LO 2/1986) -> Comunidad Autónoma: policía autonómica donde existe.",
        "articulo_legal": "LBRL art. 25.2.f + LO 2/1986",
        "fuente_url": "https://www.boe.es/buscar/act.php?id=BOE-A-1986-6859",
        "palabras_clave": ["policía local", "policia municipal", "multas de tráfico",
                           "agente de tráfico", "denuncia municipal"],
    },
    {
        "nombre": "Policía Nacional y Guardia Civil",
        "slug": "policia-nacional",
        "descripcion_llana": "Seguridad ciudadana, DNI y delitos: Policía Nacional "
        "(ciudades) y Guardia Civil (rural). Dependen del Estado, no del ayuntamiento.",
        "descripcion_tecnica": "Estado: Policía Nacional y Guardia Civil (LO 2/1986, "
        "art. 104 CE) -> Ayuntamiento NO manda efectivos estatales; coopera con la "
        "policía local.",
        "articulo_legal": "LO 2/1986 + art. 104 CE",
        "fuente_url": "https://www.boe.es/buscar/act.php?id=BOE-A-1986-6859",
        "palabras_clave": ["policía nacional", "guardia civil", "dni", "pasaporte",
                           "seguridad ciudadana", "comisaría"],
    },
    {
        "nombre": "Licencias de obra y urbanismo",
        "slug": "licencias-obra",
        "descripcion_llana": "Las licencias de obra las da el ayuntamiento con su "
        "planeamiento (PGOU). La Generalitat fiscaliza urbanismo, pero la licencia "
        "es municipal.",
        "descripcion_tecnica": "Ayuntamiento: licencias y planeamiento (LBRL art. "
        "25.2.a; LOTUP Ley 5/2014 en la CV) -> Comunidad Autónoma: fiscalización "
        "urbanística y plan territorial -> Estado: legislación básica (Ley 39/2015 "
        "procedimientos; suelo: RDL 7/2015).",
        "articulo_legal": "LBRL art. 25.2.a + LOTUP (Ley 5/2014)",
        "fuente_url": "https://www.boe.es/buscar/act.php?id=BOE-A-1985-11672",
        "palabras_clave": ["licencia de obra", "obra sin licencia", "urbanismo",
                           "pgou", "certificado urbanístico", "obra mayor", "obra menor"],
    },
    {
        "nombre": "Pensiones",
        "slug": "pensiones",
        "descripcion_llana": "Las pensiones las paga y gestiona la Seguridad Social "
        "del Estado. Ninguna comunidad autónoma ni ayuntamiento puede subir, bajar "
        "o revalorizar una pensión.",
        "descripcion_tecnica": "Estado: Seguridad Social y pensiones (LGSS, RDLeg "
        "8/2015; art. 149.1.17 CE) -> Comunidad Autónoma NO decide cuantías -> "
        "Ayuntamiento NO decide cuantías.",
        "articulo_legal": "LGSS (RDLeg 8/2015) + art. 149.1.17 CE",
        "fuente_url": "https://www.boe.es/eli/es/rdlg/2015/10/30/8",
        "palabras_clave": ["pensión", "pensiones", "jubilación", "seguridad social",
                           "subir las pensiones", "pagar las pensiones"],
    },
    {
        "nombre": "Vivienda pública y ayudas al alquiler",
        "slug": "vivienda-publica",
        "descripcion_llana": "Las VPO, las ayudas al alquiler y los planes de vivienda "
        "los gestiona tu Comunidad Autónoma (con marco estatal). El ayuntamiento "
        "puede ceder suelo, pero no crea VPO.",
        "descripcion_tecnica": "Estado: legislación básica y planes estatales (art. "
        "47 CE; Ley 12/2023 por el derecho a la vivienda) -> Comunidad Autónoma: VPO, "
        "plan de vivienda y ayudas (Estatut art. 60) -> Ayuntamiento: suelo y "
        "informes (LBRL art. 25.2).",
        "articulo_legal": "Ley 12/2023 + Estatut art. 60",
        "fuente_url": "https://www.boe.es/eli/es/l/2023/05/24/12",
        "palabras_clave": ["vpo", "vivienda pública", "ayuda al alquiler", "alquiler joven",
                           "vivienda protegida", "plan de vivienda"],
    },
    {
        "nombre": "Transporte público — urbano e interurbano",
        "slug": "transporte-publico",
        "descripcion_llana": "El autobús urbano es del ayuntamiento. El metro, el "
        "tranvía y el transporte interurbano son de la Generalitat; los trenes de "
        "cercanías, del Estado.",
        "descripcion_tecnica": "Ayuntamiento: transporte urbano (LBRL art. 25.2.c) -> "
        "Comunidad Autónoma: transporte interurbano y metropolitano (Estatut art. "
        "57 bis) -> Estado: cercanías y larga distancia (art. 149.1.21 CE).",
        "articulo_legal": "LBRL art. 25.2.c + art. 149.1.21 CE",
        "fuente_url": "https://www.boe.es/buscar/act.php?id=BOE-A-1985-11672",
        "palabras_clave": ["autobús urbano", "bus urbano", "transporte público",
                           "metro", "cercanías", "emt", "bonobús"],
    },
    {
        "nombre": "Ordenación del tráfico y radares urbanos",
        "slug": "ordenacion-trafico",
        "descripcion_llana": "En las calles urbanas, el ayuntamiento ordena el tráfico "
        "y pone radares (con la ley estatal por delante). En carretera, manda la DGT.",
        "descripcion_tecnica": "Estado: legislación de tráfico (RDL 6/2015) y DGT -> "
        "Ayuntamiento: ordenación del tráfico en vía urbana, radares y señalética "
        "municipal (LBRL art. 25.2.g; RDL 6/2015 art. 13.3).",
        "articulo_legal": "RDLg 6/2015 art. 13.3 + LBRL art. 25.2.g",
        "fuente_url": "https://www.boe.es/eli/es/rdlg/2015/10/30/6",
        "palabras_clave": ["radares", "radar municipal", "ordenación del tráfico",
                           "multas de tráfico", "zona 30", "aparcamiento"],
    },
    {
        "nombre": "Empadronamiento",
        "slug": "empadronamiento",
        "descripcion_llana": "Empadronarse es un derecho y un trámite municipal: el "
        "ayuntamiento inscribe y certifica el padrón. Es la puerta para sanidad, "
        "escuela y ayudas.",
        "descripcion_tecnica": "Ayuntamiento: gestión del padrón (LBRL art. 16; RDL "
        "169/1986) -> Estado: coordinación del padrón (INE) -> Nadie más puede "
        "empadronarte.",
        "articulo_legal": "LBRL art. 16 + RDL 169/1986",
        "fuente_url": "https://www.boe.es/buscar/act.php?id=BOE-A-1985-11672",
        "palabras_clave": ["empadronamiento", "empadronarse", "padrón municipal",
                           "volante de empadronamiento", "certificado de empadronamiento"],
    },
    {
        "nombre": "Catastro inmobiliario",
        "slug": "catastro",
        "descripcion_llana": "El Catastro es del Estado (AEAT Catastro). El "
        "ayuntamiento colabora y recauda el IBI con esos datos, pero no puede "
        "modificar la referencia catastral ni los valores.",
        "descripcion_tecnica": "Estado: Catastro Inmobiliario (RDL 1/2004; AEAT "
        "Catastro) -> Ayuntamiento: colaboración y recaudación del IBI (LBRL art. "
        "25.2.f) -> Comunidad Autónoma NO gestiona el catastro (salvo Álava, "
        "Gipuzkoa: foral).",
        "articulo_legal": "RDLeg 1/2004 (TR Catastro) + LBRL art. 25.2.f",
        "fuente_url": "https://www.boe.es/eli/es/rdlg/2004/03/05/1",
        "palabras_clave": ["catastro", "referencia catastral", "valor catastral",
                           "certificado catastral", "catastral"],
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
