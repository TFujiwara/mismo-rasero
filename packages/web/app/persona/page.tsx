import { apiGet } from "@/lib/api";

type Persona = {
  id: number;
  nombre: string;
  cargo: string | null;
  admin: string | null;
  fecha_inicio: string | null;
  circunscripcion: string | null;
  grupo: string | null;
  biografia: string | null;
  fuente_url: string | null;
};

export const dynamic = "force-dynamic";

export default async function PersonaPage({
  searchParams,
}: {
  searchParams: { nombre?: string };
}) {
  const nombre = (searchParams.nombre ?? "").trim();
  let personas: Persona[] | null = null;
  let error: string | null = null;

  if (nombre.length >= 3) {
    try {
      personas = await apiGet<Persona[]>(
        `/personas?nombre=${encodeURIComponent(nombre)}`
      );
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    }
  }

  return (
    <div>
      <p className="font-mono text-[11px] uppercase tracking-[1px] text-ink-soft">
        El registro dice
      </p>
      <h1 className="font-display text-[30px] font-semibold text-azul-oscuro">
        Tus representantes
      </h1>
      <p className="mt-2 max-w-[600px] text-[14px] leading-relaxed text-ink-soft">
        Busca un diputado o diputada del Congreso: grupo parlamentario,
        circunscripción, fecha de alta y biografía — con la fuente oficial del
        Congreso delante.
      </p>

      <form action="/persona" className="mt-6 flex flex-wrap gap-2">
        <input
          name="nombre"
          defaultValue={nombre}
          placeholder="Nombre y apellidos…"
          className="min-w-[240px] flex-1 rounded-sm border border-linea bg-paper-raised px-4 py-3 text-[16px] outline-none focus:border-azul"
        />
        <button className="rounded-sm bg-azul px-6 py-3 font-mono text-[12px] uppercase tracking-[1px] text-white hover:bg-azul-oscuro">
          Buscar
        </button>
      </form>

      {error && (
        <p className="mt-8 rounded-sm border border-sello-rojo bg-sello-rojo-suave p-4 font-mono text-[12px] text-sello-rojo">
          El servicio no responde: {error}
        </p>
      )}

      {personas !== null && personas.length === 0 && nombre.length >= 3 && (
        <p className="mt-8 text-[13.5px] text-ink-soft">
          Sin resultados para <b>{nombre}</b>. El buscador cubre el Congreso de
          los Diputados (todas las legislaturas con datos abiertos).
        </p>
      )}

      <div className="mt-8 space-y-4">
        {(personas ?? []).map((p) => (
          <article
            key={p.id}
            className="rounded-sm border border-linea bg-paper-raised p-5"
          >
            <h2 className="font-display text-[17px] font-semibold text-azul-oscuro">
              {p.nombre}
            </h2>
            <div className="mt-1.5 flex flex-wrap gap-x-4 gap-y-1 text-[13px] text-ink-soft">
              {p.grupo && <span>{p.grupo}</span>}
              {p.circunscripcion && <span>· {p.circunscripcion}</span>}
              {p.fecha_inicio && <span>· alta: {p.fecha_inicio}</span>}
            </div>
            {p.biografia && (
              <p className="mt-2 text-[12.5px] leading-relaxed text-ink-soft">
                {p.biografia}
              </p>
            )}
            <p className="mt-3 border-t border-linea pt-2 font-mono text-[10.5px] text-ink-soft">
              Fuente:{" "}
              <a
                href={p.fuente_url ?? "#"}
                target="_blank"
                className="text-azul underline decoration-azul-suave hover:decoration-azul"
              >
                Congreso de los Diputados — datos abiertos
              </a>
            </p>
          </article>
        ))}
      </div>
    </div>
  );
}
