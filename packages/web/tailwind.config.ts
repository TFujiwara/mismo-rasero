import type { Config } from "tailwindcss";

// Paleta del blueprint: papel, tinta, azul de registro, sellos rojo/verde/oro.
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#f1efe7",
        "paper-raised": "#faf9f5",
        ink: "#221f1a",
        "ink-soft": "#5b564c",
        linea: "#d9d3c3",
        azul: "#1c3a5e",
        "azul-oscuro": "#122539",
        "azul-suave": "#e4ebf1",
        sello: {
          rojo: "#96281c",
          "rojo-suave": "#f6e6e3",
          verde: "#2d5233",
          "verde-suave": "#e6ede4",
          oro: "#8f6a17",
          "oro-suave": "#f3ecd9",
        },
      },
      fontFamily: {
        serif: ["'Source Serif 4'", "Georgia", "serif"],
        display: ["Fraunces", "Georgia", "serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
