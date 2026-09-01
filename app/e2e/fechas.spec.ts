import { expect, test } from "@playwright/test";

// Filtro de fechas (issue #90). El respaldo estatico NO filtra por rango a
// proposito (se genero una sola vez con las ultimas velas; ver el comentario
// en api.ts sobre obtenerHistorico) y la propia UI lo declara. Sin backend
// levantado eso es lo unico verificable: que la app sea honesta sobre la
// limitacion, en vez de fingir un filtro que el snapshot no puede cumplir.
//
// No hay una segunda prueba "con backend en vivo" en este archivo, y no es un
// descuido: esta suite corre contra `vite preview` (build de produccion), y
// ahi `import.meta.env.DEV` queda en `false` grabado en el bundle desde que
// se compilo -- no cambia por tener un backend escuchando ni por agregarle
// proxy a `vite preview`. Es exactamente lo que pide el issue #89: en
// produccion, cero intentos a /api, pase lo que pase alrededor. Probar el
// filtrado real contra un backend vivo exigiria correr esta suite sobre
// `vite dev` en cambio, con otro servidor y otra configuracion -- una suite
// aparte, no una prueba mas en esta.
//
// El comportamiento real (que acotar el rango reduce las observaciones y
// respeta los bordes) ya se verifico a mano, dos veces, contra el backend en
// vivo: al construir el #19 (355 velas en el rango 2024-01-01 -> 2024-03-01)
// y de nuevo cuando Fabrizio revico el PR #77 (355 velas en
// 2026-01-01 -> 2026-03-01, "respetando ambos bordes"). Repetirlo aca no
// agregaria una comprobacion nueva, solo una que no puede correr con esta
// configuracion.

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
