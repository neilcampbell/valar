import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import svgr from "vite-plugin-svgr";

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    svgr({
      svgrOptions: {
        plugins: ["@svgr/plugin-svgo", "@svgr/plugin-jsx"],
        svgoConfig: {
          floatPrecision: 2,
        },
      },
    }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      "/api": {
        target: "https://afmetrics.api.nodely.io",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""), // Remove '/api' prefix
      },
      "/gov": {
        target: "https://governance.algorand.foundation/api/periods/governance-period-14/",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/gov/, ""), // Remove '/gob' prefix
      },
    },
  },
  define: {
    global: 'window'
  }
});
