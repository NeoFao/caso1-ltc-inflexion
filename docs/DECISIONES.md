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

**También aplica a `src/modelos/inventario_tsfm.py`**, anclado a `w = 7`, `h = 5`, aunque
por una razón distinta que conviene no confundir. La Semana 2 **todavía no se entregó**: vence
el 25/08. Ahí el anclaje no protege historia, evita desincronización — re-ejecutar el guion
cambiaría los tiempos que cita la Tabla 1 de `m3-modelos.md` sin que el documento se entere.
Mientras la Semana 2 sea borrador, remedirla y actualizar la tabla **sí está permitido**; lo
que no está permitido es que la evidencia cambie sola.

## D12 · Modelo fundacional: Chronos-Bolt

**Estado:** vigente desde el 21/08/2026 · cierra [#21](https://github.com/NeoFao/caso1-ltc-inflexion/issues/21)

RF-M1 exige justificar la elección según las características **medidas** de los datos y de
nuestras máquinas, no por popularidad. Los criterios se declararon antes de aplicarlos:
que corra en CPU (RNF-1), que el código esté disponible (RF-M2), que el tiempo de
inferencia quepa en el presupuesto de dos horas del modelo avanzado (RNF-4), y que no
obligue a cambiar el entorno del equipo (RNF-3).

**Se elige `amazon/chronos-bolt-small`.** Medido en CPU, contexto de 512 velas reales de
LTC:

| Candidato | Disco (MB) | RAM pico (MB) | s/ventana en lote | Bloque de validación (min) |
|---|---|---|---|---|
| **chronos-bolt-small** | **182,05** | **695,0** | **0,0061** | **0,2** |
| chronos-t5-small | 176,08 | 4 805,6 | 2,9546 | 96,3 |
| timesfm-2.5-200m | 882,32 | 1 264,6 | 0,1836 | 6,0 |

**Alternativas descartadas y el motivo:**

- **Chronos-T5** — por presupuesto, no por gusto: **96,3 minutos de sola inferencia** sobre
  el bloque de validación, sin entrenar nada, contra el techo de dos horas de RNF-4. Y 4,8 GB
  de memoria pico contra 695 MB. Es autorregresivo y muestrea 20 trayectorias por ventana;
  Bolt predice sus 9 cuantiles de una pasada.
- **TimesFM 2.5** — viable (6,0 min), pero 4,8 veces el disco y 1,8 veces la memoria de Bolt,
  y devuelve solo el pronóstico puntual. Bolt devuelve 9 cuantiles, que es lo que da
  incertidumbre para decidir entre Máximo y Mínimo.
- **IBM granite-tsfm** — descartado **antes de instalarlo**: su resolución degrada `torch` de
  2.13.0 a 2.10.0, y un entorno distinto al del resto del equipo rompe RNF-3. Comprobado con
  `uv pip install --dry-run`.
- **CryptoMamba, VTA y FinLSPM** — no compiten aquí: son candidatos al modelo **avanzado**,
  no al fundacional. Su análisis está en el capítulo de la Semana 2.

**Con qué configuración se midió, que importa:** con `w = 7`, `h = 5`, es decir un horizonte
de 12 velas, que era el contrato vigente cuando se hizo el inventario. D3 corrigió después
`h` a 1, con lo que el horizonte necesario baja a 8. **Lo que decide es el orden de magnitud
entre candidatos —Bolt es 484 veces más rápido por ventana que T5— y ese orden no depende
del horizonte.** La evidencia está anclada, no congelada por D11: la Semana 2 aún es
borrador. Remedirla con `h = 1` es legítimo y sigue pendiente como opcional, precisamente
porque no cambiaría la elección.

**Lo que esta decisión NO resuelve.** Un modelo fundacional pronostica una trayectoria, no
una etiqueta de tres clases. El puente entre ambas cosas —cabeza de clasificación sobre
representaciones congeladas, o pronosticar y aplicarle `etiquetar()`— sigue abierto. El dato
medido que lo condiciona: aplicar `etiquetar()` sobre la trayectoria de Bolt cuesta unos 12
segundos sobre todo el bloque de validación, así que la opción simple dejó de ser la barata
pero peor.

**El modelo avanzado tampoco se decide aquí.** iTransformer e Informer son los candidatos que
cumplen las dos líneas del enunciado, pero **no están medidos en nuestras máquinas**, y
elegir sin medir es exactamente lo que RF-M1 prohíbe. Es la tarea S4-M3-01.

**Evidencia:** `docs/evidencias/m3-inventario-tsfm.json` · **Análisis:** `docs/entregas/semana-2/m3-modelos.md`

## D13 · Remedir una entrega pasada produce evidencia nueva, nunca reescribe la entregada

**Estado:** vigente desde el 21/08/2026 · precisa el alcance de [D11](#d11), no la reemplaza

La D11 dice que la evidencia de una entrega hecha no se regenera, y deja abierto el
procedimiento para medir con el contrato vigente. Faltaba responder la pregunta práctica que
aparece en cuanto alguien tiene que usarlo: **si remido las tablas de una sección ya
entregada, ¿dónde van las cifras nuevas?**

**Van a un archivo nuevo en `docs/evidencias/`, declarando con qué se midieron.** La sección
entregada no se toca; se le añade, si hace falta, una línea que apunte a dónde están las
cifras vigentes. Las tablas de una entrega pasada se citan como lo que son: lo que se
presentó ese día.

**Por qué así y no actualizando en sitio.** Sobrescribir deja un entregable ya presentado
citando cifras distintas de las que se presentaron, sin registro de cuáles eran las
originales. Nadie recalcula un número que ya vio publicado, así que ese cambio no se detecta
después: se descubre solo si alguien compara el archivo contra su propio recuerdo.

**Lo que cuesta:** las cifras de la Semana 1 y las vigentes conviven, y hay que decir en cada
cita cuál se está usando. Es más trabajo que sobrescribir, y es el precio de que las dos
cosas —lo que se entregó y lo que vale hoy— sigan existiendo por separado.

**Lo que esta decisión NO impide.** Corregir en una entrega pasada un enlace roto, una ruta
que dejó de existir o el nombre de un modelo que se renombró. Eso no cambia ninguna cifra:
mantiene la cita apuntando al mismo número. Regenerar la medición sí está prohibido;
conservar la referencia a la medición original es justamente lo que la D11 quiere.

**Origen:** la planteó Alejandro (M2) el 21/08/2026 al toparse con que la D11 le impedía la
tarea que tenía pendiente, y preguntó en vez de decidirlo solo. Es el primer caso en que la
regla 3 funciona como estaba pensada.

**Aplicada en:** [#61](https://github.com/NeoFao/caso1-ltc-inflexion/pull/61), que remide las
tres tablas de métricas con `4h`, `w = 7`, `h = 1` en `m2-tablas-metricas-4h-w7-h1.json` sin
tocar `docs/entregas/semana-1/m2-metricas.md`.

## D14 · Modelo avanzado: iTransformer, e Informer queda fuera por no ser instalable

**Estado:** vigente desde el 21/08/2026 · cierra [#27](https://github.com/NeoFao/caso1-ltc-inflexion/issues/27)

El enunciado pide que el segundo modelo sea un Transformer y nombra iTransformer e Informer
entre las opciones. RF-M2 exige además que su código esté disponible públicamente.
**Disponible en internet y utilizable en nuestras máquinas no son lo mismo**, y la diferencia
ya nos mordió dos veces: CryptoMamba no compila sin CUDA y `granite-tsfm` degradaba `torch`.

**Se elige iTransformer**, con la implementación pública de lucidrains en PyPI.

### Informer queda fuera, y no por preferencia

No encontramos ninguna vía instalable en este entorno:

| Candidato | Trae | Resultado |
|---|---|---|
| `iTransformer` | iTransformer | resoluble |
| `neuralforecast>=1.7` | Informer **e** iTransformer | **no resoluble**: depende de `ray`, que no publica ruedas para Python 3.14 en Windows |
| `informer-pytorch` | Informer | **no resoluble** |

`neuralforecast` era la ruta obvia porque traía los dos juntos. Se comprueba con un comando:
`uv run python -m src.modelos.inventario_avanzado`.

**No es una prueba de que Informer sea inusable en general:** es lo que pudimos verificar en
nuestro entorno, y así se reporta. Vendorizar el código de `thuml/Time-Series-Library` sería
posible, pero mete código ajeno sin empaquetar en el repositorio y no se justifica cuando el
otro candidato del enunciado sí está disponible.

### El presupuesto de la RNF-4 no es lo que limita

Entrenar iTransformer sobre el bloque de entrenamiento tarda **27 segundos** con 141 656
parámetros, contra un techo de dos horas. Sobra por un factor de 250.

### Lo que encontró, y por qué se reporta con dispersión y no con un número

**El F1 del avanzado no es estable.** Medido sobre validación con cinco semillas:

| | |
|---|---|
| F1 macro medio | **0,343698** |
| Mínimo / máximo | 0,330725 / 0,361102 |
| **Rango** | **0,030377** |
| Desviación | 0,009937 |

**El rango supera el umbral de decisión del equipo (0,02).** Eso significa que cualquier
comparación de este modelo hecha con una sola semilla cae dentro de su propio ruido, y por eso
aquí se reporta la media con su dispersión en vez de cuatro decimales de una corrida.

Y hay una segunda fuente de variabilidad, que se midió al toparse con ella: **dos corridas con
la misma semilla no dan el mismo resultado** (0,341851 contra 0,346685, una diferencia de
0,004833). No es la semilla: son diferencias de orden 10⁻¹¹ en la reducción en punto flotante
de la CPU. Se amplifican porque `etiquetar()` decide con desigualdades **estrictas**, así que
sobre una trayectoria pronosticada casi plana una diferencia mínima voltea la etiqueta. **Es
una propiedad del puente, no del modelo**, y le aplica igual al fundacional —solo que ése no
se entrena y su pronóstico es determinista—.

### Comparado con lo demás

Con la media de las cinco semillas frente a los otros modelos sobre la misma partición:

- **No se puede afirmar que le gane al azar.** 0,3437 contra 0,3368 del `baseline_aleatorio`
  son +0,0069, muy por dentro de su propio rango de 0,0304. Y el aleatorio es el exigente
  según la D7.
- **El bosque aleatorio le gana.** 0,3905 contra 0,3437 son −0,0468, fuera del rango de ruido.
- **El fundacional le gana por poco.** 0,3686 contra 0,3437.

**El modelo más simple del proyecto sigue siendo el mejor medido**, y el más caro de los tres
es el peor. Se reporta así.

### Una confirmación independiente del resultado del #62

iTransformer es la arquitectura cuyo argumento de venta es atender *entre series*, así que si
los cinco activos de apoyo aportaran algo, es donde debería verse. Medido con cinco semillas,
la diferencia entre usar los seis y usar solo LTC es de **+0,012586** de media (de +0,002070 a
+0,025328, sin cambiar de signo): **positiva pero por debajo del umbral de 0,02**, y del mismo
orden que el ruido de corrida a corrida.

Es un matiz sobre el #62, no una contradicción: allí el intervalo de confianza sobre las filas
de evaluación incluía el cero; aquí el signo se mantiene en las cinco semillas pero la
magnitud no alcanza el umbral. **Las dos mediciones coinciden en lo que importa: no se puede
afirmar que aporten.** Otra familia de modelo, misma conclusión.

**Evidencia:** `docs/evidencias/m3-sensibilidad-avanzado-4h-w7-h1.json`,
`docs/evidencias/m3-modelos-profundos-4h-w7-h1.json` y
`docs/evidencias/m3-inventario-avanzado.json`

## D15 · Cómo se ajusta un modelo cuyo ruido de semilla supera el umbral de decisión

**Estado:** vigente desde el 21/08/2026 · responde la consulta de M3 en [#37](https://github.com/NeoFao/caso1-ltc-inflexion/issues/37)

M3 midió que el F1 macro del modelo avanzado recorre **0,330725 a 0,361102** entre cinco
semillas — un rango de **0,030377**, que **supera el umbral de decisión de 0,02** (D5). Con esa
dispersión, elegir el máximo de una rejilla no selecciona la mejor configuración: selecciona la
celda a la que le tocó la semilla más afortunada. Y si después esa celda se reporta contra
prueba, el número del informe queda inflado por la misma razón por la que no se mira prueba,
solo que más difícil de ver.

**Se decide promediar cinco semillas por celda**, la opción 1 de las tres que M3 planteó.
Es asequible —entrenar cuesta 27 s— y cambia lo que significa "la mejor configuración": pasa a
ser la mejor en promedio, no la mejor observada. Esa es la que se puede defender.

**La comparación entre celdas va pareada por semilla**, no entre medias sueltas. Lo añadió M3
al implementarlo y no estaba en las opciones planteadas: si una semilla tiende a salir bien en
todas las celdas, comparar promedios mezcla el efecto de la configuración con el de qué semillas
le tocaron a cada una. Es la misma lógica del remuestreo pareado, aplicada a la otra fuente de
variabilidad.

### El criterio se fija antes de mirar el resultado

**Si la dispersión entre semillas dentro de una celda iguala o supera la dispersión entre
celdas, no se corona ganadora.** Se reporta que la rejilla no distingue configuraciones y se
conserva la configuración por defecto.

Queda escrito aquí **antes** de correr la rejilla, y no después, porque es exactamente el caso
en que la tentación de reinterpretar el criterio es mayor. Precedente inmediato: el ajuste del
modelo fundacional dio +0,018680 con un intervalo que incluye el cero, y se reportó como que
ajustar no mejora de forma distinguible. El mismo estándar se aplica acá.

### El mecanismo, medido

La inestabilidad no viene solo de la semilla. **Dos corridas con la misma semilla** dan 0,341851
y 0,346685. El origen son diferencias de orden 10⁻¹¹ en la reducción en punto flotante, que
`etiquetar()` amplifica: exige que los **2w vecinos** sean *estrictamente* menores que el centro,
o sea catorce comparaciones estrictas encadenadas por Y lógico.

Comprobado sobre una trayectoria plana con `w = 7`: un vecino que empata con el centro produce
**Continuidad**; el mismo vecino 10⁻¹¹ por debajo produce **Máximo**.

**Esto no es un defecto del etiquetador ni se va a cambiar.** Sobre precios reales los empates
son improbables y la definición estricta es la que garantiza la propiedad de separación mínima
que usa todo el proyecto. Es una consecuencia de la vía elegida para el puente —pronosticar la
trayectoria y etiquetarla— y **afecta a cualquier modelo que pronostique una trayectoria suave**.

**Se declara en el informe como limitación**, no se corrige. Cambiar la comparación a una
tolerancia alteraría el contrato y todas las cifras publicadas, a cuatro días de la entrega, para
resolver algo que solo se manifiesta sobre trayectorias pronosticadas casi planas.

### Lo que esta decisión NO promete

Que ajustar el avanzado sirva de algo. iTransformer ya queda 0,0448 por debajo del bosque
clásico con intervalo que excluye el cero (D14), y una rejilla no cierra esa distancia. Se hace
una vez, se reporta lo que dé, y no se itera buscando un número mejor.

**Origen:** M3 planteó la consulta en el #37 antes de gastar el tiempo de cómputo, avanzó
declarando su opción como propuesta propia y no como acuerdo, y dejó el rastro por escrito. Es
el procedimiento correcto y conviene que quede dicho.

**Evidencia:** `docs/evidencias/m3-sensibilidad-avanzado-4h-w7-h1.json`

## D16 · Ninguna diferencia se afirma sobre una sola semilla

**Estado:** vigente desde el 22/08/2026 · generaliza la [D15](#d15), que solo cubría el modelo avanzado

El arnés del [#76](https://github.com/NeoFao/caso1-ltc-inflexion/pull/76) se calibró con un
extractor que **reemite ocho columnas que ya existen, con otro nombre**. Información nueva: cero.
La diferencia debería ser nula, y en media lo es —**+0,00071**—, pero por semilla recorre de
**−0,01837 a +0,02573**.

**Añadir columnas que por construcción no informan nada puede producir, en una semilla, una
"mejora" de +0,026 que cruza el umbral de decisión de 0,02.**

Ese es el tamaño del ruido de reentrenamiento del bosque. Cualquiera que enchufe algo, lo mida una
vez y reporte el número, va a reportar ruido — y lo va a reportar como un cruce del umbral.

**Regla:** una diferencia entre dos configuraciones se reporta con **cinco semillas**, y solo se
afirma que una aporta si se cumplen las tres: el intervalo excluye el cero, la diferencia media es
positiva, y **el signo se mantiene en las cinco**. La estabilidad del signo es la que separa una
diferencia real pequeña del ruido, porque el ruido cambia de signo y una diferencia real no.

### Contra qué se contrasta, medido

| Comparación | Media | Signo estable | ¿Se afirma? |
|---|---|---|---|
| Bosque contra el baseline aleatorio | **+0,04065** | sí, mínimo +0,02955 | **Sí** |
| Recorte de las 17 columnas bajo el piso de ruido | +0,00506 | sí | Sí, con su tamaño declarado |
| **Aporte de los cinco activos de apoyo** | **+0,00078** | **no**, 2 de 5 negativas | **No** |
| *Columnas duplicadas sin información nueva* | *+0,00071* | *no* | *— es el control* |

Las dos últimas filas son el punto. **El aporte multivariante medido y añadir columnas que no
contienen nada son indistinguibles entre sí**: misma magnitud hasta el cuarto decimal y la misma
inestabilidad de signo. No es una forma de hablar, es el contraste que la calibración permite
hacer.

### Por qué esta calibración existe

Salió de una instrucción de método que resultó más útil de lo que parecía: el relleno del arnés
**no podía ser ruido aleatorio**, tenía que reproducir un número conocido. Con ruido aleatorio, un
arnés roto y uno correcto habrían dado cifras igual de plausibles y no habría habido nada que
comparar.

Es la lección de S4-M2-01 medida **antes de tener nada que medir**, en vez de descubierta sobre un
resultado que ya queríamos creer.

**Lo que esta decisión NO dice.** Que una diferencia pequeña sea falsa. El recorte de las 17
columnas da +0,00506, muy por debajo de la banda de ruido de una sola semilla, y aun así se
sostiene porque no cambia de signo en ninguna. Lo que se prohíbe es afirmarlo **con una sola
medición**.

**Evidencia:** `docs/evidencias/m2-representacion-4h-w7-h1.json`
