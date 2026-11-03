import { apiGet } from "@/lib/api";

export type Match = {
  id: number;
  nombre: string;
  slug: string;
  descripcion_llana: string | null;
  cadena: string[];
  articulo_legal: string | null;
  fuente_url: string | null;
  palabra_disparadora: string;
  veredicto?: string;
  razon?: string;
  niveles_competentes?: string[];
  nivel_mencionado?: string[];
  sujeto_via?: string;
};

export type Resultado = { texto: string; matches: Match[]; nota: string };

export const EJEMPLOS = [
  "¿Puede el ayuntamiento bajar el IRPF?",
  "¿Quién arregla los baches de mi calle?",
  "¿Quién decide cuánto pago de IBI?",
  "El gobierno pone médicos en el hospital de Vila-real",
];

export default async function Resultados({ q }: { q: string }) {
  let resultado: Resultado | null = null;
  let error: string | null = null;

  if (q.trim().length >= 4) {
    try {
      resultado = await apiGet<Resultado>(
        `/verificar?texto=${encodeURIComponent(q)}`
      );
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    }
  }

  if (error) {
    return (
      <p className="mt-8 rounded-sm border border-sello-rojo bg-sello-rojo-suave p-4 font-mono text-[12px] text-sello-rojo">
        El buscador no responde: {error}
      </p>
    );
  }
  if (!resultado) return null;

  return (
    <div className="mt-8">
      <p className="border-l-[3px] border-azul bg-azul-suave px-4 py-3 text-[13.5px]">
        <b>{resultado.texto}</b>
      </p>

      {resultado.matches.length === 0 && (
        <div className="mt-6 rounded-sm border border-sello-oro bg-sello-oro-suave p-5 text-[13.5px] leading-relaxed">
          Todavía no tengo este tema indexado. El índice de competencias crece
          semana a semana; los temas que ya cubro están en la portada.
        </div>
      )}

      <div className="mt-6 space-y-5">
        {resultado.matches.map((m) => (
          <article
            key={m.id}
            className="rounded-sm border border-linea bg-paper-raised p-6"
          >
            <p className="font-mono text-[10.5px] uppercase tracking-[1px] text-ink-soft">
              Esto es lo que hay que saber
            </p>
            <h2 className="mt-1 font-display text-[19px] font-semibold text-azul-oscuro">
              {m.nombre}
            </h2>

            {m.veredicto && (
              <div className="mt-3">
                <span
                  className={`inline-block rounded-sm border-[1.5px] px-3 py-1.5 font-mono text-[11px] font-semibold uppercase tracking-[0.8px] ${
                    m.veredicto.startsWith("FALSO")
                      ? "border-sello-rojo bg-sello-rojo-suave text-sello-rojo"
                      : m.veredicto.startsWith("VERDADERO")
                        ? "border-sello-verde bg-sello-verde-suave text-sello-verde"
                        : "border-sello-oro bg-sello-oro-suave text-sello-oro"
                  }`}
                >
                  {m.veredicto}
                </span>
                {m.razon && (
                  <p className="mt-2 text-[13.5px] leading-relaxed">{m.razon}</p>
                )}
                {m.sujeto_via === "llm" && (
                  <p className="mt-1 font-mono text-[10px] text-ink-soft">
                    sujeto identificado con asistencia LLM — el veredicto sigue
                    siendo regla + fuente
                  </p>
                )}
              </div>
            )}

            {m.descripcion_llana && (
              <p className="mt-2.5 text-[14px] leading-relaxed">
                {m.descripcion_llana}
              </p>
            )}

            {m.cadena.length > 0 && (
              <div className="mt-4">
                <p className="font-mono text-[10.5px] uppercase tracking-[1px] text-ink-soft">
                  La cadena completa
                </p>
                <ol className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-2">
                  {m.cadena.map((tramo, i) => (
                    <li key={i} className="flex items-center gap-2">
                      <span className="rounded-sm bg-azul-suave px-2.5 py-1 text-[12px] leading-snug text-azul-oscuro">
                        {tramo}
                      </span>
                      {i < m.cadena.length - 1 && (
                        <span className="font-mono text-ink-soft">→</span>
                      )}
                    </li>
                  ))}
                </ol>
              </div>
            )}

            <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-linea pt-3 font-mono text-[11.5px] text-ink-soft">
              {m.articulo_legal && <span>{m.articulo_legal}</span>}
              {m.fuente_url && (
                <a
                  href={m.fuente_url}
                  target="_blank"
                  className="text-azul underline decoration-azul-suave hover:decoration-azul"
                >
                  Fuente oficial (BOE)
                </a>
              )}
            </div>
          </article>
        ))}
      </div>

      <p className="mt-6 text-[12px] leading-relaxed text-ink-soft">
        {resultado.nota}
      </p>
    </div>
  );
}
