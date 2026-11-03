import { apiGet } from "@/lib/api";

type Nivel = {
  nivel: string;
  nombre: string;
  puede: string[];
  no_puede: string[];
  fuente_texto: string;
  fuente_url: string;
  pendiente: boolean;
  mancomunidades?: string[];
  afiliacion?: string;
};

type Respuesta = {
  direccion: string;
  resuelta: boolean;
  municipio?: string;
  provincia?: string | null;
  ccaa?: string | null;
  fuente_geocoder?: string;
  display_name?: string;
  nota?: string;
  organigrama: Nivel[];
};

const NIVEL_LABEL: Record<string, string> = {
  UE: "Europa",
  Estado: "Estado",
  CCAA: "Comunidad autónoma",
  Provincia: "Provincia",
  Local: "Tu municipio",
  Supramunicipal: "Supramunicipal",
};

export const dynamic = "force-dynamic";

export default async function CallePage({
  params,
}: {
  params: { direccion: string };
}) {
  const direccion = decodeURIComponent(params.direccion);
  let res: Respuesta | null = null;
  let error: string | null = null;
  try {
    res = await apiGet<Respuesta>(
      `/quien-manda?direccion=${encodeURIComponent(direccion)}`
    );
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }

  return (
    <div>
      <h1 className="font-display text-[28px] font-semibold leading-tight text-azul-oscuro">
        ¿Quién manda en {direccion}?
      </h1>

      {error && (
        <p className="mt-6 rounded-sm border border-sello-rojo bg-sello-rojo-suave p-4 font-mono text-[12px] text-sello-rojo">
          El servicio no responde: {error}
        </p>
      )}

      {res && !res.resuelta && (
        <div className="mt-6 rounded-sm border border-sello-oro bg-sello-oro-suave p-5 text-[13.5px] leading-relaxed">
          {res.nota}
        </div>
      )}

      {res?.resuelta && (
        <>
          <p className="mt-2 text-[13px] text-ink-soft">
            Resuelto como: <b>{res.display_name}</b>
          </p>

          <div className="mt-8 space-y-5">
            {res.organigrama.map((n) => (
              <article
                key={n.nivel}
                className={`rounded-sm border p-6 ${
                  n.pendiente
                    ? "border-dashed border-sello-oro bg-sello-oro-suave/50"
                    : "border-linea bg-paper-raised"
                }`}
              >
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <p className="font-mono text-[10.5px] uppercase tracking-[1px] text-ink-soft">
                    {NIVEL_LABEL[n.nivel] ?? n.nivel}
                  </p>
                  {n.pendiente && (
                    <p className="font-mono text-[10.5px] uppercase tracking-[1px] text-sello-oro">
                      por identificar
                    </p>
                  )}
                </div>
                <h2 className="mt-1 font-display text-[19px] font-semibold text-azul-oscuro">
                  {n.nombre}
                </h2>

                {n.pendiente ? (
                  <p className="mt-2 text-[13.5px] leading-relaxed text-ink-soft">
                    Tu dirección puede depender también de mancomunidades,
                    consorcios o entes locales menores — muy opacos, y
                    precisamente por eso interesan aquí. Estamos cruzando el
                    censo oficial de entes locales para identificarlos; no
                    inventamos ninguno.
                  </p>
                ) : (
                  <>
                    {n.mancomunidades && n.mancomunidades.length > 0 && (
                      <div className="mt-2">
                        <p className="text-[13.5px] leading-relaxed text-ink-soft">
                          {n.mancomunidades.length} registradas en tu provincia
                          (registro oficial DIR3). La afiliación exacta de tu
                          municipio a una u otra llega con el Censo de Entes
                          Locales:
                        </p>
                        <ul className="mt-2 flex flex-wrap gap-2">
                          {n.mancomunidades.map((m) => (
                            <li
                              key={m}
                              className="rounded-full border border-sello-oro px-3 py-1 text-[12px] text-sello-oro"
                            >
                              {m}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {n.puede.length > 0 && (
                      <div className="mt-3 grid gap-4 sm:grid-cols-2">
                        <div>
                          <p className="font-mono text-[10.5px] uppercase tracking-[1px] text-sello-verde">
                            Puede
                          </p>
                          <ul className="mt-1.5 list-disc space-y-1 pl-4 text-[13px] leading-relaxed">
                            {n.puede.map((p) => (
                              <li key={p}>{p}</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <p className="font-mono text-[10.5px] uppercase tracking-[1px] text-sello-rojo">
                            No puede
                          </p>
                          <ul className="mt-1.5 list-disc space-y-1 pl-4 text-[13px] leading-relaxed text-ink-soft">
                            {n.no_puede.map((p) => (
                              <li key={p}>{p}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    )}
                    <p className="mt-4 border-t border-linea pt-3 font-mono text-[11.5px] text-ink-soft">
                      Fuente:{" "}
                      <a
                        href={n.fuente_url}
                        target="_blank"
                        className="text-azul underline decoration-azul-suave hover:decoration-azul"
                      >
                        {n.fuente_texto}
                      </a>
                    </p>
                  </>
                )}
              </article>
            ))}
          </div>

          <p className="mt-6 text-[12px] leading-relaxed text-ink-soft">
            Geocodificación: {res.fuente_geocoder} (cartografía colaborativa, no
            oficial del CNIG). Los límites administrativos de España en OSM
            están verificados contra el registro oficial y el nombre del
            municipio es exacto.
          </p>
        </>
      )}
    </div>
  );
}
