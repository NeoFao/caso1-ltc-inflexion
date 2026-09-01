import { expect, test } from "@playwright/test";

// El punto que mas importa del issue #90. No basta con que el grafico
// aparezca: hay que CONTAR los marcadores y compararlos con los giros que hay
// en los datos. Es exactamente lo que habria atrapado el defecto de #f903e62 --
// el backend truncaba la marca de tiempo a la fecha, seis velas de 4h caian en
// la misma etiqueta, y el grafico (que exige tiempos estrictamente crecientes)
// descartaba cinco de cada seis junto con sus marcadores. El grafico se
// dibujaba igual: solo con una sexta parte de los giros. Ninguna prueba que
// solo mirara "¿aparece un grafico?" lo hubiera visto.
//
// Se prueba sobre datos/historico-fundacional-LTC.json, no sobre
// historico-LTC.json: el snapshot de Baseline resulto tener granularidad
// diaria (una vela por dia, sin colision posible), asi que nunca podria haber
// tenido el defecto ni puede probar que la deduplicacion funciona. El de
// Fundacional si trae las seis velas de 4h por dia -- la granularidad real
// del proyecto -- y es donde una regresion de este tipo se veria.
//
// La cuenta de referencia sale del mismo JSON estatico que consume la app, no
// de un numero copiado a mano: si la evidencia cambia, la prueba se sigue
// comparando contra si misma.

test("cada giro real de los datos llega dibujado al grafico, ninguno se pierde", async ({
  page,
  request,
}) => {
  const snapshot = await request
    .get("/datos/historico-fundacional-LTC.json")
    .then((r) => r.json());
  const girosEnLosDatos = snapshot.serie.filter(
    (p: { etiqueta: number | null }) => p.etiqueta === 1 || p.etiqueta === 2,
  ).length;
  expect(girosEnLosDatos, "la muestra de prueba no tiene giros; no prueba nada").toBeGreaterThan(0);

  await page.goto("/");
  await page.getByRole("button", { name: "Histórico", exact: true }).click();
  await page.getByRole("button", { name: "Fundacional", exact: true }).click();

  await expect
    .poll(() => page.evaluate(() => (window as any).__grafico?.velas ?? 0))
    .toBe(snapshot.serie.length);

  const giroReales = await page.evaluate(() => (window as any).__grafico?.giroReales ?? -1);
  expect(giroReales, "marcadores de giros reales dibujados en el grafico").toBe(girosEnLosDatos);
});

test("el modo sintetico tambien conserva todos sus giros al dibujar", async ({ page, request }) => {
  // Sin backend (esta suite corre contra el build de produccion, ver
  // playwright.config.ts) obtenerSintetico(300) siempre cae al snapshot
  // estatico datos/sintetico.json -- generado una vez con semilla fija, no
  // "en el momento" -- asi que admite la misma comparacion exacta que
  // Fundacional, en vez de un umbral flojo.
  const snapshot = await request.get("/datos/sintetico.json").then((r) => r.json());
  const girosEnLosDatos = snapshot.serie.filter(
    (p: { etiqueta: number | null }) => p.etiqueta === 1 || p.etiqueta === 2,
  ).length;
  expect(girosEnLosDatos, "la muestra de prueba no tiene giros; no prueba nada").toBeGreaterThan(0);

  await page.goto("/");
  await page.getByRole("button", { name: "Sintético", exact: true }).click();

  await expect
    .poll(() => page.evaluate(() => (window as any).__grafico?.velas ?? 0))
    .toBe(snapshot.serie.length);

  const giroReales = await page.evaluate(() => (window as any).__grafico?.giroReales ?? -1);
  expect(giroReales, "marcadores de giros reales dibujados en el grafico").toBe(girosEnLosDatos);
});
