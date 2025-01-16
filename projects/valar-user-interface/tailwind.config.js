import animate from "tailwindcss-animate";

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          dark: "#0E3438",
          DEFAULT: "#145C69",
          light: "#1D7B8C",
        },
        secondary: {
          dark: "#3FAEC9",
          DEFAULT: "#69CBE3",
          light: "#A2EDFF",
        },
        validator: {
          DEFAULT: "#6EA2AB",
        },
        tertiary: {
          dark: "#4D7177",
          DEFAULT: "#6EA2AB",
          light: "#A4CFD6",
        },
        text: {
          DEFAULT: "#FFFFFF",
          secondary: "#F1F5F9",
          tertiary: "#CBD5E1",
        },
        error: { DEFAULT: "#DC2626", background: "#FEE2E2" },
        warning: "#EA580C",
        success: {
          DEFAULT: "#16A34A",
          dark: "#004434",
          background: "#99B9B1",
        },
        golden: {
          DEFAULT: "#CF7F06",
          light: "F9A018",
          background: "#FEF6E8",
        },
        hover: "#414145",
        border: "#33333D",
        background: {
          DEFAULT: "#1C1C21",
          light: "#25252C",
        },
        gradient: {
          light: "#0E343800",
          dark: "#0E3438CC",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: {
            height: "0",
          },
          to: {
            height: "var(--radix-accordion-content-height)",
          },
        },
        "accordion-up": {
          from: {
            height: "var(--radix-accordion-content-height)",
          },
          to: {
            height: "0",
          },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [animate],
};
