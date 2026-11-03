import Pendiente from "../pendiente";

export default function PersonaPage() {
  return (
    <Pendiente
      folio="§05 — pilar 5 · pendiente Fase 4"
      titulo="El mapa de personas"
      texto="DIR3, sueldo bruto anual, patrimonio declarado, agenda de los últimos 30 días, comisiones, votaciones de los últimos plenos y % de promesas cumplidas — con fuente en cada dato (Ley 19/2013, registros de bienes de Congreso/Senado/Corts/plenos)."
      endpoint="GET /api/v1/persona/{id}"
    />
  );
}
