import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        bg: "#f8fafc", // slate-50 for clean modern bg
        surface: "#ffffff",
        "med-bg": "#f1f5f9", // slate-100 for secondary areas
        border: "#e2e8f0", // slate-200 for clean thin borders
        "border-dark": "#cbd5e1", // slate-300
        text: "#0f172a", // slate-900 for dark text
        "text-secondary": "#475569", // slate-600
        "text-muted": "#94a3b8", // slate-400
        accent: "#0d9488", // medical teal-600 for premium clinic feel
        "accent-hover": "#0f766e", // teal-700
        "accent-light": "#f0fdfa", // teal-50
        "brand-indigo": "#4f46e5", // indigo-600
        "brand-indigo-light": "#eef2ff", // indigo-50
        success: "#10b981", // emerald-500
        "success-light": "#ecfdf5",
        warning: "#f59e0b", // amber-500
        "warning-light": "#fffbeb",
        danger: "#ef4444", // red-500
        "danger-light": "#fef2f2",
      },
      fontFamily: {
        sans: ['"Inter"', '"Segoe UI"', "system-ui", "sans-serif"],
      },
      fontSize: {
        "heading-lg": ["1.75rem", { lineHeight: "1.2", fontWeight: "700", letterSpacing: "-0.025em" }],
        "heading-md": ["1.25rem", { lineHeight: "1.3", fontWeight: "600", letterSpacing: "-0.02em" }],
        "heading-sm": ["1rem", { lineHeight: "1.4", fontWeight: "600", letterSpacing: "-0.01em" }],
        label: ["0.75rem", { lineHeight: "1", fontWeight: "500", letterSpacing: "0.05em" }],
      },
      boxShadow: {
        sm: "0 1px 2px 0 rgb(0 0 0 / 0.03)",
        DEFAULT: "0 1px 3px 0 rgb(0 0 0 / 0.04), 0 1px 2px -1px rgb(0 0 0 / 0.03)",
        md: "0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.03)",
      },
      animation: {
        "fade-in": "fadeIn 0.2s ease-out",
        "slide-up": "slideUp 0.2s ease-out",
        "pulse-dot": "pulseDot 2s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseDot: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.4" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
