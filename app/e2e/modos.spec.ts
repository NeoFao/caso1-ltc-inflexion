import { expect, test } from "@playwright/test";

// Los tres modos (issue #90): que el selector cambie la vista y ninguna quede
// en blanco sin decirlo. "En blanco sin decirlo" es el caso malo: Tiempo real
// muestra "Pendiente (RF-U3)" a proposito, y eso SI cuenta como no-vacio,
// porque le dice al usuario por que no hay grafico. Lo que no puede pasar es
// un contenedor vacio sin ningun texto.

test.describe("los tres modos", () => {
  test("Sintetico dibuja una vista con contenido", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Sintético", exact: true }).click();
    const vista = page.getByTestId("vista");
    await expect(vista).not.toBeEmpty();
    await expect(page.getByTestId("vista-cargando")).toHaveCount(0);
    // El grafico es un <canvas> de lightweight-charts, sin texto: se comprueba
    // que el hook de depuracion (ver Grafico.tsx) registro velas.
    await expect
      .poll(() => page.evaluate(() => (window as any).__grafico?.velas ?? 0))
      .toBeGreaterThan(0);
  });

  test("Historico dibuja una vista con contenido", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Histórico", exact: true }).click();
    await expect(page.getByTestId("vista")).not.toBeEmpty();
    await expect
      .poll(() => page.evaluate(() => (window as any).__grafico?.velas ?? 0))
      .toBeGreaterThan(0);
  });

  test("Tiempo real declara por que esta vacio, en vez de quedar en blanco", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Tiempo real", exact: true }).click();
    const pendiente = page.getByTestId("vista-pendiente");
    await expect(pendiente).toBeVisible();
    await expect(pendiente).toContainText("Pendiente");
  });
});
