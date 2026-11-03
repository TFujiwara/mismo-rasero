import Pendiente from "../pendiente";

export default function ProgramaPage() {
  return (
    <Pendiente
      folio="§07 — pilar 7 · pendiente Fase 5"
      titulo="Verificador de programas electorales"
      texto="Cruce del PDF del programa con el mapa de competencias: 'el Ayuntamiento construirá 10 hospitales' se marca en rojo — es competencia de la Generalitat (Estatut art. 54). % de promesas posibles/imposibles/cumplidas por partido y año."
      endpoint="GET /api/v1/programa/{partido}/{ano}"
    />
  );
}
