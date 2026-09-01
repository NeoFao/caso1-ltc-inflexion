import { expect, test } from "@playwright/test";

// Selector Baseline / Fundacional (issue #90 y #24): que las dos den cifras
// distintas, y que las de Fundacional sean las de la evidencia -- no un numero
// cualquiera que coincida por casualidad. El valor esperado se lee del propio
// snapshot que sirve la app (datos/historico-fundacional-LTC.json), no se
// hardcodea, para no duplicar un numero que ya vive en un solo lugar.

test("Fundacional muestra las cifras de su propia evidencia, distintas de Baseline", async ({
  page,
  request,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Histórico", exact: true }).click();

  const f1MacroValor = page.getByTestId("f1-macro-valor");
  await expect(f1MacroValor).not.toHaveText("—");
  const f1Baseline = await f1MacroValor.textContent();

  await page.getByRole("button", { name: "Fundacional", exact: true }).click();
  await expect
    .poll(async () => (await f1MacroValor.textContent()) !== f1Baseline)
    .toBe(true);
  const f1Fundacional = await f1MacroValor.textContent();

  const snapshot = await request
    .get("/datos/historico-fundacional-LTC.json")
    .then((r) => r.json());
  expect(f1Fundacional).toBe(snapshot.metricas.f1_macro.toFixed(3));

  // El aviso de "ventana de validacion" es la otra senal de que de verdad
  // cambio de fuente de datos, no solo de etiqueta.
  await expect(page.getByText(/ventana de validación/i)).toBeVisible();
});

test("Volver a Baseline restaura el selector de activo y de fechas", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Histórico", exact: true }).click();
  await page.getByRole("button", { name: "Fundacional", exact: true }).click();
  await expect(page.getByLabel("Criptomoneda")).toHaveCount(0);

  await page.getByRole("button", { name: "Baseline", exact: true }).click();
  await expect(page.getByLabel("Criptomoneda")).toBeVisible();
  await expect(page.getByLabel("Desde")).toBeVisible();
});
