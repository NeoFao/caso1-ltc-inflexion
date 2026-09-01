import { defineConfig, devices } from "@playwright/test";

// E2E de la aplicacion (issue #90). Corre contra el build de produccion servido
// por `vite preview`, sin backend: el respaldo estatico alcanza para las tres
// vistas, el selector de modelo y el conteo de marcadores. Ver e2e/README.md
// para el detalle de por que el filtro de fechas es la unica excepcion.
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: "list",
  use: {
    baseURL: "http://localhost:4173",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npm run build && npm run preview -- --port 4173 --strictPort",
    url: "http://localhost:4173",
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
