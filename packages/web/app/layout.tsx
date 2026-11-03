import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mismo Rasero — quién puede hacer qué, con la ley delante",
  description:
    "A gobierno y oposición se les aplica el mismo rasero. Contrastes de frases, presupuestos y organigramas con fuente oficial en cada dato.",
};

const NAV = [
  { href: "/", label: "Inicio" },
  { href: "/verificador", label: "¿Es verdad?" },
  { href: "/calle", label: "Tu calle" },
  { href: "/fiscalidad", label: "Tu dinero" },
  { href: "/reclama", label: "Reclamar" },
  { href: "/metodologia", label: "Cómo funciona" },
];

const PROXIMAMENTE = [
  { href: "/persona", label: "Tus representantes" },
  { href: "/programa", label: "Programas electorales" },
  { href: "/radar", label: "Radar de discurso" },
  { href: "/video", label: "Verificación de vídeo" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <header className="sticky top-0 z-20 border-b border-linea bg-paper/95 backdrop-blur">
          <div className="mx-auto flex max-w-[980px] flex-wrap items-center gap-x-8 gap-y-2 px-6 py-3.5">
            <Link href="/" className="font-display text-[19px] font-semibold text-azul-oscuro">
              Mismo Rasero
            </Link>
            <nav className="flex flex-wrap gap-x-5 gap-y-1 text-[13.5px]">
              {NAV.map((n) => (
                <Link
                  key={n.href}
                  href={n.href}
                  className="text-ink-soft underline-offset-4 hover:text-azul hover:underline"
                >
                  {n.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>

        <main className="mx-auto max-w-[880px] px-6 pb-20 pt-12">{children}</main>

        <footer className="border-t border-linea bg-paper-raised">
          <div className="mx-auto flex max-w-[880px] flex-wrap gap-x-12 gap-y-6 px-6 py-10 text-[12.5px]">
            <div>
              <p className="mb-2 font-mono text-[10px] uppercase tracking-[1px] text-ink-soft">
                Próximamente
              </p>
              <ul className="space-y-1.5">
                {PROXIMAMENTE.map((p) => (
                  <li key={p.href}>
                    <Link href={p.href} className="text-ink-soft hover:text-azul">
                      {p.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            <div className="max-w-[380px] text-[12px] leading-relaxed text-ink-soft">
              <p>
                Cada respuesta lleva la fuente oficial: el boletín (BOE, DOGV, BOP)
                donde está escrito. No decimos que alguien mienta: mostramos lo que
                dijo y lo que dice la norma.
              </p>
              <p className="mt-2 font-mono text-[10.5px] tracking-[0.5px]">
                Mismo Rasero · Blueprint técnico v2.5 · Comunitat Valenciana
              </p>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
