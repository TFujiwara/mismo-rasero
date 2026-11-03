import { apiGet } from "@/lib/api";

type Impuesto = {
  nombre: string;
  quien_legisla: string | null;
  quien_recauda: string | null;
  quien_decide_tipo: string | null;
  reparto_100_euros: { destino: string; porcentaje: number; por_que: string }[];
  fuente_ley_url: string | null;
  ordenanza_bop_url: string | null;
};

type Respuesta = {
  titulo: string;
  impuestos: Impuesto[];
  nota: string;
};

type Desglose = {
  administracion: string;
  ejercicio: number;
  ingresos_total_euros: number;
  gastos_total_euros: number;
  gastos_por_capitulo: { capitulo: string; nombre: string; importe_euros: number; pct: number }[];
  comparativa: {
    ano_anterior: number;
    ano_ultimo: number;
    totales: { ingresos: Delta; gastos: Delta };
    por_capitulo: (Delta & { capitulo: string; nombre: string })[];
  } | null;
  fuente_url: string;
  fuente: string;
};

type Delta = {
  importe_2023?: number;
  importe_2024?: number;
  delta_pct: number | null;
  [k: string]: unknown;
};

const DELTA_TXT = (d: number | null) =>
  d === null ? "—" : `${d > 0 ? "+" : ""}${d}%`;

const COLORES = ["bg-azul", "bg-sello-oro", "bg-sello-verde", "bg-sello-rojo"];

const MEUR = (n: number) =>
  n >= 1_000_000 ? `${(n / 1_000_000).toLocaleString("es-ES", { maximumFractionDigits: 1 })} M€`
    : `${n.toLocaleString("es-ES")} €`;

export const dynamic = "force-dynamic";

export default async function FiscalidadPage({
  searchParams,
}: {
  searchParams: { municipio?: string };
}) {
  const municipio = (searchParams.municipio ?? "").trim();
  let res: Respuesta | null = null;
  let desglose: Desglose | null = null;
  let error: string | null = null;
  try {
    res = await apiGet<Respuesta>("/fiscalidad");
    if (municipio.length >= 3) {
      try {
        desglose = await apiGet<Desglose>(
          `/presupuestos/municipio/${encodeURIComponent(municipio)}`
        );
      } catch {
        desglose = null; // sin datos de ese municipio: se muestra el aviso
      }
    }
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }

  return (
    <div>
      <p className="font-mono text-[11px] uppercase tracking-[1px] text-ink-soft">
        Los datos dicen
      </p>
      <h1 className="font-display text-[30px] font-semibold text-azul-oscuro">
        {res?.titulo ?? "De cada 100 € que pagas, ¿quién se queda qué?"}
      </h1>
      <p className="mt-2 max-w-[600px] text-[14px] leading-relaxed text-ink-soft">
        El reparto del dinero con la ley delante: quién lo legisla, quién lo
        recauda y a dónde va cada tramo.
      </p>

      {error && (
        <p className="mt-8 rounded-sm border border-sello-rojo bg-sello-rojo-suave p-4 font-mono text-[12px] text-sello-rojo">
          El servicio no responde: {error}
        </p>
      )}

      <section className="mt-10 rounded-sm border border-azul bg-azul-suave p-6">
        <h2 className="font-display text-[19px] font-semibold text-azul-oscuro">
          Y en tu ayuntamiento, ¿cómo se reparte?
        </h2>
        <p className="mt-1 text-[13px] text-ink-soft">
          Presupuesto real, capítulo a capítulo, con los datos que Hacienda
          publica del ejercicio más reciente.
        </p>
        <form action="/fiscalidad" className="mt-3 flex flex-wrap gap-2">
          <input
            name="municipio"
            defaultValue={municipio}
            placeholder="Vila-real, Castellón, Onda…"
            className="min-w-[240px] flex-1 rounded-sm border border-linea bg-paper-raised px-3.5 py-2.5 outline-none focus:border-azul"
          />
          <button className="rounded-sm bg-azul px-5 py-2.5 font-mono text-[11.5px] uppercase tracking-[1px] text-white hover:bg-azul-oscuro">
            Ver presupuesto
          </button>
        </form>

        {municipio.length >= 3 && !desglose && (
          <p className="mt-4 text-[13px] text-ink-soft">
            Todavía no tengo el presupuesto de {municipio} indexado. Se ingesta
            desde el portal público de Hacienda; pide que lo incluya en la
            próxima carga.
          </p>
        )}

        {desglose && (
          <div className="mt-5 rounded-sm border border-linea bg-paper-raised p-5">
            <p className="font-display text-[17px] font-semibold text-azul-oscuro">
              {desglose.administracion} · ejercicio {desglose.ejercicio}
            </p>
            <p className="mt-1 font-mono text-[12px] text-ink-soft">
              Ingresos {MEUR(desglose.ingresos_total_euros)} = Gastos{" "}
              {MEUR(desglose.gastos_total_euros)}
            </p>
            <div className="mt-4 space-y-2">
              {desglose.gastos_por_capitulo.map((g) => (
                <div key={g.capitulo}>
                  <div className="flex justify-between text-[12.5px]">
                    <span>{g.nombre}</span>
                    <span className="font-mono text-ink-soft">
                      {MEUR(g.importe_euros)} · {g.pct}%
                    </span>
                  </div>
                  <div className="mt-0.5 h-3.5 w-full overflow-hidden rounded-sm bg-azul-suave">
                    <div className="h-full bg-azul" style={{ width: `${g.pct}%` }} />
                  </div>
                </div>
              ))}
            </div>
            {desglose.comparativa && (
              <div className="mt-5">
                <p className="font-mono text-[10.5px] uppercase tracking-[1px] text-ink-soft">
                  Comparación {desglose.comparativa.ano_anterior} →{" "}
                  {desglose.comparativa.ano_ultimo}
                </p>
                <table className="mt-2 w-full border-collapse text-[12px]">
                  <thead>
                    <tr>
                      <th className="bg-azul px-2 py-1.5 text-left font-mono text-[9.5px] uppercase text-[#e8eef4]">
                        Capítulo
                      </th>
                      <th className="bg-azul px-2 py-1.5 text-right font-mono text-[9.5px] uppercase text-[#e8eef4]">
                        {desglose.comparativa.ano_anterior}
                      </th>
                      <th className="bg-azul px-2 py-1.5 text-right font-mono text-[9.5px] uppercase text-[#e8eef4]">
                        {desglose.comparativa.ano_ultimo}
                      </th>
                      <th className="bg-azul px-2 py-1.5 text-right font-mono text-[9.5px] uppercase text-[#e8eef4]">
                        Δ
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {desglose.comparativa.por_capitulo.map((f) => (
                      <tr key={f.capitulo}>
                        <td className="border-b border-linea px-2 py-1.5">{f.nombre}</td>
                        <td className="border-b border-linea px-2 py-1.5 text-right font-mono">
                          {MEUR(Number(f[`importe_${desglose!.comparativa!.ano_anterior}`] ?? 0))}
                        </td>
                        <td className="border-b border-linea px-2 py-1.5 text-right font-mono">
                          {MEUR(Number(f[`importe_${desglose!.comparativa!.ano_ultimo}`] ?? 0))}
                        </td>
                        <td className="border-b border-linea px-2 py-1.5 text-right font-mono text-ink-soft">
                          {DELTA_TXT(f.delta_pct)}
                        </td>
                      </tr>
                    ))}
                    <tr className="bg-azul-suave font-semibold">
                      <td className="px-2 py-1.5">Total gastos</td>
                      <td className="px-2 py-1.5 text-right font-mono">
                        {MEUR(Number(desglose.comparativa.totales.gastos[`importe_${desglose.comparativa.ano_anterior}`] ?? 0))}
                      </td>
                      <td className="px-2 py-1.5 text-right font-mono">
                        {MEUR(Number(desglose.comparativa.totales.gastos[`importe_${desglose.comparativa.ano_ultimo}`] ?? 0))}
                      </td>
                      <td className="px-2 py-1.5 text-right font-mono">
                        {DELTA_TXT(desglose.comparativa.totales.gastos.delta_pct)}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            )}

            <p className="mt-4 border-t border-linea pt-3 font-mono text-[11px] text-ink-soft">
              Fuente:{" "}
              <a
                href={desglose.fuente_url}
                target="_blank"
                className="text-azul underline decoration-azul-suave hover:decoration-azul"
              >
                {desglose.fuente}
              </a>
            </p>
          </div>
        )}
      </section>

      <div className="mt-8 space-y-6">
        {(res?.impuestos ?? []).map((i, idx) => (
          <article
            key={i.nombre}
            className="rounded-sm border border-linea bg-paper-raised p-6"
          >
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="font-display text-[20px] font-semibold text-azul-oscuro">
                {i.nombre}
              </h2>
              <p className="font-mono text-[11px] uppercase tracking-[1px] text-ink-soft">
                100 € →
              </p>
            </div>

            <div className="mt-3">
              <div className="flex h-7 w-full overflow-hidden rounded-sm">
                {i.reparto_100_euros.map((r, k) => (
                  <div
                    key={r.destino}
                    className={`${COLORES[k % COLORES.length]} flex items-center justify-center text-[11px] font-mono text-white`}
                    style={{ width: `${r.porcentaje}%` }}
                    title={r.destino}
                  >
                    {r.porcentaje}%
                  </div>
                ))}
              </div>
              <ul className="mt-2 space-y-0.5">
                {i.reparto_100_euros.map((r, k) => (
                  <li key={r.destino} className="flex items-center gap-2 text-[12.5px] text-ink-soft">
                    <span className={`inline-block h-2.5 w-2.5 rounded-sm ${COLORES[k % COLORES.length]}`} />
                    <b className="text-ink">{r.destino}</b> — {r.por_que}
                  </li>
                ))}
              </ul>
            </div>

            <dl className="mt-4 space-y-1.5 border-t border-linea pt-3 text-[13px] leading-relaxed">
              {i.quien_legisla && (
                <div className="flex gap-2">
                  <dt className="font-mono text-[10.5px] uppercase tracking-[1px] text-ink-soft [min-width:120px] shrink-0 pt-0.5">
                    Legisla
                  </dt>
                  <dd>{i.quien_legisla}</dd>
                </div>
              )}
              {i.quien_recauda && (
                <div className="flex gap-2">
                  <dt className="font-mono text-[10.5px] uppercase tracking-[1px] text-ink-soft [min-width:120px] shrink-0 pt-0.5">
                    Recauda
                  </dt>
                  <dd>{i.quien_recauda}</dd>
                </div>
              )}
              {i.quien_decide_tipo && (
                <div className="flex gap-2">
                  <dt className="font-mono text-[10.5px] uppercase tracking-[1px] text-ink-soft [min-width:120px] shrink-0 pt-0.5">
                    Decide el tipo
                  </dt>
                  <dd>{i.quien_decide_tipo}</dd>
                </div>
              )}
            </dl>

            <div className="mt-3 flex flex-wrap gap-4 border-t border-linea pt-3 font-mono text-[11.5px]">
              {i.fuente_ley_url && (
                <a
                  href={i.fuente_ley_url}
                  target="_blank"
                  className="text-azul underline decoration-azul-suave hover:decoration-azul"
                >
                  Ley (BOE)
                </a>
              )}
              {i.ordenanza_bop_url && (
                <a
                  href={i.ordenanza_bop_url}
                  target="_blank"
                  className="text-azul underline decoration-azul-suave hover:decoration-azul"
                >
                  Ordenanza (BOP)
                </a>
              )}
            </div>
          </article>
        ))}
      </div>

      {res?.nota && (
        <p className="mt-6 text-[12px] leading-relaxed text-ink-soft">{res.nota}</p>
      )}
    </div>
  );
}
