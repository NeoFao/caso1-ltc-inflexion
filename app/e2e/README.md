# Pruebas de extremo a extremo (issue #90)

Abren la aplicación de verdad con Playwright y recorren lo que hace un usuario, en
vez de probar componentes o funciones por separado. Existen porque el defecto de
`f903e62` era invisible en las dos capas por separado: el arnés de M0 medía bien,
el frontend dibujaba un gráfico, y el 84,4 % de los puntos de inflexión no llegaba
a la vista — el defecto vivía entre las dos capas, y solo una prueba que abriera
la app de verdad y **contara los marcadores** lo hubiera atrapado.

## Cómo correrlas

```bash
npm --prefix app run test:e2e
```

La primera vez, instalá el navegador (una sola vez por máquina):

```bash
npx --prefix app playwright install chromium
```

No hace falta levantar nada a mano: `playwright.config.ts` construye la app
(`npm run build`) y la sirve con `vite preview` antes de correr las pruebas.

## Por qué corren a mano y no en CI

`.github/workflows/ci.yml` es infraestructura compartida (M0), y hoy es
deliberadamente solo Python: "no descarga datos ni modelos... para que un fallo
de CI signifique siempre 'alguien rompió algo'". Agregar Playwright ahí exige
Node, `npm install`, descargar un navegador (~100 MB) y un paso de build —un
cambio de infraestructura que le toca decidir a quien la mantiene, no algo para
sumar en silencio desde `app/`.

Por eso esta suite se documenta para correr **a mano**, antes de cada entrega —
que es exactamente lo que pide el rol de QA del issue #90: "correr la aplicación
antes de cada entrega, no solo la suite [de pytest]".

## Por qué no necesitan el backend

`playwright.config.ts` sirve el build de producción (`vite preview`), que —desde
el issue #89— no intenta `/api` sin `VITE_API_BASE` configurada. Todas las
pruebas corren contra el respaldo estático (`app/public/datos/*.json`), que es
exactamente lo que un lector externo del sitio desplegado ve.

La única excepción es el filtro de fechas: el respaldo estático no filtra por
rango a propósito (ver el comentario en `src/api.ts`), así que `fechas.spec.ts`
solo prueba, sin backend, que la app **declara** la limitación en vez de fingir
un filtro.

No hay una segunda prueba que ejercite el filtrado real contra un backend en
vivo, y no es un descuido — lo intenté y encontré por qué no se puede con esta
configuración. Un primer intento detectaba si `/api/config` respondía antes de
decidir si correr esa prueba o saltarla; parecía razonable, pero `vite preview`
sirve `index.html` con 200 para cualquier ruta que no reconoce (el *fallback*
de una SPA), así que la comprobación daba **falso positivo** aun sin backend
escuchando, y la prueba fallaba en vez de saltarse. Corregir eso no alcanzaba:
`import.meta.env.DEV` queda grabado en `false` dentro del bundle desde que se
compila (issue #89), así que ningún proxy en `vite preview` hace que la app
intente `/api` una vez construida para producción. Probar el filtrado real
exigiría correr esta suite entera sobre `vite dev` en cambio, con otro
servidor y otra configuración — una suite aparte, no una prueba más en esta.

El comportamiento real ya se verificó a mano, dos veces, contra el backend en
vivo: al construir el #19, y de nuevo cuando Fabrizio revisó el PR #77 ("355
velas en el rango 2026-01-01 → 2026-03-01, respetando ambos bordes"). El
detalle de cómo se descartó la segunda prueba está en `fechas.spec.ts`.

## El hook de depuración en `Grafico.tsx`

`lightweight-charts` dibuja en un `<canvas>`: no hay nodos del DOM que contar
para verificar que un giro llegó a la vista. `Grafico.tsx` expone
`window.__grafico = { velas, marcadores, giroReales }` después de cada
`setMarkers()` — exactamente los mismos números que ya calculó para dibujar, no
un cálculo nuevo (RF-U6 sigue intacto: no es una métrica, es instrumentación de
prueba). `marcadores.spec.ts` compara `giroReales` contra los giros que trae el
JSON servido, que es la comprobación que el defecto de `f903e62` necesitaba.

## Comprobado que fallan cuando deben

Regla 10: una prueba que nunca se vio fallar no es un control. Antes de mandar
esta suite se truncó a propósito, sobre una copia local, la marca de tiempo de
`datos/historico-fundacional-LTC.json` a solo el día (`fecha.slice(0, 10)`) —
el mismo defecto que tenía `f903e62`, reintroducido sobre el snapshot en vez de
sobre `src/api/`, que no es mía.

`historico-LTC.json` (el respaldo de Baseline) resultó tener granularidad
diaria — una vela por día, sin colisión posible — así que no sirve para esta
comprobación; por eso `marcadores.spec.ts` prueba sobre el snapshot de
Fundacional, que sí trae las seis velas de 4h por día.

Con la fecha truncada, `marcadores.spec.ts` falló así:

```
Expected: 1959
Received: 327
```

327 ≈ 1959 ÷ 6: exactamente el colapso de "una vela sobrevive de cada seis" que
describe `f903e62`. Restaurada la fecha completa, la suite vuelve a pasar (2
passed). No quedó como prueba automática del repositorio porque depende de
corromper un archivo a propósito; queda documentado acá, con el resultado real,
como la comprobación que exige el criterio de aceptación.
