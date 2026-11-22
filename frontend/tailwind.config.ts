import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "rgb(var(--c-bg) / <alpha-value>)",
        surface: "rgb(var(--c-surface) / <alpha-value>)",
        card: "rgb(var(--c-card) / <alpha-value>)",
        brand: {
          DEFAULT: "rgb(var(--c-brand) / <alpha-value>)",
          bright: "rgb(var(--c-brand-bright) / <alpha-value>)",
          fg: "rgb(var(--c-brand-fg) / <alpha-value>)",
        },
        breaking: {
          DEFAULT: "rgb(var(--c-breaking) / <alpha-value>)",
          bright: "rgb(var(--c-breaking-bright) / <alpha-value>)",
        },
        ink: {
          DEFAULT: "rgb(var(--c-ink) / <alpha-value>)",
          muted: "rgb(var(--c-ink-muted) / <alpha-value>)",
        },
        edge: "rgb(var(--c-edge) / <alpha-value>)",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "var(--font-sans)", "serif"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(0,0,0,0.05)",
        "card-hover": "0 12px 28px -18px rgba(0,0,0,0.35)",
        glow: "0 0 0 1px rgba(234,88,12,0.25), 0 10px 34px -14px rgba(234,88,12,0.35)",
      },
    },
  },
  plugins: [],
};

export default config;
