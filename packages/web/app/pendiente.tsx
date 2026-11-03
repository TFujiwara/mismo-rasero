type Props = {
  folio: string;
  titulo: string;
  texto: string;
  endpoint: string;
};

export default function Pendiente({ folio, titulo, texto, endpoint }: Props) {
  return (
    <div>
      <p className="font-mono text-[11px] uppercase tracking-[1px] text-ink-soft">
        {folio}
      </p>
      <h1 className="font-display text-[28px] font-semibold text-azul-oscuro">
        {titulo}
      </h1>
      <div className="mt-6 rounded-sm border border-sello-oro bg-sello-oro-suave p-5 text-[13px] leading-relaxed text-ink">
        {texto}
      </div>
      <p className="mt-4 font-mono text-[11px] text-ink-soft">
        Endpoint destino: <code>{endpoint}</code>
      </p>
    </div>
  );
}
