import Pendiente from "../pendiente";

export default function VideoPage() {
  return (
    <Pendiente
      folio="§12 — módulo vídeo · pendiente Fase 6"
      titulo="Verificación de vídeo"
      texto="Pega una URL (YouTube, Atresplayer, Mitele, RTVE Play, TikTok) o un m3u8 HLS: transcripción con timestamps, diarización (voces, nunca personas), OCR de chyrons y verificación de cada claim con el mismo motor del texto. El vídeo se borra tras el análisis — solo se persiste texto. Nunca se genera ni redistribuye ningún fragmento."
      endpoint="POST /api/v1/video/ingest"
    />
  );
}
