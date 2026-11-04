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
    {
        "nombre": "Prestación por desempleo (el paro)",
        "slug": "desempleo",
        "descripcion_llana": "El paro lo gestiona el SEPE, del Estado, con la regla "
        "de la Ley General de la Seguridad Social. Ni la CCAA ni el ayuntamiento "
        "pueden cambiar cuantías o duración.",
        "descripcion_tecnica": "Estado: SEPE y prestación por desempleo (LGSS, "
        "RDLeg 8/2015; art. 149.1.17 CE) -> Comunidad Autónoma NO decide cuantías "
        "-> Ayuntamiento NO decide cuantías.",
        "articulo_legal": "LGSS (RDLeg 8/2015)",
        "fuente_url": "https://www.boe.es/eli/es/rdlg/2015/10/30/8",
        "palabras_clave": ["paro", "desempleo", "prestación por desempleo",
                           "sepe", "subsidio", "el subsidio del paro"],
    },
    {
        "nombre": "IVTM — Impuesto de circulación",
        "slug": "ivtm",
        "descripcion_llana": "El impuesto de circulación lo decide, fija y cobra tu "
        "ayuntamiento dentro de la horquilla legal que fija el Estado.",
        "descripcion_tecnica": "Estado: TRLHL (RDLg 2/2004, art. 95-100) fija el "
        "impuesto y su horquilla -> Ayuntamiento: fija el tipo en ordenanza "
        "(BOP), gestiona y recauda el 100%.",
        "articulo_legal": "RDLg 2/2004 art. 95-100",
        "fuente_url": "https://www.boe.es/eli/es/rdlg/2004/03/05/2",
        "palabras_clave": ["ivtm", "impuesto de circulación", "impuesto de matrícula",
                           "pagar el circulación", "bajar el circulación"],
    },
    {
        "nombre": "Plusvalía municipal (IIVTNU)",
        "slug": "plusvalia",
        "descripcion_llana": "La plusvalía municipal la fija y cobra tu "
        "ayuntamiento; el Estado regula el impuesto y sus límites tras las "
        "sentencias del Constitucional.",
        "descripcion_tecnica": "Estado: TRLHL (RDLg 2/2004, art. 96-110, redactado "
        "tras STC 59/2017 y 126/2019) -> Ayuntamiento: fija el tipo en ordenanza "
        "y liquida cuando vendes o donas un inmueble.",
        "articulo_legal": "RDLg 2/2004 art. 96-110",
        "fuente_url": "https://www.boe.es/eli/es/rdlg/2004/03/05/2",
        "palabras_clave": ["plusvalía", "plusvalia municipal", "iivtnu",
                           "plusvalía al vender", "impuesto de plusvalía"],
    },
    {
        "nombre": "Costas — playas y dominio público marítimo",
        "slug": "costas",
        "descripcion_llana": "Las playas y la franja costera son dominio público "
        "del Estado (Costas). El ayuntamiento limpia y presta servicios en la "
        "playa, pero las licencias y deslindeciones son del Estado.",
        "descripcion_tecnica": "Estado: dominio público marítimo-terrestre (Ley "
        "22/1988 de Costas; Costas del Estado/MITECO) -> Ayuntamiento: servicios "
        "en la playa (limpieza, socorrismo si convenio) -> Comunidad Autónoma: "
        "algún papel en urbanismo colindante.",
        "articulo_legal": "Ley 22/1988 de Costas",
        "fuente_url": "https://www.boe.es/eli/es/l/1988/07/28/22",
        "palabras_clave": ["costas", "playas", "playa pública", "deslinde",
                           "chiringuito", "dominio público marítimo"],
    },
    {
        "nombre": "Extranjería — residencia y permisos",
        "slug": "extranjeria",
        "descripcion_llana": "Permisos de residencia y trabajo, asilo y extranjería "
        "son del Estado. Ninguna comunidad ni ayuntamiento puede dar papeles — "
        "aunque sí padronar (que es municipal).",
        "descripcion_tecnica": "Estado: extranjería (LO 4/2000; art. 149.1.2 CE) -> "
        "Comunidad Autónoma NO expide permisos -> Ayuntamiento: solo el padrón "
        "(LBRL art. 16).",
        "articulo_legal": "LO 4/2000 + art. 149.1.2 CE",
        "fuente_url": "https://www.boe.es/eli/es/lo/2000/01/11/4",
        "palabras_clave": ["extranjería", "permiso de residencia", "papeles",
                           "asilo", "refugiados", "nIE", "TIE"],
    },
    {
        "nombre": "Evaluación ambiental — estudios de impacto",
        "slug": "evaluacion-ambiental",
        "descripcion_llana": "Los estudios de impacto ambiental de grandes obras "
        "los tramita el Estado o la Comunidad según quién autorice la obra; la "
        "ley marco es estatal.",
        "descripcion_tecnica": "Estado: ley marco de evaluación ambiental (Ley "
        "21/2013) y proyectos estatales -> Comunidad Autónoma: proyectos "
        "autonómicos y su evaluación -> Ayuntamiento: alegaciones en su término.",
        "articulo_legal": "Ley 21/2013 de evaluación ambiental",
        "fuente_url": "https://www.boe.es/eli/es/l/2013/12/09/21",
        "palabras_clave": ["impacto ambiental", "evaluación ambiental",
                           "declaración de impacto", "obra ambiental", "medio ambiente"],
    },
    {
        "nombre": "Universidad pública",
        "slug": "universidad",
        "descripcion_llana": "Las universidades públicas las crea una ley y las "
        "financian Estado y Comunidad: la Comunidad gestiona el día a día y las "
        "plazas de profesorado.",
        "descripcion_tecnica": "Estado: marco del Sistema Universitario (LSU, LO "
        "2/2023) y universidades estatales -> Comunidad Autónoma: crea y financia "
        "universidades, plazas y profesorado (Estatut art. 57) -> Ayuntamiento NO.",
        "articulo_legal": "LSU (LO 2/2023) + Estatut art. 57",
        "fuente_url": "https://www.boe.es/eli/es/lo/2023/03/22/2",
        "palabras_clave": ["universidad", "universidades públicas", "plazas universidad",
                           "profesor universitario", "grados", "máster oficial"],
    },
    {
        "nombre": "PAC — ayudas agrícolas europeas",
        "slug": "pac-subsidios",
        "descripcion_llana": "Las ayudas agrícolas son dinero europeo (PAC) que "
        "gestiona tu Comunidad Autónoma. Bruselas pone las reglas y el dinero; "
        "la Generalitat o la consejería de agricultura paga.",
        "descripcion_tecnica": "UE: reglas y financiación de la PAC (Reglamento "
        "(UE) 2021/2115) -> Estado: marco nacional (RDL 1/2025) -> Comunidad "
        "Autónoma: pago y control de las ayudas (ej. Generalitat, Conselleria "
        "d'Agricultura).",
        "articulo_legal": "Reglamento (UE) 2021/2115",
        "fuente_url": "https://eur-lex.europa.eu/eli/reg/2021/2115/oj",
        "palabras_clave": ["pac", "subvenciones agrícolas", "ayudas agrícolas",
                           "agricultura", "campo", "pago único"],
    },
    {
        "nombre": "Becas públicas",
        "slug": "becas",
        "descripcion_llana": "Las becas generales las convoca el Ministerio de "
        "Educación (Estado). Las CCAA añaden convocatorias propias; el "
        "ayuntamiento no da becas de estudio.",
        "descripcion_tecnica": "Estado: becas generales (RD 1723/2007; Ministerio "
        "de Educación) -> Comunidad Autónoma: convocatorias propias y "
        "universidades -> Ayuntamiento NO otorga becas generales.",
        "articulo_legal": "RD 1723/2007 (becas generales)",
        "fuente_url": "https://www.boe.es/eli/es/rd/2007/12/21/1723",
        "palabras_clave": ["becas", "beca", "beca mec", "becas generales",
                           "beca de estudios", "ayuda al estudio"],
    },
    {
        "nombre": "Medicamentos y farmacia",
        "slug": "farmacia",
        "descripcion_llana": "Los medicamentos los autoriza la Agencia Española de "
        "Medicamentos (Estado). Las oficinas de farmacia las autoriza la Comunidad "
        "Autónoma; el ayuntamiento no interviene.",
        "descripcion_tecnica": "Estado: medicamentos y AEMPS (Ley 29/2006) -> "
        "Comunidad Autónoma: autorización y ordenación de oficinas de farmacia -> "
        "Ayuntamiento NO interviene.",
        "articulo_legal": "Ley 29/2006 de garantías y uso racional de medicamentos",
        "fuente_url": "https://www.boe.es/eli/es/l/2006/07/26/29",
        "palabras_clave": ["medicamentos", "farmacia", "oficina de farmacia",
                           "aemps", "receta médica", "precio de medicamentos"],
    },
    {
        "nombre": "Contratos públicos (licitaciones)",
        "slug": "contratos-publicos",
        "descripcion_llana": "Las reglas de los contratos públicos las fija una ley "
        "estatal; cada administración (ayuntamiento, Generalitat, Estado) licita "
        "sus propios contratos con esas reglas.",
        "descripcion_tecnica": "Estado: ley marco de contratos (Ley 9/2017) -> "
        "Cada administración licita lo suyo: ayuntamiento (obras y servicios "
        "municipales), Comunidad, Estado -> Los pliegos y adjudicaciones se "
        "publican en la plataforma estatal y en los boletines.",
        "articulo_legal": "Ley 9/2017 de Contratos del Sector Público",
        "fuente_url": "https://www.boe.es/eli/es/l/2017/11/08/9",
        "palabras_clave": ["contratos públicos", "licitación", "licitaciones",
                           "adjudicación", "pliego", "contratación pública"],
    },
    {
        "nombre": "Energía eléctrica — tarifas y factura",
        "slug": "energia-electrica",
        "descripcion_llana": "Las tarifas y el mercado eléctrico los regula el "
        "Estado (CNMC). Tu ayuntamiento no puede bajar la luz — solo el alumbrado "
        "público que paga como consumidor.",
        "descripcion_tecnica": "Estado: sector eléctrico (Ley 24/2013; CNMC "
        "regula tarifas y peajes) -> Comunidad Autónoma: autorización de "
        "instalaciones menores -> Ayuntamiento: alumbrado público (es un "
        "consumidor más, LBRL art. 25.2).",
        "articulo_legal": "Ley 24/2013 del Sector Eléctrico",
        "fuente_url": "https://www.boe.es/eli/es/l/2013/12/26/24",
        "palabras_clave": ["luz", "energía eléctrica", "factura de la luz",
                           "tarifa eléctrica", "pvpc", "apagón", "alumbrado público"],
    },
    {
        "nombre": "Permiso de conducir",
        "slug": "permiso-conducir",
        "descripcion_llana": "El carnet de conducir lo expide la DGT, del Estado. "
        "Ni la comunidad ni el ayuntamiento pueden dártelo o retirártelo.",
        "descripcion_tecnica": "Estado: permisos de conducción (RDLg 6/2015; DGT) -> "
        "Comunidad Autónoma NO expide -> Ayuntamiento NO expide.",
        "articulo_legal": "RDLg 6/2015 (Ley de Tráfico)",
        "fuente_url": "https://www.boe.es/eli/es/rdlg/2015/10/30/6",
        "palabras_clave": ["carnet de conducir", "permiso de conducir",
                           "retirada del carnet", "puntos del carnet", "dgt"],
    },
    {
        "nombre": "Dependencia — Ley de Dependencia",
        "slug": "dependencia",
        "descripcion_llana": "Las ayudas para personas dependientes (ayuda a domicilio, "
        "residencias, cuidadoras) las gestiona tu Comunidad Autónoma con el marco "
        "estatal de la Ley de Dependencia. El ayuntamiento participa en algunos "
        "servicios sociales.",
        "descripcion_tecnica": "Estado: marco (Ley 39/2006, SAAD) -> Comunidad "
        "Autónoma: valora grados y paga/gestiona los servicios -> Ayuntamiento: "
        "algunos servicios sociales de proximidad (LBRL art. 25.2.k).",
        "articulo_legal": "Ley 39/2006 (SAAD) + LBRL art. 25.2.k",
        "fuente_url": "https://www.boe.es/eli/es/l/2006/12/14/39",
        "palabras_clave": ["dependencia", "ley de dependencia", "ayuda a domicilio",
                           "residencia", "cuidadora", "grado de dependencia", "saad"],
    },
    {
        "nombre": "Inspección de trabajo",
        "slug": "inspeccion-trabajo",
        "descripcion_llana": "Las denuncias por explotación laboral, sin contrato o "
        "impago las tramita la Inspección de Trabajo, que es del Estado.",
        "descripcion_tecnica": "Estado: Inspección de Trabajo y Seguridad Social "
        "(RDLeg 5/2000, TRLISOS) -> Comunidad Autónoma NO inspecciona (salvo "
        "transferidas algunas funciones) -> Ayuntamiento NO inspecciona.",
        "articulo_legal": "RDLeg 5/2000 (TRLISOS)",
        "fuente_url": "https://www.boe.es/eli/es/rdlg/2000/08/04/5",
        "palabras_clave": ["inspección de trabajo", "trabajo sin contrato",
                           "explotación laboral", "impago de sueldo", "denuncia laboral"],
    },
    {
        "nombre": "Incendios forestales",
        "slug": "incendios-forestales",
        "descripcion_llana": "Apagar incendios forestales es de la Comunidad "
        "Autónoma (con refuerzo estatal de BRIF si se pide). El ayuntamiento no "
        "manda en el monte.",
        "descripcion_tecnica": "Comunidad Autónoma: extinción y prevención en su "
        "monte (Ley 43/2003 de Montes; competencias estatutarias) -> Estado: "
        "refuerzo BRIF si se solicita -> Ayuntamiento: suburbano y avisos.",
        "articulo_legal": "Ley 43/2003 de Montes",
        "fuente_url": "https://www.boe.es/eli/es/l/2003/11/21/43",
        "palabras_clave": ["incendio forestal", "incendios", "monte", "quema agrícola",
                           "brif", "preaviso de incendios"],
    },
    {
        "nombre": "Patrimonio histórico y cultural",
        "slug": "patrimonio-cultural",
        "descripcion_llana": "Proteger castillos, yacimientos y bienes culturales es "
        "de las CCAA (con la ley estatal de base). El ayuntamiento cuida los bienes "
        "que le pertenecen.",
        "descripcion_tecnica": "Estado: ley básica de patrimonio histórico (Ley "
        "16/1985) -> Comunidad Autónoma: catálogo, excavaciones y autorizaciones "
        "-> Ayuntamiento: bienes municipales y conservación urbana.",
        "articulo_legal": "Ley 16/1985 del Patrimonio Histórico Español",
        "fuente_url": "https://www.boe.es/eli/es/l/1985/06/25/16",
        "palabras_clave": ["patrimonio", "yacimiento", "castillo", "bien de interés cultural",
                           "excavación", "monumento histórico"],
    },
    {
        "nombre": "Políticas de igualdad",
        "slug": "igualdad",
        "descripcion_llana": "El marco de igualdad entre mujeres y hombres es ley "
        "estatal; las CCAA desarrollan políticas propias; los ayuntamientos tienen "
        "sus concejalías de igualdad.",
        "descripcion_tecnica": "Estado: marco (LO 3/2007; Ley Orgánica 1/2004 "
        "violencia de género) -> Comunidad Autónoma: políticas y centros -> "
        "Ayuntamiento: concejalías de igualdad y servicios de proximidad.",
        "articulo_legal": "LO 3/2007 para la igualdad efectiva",
        "fuente_url": "https://www.boe.es/eli/es/lo/2007/03/22/3",
        "palabras_clave": ["igualdad", "violencia de género", "políticas de igualdad",
                           "centro de la mujer", "brecha salarial"],
    },
    {
        "nombre": "Cementerios",
        "slug": "cementerios",
        "descripcion_llana": "Los cementerios son un servicio obligatorio del "
        "ayuntamiento: nichos, enterramientos y sus tasas municipales.",
        "descripcion_tecnica": "Ayuntamiento: cementerio municipal, nichos y tasas "
        "(LBRL art. 25.2; servicio obligatorio) -> Comunidad Autónoma: sanidad "
        "funeraria -> Estado: reglamento general de policías funerarias.",
        "articulo_legal": "LBRL art. 25.2 (servicio obligatorio)",
        "fuente_url": "https://www.boe.es/buscar/act.php?id=BOE-A-1985-11672",
        "palabras_clave": ["cementerio", "nicho", "enterramiento", "sepultura",
                           "tasas de cementerio", "funeraria municipal"],
    },
    {
        "nombre": "Mercados y comercio ambulante",
        "slug": "comercio-ambulante",
        "descripcion_llana": "Los mercados municipales y los puestos ambulantes los "
        "autoriza y ordena el ayuntamiento con sus ordenanzas.",
        "descripcion_tecnica": "Ayuntamiento: mercados municipales, ferias y comercio "
        "ambulante (LBRL art. 25.2.a; ordenanzas municipales) -> Comunidad Autónoma: "
        "marco de comercio interior.",
        "articulo_legal": "LBRL art. 25.2.a",
        "fuente_url": "https://www.boe.es/buscar/act.php?id=BOE-A-1985-11672",
        "palabras_clave": ["mercado municipal", "comercio ambulante", "feria",
                           "puesto callejero", "mercadillo"],
    },
    {
        "nombre": "Viviendas turísticas",
        "slug": "vivienda-turistica",
        "descripcion_llana": "Los pisos turísticos necesitan registro autonómico y "
        "cumplir la ordenanza municipal: ambos niveles intervienen.",
        "descripcion_tecnica": "Comunidad Autónoma: registro de viviendas turísticas "
        "(Decreto 75/2023 CV) -> Ayuntamiento: licencia y compatibilidad con "
        "ordenanza municipal (LBRL art. 25.2.a) -> Estado: marco de vivienda "
        "(Ley 12/2023 lo regula para alquiler).",
        "articulo_legal": "Ley 12/2023 + LBRL art. 25.2.a",
        "fuente_url": "https://www.boe.es/eli/es/l/2023/05/24/12",
        "palabras_clave": ["piso turístico", "vivienda turística", "airbnb",
                           "alquiler turístico", "licencia turística"],
    },
    {
        "nombre": "IAE — Impuesto de Actividades Económicas",
        "slug": "iae",
        "descripcion_llana": "El IAE lo pagan los negocios y lo fija y recauda el "
        "ayuntamiento dentro del marco estatal (los pequeños negocios están "
        "exentos por ley).",
        "descripcion_tecnica": "Estado: TRLHL (RDLg 2/2004, art. 78-91) define el "
        "impuesto y las exenciones (matríz y exentos <1M€) -> Ayuntamiento: fija "
        "tipos en ordenanza y recauda el 100%.",
        "articulo_legal": "RDLg 2/2004 art. 78-91",
        "fuente_url": "https://www.boe.es/eli/es/rdlg/2004/03/05/2",
        "palabras_clave": ["iae", "impuesto de actividades económicas",
                           "licencia fiscal", "alta de autónomos", "iae exento"],
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
