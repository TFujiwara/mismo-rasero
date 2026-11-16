import { apiGet } from "@/lib/api";

type Respuesta = {
  motor: {
    competencias_indexadas: number;
    nota: string;
  };
  por_partido: {
    partido: string | null;
    total_verificaciones: number;
    pct_verificado: number;
  }[];
  nota: string;
};

export const dynamic = "force-dynamic";

export default async function AuditoriaPage() {
  let res: Respuesta | null = null;
  let error: string | null = null;
  try {
    res = await apiGet<Respuesta>("/auditoria/sesgo");
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }

  return (
    <div>
      <p className="font-mono text-[11px] uppercase tracking-[1px] text-ink-soft">
        §11 — la promesa hecha pantalla
      </p>
      <h1 className="font-display text-[30px] font-semibold text-azul-oscuro">
        El mismo rasero, demostrado
      </h1>
      <p className="mt-2 max-w-[640px] text-[14px] leading-relaxed text-ink-soft">
        No basta con prometer neutralidad: se puede auditar. Esta página expone
        cómo funciona el motor y qué cubre — sin curación editorial, sin
        interpretación. Si un día un partido concentra más veredictos negativos,
        el dato quedará aquí visible para que cualquiera lo contraste con la
        realidad.
      </p>

      {error && (
        <p className="mt-8 rounded-sm border border-sello-rojo bg-sello-rojo-suave p-4 font-mono text-[12px] text-sello-rojo">
          El servicio no responde: {error}
        </p>
      )}

      {res && (
        <>
          <section className="mt-8 rounded-sm border border-azul bg-azul-suave p-6">
            <h2 className="font-display text-[18px] font-semibold text-azul-oscuro">
              Cómo funciona el motor
            </h2>
            <div className="mt-3 grid gap-4 sm:grid-cols-2">
              <div>
                <p className="font-mono text-[28px] font-semibold text-azul">
                  {res.motor.competencias_indexadas}
                </p>
                <p className="text-[12.5px] text-ink-soft">
                  competencias con cadena competencial, artículo y fuente
                  verificada vía ELI
                </p>
              </div>
              <div className="text-[12.5px] leading-relaxed text-ink-soft">
                <p>El veredicto lo decide una <b>regla</b> contra la cadena
                competencial — nunca un modelo de lenguaje.</p>
                <p className="mt-1.5">
                  El mismo criterio para cualquier cargo: gobierno u oposición,
                  sin ramas por actor en el código (auditable en el repo).
                </p>
              </div>
            </div>
          </section>

          <section className="mt-8">
            <h2 className="border-b border-linea pb-1.5 font-display text-[19px] font-semibold text-azul-oscuro">
              Declaraciones indexadas por partido
            </h2>
            {res.por_partido.length === 0 ? (
              <p className="mt-3 text-[13.5px] text-ink-soft">
                Todavía no hay declaraciones del radar (§10) indexadas. Cuando el
                radar entre en producción, aquí se verá el desglose por partido
                y rol — sin curación, el dato crudo.
              </p>
            ) : (
              <table className="mt-3 w-full border-collapse text-[12px]">
                <thead>
                  <tr>
                    <th className="bg-azul px-2 py-2 text-left font-mono text-[9.5px] uppercase text-[#e8eef4]">
                      Partido
                    </th>
                    <th className="bg-azul px-2 py-2 text-right font-mono text-[9.5px] uppercase text-[#e8eef4]">
                      Declaraciones
                    </th>
                    <th className="bg-azul px-2 py-2 text-right font-mono text-[9.5px] uppercase text-[#e8eef4]">
                      Verificadas
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {res.por_partido.map((p, i) => (
                    <tr key={p.partido ?? i} className={i % 2 ? "bg-azul/[0.03]" : ""}>
                      <td className="border-b border-linea px-2 py-2">{p.partido ?? "—"}</td>
                      <td className="border-b border-linea px-2 py-2 text-right font-mono">
                        {p.total_verificaciones}
                      </td>
                      <td className="border-b border-linea px-2 py-2 text-right font-mono">
                        {p.pct_verificado}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>

          <p className="mt-6 text-[12px] leading-relaxed text-ink-soft">
            {res.nota}
          </p>
        </>
      )}
    </div>
  );
}
