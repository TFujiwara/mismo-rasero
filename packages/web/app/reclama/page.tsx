import { apiGet } from "@/lib/api";

type Tramite = {
  id: number;
  tramite: string;
  donde: string | null;
  sede_url: string | null;
  articulo_ampara: string | null;
  plazo_dias: number | null;
};

export const dynamic = "force-dynamic";

export default async function ReclamaPage() {
  let tramites: Tramite[] | null = null;
  let error: string | null = null;
  try {
    tramites = await apiGet<Tramite[]>("/accion");
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }

  return (
    <div>
      <p className="font-mono text-[11px] uppercase tracking-[1px] text-ink-soft">
        El artículo dice
      </p>
      <h1 className="font-display text-[30px] font-semibold text-azul-oscuro">
        Reclamar, paso a paso
      </h1>
      <p className="mt-2 max-w-[600px] text-[14px] leading-relaxed text-ink-soft">
        Cuando sabes quién manda, el siguiente paso es usarlo. Estos son los
        trámites que funcionan — cada uno con el artículo de la ley que te ampara.
      </p>

      {error && (
        <p className="mt-8 rounded-sm border border-sello-rojo bg-sello-rojo-suave p-4 font-mono text-[12px] text-sello-rojo">
          No se pudo cargar la lista: {error}
        </p>
      )}

      <div className="mt-8 space-y-5">
        {(tramites ?? []).map((t, i) => (
          <article
            key={t.id}
            className="rounded-sm border border-linea bg-paper-raised p-6"
          >
            <p className="font-mono text-[11px] text-ink-soft">
              Trámite {String(i + 1).padStart(2, "0")}
            </p>
            <h2 className="mt-1 font-display text-[18px] font-semibold text-azul-oscuro">
              {t.tramite}
            </h2>
            {t.donde && (
              <p className="mt-2 text-[13.5px] leading-relaxed">{t.donde}</p>
            )}
            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-linea pt-3 font-mono text-[11.5px] text-ink-soft">
              {t.articulo_ampara && <span>{t.articulo_ampara}</span>}
              {t.plazo_dias && (
                <span>
                  Plazo: {t.plazo_dias >= 365
                    ? `${Math.round(t.plazo_dias / 365)} año`
                    : `${t.plazo_dias} días`}
                </span>
              )}
              {t.sede_url && (
                <a
                  href={t.sede_url}
                  target="_blank"
                  className="text-azul underline decoration-azul-suave hover:decoration-azul"
                >
                  Presentarlo aquí
                </a>
              )}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
