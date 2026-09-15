import { expect, test } from "@playwright/test";

// Issue #150. El control del umbral no sirve de nada si mover el deslizador no cambia
// lo que se dibuja: la vista se veria igual y nadie lo notaria, que es la forma exacta
// del defecto que este proyecto viene catalogando.
//
// Los marcadores se dibujan en un <canvas>, asi que no hay nodos del DOM que contar.
// Se leen del hook `__grafico`, que expone lo mismo que se le paso a setMarkers().

async function grafico(page: import("@playwright/test").Page) {
  return page.evaluate(
    () => (window as unknown as Record<string, { marcadores: number; umbral: number | null }>).__grafico,
  );
}

test("subir el umbral hace que el sistema avise menos, y bajarlo mas", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Tiempo real" }).click();
  await expect(page.getByTestId("control-umbral")).toBeVisible();

  const deslizador = page.getByLabel("Umbral de confianza para avisar");

  // El extremo bajo: el sistema no se calla nunca.
  await deslizador.fill("0");
  await expect(page.getByText(/no se calla nunca/i)).toBeVisible();
  const conTodo = await grafico(page);

  // El extremo alto: se calla casi siempre.
  await deslizador.fill("10");
  const conPocos = await grafico(page);

  expect(conTodo.marcadores).toBeGreaterThan(conPocos.marcadores);
});

test("el punto de operacion muestra siempre la cifra del azar al lado", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Tiempo real" }).click();

  const control = page.getByTestId("control-umbral");
  await expect(control).toBeVisible();
  // "acierta el 10 %" a secas no significa nada: la comparacion es lo que informa.
  await expect(control.getByText(/El azar, igual de hablador/i)).toBeVisible();
  await expect(control.getByText(/Veces el azar/i)).toBeVisible();
  await expect(control.getByText(/tramos a favor/i)).toBeVisible();
});

test("Tiempo real dice la fecha de su ultima vela en vez de prometer que esta al dia", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Tiempo real" }).click();

  await expect(page.getByTestId("ultima-vela")).toContainText(/La última vela de este panel es del/i);
  // Issue #149: la promesa que no se podia cumplir.
  await expect(page.getByText(/LTC al día/i)).toHaveCount(0);
});

test("cada metrica trae su piso del azar, y la exactitud dice que no decide", async ({ page }) => {
  await page.goto("/");
  const metricas = page.getByTestId("metricas");
  await expect(metricas).toBeVisible();

  // Issue #151.2: un numero suelto no se puede leer sin su piso.
  await expect(page.getByTestId("f1-macro")).toContainText(/azar 0\./);
  await expect(page.getByTestId("precision-direccional")).toContainText(/azar 0\./);
  // Issue #151.3: la exactitud estaba con el mismo peso que el F1 macro.
  await expect(page.getByTestId("exactitud")).toContainText(/no decide/i);
});

test("la leyenda explica por que el problema es dificil, no solo los colores", async ({ page }) => {
  await page.goto("/");
  // Issue #151.4.
  await expect(page.getByTestId("leyenda")).toContainText(/% de las velas son continuidad/i);
});

test("la primera pantalla dice que hace el sistema, con la cifra del azar", async ({ page }) => {
  await page.goto("/");
  // Issue #151.1.
  const titular = page.getByTestId("titular");
  await expect(titular).toContainText(/si el precio está por girar/i);
  // Las dos cifras juntas: sin la del azar, la del modelo no se puede leer.
  await expect(titular).toContainText(/F1 macro/i);
  await expect(titular).toContainText(/el azar/i);
  await expect(titular).toContainText(/0\.\d{3}/);
});
