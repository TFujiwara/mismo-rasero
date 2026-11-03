import Resultados, { EJEMPLOS } from "../resultados";

export const dynamic = "force-dynamic";

export default async function VerificadorPage({
  searchParams,
}: {
  searchParams: { q?: string };
}) {
  const q = (searchParams.q ?? "").trim();

  return (
    <div>
      <p className="font-mono text-[11px] uppercase tracking-[1px] text-ink-soft">
        La ley dice
      </p>
      <h1 className="font-display text-[30px] font-semibold leading-tight text-azul-oscuro">
        ¿Es verdad que…?
      </h1>
      <p className="mt-2 max-w-[600px] text-[14px] leading-relaxed text-ink-soft">
        Escribe la frase — lo que has oído en un mitin, en la radio o en el
        grupo del barrio — y te decimos si esa administración puede hacerlo
        realmente, con el artículo de la ley delante. El veredicto lo decide
        una regla contra la cadena competencial, nunca un modelo.
      </p>

      <form action="/verificador" className="mt-6 flex flex-wrap gap-2">
        <input
          name="q"
          defaultValue={q}
          placeholder="El ayuntamiento bajará el IRPF…"
          className="min-w-[280px] flex-1 rounded-sm border border-linea bg-paper-raised px-4 py-3.5 text-[16px] outline-none focus:border-azul"
        />
        <button className="rounded-sm bg-azul px-6 py-3.5 font-mono text-[12px] uppercase tracking-[1px] text-white hover:bg-azul-oscuro">
          Comprobar
        </button>
      </form>

      {!q && (
        <div className="mt-6 flex flex-wrap gap-2">
          {EJEMPLOS.map((s) => (
            <a
              key={s}
              href={`/verificador?q=${encodeURIComponent(s)}`}
              className="rounded-full border border-linea bg-paper-raised px-3.5 py-1.5 text-[12.5px] text-ink-soft hover:border-azul hover:text-azul"
            >
              {s}
            </a>
          ))}
        </div>
      )}

      <Resultados q={q} />
    </div>
  );
}
