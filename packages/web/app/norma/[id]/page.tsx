import { apiGet } from "@/lib/api";

type Norma = {
  id: number;
  titulo: string;
  rango: string | null;
  fecha_pub: string | null;
  numero_boletin: string | null;
  url_pdf: string;
  hash_sha256: string;
};

type Flujo = {
  flujo_id: number;
  tema: string | null;
  nodos: { paso: string; estado: string; norma_id: number | null; url: string | null }[];
  timeline: Record<string, unknown> | null;
};

export const dynamic = "force-dynamic";

const PASOS = ["DOUE", "BOE", "DOGV", "BOP"];

export default async function NormaPage({
  params,
}: {
  params: { id: string };
}) {
  const id = Number(params.id);
  let norma: Norma | null = null;
  let flujo: Flujo | null = null;
  let error: string | null = null;
  try {
    norma = await apiGet<Norma>(`/normas/${id}`);
    try {
      flujo = await apiGet<Flujo>(`/norma/${id}/flujo`);
    } catch {
      flujo = null; // no participar en ningún flujo no es un error de página
    }
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }

  return (
    <div>
      {error ? (
        <p className="mt-6 rounded-sm border border-sello-rojo bg-sello-rojo-suave p-4 font-mono text-[12px] text-sello-rojo">
          {error}
        </p>
      ) : (
        norma && (
          <>
            <p className="font-mono text-[11px] uppercase tracking-[1px] text-ink-soft">
              {norma.rango} · {norma.fecha_pub}
              {norma.numero_boletin ? ` · BOE nº ${norma.numero_boletin}` : ""}
            </p>
            <h1 className="mt-1 max-w-[680px] font-display text-[26px] font-semibold leading-tight text-azul-oscuro">
              {norma.titulo}
            </h1>
            <div className="mt-4 flex flex-wrap gap-4 font-mono text-[11.5px]">
              <a
                href={norma.url_pdf}
                target="_blank"
                className="rounded-sm bg-azul px-4 py-2 uppercase tracking-[1px] text-white hover:bg-azul-oscuro"
              >
                PDF oficial
              </a>
              <span className="self-center text-ink-soft">
                hash sha256: {norma.hash_sha256.slice(0, 24)}…
              </span>
            </div>

            {flujo && (
              <div className="mt-10">
                <h2 className="border-b border-linea pb-1.5 font-display text-[19px] font-semibold text-azul-oscuro">
                  Su camino hasta tu calle
                </h2>
                {flujo.tema && (
                  <p className="mt-2 text-[13.5px] text-ink-soft">{flujo.tema}</p>
                )}

                <ol className="mt-6 flex flex-wrap items-center gap-y-4">
                  {PASOS.map((paso, i) => {
                    const nodo = flujo!.nodos.find((n) => n.paso === paso);
                    const ok = nodo?.estado === "ok";
                    return (
                      <li key={paso} className="flex items-center gap-3">
                        <div
                          className={`rounded-sm border px-4 py-3 text-center ${
                            ok
                              ? "border-azul bg-azul-suave"
                              : "border-dashed border-linea bg-transparent"
                          }`}
                        >
                          <p className={`font-mono text-[13px] font-semibold ${ok ? "text-azul-oscuro" : "text-ink-soft"}`}>
                            {paso}
                          </p>
                          <p className="mt-0.5 font-mono text-[9.5px] uppercase tracking-[1px]">
                            {ok ? "publicado" : "pendiente"}
                          </p>
                        </div>
                        {i < PASOS.length - 1 && (
                          <span className="font-mono text-ink-soft">→</span>
                        )}
                      </li>
                    );
                  })}
                </ol>

                {flujo.timeline &&
                  Array.isArray((flujo.timeline as { nodos?: unknown[] }).nodos) && (
                    <ul className="mt-4 space-y-1.5 text-[12.5px] leading-relaxed text-ink-soft">
                      {(
                        (flujo.timeline as { nodos: { paso: string; nota?: string }[] })
                          .nodos
                      ).map((n) => (
                        <li key={n.paso}>
                          <b className="text-ink">{n.paso}:</b> {n.nota}
                        </li>
                      ))}
                    </ul>
                  )}
              </div>
            )}

            {!flujo && (
              <p className="mt-8 text-[13px] text-ink-soft">
                Esta norma no participa todavía en ningún flujo normativo
                indexado (DOUE → BOE → DOGV → BOP).
              </p>
            )}
          </>
        )
      )}
    </div>
  );
}
