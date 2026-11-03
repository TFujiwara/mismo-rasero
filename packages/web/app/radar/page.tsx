import Pendiente from "../pendiente";

export default function RadarPage() {
  return (
    <Pendiente
      folio="§10 — transversal · pendiente Fase 7"
      titulo="Radar R0R1R2 + DISARM"
      texto="Hecho literal (R0) + marco (R1) + metanarrativa (R2, 12 fijas) + etiquetado DISARM Red/Blue sobre cada declaración, sin distinción entre gobierno y oposición (§11 — neutralidad auditable). Export STIX2."
      endpoint="GET /api/v1/radar/incidente/{id}"
    />
  );
}
