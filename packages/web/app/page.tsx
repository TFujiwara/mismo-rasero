import Link from "next/link";

const HERRAMIENTAS = [
  {
    href: "/verificador",
    t: "¿Es verdad que…?",
    d: "Comprueba cualquier frase — de un mitin, de la radio, del grupo del barrio — y mira qué administración puede hacerla de verdad, con el artículo de la ley delante.",
    cta: "Comprobar una frase",
  },
  {
    href: "/calle",
    t: "Tu calle",
    d: "Qué administraciones hay encima de tu casa — ayuntamiento, mancomunidad, diputación, Generalitat, Estado, Europa — y qué puede hacer cada una.",
    cta: "Consultar tu dirección",
  },
  {
    href: "/reclama",
    t: "Reclamar",
    d: "Bache, farola fundida, una administración que no responde: el trámite exacto, dónde presentarlo y el plazo que tienes.",
    cta: "Ver los trámites",
  },
];

export default function Home() {
  return (
    <div>
      <h1 className="max-w-[680px] font-display text-[36px] font-semibold leading-[1.12] tracking-tight text-azul-oscuro">
        Quién puede hacer qué en tu vida —{" "}
        <span className="text-ink-soft">con la ley delante</span>
      </h1>
      <p className="mt-4 max-w-[600px] text-[15px] leading-relaxed text-ink-soft">
        España tiene tres niveles de gobierno, más de ocho mil ayuntamientos y
        un puñado de entes que casi nadie sabe que existen. Cuando alguien
        promete &quot;bajar el IRPF&quot; desde el ayuntamiento, está prometiendo
        algo que no le corresponde — y casi nadie puede comprobarlo en el
        momento. Aquí sí se puede.
      </p>

      <div className="mt-7 flex flex-wrap gap-3">
        <Link
          href="/verificador?q=El%20ayuntamiento%20bajar%C3%A1%20el%20IRPF"
          className="rounded-sm bg-azul px-6 py-3 font-mono text-[12px] uppercase tracking-[1px] text-white hover:bg-azul-oscuro"
        >
          Pruébalo con un ejemplo real
        </Link>
        <Link
          href="/metodologia"
          className="rounded-sm border border-azul px-6 py-3 font-mono text-[12px] uppercase tracking-[1px] text-azul hover:bg-azul-suave"
        >
          Cómo funciona
        </Link>
      </div>

      <h2 className="mt-14 border-b border-linea pb-1.5 font-display text-[22px] font-semibold text-azul-oscuro">
        Qué puedes hacer hoy
      </h2>
      <div className="mt-5 grid gap-4 sm:grid-cols-3">
        {HERRAMIENTAS.map((c) => (
          <div
            key={c.href}
            className="flex flex-col rounded-sm border border-linea bg-paper-raised p-5"
          >
            <p className="font-display text-[17px] font-semibold text-azul-oscuro">
              {c.t}
            </p>
            <p className="mt-1.5 flex-1 text-[13px] leading-relaxed text-ink-soft">
              {c.d}
            </p>
            <Link
              href={c.href}
              className="mt-4 font-mono text-[11.5px] uppercase tracking-[0.8px] text-azul hover:underline"
            >
              {c.cta} →
            </Link>
          </div>
        ))}
      </div>

      <h2 className="mt-14 border-b border-linea pb-1.5 font-display text-[22px] font-semibold text-azul-oscuro">
        Cómo trabajamos
      </h2>
      <div className="mt-5 space-y-4 text-[13.5px] leading-relaxed">
        <div className="flex gap-4">
          <span className="font-mono text-[11px] uppercase tracking-[1px] text-ink-soft [width:110px] shrink-0 pt-0.5">
            Fuente siempre
          </span>
          <p className="text-ink-soft">
            Leemos los boletines oficiales — BOE, DOGV, los BOP provinciales —
            y citamos el documento exacto en cada respuesta: artículo y enlace
            al PDF original. Nada de opiniones sin respaldo.
          </p>
        </div>
        <div className="flex gap-4">
          <span className="font-mono text-[11px] uppercase tracking-[1px] text-ink-soft [width:110px] shrink-0 pt-0.5">
            Mismo rasero
          </span>
          <p className="text-ink-soft">
            Gobierno y oposición se comprueban con el mismo criterio, y las
            estadísticas por partido se publican abiertas para que cualquiera
            pueda auditar la neutralidad.
          </p>
        </div>
        <div className="flex gap-4">
          <span className="font-mono text-[11px] uppercase tracking-[1px] text-ink-soft [width:110px] shrink-0 pt-0.5">
            Sin acusaciones
          </span>
          <p className="text-ink-soft">
            Nunca decimos que alguien mienta. Mostramos lo que se dijo y lo que
            dice la norma — el contraste habla solo, y la fuente lo permite
            verificar en un clic.
          </p>
        </div>
      </div>

      <div className="mt-12 rounded-sm border border-linea bg-azul-suave p-6 text-[13.5px] leading-relaxed">
        <b className="text-azul-oscuro">El proyecto está en construcción</b> y
        es honesto con sus huecos: la geolocalización de direcciones, los
        perfiles de representantes y el cruce de programas electorales están en
        camino. Lo que ya funciona, funciona con datos reales y fuente citada.
      </div>
    </div>
  );
}
