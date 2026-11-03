import { apiGet } from "@/lib/api";

type Tecnica = {
  id: string;
  fase: string | null;
  tactica: string | null;
  nombre: string;
  descripcion: string | null;
  url: string | null;
  tipo: string | null;
};

type Counter = { id: string; nombre: string; descripcion: string | null };

export const dynamic = "force-dynamic";

const FASES = ["", "Plan", "Prepare", "Execute", "Assess"];

export default async function DisarmPage({
  searchParams,
}: {
  searchParams: { tipo?: string; q?: string; fase?: string };
}) {
  const tipo = (searchParams.tipo ?? "RED").toUpperCase() === "BLUE" ? "BLUE" : "RED";
  const q = searchParams.q ?? "";
  const fase = searchParams.fase ?? "";

  let items: (Tecnica | Counter)[] = [];
  let error: string | null = null;
  try {
    if (tipo === "BLUE") {
      items = await apiGet<Counter[]>(
        `/disarm/counters${q ? `?q=${encodeURIComponent(q)}` : ""}`
      );
    } else {
      const params = new URLSearchParams({ tipo: "RED" });
      if (q) params.set("q", q);
      if (fase) params.set("fase", fase);
      items = await apiGet<Tecnica[]>(`/disarm/techniques?${params}`);
    }
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }

  return (
    <div>
      <p className="font-mono text-[11px] uppercase tracking-[1px] text-ink-soft">
        §15 — framework
      </p>
      <h1 className="font-display text-[28px] font-semibold text-azul-oscuro">
        DISARM — explorador Red/Blue
      </h1>
      <p className="mt-2 max-w-[680px] text-[13.5px] leading-relaxed text-ink-soft">
        Técnicas del atacante (RED) y contramedidas (BLUE), cargadas del framework
        oficial. El motor del Pilar 6 etiqueta con estos códigos cada declaración.
      </p>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <a
          href={`/disarm?tipo=RED${q ? `&q=${encodeURIComponent(q)}` : ""}`}
          className={`rounded-sm border px-4 py-2 font-mono text-[11px] uppercase tracking-[0.8px] ${
            tipo === "RED"
              ? "border-sello-rojo bg-sello-rojo-suave text-sello-rojo"
              : "border-linea text-ink-soft"
          }`}
        >
          RED — técnicas
        </a>
        <a
          href={`/disarm?tipo=BLUE${q ? `&q=${encodeURIComponent(q)}` : ""}`}
          className={`rounded-sm border px-4 py-2 font-mono text-[11px] uppercase tracking-[0.8px] ${
            tipo === "BLUE"
              ? "border-sello-verde bg-sello-verde-suave text-sello-verde"
              : "border-linea text-ink-soft"
          }`}
        >
          BLUE — contramedidas
        </a>
        <form action="/disarm" className="flex gap-2">
          <input type="hidden" name="tipo" value={tipo} />
          <input
            name="q"
            defaultValue={q}
            placeholder="filtrar por nombre o código…"
            className="w-64 rounded-sm border border-linea bg-paper-raised px-3 py-2 font-mono text-[12px] outline-none focus:border-azul"
          />
          <button className="rounded-sm bg-azul px-4 py-2 font-mono text-[11px] uppercase text-white">
            Filtrar
          </button>
        </form>
      </div>

      {tipo === "RED" && (
        <div className="mt-3 flex gap-2">
          {FASES.map((f) => (
            <a
              key={f || "todas"}
              href={`/disarm?tipo=RED${f ? `&fase=${f}` : ""}${q ? `&q=${encodeURIComponent(q)}` : ""}`}
              className={`rounded-full px-3 py-1 font-mono text-[10px] uppercase tracking-[0.4px] ${
                fase === f
                  ? "bg-azul-suave text-azul-oscuro"
                  : "bg-transparent text-ink-soft"
              }`}
            >
              {f || "todas las fases"}
            </a>
          ))}
        </div>
      )}

      {error ? (
        <p className="mt-6 rounded-sm border border-sello-rojo bg-sello-rojo-suave p-4 font-mono text-[12px] text-sello-rojo">
          API no disponible: {error} — ¿está corriendo en {":8000"}?
        </p>
      ) : (
        <table className="mt-6 w-full border-collapse text-[12px]">
          <thead>
            <tr>
              <th className="bg-azul px-2.5 py-2 text-left font-mono text-[9.5px] uppercase tracking-[0.6px] text-[#e8eef4]">
                ID
              </th>
              <th className="bg-azul px-2.5 py-2 text-left font-mono text-[9.5px] uppercase tracking-[0.6px] text-[#e8eef4]">
                Nombre
              </th>
              <th className="bg-azul px-2.5 py-2 text-left font-mono text-[9.5px] uppercase tracking-[0.6px] text-[#e8eef4]">
                {tipo === "RED" ? "Táctica" : "Descripción"}
              </th>
            </tr>
          </thead>
          <tbody>
            {items.map((it, i) => (
              <tr key={it.id} className={i % 2 ? "bg-azul/[0.03]" : ""}>
                <td className="border-b border-linea px-2.5 py-2 font-mono text-[11px]">
                  {it.id}
                </td>
                <td className="border-b border-linea px-2.5 py-2">
                  {it.nombre}
                </td>
                <td className="border-b border-linea px-2.5 py-2 text-ink-soft">
                  {tipo === "RED" ? (it as Tecnica).tactica ?? "—" : it.descripcion ?? "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {items.length === 0 && !error && (
        <p className="mt-6 text-[13px] text-ink-soft">
          Sin resultados. Si la tabla está vacía, ejecuta el seed:{" "}
          <code className="bg-azul-suave px-1.5 py-0.5 font-mono text-[11px]">
            uv run disarm-import
          </code>
        </p>
      )}
    </div>
  );
}
