import { expect, test } from "@playwright/test";

// Regresion del #144, encontrado por M1 en la revision de QA previa a la entrega
// (#115). El selector Baseline/Fundacional solo se dibuja en Historico, pero su
// estado sobrevive al cambio de modo. Con el orden que tenia el encadenado de
// peticiones, el camino Historico -> Fundacional -> Tiempo real seguia sirviendo
// el precalculado del fundacional -- fecha vieja, ventana de validacion -- bajo
// el aviso de Tiempo real de que los datos son los ultimos disponibles.
//
// No daba error ni dejaba la vista vacia: mostraba datos correctos de otra cosa,
// que es la forma en que un fallo asi llega hasta una exposicion en vivo.
//
// La prueba no fija cifras: compara los dos caminos hacia el mismo modo. Tiempo
// real tiene que dar lo mismo se llegue como se llegue.

test("Tiempo real muestra lo mismo se llegue directo o pasando por Fundacional", async ({
  page,
}) => {
  await page.goto("/");

  await page.getByRole("button", { name: "Tiempo real", exact: true }).click();
  const f1 = page.getByTestId("f1-macro-valor");
  await expect(f1).not.toHaveText("—");
  const directo = await f1.textContent();

  // El camino largo: pasar por Historico, elegir Fundacional y de ahi a Tiempo
  // real, sin recargar la pagina.
  await page.getByRole("button", { name: "Histórico", exact: true }).click();
  await page.getByRole("button", { name: "Fundacional", exact: true }).click();
  await expect(page.getByText(/ventana de validación/i)).toBeVisible();

  await page.getByRole("button", { name: "Tiempo real", exact: true }).click();
  await expect(page.getByTestId("vista-cargando")).toHaveCount(0);
  await expect(f1).toHaveText(directo!);
});

test("Tiempo real no arrastra las senales del fundacional precalculado", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Histórico", exact: true }).click();
  await page.getByRole("button", { name: "Fundacional", exact: true }).click();
  await page.getByRole("button", { name: "Tiempo real", exact: true }).click();
  await expect(page.getByTestId("vista-cargando")).toHaveCount(0);

  // Las tres marcas que delataban el arrastre, y que no pueden convivir con el
  // aviso de Tiempo real.
  await expect(page.getByText(/ventana fija · precalculado sin backend/i)).toHaveCount(0);
  await expect(page.getByText(/Predicciones precalculadas del modelo fundacional/i)).toHaveCount(0);
  await expect(page.getByText(/ventana de validación/i)).toHaveCount(0);

  await expect(page.getByTestId("vista-sin-confirmar")).toBeVisible();
});

test("Sintetico tampoco arrastra el fundacional", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Histórico", exact: true }).click();
  await page.getByRole("button", { name: "Fundacional", exact: true }).click();
  await page.getByRole("button", { name: "Sintético", exact: true }).click();
  await expect(page.getByTestId("vista-cargando")).toHaveCount(0);

  await expect(page.getByText(/Predicciones precalculadas del modelo fundacional/i)).toHaveCount(0);
});

test("Volver a Historico conserva Fundacional, que es donde si aplica", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Histórico", exact: true }).click();
  await page.getByRole("button", { name: "Fundacional", exact: true }).click();
  await page.getByRole("button", { name: "Tiempo real", exact: true }).click();
  await page.getByRole("button", { name: "Histórico", exact: true }).click();

  // Arreglar el arrastre no puede costar la eleccion del usuario: al volver,
  // Fundacional sigue elegido y su vista vuelve.
  await expect(page.getByRole("button", { name: "Fundacional", exact: true })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await expect(page.getByText(/ventana de validación/i)).toBeVisible();
});
