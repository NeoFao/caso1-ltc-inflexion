import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  // Base relativa para que el mismo build funcione en localhost y bajo el
  // subdirectorio de GitHub Pages (/caso1-ltc-inflexion/) sin configurar nada
  // distinto por entorno.
  base: "./",
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // El backend corre en 8000. El proxy evita configurar CORS en produccion y
    // deja que el frontend hable siempre con rutas relativas /api/*.
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
