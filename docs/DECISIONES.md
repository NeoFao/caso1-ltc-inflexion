# Decisiones del proyecto

**Este archivo es la única fuente de verdad sobre qué decidió el equipo.**

Si alguien dice "esto lo acordamos", tiene que poder señalar una fila de aquí. Una
decisión que no está en este archivo no es una decisión del equipo: es la opinión de
quien la enuncia, por razonable que sea.

## Por qué existe

Durante la Semana 2 quedaron escritas dentro del código cinco atribuciones a decisiones
que nadie había tomado. Se detectaron y se retiraron en el PR #60, pero el episodio
dejó una lección que vale más que la corrección:

> Un número mal se descubre cuando alguien lo recalcula. **Una atribución falsa no se
> descubre nunca**, porque nadie recalcula quién decidió qué.

De ahí las tres reglas del proyecto:

1. **Todo número nuevo tiene que reproducir uno conocido antes de publicarse.**
2. **Toda decisión que se cite como acordada tiene que poder señalar dónde se acordó.**
3. **Una decisión se acuerda en el repositorio —este archivo, un issue, un PR— y nunca
   en un mensaje suelto.**

## Cómo se cambia una decisión

No se edita la fila. Se añade una nueva con el identificador siguiente, se marca la
anterior como **Reemplazada por**, y se explica qué evidencia nueva lo justifica. El
historial de por qué se pensó algo vale tanto como la conclusión.

Las decisiones marcadas **fijada por prueba** las verifica `tests/test_decisiones.py`.
Cambiarlas sin actualizar este archivo hace fallar el CI, que es exactamente lo que se
busca: que nadie las cambie por accidente.

---

## D1 · Granularidad: velas de 4 horas

**Estado:** vigente desde el 18/08/2026 · **fijada por prueba**

Con velas diarias **ninguna** combinación de ventana alcanza el piso de 300 ejemplos de
la clase minoritaria en entrenamiento; la mejor deja 149. Con velas de 4 horas, `w = 7`
deja 420. Las dos granularidades cubren el mismo período, porque la ventana común la
acota Solana: bajar la granularidad no añade historia, subdivide la que hay, de 2 185
observaciones a 13 114.

**Costo aceptado:** más ruido de microestructura y figuras menos legibles.

**Evidencia:** `docs/evidencias/estudio-w-h.json` · **Estudio:** `docs/04-decision-w-h-granularidad.md`

## D2 · Ventana del etiquetado: `w = 7`

**Estado:** vigente desde el 18/08/2026 · **fijada por prueba**

Criterio acordado **antes** de medir: el `w` más grande que cumpla el piso de 300,
porque una ventana grande produce etiquetas más significativas. Sobre el panel de 4
horas eso da 7. Que `w = 10` quedara en 299, uno por debajo, muestra que el criterio
discriminó de verdad en lugar de aprobar cualquier valor.

**Evidencia:** `docs/evidencias/estudio-w-h.json`

## D3 · Horizonte de pronóstico: `h = 1`

**Estado:** vigente desde el 18/08/2026 · **fijada por prueba** · **corrige una propuesta previa**

La información mutua entre lo observable en `t` y la etiqueta en `t+h` cae 4,2 veces al
pasar de `h = 1` a `h = 3` y después se aplana, en las cuatro configuraciones medidas.

**Corrige explícitamente una propuesta anterior de `h = 5`**, que se había hecho por
juicio y no por medición. Se deja registrado porque el error de método importa más que
el valor: se había elegido por parecer más útil, no por evidencia.

**Advertencia que acompaña a esta decisión:** el nivel absoluto de información mutua es
bajo para todo horizonte, incluido `h = 1`. Lo que se interpreta es la forma de la
curva, no su magnitud.

**Evidencia:** `docs/evidencias/estudio-w-h.json`

## D4 · Piso de ejemplos de la clase minoritaria: 300

**Estado:** vigente · **fijada por prueba**

Es una **propuesta del equipo, no un umbral de la literatura**, y así se reporta. Existe
para que la elección de granularidad y ventana tuviera un criterio explícito fijado
antes de mirar los resultados, en lugar de resolverse por intuición.

## D5 · Métrica de decisión: F1 macro, y qué es el umbral

**Estado:** vigente · **fijada por prueba**

La exactitud queda descartada como métrica de decisión: un modelo que no detecta ningún
punto de inflexión alcanza 86,9 % de exactitud. Se usa **F1 macro**, que da igual peso a
las tres clases, acompañado de la Precisión Direccional.

**Sobre `DELTA_F1_DECISIVO = 0,02`:** es una **convención del equipo acordada de
antemano, no un contraste estadístico**. Fijarlo antes de mirar resultados fue lo
correcto; presentarlo como prueba de significancia no lo sería. **Cuando el margen y su
intervalo de confianza discrepen, manda el intervalo.**

**Evidencia:** `docs/evidencias/m2-baselines.json`, `docs/evidencias/m2-incertidumbre.json`

## D6 · Características sobre retornos, no sobre precios en nivel

**Estado:** vigente

Ninguna de las seis series rechaza la raíz unitaria sobre precios en nivel; las seis la
rechazan sobre retornos. Dos mediciones independientes confirmaron después la
consecuencia práctica: los rezagos en nivel producían un efecto aparente de 0,10 en la
ablación que se desploma a 0,003 al expresarlos de forma relativa, y quitarlos mejora el
bosque de referencia en 0,0229.

**Pendiente de aplicar:** el cambio del valor por defecto está en el PR #58, **retenido**
hasta que M3 adopte `columnas_en_nivel_de_precio()` y renombre sus variantes. Sin eso,
la variante que sostiene la mejor cifra del proyecto pasaría a medir otra cosa bajo el
mismo nombre.

## D7 · Los tres baselines son el piso obligatorio

**Estado:** vigente

Todo modelo se compara contra el trivial, el mayoritario y el aleatorio. Cada uno
descarta una explicación alternativa distinta, y el aleatorio es el más exigente en F1
macro, así que es el que hay que superar.

## D8 · Fuente de datos y ventana histórica

**Estado:** vigente

Precios de la interfaz pública de Binance, seis parejas contra USDT. La ventana arranca
el **11 de agosto de 2020** porque la acota Solana, el activo de listado más reciente, y
un panel multivariante exige que las seis series existan simultáneamente.

**Se reporta como lo que es:** son los precios de *un* exchange y no un promedio
ponderado del mercado.

## D9 · Se fusiona siempre con squash

**Estado:** vigente desde el 20/08/2026

GitHub atribuye correctamente el commit resultante al autor del PR. Con merge commit no
lo hace: el PR #53 dejó en `main` un commit atribuido a una identidad por defecto mal
configurada en lugar de a su autor.

**No se reescribe `main`** para corregir los ya fusionados: el costo de romperle el clon
a los cuatro supera al del error, que queda registrado aquí.

Importa porque el curso evalúa contribución individual.

## D10 · El backend en vivo no se publica

**Estado:** vigente desde el 19/08/2026

Los Spaces de Docker de Hugging Face dejaron de ser gratuitos; solo quedan los Static,
que no pueden correr FastAPI. Se cierra sin buscar otro proveedor porque **el backend en
vivo no es un requisito del enunciado**: la página publicada funciona con el snapshot
congelado y declara su antigüedad en la cabecera.

Lo único que se ganaría pagando es que la cabecera diga *hoy* en vez de *hace tres días*.

## D11 · La evidencia de una entrega hecha no se regenera

**Estado:** vigente desde el 18/08/2026

`scripts/figuras_marco_teorico.py` está anclado a velas diarias y `w = 5` **a
propósito**, y no lee el contrato. La evidencia de la Semana 1 se midió así y el
documento cita esos números: leerlos del contrato haría que re-ejecutar el guion
cambiara la evidencia y dejara al entregable citando valores que ya no existen, en
silencio.

**La evidencia de una entrega hecha es historia, no una vista del contrato vigente.**

Para producir las figuras de una entrega futura se cambian esos valores a propósito y se
declara en el documento con qué se midió.
