import Link from "next/link";

export default function MetodologiaPage() {
  return (
    <div>
      <h1 className="font-display text-[30px] font-semibold text-azul-oscuro">
        Cómo funciona
      </h1>

      <div className="mt-8 space-y-8">
        <section>
          <h2 className="border-b border-linea pb-1.5 font-display text-[19px] font-semibold text-azul-oscuro">
            De dónde salen los datos
          </h2>
          <p className="mt-3 text-[13.5px] leading-relaxed text-ink-soft">
            De los boletines oficiales: el BOE del Estado, el DOGV de la
            Generalitat, el BOP de tu diputación. Todo lo que publican las
            administraciones es de dominio público. Este sitio lo descarga, lo
            indexa y lo cita. Cada respuesta lleva el enlace al PDF oficial para
            que lo compruebes tú mismo.
          </p>
        </section>

        <section>
          <h2 className="border-b border-linea pb-1.5 font-display text-[19px] font-semibold text-azul-oscuro">
            Cómo respondemos
          </h2>
          <ul className="mt-3 list-disc space-y-1.5 pl-5 text-[13.5px] leading-relaxed text-ink-soft">
            <li>
              Nunca decimos que alguien mienta. Mostramos lo que se dijo y lo que
              dice la norma — el contraste habla solo.
            </li>
            <li>
              El mismo rasero para todos: gobierno y oposición se verifican igual,
              y publicamos abiertamente las estadísticas por partido para que
              cualquiera pueda auditar si es así de verdad.
            </li>
            <li>
              Cada dato lleva fuente. Si el dato está mal, la fuente lo delata —
              y el código es abierto, cualquiera puede revisarlo.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="border-b border-linea pb-1.5 font-display text-[19px] font-semibold text-azul-oscuro">
            Lo que todavía no sabe responder
          </h2>
          <p className="mt-3 text-[13.5px] leading-relaxed text-ink-soft">
            Este proyecto está en construcción y es honesto con sus huecos: el
            mapa de tu calle con geolocalización, los perfiles de representantes,
            el cruce de programas electorales y la verificación de vídeo están en
            camino. No inventamos respuestas para lo que aún no sabemos.
          </p>
        </section>

        <section>
          <h2 className="border-b border-linea pb-1.5 font-display text-[19px] font-semibold text-azul-oscuro">
            Marco legal
          </h2>
          <p className="mt-3 text-[13.5px] leading-relaxed text-ink-soft">
            Los cargos públicos tienen menor protección del honor que un
            particular (STC 171/1990) y existe derecho de rectificación inmediata
            (LO 2/1984): si algo de lo publicado es inexacto, se rectifica. El
            tratamiento de datos se ajusta al RGPD y se está revisando con
            asesoría jurídica especializada antes de cualquier publicación
            pública amplia.
          </p>
        </section>
      </div>
    </div>
  );
}
