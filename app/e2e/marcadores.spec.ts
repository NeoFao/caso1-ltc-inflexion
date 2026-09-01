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
// La cuenta de referencia sale del mismo JSON estatico que consume la app, no
// de un numero copiado a mano: si la evidencia cambia, la prueba se sigue
// comparando contra si misma.
//
// Se prueba sobre los dos snapshots de 4h que sirve la app -- Baseline
// (historico-LTC.json) y Fundacional (historico-fundacional-LTC.json) --
// porque hasta el #95 el de Baseline tenia granularidad diaria (una vela por
// dia, sin colision posible) y no podia probar nada de esto. Regenerado con
// scripts/exportar_estatico.py contra el contrato vigente (4h), ahora si trae
// las seis velas de 4h por dia y es el modo por el que entra la mayoria de
// quien visita el sitio -- vale la pena cubrirlo tambien, no solo Fundacional.

for (const [etiquetaModo, boton, archivo] of [
  ["Baseline", null, "historico-LTC.json"],
  ["Fundacional", "Fundacional", "historico-fundacional-LTC.json"],
] as const) {
  test(`cada giro real llega dibujado al grafico en ${etiquetaModo}, ninguno se pierde`, async ({
    page,
    request,
  }) => {
    const snapshot = await request.get(`/datos/${archivo}`).then((r) => r.json());
    const girosEnLosDatos = snapshot.serie.filter(
      (p: { etiqueta: number | null }) => p.etiqueta === 1 || p.etiqueta === 2,
    ).length;
    expect(
      girosEnLosDatos,
      "la muestra de prueba no tiene giros; no prueba nada",
    ).toBeGreaterThan(0);

    await page.goto("/");
    await page.getByRole("button", { name: "Histórico", exact: true }).click();
    if (boton) await page.getByRole("button", { name: boton, exact: true }).click();

    await expect
      .poll(() => page.evaluate(() => (window as any).__grafico?.velas ?? 0))
      .toBe(snapshot.serie.length);

    const giroReales = await page.evaluate(() => (window as any).__grafico?.giroReales ?? -1);
    expect(giroReales, "marcadores de giros reales dibujados en el grafico").toBe(girosEnLosDatos);
  });
}

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
