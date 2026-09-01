import { expect, test } from "@playwright/test";

// Filtro de fechas (issue #90). El respaldo estatico NO filtra por rango a
// proposito (se genero una sola vez con las ultimas velas; ver el comentario
// en api.ts sobre obtenerHistorico) y la propia UI lo declara. Sin backend
// levantado eso es lo unico verificable: que la app sea honesta sobre la
// limitacion, en vez de fingir un filtro que el snapshot no puede cumplir.
//
// Cuando SI hay backend disponible (se detecta con un fetch corto antes de
// correr), se prueba el comportamiento real: acotar el rango reduce las
// observaciones y respeta los bordes pedidos. Si no hay backend, ese caso se
// salta con motivo explicito -- no se falsea un resultado.

async function hayBackend(request: import("@playwright/test").APIRequestContext) {
  try {
    const r = await request.get("/api/config", { timeout: 1500 });
    return r.ok();
  } catch {
    return false;
  }
}

test("sin backend, declara la limitacion en vez de fingir que filtro", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Histórico", exact: true }).click();

  const observacionesAntes = await page.getByTestId("observaciones-valor").textContent();

  await page.getByLabel("Desde").fill("2024-01-01");
  await page.getByLabel("Hasta").fill("2024-03-01");

  // Con el respaldo estatico el numero de observaciones no cambia -- es
  // exactamente lo que hace deshonesto fingir un filtro, y por eso la app
  // muestra el aviso en vez de una cifra recortada que no corresponde al rango.
  await expect(page.getByText(/requiere el backend en vivo/i)).toBeVisible();
  await expect(page.getByTestId("observaciones-valor")).toHaveText(observacionesAntes ?? "");
});

test("con backend en vivo, acotar el rango reduce las observaciones y respeta los bordes", async ({
  page,
  request,
}) => {
  test.skip(!(await hayBackend(request)), "no hay backend levantado en /api; se salta este caso");

  await page.goto("/");
  await page.getByRole("button", { name: "Histórico", exact: true }).click();
  await expect(page.getByTestId("observaciones-valor")).not.toHaveText("0");

  const totalTexto = await page.getByTestId("observaciones-valor").textContent();
  const total = Number((totalTexto ?? "0").replace(/[^\d]/g, ""));

  await page.getByLabel("Desde").fill("2024-01-01");
  await page.getByLabel("Hasta").fill("2024-03-01");

  await expect
    .poll(async () => {
      const texto = await page.getByTestId("observaciones-valor").textContent();
      return Number((texto ?? "0").replace(/[^\d]/g, ""));
    })
    .toBeLessThan(total);

  const respuesta = await request
    .get("/api/historico?activo=LTC&desde=2024-01-01&hasta=2024-03-01")
    .then((r) => r.json());
  const fechas = respuesta.serie.map((p: { fecha: string }) => new Date(p.fecha).getTime());
  expect(Math.min(...fechas)).toBeGreaterThanOrEqual(new Date("2024-01-01T00:00:00Z").getTime());
  expect(Math.max(...fechas)).toBeLessThanOrEqual(new Date("2024-03-01T23:59:59Z").getTime());
});
