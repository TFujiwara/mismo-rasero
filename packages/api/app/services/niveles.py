"""Niveles administrativos — detección del sujeto de una frase y competencias
por nivel. Determinista: sin LLM para los casos comunes.

NIVELES_COMPETENTES mapea slug de competencia → niveles que DECIDEN (los del
DDE §02/§06). Si la frase menciona un nivel que no decide, el veredicto es
FALSO COMPETENCIAL con fuente; si menciona uno que decide, VERDADERO; si no
hay sujeto claro, informativo.
"""

from __future__ import annotations

import re

from app.services.verificar import normaliza

UE = "UE"
ESTADO = "Estado"
CCAA = "CCAA"
PROVINCIA = "Provincia"
LOCAL = "Local"

# qué nivel decide cada competencia sembrada (§02, §03, §06)
NIVELES_COMPETENTES: dict[str, list[str]] = {
    "salario-minimo": [ESTADO],
    "sanidad-plazas": [CCAA],
    "via-publica": [LOCAL, PROVINCIA],
    "ibi": [LOCAL],
    "irpf": [ESTADO, CCAA],
    "educacion-publica": [CCAA],
    "basuras": [LOCAL],
    "agua-abastecimiento": [LOCAL],
    "carreteras": [LOCAL, PROVINCIA, CCAA, ESTADO],  # según titularidad de la vía
    "policia-local": [LOCAL],
    "policia-nacional": [ESTADO],
    "licencias-obra": [LOCAL],
    "pensiones": [ESTADO],
    "vivienda-publica": [CCAA],
    "transporte-publico": [LOCAL, CCAA, ESTADO],     # urbano / interurbano / cercanías
    "ordenacion-trafico": [LOCAL],
    "empadronamiento": [LOCAL],
    "catastro": [ESTADO],
}

# pistas de sujeto por nivel — regex sobre texto normalizado (sin tildes)
PISTAS_NIVEL: dict[str, tuple[str, ...]] = {
    LOCAL: (r"\bayuntamiento\b", r"\bajuntament\b", r"\balcald\w+", r"\bmunicipio\b",
            r"\bconcejal\w*", r"\bmi (calle|barrio|pueblo|ciudad)\b", r"\blocal\b"),
    PROVINCIA: (r"\bdiputacion\b", r"\bcabildo\b", r"\bconsell insular\b"),
    CCAA: (r"\bgeneralitat\b", r"\bcomunidad autonom", r"\bccaa\b", r"\bautonomic\w+",
           r"\bconsell\b", r"\bjunta de andalucia\b", r"\bgobierno vasco\b",
           r"\bjunta de castilla", r"\bgobierno de canarias\b", r"\bxunta\b",
           r"\bjunta de extremadura\b", r"\bgobierno de aragon\b", r"\bgobierno de navarra\b",
           r"\bgobierno de cantabria\b", r"\bgobierno de la rioja\b", r"\bgobierno balear\b"),
    ESTADO: (r"\bgobierno central\b", r"\bministerio\b", r"\bestado espanol\b",
             r"\bgobierno de espana\b", r"\bcongreso\b", r"\bgobierno de la nacion\b",
             r"\bestado\b", r"\bel gobierno\b"),
    UE: (r"\bbruselas\b", r"\bunion europea\b", r"\bcomision europea\b",
         r"\bue\b", r"\beuropa\b"),
}

NOMBRE_NIVEL = {
    UE: "la Unión Europea",
    ESTADO: "el Estado",
    CCAA: "tu comunidad autónoma",
    PROVINCIA: "tu diputación/provincia",
    LOCAL: "tu ayuntamiento",
}


def detectar_nivel(texto: str) -> list[str]:
    """Niveles administrativos mencionados en la frase. [] = ninguno claro."""
    t = normaliza(texto)
    detectados = []
    for nivel, pistas in PISTAS_NIVEL.items():
        if any(re.search(p, t) for p in pistas):
            detectados.append(nivel)
    return detectados


def veredicto_competencial(
    slug: str, texto: str, niveles_override: list[str] | None = None
) -> dict:
    """Cruza el nivel mencionado en la frase contra el nivel competente.

    niveles_override: niveles detectados por el LLM cuando la regex no llegó
    (mismo tratamiento — el veredicto lo decide la regla).

    Devuelve {veredicto, razon} — el veredicto SIEMPRE lo decide la regla,
    nunca un modelo: el LLM (si está enchufado) solo ayuda a EXTRAER, y su
    salida pasa por aquí igual que la regex.
    """
    niveles_comp = NIVELES_COMPETENTES.get(slug, [])
    mencionados = niveles_override if niveles_override else detectar_nivel(texto)

    if not niveles_comp:
        return {"veredicto": "SIN DATOS DE COMPETENCIA",
                "razon": "esta competencia aún no tiene nivel competente "
                         "estructurado en el índice"}
    if not mencionados:
        return {"veredicto": "SIN SUJETO CLARO",
                "razon": "no identifico qué administración mencionas — esto es "
                         "lo que decide " + ", ".join(NOMBRE_NIVEL[n] for n in niveles_comp)}

    interseccion = [n for n in mencionados if n in niveles_comp]
    if interseccion:
        return {
            "veredicto": "VERDADERO COMPETENCIAL",
            "razon": f"{NOMBRE_NIVEL[interseccion[0]]} sí tiene competencia en esto "
                     "(entre otros niveles que deciden: "
                     + ", ".join(NOMBRE_NIVEL[n] for n in niveles_comp) + ")",
        }
    return {
        "veredicto": "FALSO COMPETENCIAL",
        "razon": f"{NOMBRE_NIVEL[mencionados[0]]} NO decide esto — lo deciden "
                 + ", ".join(NOMBRE_NIVEL[n] for n in niveles_comp),
    }
