"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function CalleIndex() {
  const router = useRouter();
  const [direccion, setDireccion] = useState("");

  function ir(e: React.FormEvent) {
    e.preventDefault();
    if (direccion.trim()) {
      router.push(`/calle/${encodeURIComponent(direccion.trim())}`);
    }
  }

  return (
    <div>
      <p className="font-mono text-[11px] uppercase tracking-[1px] text-ink-soft">
        El registro dice
      </p>
      <h1 className="font-display text-[30px] font-semibold text-azul-oscuro">
        Tu calle, sin burocracia
      </h1>
      <p className="mt-2 max-w-[600px] text-[14px] leading-relaxed text-ink-soft">
        Escribe tu dirección y mira qué administraciones hay encima de tu casa:
        el ayuntamiento, la mancomunidad, la diputación, la Generalitat, el
        Estado, Europa — y qué puede hacer cada una.
      </p>
      <form onSubmit={ir} className="mt-6 flex flex-wrap gap-2">
        <input
          value={direccion}
          onChange={(e) => setDireccion(e.target.value)}
          required
          placeholder="Carrer Ermita 12, Vila-real"
          className="w-full max-w-md rounded-sm border border-linea bg-paper-raised px-4 py-3 text-[16px] outline-none focus:border-azul"
        />
        <button className="rounded-sm bg-azul px-6 py-3 font-mono text-[12px] uppercase tracking-[1px] text-white hover:bg-azul-oscuro">
          Consultar
        </button>
      </form>
      <p className="mt-4 text-[12px] text-ink-soft">
        Ejemplo:{" "}
        <Link
          href="/calle/Carrer%20Ermita%2012,%20Vila-real"
          className="text-azul underline decoration-azul-suave hover:decoration-azul"
        >
          Carrer Ermita 12, Vila-real
        </Link>
      </p>
    </div>
  );
}
