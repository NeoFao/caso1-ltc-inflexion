import { expect, test } from "@playwright/test";

// Los tres modos (issue #90): que el selector cambie la vista y ninguna quede
// en blanco sin decirlo. Tiempo real (D21, issue #28) dejo de ser un mensaje de
// "pendiente": reutiliza el historico real de LTC y dibuja igual que Historico,
// con un aviso propio sobre que las ultimas velas no estan confirmadas todavia.

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

  test("Tiempo real dibuja una vista con contenido y declara que la cola no esta confirmada", async ({
    page,
  }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Tiempo real", exact: true }).click();
    await expect(page.getByTestId("vista")).not.toBeEmpty();
    await expect
      .poll(() => page.evaluate(() => (window as any).__grafico?.velas ?? 0))
      .toBeGreaterThan(0);

    const aviso = page.getByTestId("vista-sin-confirmar");
    await expect(aviso).toBeVisible();
    await expect(aviso).toContainText("todavía no");
  });
});
