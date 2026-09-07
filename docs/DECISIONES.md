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

- **No se puede afirmar que le gane al azar.** 0,3437 contra 0,3368 del `baseline_aleatorio`:
  una ventaja que cabe holgadamente dentro del rango de **0,030377** que el propio modelo
  recorre entre semillas. Y el aleatorio es el exigente según la D7.
- **El bosque aleatorio le gana.** 0,3905 contra 0,3437, y esa desventaja **supera** el rango
  de 0,030377, así que no se explica por el ruido de la semilla.
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
contienen nada son indistinguibles entre sí**: los separa menos de la trescientava parte
del umbral de decisión, y comparten la misma
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

## D17 · La hora del día no se incorpora como característica

**Estado:** vigente desde el 25/08/2026 · completa el argumento de estacionalidad del marco teórico

El marco teórico de la Semana 1 descarta codificar el **día de la semana**, y el argumento es
correcto: el mercado de criptoactivos opera de forma continua, sin apertura ni cierre, así que no
existe el mecanismo institucional que produce el efecto de calendario que documenta French (1980).

**Ese argumento no cubría la hora del día.** Y desde que el panel de trabajo son velas de 4 horas
—seis por día— sí hay un mecanismo plausible: los operadores humanos duermen, y el volumen se
concentra cuando están despiertas las plazas grandes. Era la única familia de características de
calendario ni construida ni medida.

**Criterio, fijado antes de mirar:** la hora entra solo si supera el contraste de independencia al
5 % **y** su información mutua alcanza a la de las columnas que ya usamos.

### Medido

| Hora UTC | Giros |
|---|---|
| 00:00 | 8,70 % |
| 04:00 | **8,15 %** |
| 08:00 | 8,84 % |
| 12:00 | 9,84 % |
| 16:00 | **10,49 %** |
| 20:00 | 9,71 % |

El rango es de **2,3363 puntos** y el máximo cae a las 16:00 UTC, que es cuando abre Estados
Unidos. Se ve como un patrón.

**No lo es.** El contraste de independencia da **p = 0,08252**: no hay asociación al 5 %. Y la
información mutua de la hora con la etiqueta es **0,001828**, contra **0,010217** de media en las
63 columnas vigentes — unas cinco veces menos.

**No se incorpora.** Añadirla sería añadir ruido con nombre, que es justo lo que la D16 enseña a
no hacer: una diferencia que se ve grande y no supera su propio control.

**Lo que esta decisión NO dice.** Que no exista estructura intradía en el mercado. Dice que, con
esta definición de punto de inflexión y esta granularidad, **no la podemos distinguir del azar**.

**Origen:** el profesor mencionó la ingeniería de características en clase el 25/08/2026. Al
revisar qué familias teníamos cubiertas apareció que la hora era la única sin medir. La respuesta
resultó ser negativa, y por eso queda escrita: para que nadie la vuelva a proponer sin saber que
ya se midió.

**Evidencia:** `docs/evidencias/estacionalidad-intradia.json` · **Reproducible:** `uv run python -m scripts.estacionalidad_intradia`

## D18 · El bloque de prueba se toca una sola vez, con el protocolo escrito de antemano

**Estado:** vigente desde el 30/08/2026 · el procedimiento completo está en [`docs/09-protocolo-bloque-prueba.md`](09-protocolo-bloque-prueba.md)

El proyecto tiene diecisiete decisiones y ninguna hablaba del bloque de prueba. La práctica era
correcta —las **40 evaluaciones** de `resultados.csv` son todas sobre validación, la reserva está
intacta— pero dependía de que nadie se olvidara.

**La asimetría que hace esto urgente:** después de ver el número, cualquier criterio que elijamos
ya está contaminado por conocerlo. No por mala fe, sino porque es imposible desconocerlo. Un
protocolo escrito después no es un protocolo.

### Lo que queda fijado

**Qué se evalúa:** una configuración por familia —clásico, fundacional y avanzado—, elegida sobre
validación y **nombrada antes** de correr nada. Sin variantes, sin «probamos las dos a ver».

**Las tres ya están nombradas**, con fecha anterior a cualquier corrida sobre prueba: el clásico
`bosque_aleatorio_rezagos_relativos`, el fundacional `chronos_bolt` con `chronos-bolt-small`,
contexto 512 y cuantil 0,5, y el avanzado `itransformer` con lookback 96 y dimensión 64. Las dos
de M3 son las configuraciones por omisión, y en los dos casos **las eligió una medición que dijo
que ajustar no mejoraba**: en el fundacional porque la ganancia de la rejilla tiene un intervalo
que incluye el cero, y en el avanzado porque se disparó el criterio de la [D15](#d15). La tabla
con sus cifras de validación y sus razones está en la sección 3 del protocolo.

**La regla de decisión:** el proyecto declara que detecta puntos de inflexión si el mejor modelo
cumple **las tres** condiciones de la [D16](#d16) sobre prueba — supera al `baseline_aleatorio`,
el intervalo del 95 % de esa diferencia excluye el cero, y el signo no cambia entre las cinco
semillas. No se inventa un criterio nuevo para el resultado final.

**El umbral de la [D5](#d5) no aplica acá.** Se fijó para decidir entre modelos nuestros; contra
un baseline lo que importa es si la diferencia se distingue del azar.

**Lo que dice el informe en cada desenlace, redactado antes de saber cuál toca**, incluido el
peor: si la diferencia es negativa, se reporta que el modelo no supera al azar sobre datos nuevos
y **no se busca una configuración que sí lo haga**. En los tres casos se reporta la primera y
única cifra que salga.

### Lo que conocer el bloque no contamina

El tamaño (1 968 filas), el balance de clases y los tres baselines **ya están medidos** sobre
prueba, y eso no gasta la reserva: ninguno se elige ni se ajusta mirando el resultado. Lo que la
gasta es medir un modelo **nuestro** sobre ella.

Dato a tener presente: prueba está más desbalanceada que validación —91,22 % de Continuidad
contra 90,15 %—, así que una caída del F1 macro entre un conjunto y otro no es por sí sola señal
de sobreajuste.

### Por qué todavía no se corre

Con los dos modelos ya fijados por [D12](#d12) y [D14](#d14), y sin ajuste que los distinga, la
precondición está cumplida. Aun así **se espera**, por una razón medida: esta semana aparecieron
**nueve defectos silenciosos** en el proyecto, varios de ellos en el instrumento de medición. La
probabilidad de que algo cambie antes del informe final no es especulativa.

Gastar la reserva ahora y que después cambie una cifra deja dos opciones malas: reportar un número
viejo, o gastarla dos veces. **Se corre cuando el código esté congelado**, y esa congelación es
una decisión del equipo que se registra acá cuando se tome.

**Origen:** lo planteó Alejandro (M2) el 30/08/2026 al notar que el hueco existía, con el
protocolo escrito y la verificación de que la reserva seguía intacta. Pidió explícitamente que
fuera una fila y no un documento suyo, citando la regla 3.

### Cuándo se congela el código, con fecha

Decir «se corre cuando el código esté congelado» sin fecha es no decidir. La congelación va al
calendario:

| | |
|---|---|
| **Viernes 4 de septiembre** | Congelación. Nadie fusiona nada que pueda mover una cifra |
| **Sábado 5 de septiembre** | Se corre la medición sobre el bloque de prueba, una sola vez |
| **Domingo 6 y lunes 7** | Se redacta el informe con esa cifra |
| **Martes 8 de septiembre** | Entrega final |

**Qué se puede tocar después de congelar:** redacción, figuras que no citen cifras nuevas,
correcciones de enlaces y de nombres. Lo que la [D13](#d13) ya permite sobre una entrega hecha.

**Qué no:** nada en `contracts/`, `src/` ni `docs/evidencias/`. Si aparece un defecto que mueve
una cifra después del viernes, **se descongela explícitamente**, se arregla, y la medición se
repite declarando el motivo en el pestillo. No se parchea en silencio.

**Las tres precondiciones**, y por eso la fecha no es antes:

1. El panel público publica lo que la D18 declara ([#92](https://github.com/NeoFao/caso1-ltc-inflexion/issues/92), fase 1).
2. Las pruebas de extremo a extremo corren ([#90](https://github.com/NeoFao/caso1-ltc-inflexion/issues/90)).
3. La consulta sobre tiempo real está respondida, o se declara sin responder y se elige una lectura.

**Por qué no antes, medido:** en dos semanas aparecieron diez defectos silenciosos, tres de ellos
en el propio instrumento de medición. Congelar el jueves y descubrir el once el viernes deja dos
opciones malas: reportar un número viejo, o gastar la reserva dos veces.

**Y por qué no después:** el informe necesita dos días de redacción con la cifra ya en la mano.
Medir el lunes es escribir la conclusión con el número recién salido, que es exactamente cuando se
cometen los errores que este protocolo existe para evitar.

### Toda cifra del protocolo es la media de cinco semillas, incluidas las de validación

M2 encontró que la celda del clásico citaba **0,3905**, que es la corrida de la semilla 0 y
resulta ser **la más alta de las cinco** — la media es 0,380975 y el rango 0,016823.

Como el protocolo manda comparar validación contra prueba, partir del máximo exagera la caída, sin
que nada falle y en la dirección que nos hace parecer más apoyados en validación de lo que
estuvimos. **Después ya no se corrige sin que parezca que se corrigió porque no gustó.**

De los cuatro modelos, el único cuya semilla por omisión coincide con el máximo de las cinco es
justo el que había entrado al protocolo. Es casualidad, y por eso hacía falta mirarlo.

### Los baselines sobre prueba se miden con cinco semillas, y eso tampoco gasta la reserva

La tabla de baselines cita `baseline_aleatorio` en 0,3435, que es **una corrida**. Ese baseline se
mueve: sobre validación su rango entre semillas es **0,017370**, del mismo orden que la ventaja
que hay que distinguir.

**Y es el piso contra el que esta decisión mide las tres condiciones.** Un piso ruidoso hace
ruidosa la comparación entera.

**Se autoriza medirlos con cinco semillas sobre prueba.** El argumento de la sección 2 se sostiene
igual con cinco que con una: lo que gasta la reserva es **elegir o ajustar un modelo nuestro**
mirándola, y un baseline no se elige ni se ajusta — se calcula. Repetirlo con otra semilla no
añade ninguna decisión que dependa del resultado.

**Evidencia:** `docs/evidencias/resultados.csv` — 40 evaluaciones, todas sobre validación.

## D19 · «Modelo de referencia» designa al bosque; el de la ablación es el «modelo lineal de contraste»

**Estado:** vigente desde el 31/08/2026 · el renombrado en `src/features/` queda pendiente de M2

El término está repartido, y no es una cuestión de prolijidad. Con las mismas palabras, dos
documentos del proyecto se contradicen:

| Dónde | Qué dice | Qué mide |
|---|---|---|
| `m0-conclusion.md`, **entregado** | «el modelo de referencia supera al azar» | el bosque, +0,0537 |
| `docs/06`, de M2 | «el modelo de referencia no le gana al azar» | la logística, 0,2550 |

**Las dos son ciertas sobre lo que midieron.** Con el mismo término se contradicen.

**El término está definido**, y del lado entregado: `m0-procedimiento.md` dice explícitamente que
*baseline* designa a los tres triviales y **modelo de referencia** designa al bosque. Eso lo fija.

**El que cede es el lado de M2.** No por jerarquía: porque la definición está en un documento ya
entregado y la [D13](#d13) lo protege, mientras que el módulo de características se puede
renombrar sin tocar ninguna cifra.

**El nombre nuevo es «modelo lineal de contraste».** Dice las tres cosas que hacen falta: que es
lineal, que existe para contrastar familias en igualdad de condiciones, y que **no** es el modelo
del proyecto. Lo propuso M2 y es mejor que las alternativas que consideré —«comparador» no dice
que sea lineal, «regresión de referencia» conserva la palabra que causa el choque.

**Lo que el renombrado no puede hacer:** cambiar una sola cifra. Regenerar `m2-ablacion.json`
tiene que dar los mismos valores con otras claves, y eso se comprueba comparando hoja por hoja,
como en el [#74](https://github.com/NeoFao/caso1-ltc-inflexion/pull/74).

**Origen:** M2 fue a hacer el renombrado que debía, encontró que el término estaba repartido y con
definiciones opuestas, y **no eligió el reemplazo por su cuenta** — pidió que lo decidiera quien
había fijado el vocabulario. Es la regla 3 aplicada a algo que no es un número.

## D20 · No hay relación inversa entre los seis activos, y eso explica el resultado de S4-M2-01

**Estado:** vigente desde el 01/09/2026 · responde una observación del profesor en clase

El profesor señaló que al usar variables exógenas lo que hay que buscar es que sean
**proporcionales o inversamente proporcionales** a la objetivo. Una que se mueve igual aporta
poco; una que se mueve al revés aporta información que la objetivo no tiene.

**Medido: entre los seis activos no hay ninguna relación inversa.** Los quince pares van de
**+0,5175 a +0,8300**, y con LTC en particular de +0,5831 (SOL) a +0,7528 (ETH).

### Esto explica un resultado que teníamos medido y no entendido

S4-M2-01 encontró que los cinco activos de apoyo **no aportan de forma distinguible**: +0,00078,
con el signo cambiando entre semillas. Hasta ahora eso era un hecho sin mecanismo.

**El mecanismo es la proporcionalidad.** Los cinco se mueven fuertemente con LTC, así que casi
todo lo que traen ya está en LTC. No es que sean malas variables: es que son **redundantes** con
la objetivo, y la redundancia no informa.

### Se intentó construir una decorrelacionada con los mismos datos

Antes de concluir que hace falta traer un activo de fuera, se probó construirla. Criterio fijado
antes de mirar: se considera decorrelacionada si `|correlación| < 0,3`.

| Variable construida | Correlación con LTC | ¿Decorrelaciona? |
|---|---|---|
| Fuerza relativa LTC/BTC | +0,7530 | no |
| Fuerza relativa LTC/ETH | +0,5148 | no |
| **Fuerza relativa LTC/SOL** | **+0,1903** | **sí** |
| Fuerza relativa LTC/XRP | +0,3269 | no |
| **Fuerza relativa LTC/ADA** | **+0,2763** | **sí** |
| Exceso sobre la media del resto | +0,5074 | no |

**Dos sí.** Los cocientes contra los activos menos correlacionados traen información que los
retornos de LTC no tienen.

### Y aun así no se incorporan, porque se midió si servían

**Decorrelacionar no es informar.** Una variable puede traer información distinta y que esa
información no sirva para esta etiqueta, así que se probó sobre el modelo con cinco semillas:

**Diferencia media: −0,004065, y el signo cambia entre semillas.** Por las tres condiciones de la
[D16](#d16) no se puede afirmar que aporte, y la media apunta a que empeora.

**No se incorporan.** Se deja medido y escrito, que es distinto de no haberlo pensado.

### Lo que esta decisión NO dice

Que no exista una variable inversamente proporcional útil. Dice que **no la hay entre los seis que
fija el enunciado**, y que no se puede construir con ellos. Una candidata real —índice del dólar,
oro, volatilidad implícita— saldría de fuera de la lista, y eso es una pregunta para el profesor
antes que una decisión nuestra.

**Evidencia:** `docs/evidencias/relacion-exogenas.json` · **Reproducible:** `uv run python -m scripts.relacion_exogenas`

## D21 · Qué muestra la vista en tiempo real, decidido por el equipo

**Estado:** vigente desde el 01/09/2026 · desbloquea [#26](https://github.com/NeoFao/caso1-ltc-inflexion/issues/26) y [#28](https://github.com/NeoFao/caso1-ltc-inflexion/issues/28)

La consulta al profesor no se va a enviar. La decisión la toma el equipo con lo que él dijo en
clase, y queda escrita para que sea defendible.

### El punto de partida, que no es lo que parecía

**El modelo ya predice de verdad.** Estando parado en `t`, y con información disponible solo hasta
`t`, anuncia qué será el instante `t + h`. Lo garantiza `verificar_sin_fuga()`, que perturba todo
el futuro y exige que las características del pasado no cambien; y hay una prueba de que esa
comprobación detecta una fuga deliberada.

Lo que no se puede adelantar es la **verificación**: confirmar si el anuncio de `t` fue correcto
exige las `w` velas posteriores a `t + h`, o sea `h + w` = **8 velas, 32 horas**.

Así que nunca hubo dos sistemas posibles. Había un sistema y dos formas de mostrarlo.

### Lo decidido

**La vista muestra el anuncio en el momento, y la confirmación cuando llega.** Las dos cosas, no
una.

- Al llegar la vela `t`, el sistema anuncia su predicción para `t + h` y la marca como **pendiente
  de confirmar**.
- Cuando pasan las 32 horas y la etiqueta real existe, esa misma predicción cambia a **acertada**
  o **fallada**.

**Por qué así.** El profesor pidió que el modelo funcione **en generalidad** y no solo sobre datos
que ya se le metieron. Una vista que solo mostrara lo ya verificable escondería precisamente la
parte que responde a eso: que el sistema se compromete antes de saber. Y una que solo mostrara
anuncios sin confirmar no permitiría juzgar si acierta.

**Lo que esto obliga a mostrar, y es deliberado.** Las predicciones más recientes —las últimas 8
velas— aparecen siempre sin confirmar. Eso no es un defecto de la vista: **es la latencia real del
problema**, y ocultarla sería el tipo de presentación que hace parecer mejor un sistema de lo que
es.

**Evidencia de que la predicción es genuina:** `tests/test_fuga.py`, y la propia
`verificar_sin_fuga()` en `src/evaluacion/fuga.py`.

## D22 · Se entrega el martes 8 un informe único que cubre las semanas 3, 4 y 5

**Estado:** la fecha sigue vigente · **la parte de «un informe único en vez de tres» la reemplaza la [D26](#d26)**, después de que el profesor contestara la suposición que esta decisión declaró · vigente desde el 01/09/2026

El calendario nunca se confirmó. El enunciado tiene cinco entregas semanales desde el 18 de
agosto, lo que llevaría la última al 15 de septiembre; nuestra propia planificación anotó el 8.
La duda estaba en la consulta y la consulta no se envía.

**Se decide entregar el martes 8 de septiembre.** Si la fecha real fuera el 15, entregar antes no
perjudica; al revés no hay remedio.

**Y se entrega un informe único**, no tres documentos semanales. Dos razones:

1. **El enunciado pide un informe técnico**, en singular, entre los dos entregables del proyecto.
   Las entregas semanales son avances de ese informe, no productos separados.
2. Si las tres semanas se entregan el mismo día, **tres documentos que se solapan es peor que uno
   completo**: obliga al lector a reconstruir qué versión de cada cifra vale.

El informe cubre lo que piden las tres semanas: el modelo fundacional, el avanzado, las pruebas de
detección y el reporte final. Su estructura está en `docs/entregas/informe-final/README.md`.

**Lo que esta decisión asume, y hay que decirlo en el informe:** que agrupar es aceptable. Si el
profesor esperaba tres documentos, lo que recibe los contiene a los tres, y eso se declara en la
introducción en vez de esperar que no se note.

## D23 · Se descongela para tres cambios que no mueven ninguna cifra publicada, y la corrida final se atrasa al lunes 7

**Estado:** vigente desde el 06/09/2026 · aplica el procedimiento que la [D18](#d18) dejó escrito

La D18 congeló el código el viernes 4 y prohibió tocar `contracts/`, `src/` y `docs/evidencias/`.
También previó este caso: **si hace falta cambiar algo después, se descongela explícitamente y se
declara el motivo, no se parchea en silencio.** Esto es eso.

### Qué se descongela, y por qué cada uno

| Cambio | Qué toca | Por qué entra |
|---|---|---|
| [#97](https://github.com/NeoFao/caso1-ltc-inflexion/pull/97) | `docs/evidencias/`, `src/features/` | Fase 2 del [#92](https://github.com/NeoFao/caso1-ltc-inflexion/issues/92): las seis métricas por semilla del bosque. **Añade claves, no cambia valores** |
| [#98](https://github.com/NeoFao/caso1-ltc-inflexion/pull/98) | `docs/evidencias/`, `src/modelos/`, `docs/09` | Lo mismo para el avanzado, con la semilla declarada. El [#103](https://github.com/NeoFao/caso1-ltc-inflexion/pull/103) está apilado encima |
| [#105](https://github.com/NeoFao/caso1-ltc-inflexion/pull/105) | `src/evaluacion/` | **Sin esto la corrida final no se puede hacer**: el pestillo moría en el segundo modelo con la reserva gastada ([#100](https://github.com/NeoFao/caso1-ltc-inflexion/issues/100)) |

**El [#96](https://github.com/NeoFao/caso1-ltc-inflexion/pull/96) no necesita descongelación**, y se
deja dicho para que no se cite mal: toca solo `app/`, que la congelación nunca cubrió. Lo mismo el
[#104](https://github.com/NeoFao/caso1-ltc-inflexion/pull/104), que es una sección del informe.

### El criterio, que es lo que hay que poder defender

La congelación existe para que **no se mueva un número que el informe ya cita**. No existe para
impedir que se añada detalle que faltaba, ni para impedir arreglar el instrumento con el que
todavía no se ha medido.

Los tres cumplen: **ninguno cambia una cifra publicada.** El #97 y el #98 añaden claves a archivos
de evidencia sin tocar los valores existentes; el #105 arregla el pestillo, que nunca produjo una
cifra porque nunca llegó a correr sobre la reserva.

### Lo que esta decisión NO autoriza

Cualquier otro cambio en `contracts/`, `src/` o `docs/evidencias/`. La descongelación es **para
estos tres y se vuelve a cerrar al fusionarlos.** Si aparece un cuarto, se añade acá antes de
tocarlo, no después.

### Por qué la corrida del bloque de prueba no se hizo el sábado 5

Queda registrado porque el calendario de la D18 lo fijaba y no se cumplió, y una fecha incumplida
sin explicación se lee después como descuido.

Al preparar la corrida aparecieron **tres defectos que la habrían roto a mitad de camino**, dos de
ellos gastando la reserva antes de morir:

1. **El pestillo contaba modelos en vez de corridas.** Moría en el modelo 2 de 6 con el archivo ya
   escrito, y a partir de ahí cualquier arreglo obligaba a declarar un motivo: el registro habría
   dicho para siempre que la reserva se tocó dos veces. Lo reportó M3 el 02/09 en el #100.
2. **El #101 introducía un `KeyError`** justo antes de escribir `m3-modelos-profundos-…-prueba.json`,
   con los seis modelos ya evaluados y la reserva ya gastada. Se perdían los intervalos pareados y
   el veredicto, que son las cifras con las que la sección 5 del protocolo aplica las tres
   condiciones de la [D16](#d16).
3. **`--sin-variantes` no es obligatorio sobre `prueba`**, así que el cumplimiento de la sección 3
   del protocolo dependía de que quien corriera se acordara de escribirla.

**Correrla el sábado habría gastado la reserva sin obtener el número.** El atraso cuesta un día de
redacción; la alternativa costaba la reserva, que es lo único del proyecto que no se puede reponer.

**La fecha nueva es el lunes 7 de septiembre**, y es firme salvo que el defecto 2 siga abierto. Va
después de un **ensayo en seco sobre validación con las banderas exactas**, que es obligatorio: los
tres defectos se habrían caído ahí.

El resto del calendario de la D18 no cambia: se entrega el martes 8. La redacción se comprime a un
día, y eso es el costo aceptado.

### Lo que se aprende, y vale más que los tres arreglos

Los tres defectos estaban **en el camino que solo recorre la corrida final**, y ninguno se veía en
las pruebas unitarias, que pasaban. El pestillo se había visto fallar en su propia prueba, pero
nunca en el camino por el que iba a pasar el sábado.

**Un control probado en aislamiento no es un control probado.** Se añade a las reglas del proyecto:
todo camino que solo se recorre una vez se ensaya entero antes, sobre datos que sí se puedan gastar.

**Origen:** M2 avisó el 06/09 de que la medición no se había corrido, con tres comprobaciones
independientes de que la reserva seguía intacta, y pidió que se decidiera ese mismo día en vez del
lunes. Es la misma forma que el #100: traer el problema antes de que sea urgente.

---

## D24 · Qué criterio responde «¿aporta?» y cuál responde «¿lo elegimos?», y la corrección a la D14

**Estado:** **veredicto retirado por la [D25](#d25)** el 07/09/2026 · la corrección de criterio
que trae **sigue vigente** · corrige la lectura de la [D14](#d14), que **no se reescribe** · pedida
por M0 al detectar el choque con la sección de M3 del informe

> **Leer con la D25 al lado.** Lo que esta decisión corrigió del criterio —que el umbral de la D5
> respondía una pregunta de decisión y no de distinguibilidad— sigue en pie. Lo que **no** se
> sostiene es su veredicto: la condición 2 no se reproduce cuando entra el iTransformer, y la fila
> «las tres se cumplen» de más abajo quedó retirada. Se deja escrita porque el documento acumula el
> historial y no lo reescribe.

### El choque

La D14 concluye, sobre los activos de apoyo en el modelo avanzado, que **«no se puede afirmar que
aporten»**. La sección de M3 del informe final concluye que **sí aportan**. Las dos citan la misma
evidencia.

**No discrepan en los números. Discrepan en qué regla aplicaron** — y la que apliqué en la D14 no
era la que correspondía.

### Las dos preguntas no son la misma

| Pregunta | Qué la responde | Por qué |
|---|---|---|
| ¿El aporte se distingue del azar? | Las tres condiciones de la [D16](#d16) | Es una pregunta de distinguibilidad |
| ¿Alcanza para preferir una configuración? | El umbral de 0,02 de la [D5](#d5) | Es una convención de decisión del equipo |

Esto ya estaba escrito y no lo vi: la **sección 5 del protocolo** dice textualmente que *«el umbral
de 0,02 (D5) no se aplica aquí. Ese umbral se fijó para decidir entre modelos nuestros; contra un
baseline, lo que importa es si la diferencia se distingue del azar»*.

La D14 usó el umbral de la D5 para responder una pregunta de distinguibilidad.

### Lo que dice el criterio que corresponde

Las tres condiciones de la D16, sobre el modelo avanzado:

1. **La diferencia es positiva** — media **+0,012586**, la misma que la D14 midió y reportó.
2. **El intervalo pareado excluye el cero** — [0,000434 , 0,044067], en
   `m3-modelos-profundos-4h-w7-h1.json`. Ese intervalo **ya estaba en la evidencia que la D14
   cita**, y la D14 no lo usó.
3. **El signo no cambia** — positivo en las cinco semillas, de +0,002070 a +0,025328.

**Las tres salen de la evidencia que la D14 ya tenía delante.** No hace falta ninguna medición
nueva para corregir la lectura, y por eso esta decisión no depende de ningún barrido posterior.

**Las tres se cumplen: el aporte es distinguible.** — **RETIRADO por la [D25](#d25):** la condición 2 no se reproduce.

### El argumento de la D14 que no se sostiene, y por qué

La D14 dice que el aporte es *«del mismo orden que el ruido de corrida a corrida»*. Ese ruido se
midió: **0,004833** entre dos procesos con la misma semilla. El aporte medio es más del doble.

Pero lo que de verdad los separa no es la magnitud: **el ruido de punto flotante no tiene signo** y
el aporte fue positivo en **las cinco** semillas. Si no hubiera efecto, que las cinco cayeran del
mismo lado tiene probabilidad **1 en 16**. Por eso la tercera condición de la D16 es la del signo, y
por eso mirar solo la magnitud contra un umbral se pierde justo la parte que discrimina.

### Lo que la D14 acertó y sigue vigente

- **La magnitud es pequeña**, por debajo del umbral que el equipo fijó para preferir una
  configuración sobre otra. La [D20](#d20) explica por qué: los seis activos son fuertemente
  proporcionales y **no hay ninguna relación inversa**, así que traen poco que LTC no tenga.
- **El avanzado con los cinco apoyos sigue por debajo del bosque sin ellos.** Aportar no es
  rescatar.
- Todo lo demás de la D14 —la elección de iTransformer, Informer fuera por no instalable, la
  dispersión entre semillas, el presupuesto— no lo toca esta decisión.

### Lo que se corrige, exactamente

Donde la D14 dice *«las dos mediciones coinciden en lo que importa: no se puede afirmar que
aporten»*, **no coinciden**: sobre el bosque el intervalo del #62 incluye el cero, y sobre el
avanzado lo excluye. Presentarlo como confirmación independiente fue afirmar de más.

**La frase correcta, y la que va al informe:**

> El aporte de los activos de apoyo es **distinguible del azar en el modelo avanzado y demasiado
> pequeño para cambiar ninguna decisión**. Sobre el bosque no se distingue. No es el mismo
> resultado en las dos familias, y la limitación se declara por familia y no en general.

### Consecuencia para el informe

La **limitación 1** del esqueleto no se declara en general. Se declara para el bosque —que es donde
se midió el 0,00078— y el resultado del avanzado se reporta aparte con su matiz.

**Evidencia:** `docs/evidencias/m3-sensibilidad-avanzado-4h-w7-h1.json` --donde vive el
+0,012586-- y `docs/evidencias/m3-modelos-profundos-4h-w7-h1.json`. El puntero decia
`-completa-`, que es otro archivo; corregido en la [D25](#d25).

**Origen:** M0 detectó que la D14 y la sección de M3 del informe se contradecían y **no eligió cuál
valía**: pidió la lectura a quien había escrito las dos. La regla 3, aplicada a una conclusión en
vez de a un número.

---

## D25 · La condición 2 de la D16 exige predicciones reproducibles, y el iTransformer no lo es

**Estado:** propuesta desde el 07/09/2026 · **retira el veredicto de la [D24](#d24)** y conserva su
corrección de criterio · se decide **antes** de tocar el bloque de prueba, que es el punto

### Lo que encontró el ensayo en seco

La D24 concluyó que las tres condiciones de la [D16](#d16) se cumplen sobre el aporte de los activos
de apoyo. El ensayo en seco de M0 volvió a medir validación y **la segunda no se reproduce**:

| Condición | Corrida comprometida | Ensayo en seco |
|---|---|---|
| 1 · La diferencia es positiva | +0,012586 | positiva otra vez |
| 2 · El intervalo excluye el cero | [0,000434 , 0,044067] · **sí** | [−0,001736 , 0,045490] · **no** |
| 3 · El signo no cambia en las cinco | positivo en las cinco | positivo en las cinco |

El límite de la corrida comprometida vivía a menos de una milésima del cero. **La frase «las tres se
cumplen» no se sostiene, y era mía.**

### Por qué pasa, y por qué no es mala suerte

`intervalo_diferencia` siembra su generador: el intervalo es determinista **dadas las predicciones**.
Lo que se mueve son las predicciones del iTransformer, que no es reproducible entre procesos por lo
que documenta la [D15](#d15).

Y ahí está el fondo del asunto: **la condición 2 y la condición 3 miden incertidumbres distintas.**
El remuestreo pareado resamplea las **filas** y condiciona en un solo sorteo del entrenamiento; la
condición 3 mira **cinco sorteos** del entrenamiento. Cuando el sorteo del entrenamiento es la
fuente dominante, un intervalo de una corrida no es un instrumento frágil: **es el instrumento
equivocado**, porque su supuesto —predicciones fijas— no se cumple.

Se ve en las medias: el bosque queda en 0,380975 y el iTransformer en 0,345357, y la desventaja
cae **del mismo lado en las cinco semillas**, mientras el intervalo pareado de una corrida cruza el
cero.

### Se midió si el iTransformer se puede hacer reproducible. No con lo que hay

La opción de fijar el entrenamiento se probó antes de descartarla, con tres palancas, y la pérdida
final siguió cambiando entre procesos con las tres:

| Palanca | ¿Reproduce entre procesos? |
|---|---|
| `torch.set_num_threads(1)` + `use_deterministic_algorithms(True)` | no |
| `PYTHONHASHSEED` fijo | no |
| Semilla fija (lo que ya se hacía) | no |

La D15 se sostiene: es el orden de reducción en punto flotante, y no se elimina con esas palancas.

### La regla principal del protocolo NO está afectada, y conviene decirlo

La sección 5 del protocolo aplica las tres condiciones al **mejor modelo contra el
`baseline_aleatorio`**. Los dos reproducen bit a bit entre procesos — medido sobre las 1 959 filas
de validación, con el mismo SHA-256 de las predicciones en dos procesos distintos. El fundacional es
*zero-shot* y tampoco muestrea.

**El problema está acotado a los contrastes en los que entra el iTransformer.**

### Lo que se decide

1. **Donde entre un modelo no reproducible, la condición 2 se reporta pero no decide.** El peso lo
   lleva la condición 3, que sí se reproduce. La condición 2 se publica con las dos mediciones a la
   vista, no con una sola.
2. **Para todo lo demás la condición 2 queda intacta**, incluida la regla de la sección 5.
3. **Se retira el veredicto de la D24**: no se puede afirmar que los activos de apoyo aporten de
   forma distinguible. **Lo que la D24 corrigió del criterio sigue en pie** — el umbral de la D5
   respondía una pregunta de decisión y no de distinguibilidad, y eso no lo toca este hallazgo.
4. La conclusión vuelve a coincidir con la de la [D14](#d14), **por una razón distinta de la que la
   D14 dio**. Que el resultado sea el mismo no vuelve correcto el argumento de entonces.

### Lo que sí se sostiene, y va al informe

> Los activos de apoyo dan una diferencia **positiva en las cinco semillas de dos barridos
> independientes**, y **no se puede afirmar que sea distinguible del azar** por el estándar que el
> equipo fijó. El iTransformer queda **por debajo del bosque en las cinco semillas** —0,345357 de
> media contra 0,380975— y esa desventaja tampoco se afirma por intervalo.

### La forma mejor, que no se adopta hoy

Lo correcto a futuro es aplicar la condición 2 **dentro de cada semilla** y leer en cuántas de las
cinco excluye el cero: eso respeta el supuesto del remuestreo en vez de violarlo, y cuesta poco
porque las cinco semillas ya se corren. **No se adopta antes de la corrida final**: obligaría a
cambiar el guion otra vez y a repetir el ensayo en seco, y a dos días de la entrega el riesgo es
peor que el beneficio. Queda anotado para el informe como lo que haríamos distinto.

### Corrección de una cita

La D24 pone como evidencia `m3-sensibilidad-avanzado-completa-4h-w7-h1.json`, pero el +0,012586 vive
en `m3-sensibilidad-avanzado-4h-w7-h1.json`, sin *completa*. La cifra estaba bien medida y bien
descrita; el nombre del archivo bailó. Se corrige el puntero, que no es una conclusión sino una
referencia rota.

**Evidencia:** `docs/evidencias/m0-ensayo-en-seco-validacion-con-variantes-4h-w7-h1.json`,
`docs/evidencias/m3-sensibilidad-avanzado-4h-w7-h1.json` y
`docs/evidencias/m3-modelos-profundos-4h-w7-h1.json`

**Origen:** M0 encontró que la condición 2 no se reproducía y **no decidió por su cuenta qué hacer
con una decisión ajena**: trajo la medición y las opciones. La regla 3, otra vez, y esta vez sobre
una conclusión mía que había que retirar.

---

## D26 · Se entregan las dos formas: los avances por semana y el informe único

**Estado:** vigente desde el 07/09/2026 · **reemplaza la segunda mitad de la [D22](#d22)** · el
profesor respondió la suposición que la D22 había declarado

### Qué pasó

La D22 decidió entregar **un informe único** en vez de tres documentos semanales, y dejó escrita la
suposición sobre la que se apoyaba:

> **Lo que esta decisión asume, y hay que decirlo en el informe:** que agrupar es aceptable. Si el
> profesor esperaba tres documentos, lo que recibe los contiene a los tres.

**El profesor contestó esa suposición**, y dice lo contrario:

> Recordar hacer los avances por separado, esto con el fin de poder ver en detalle y profundizar en
> conceptos teóricos.

La suposición queda refutada. No hace falta discutirla: se declaró como suposición justamente para
poder retirarla sin rehacer el razonamiento.

### Lo que se decide

**Se entregan las dos cosas.** No es un compromiso: cada forma responde algo que la otra no.

| Forma | Qué aporta | Por qué no la reemplaza la otra |
|---|---|---|
| **Avances por semana** (3, 4 y 5) | Permite seguir un tema hasta el fondo sin la comparación entre modelos encima | Es lo que el profesor pide, y su razón es poder profundizar en los conceptos |
| **Informe único** | Una sola versión vigente de cada cifra, con las limitaciones declaradas juntas | El enunciado pide **un informe técnico**, en singular, entre los dos entregables |

El primer argumento de la D22 sigue en pie —el enunciado pide un informe técnico en singular— y por
eso el informe único no se retira. Lo que se retira es la parte que decía que los semanales **no** se
entregan.

### El riesgo que la D22 señalaba, y cómo se evita

La D22 avisaba de que «tres documentos que se solapan es peor que uno completo: obliga al lector a
reconstruir qué versión de cada cifra vale». **Ese riesgo es real y no desaparece por entregar las
dos formas.**

Se evita por construcción: los documentos semanales **no contienen texto propio de contenido
técnico**. Son ensamblados de los mismos archivos que el informe final, con la introducción y la
conclusión de cada semana como único material nuevo. Una cifra vive en un solo lugar; si cambia,
cambia en los dos documentos al regenerarlos.

Es lo mismo que ya hacía el ensamblador de las semanas 1 y 2, y por eso no hizo falta herramienta
nueva: `CARPETA_ENTREGA=semana-3 npm run ensamblar --prefix scripts`.

### Lo que había y lo que faltaba

Conviene dejarlo escrito porque el equipo creía que los semanales ya existían:

| Semana | Estado antes de esta decisión |
|---|---|
| 1 y 2 | **Existían**, con su `secciones.json` y su Word generado |
| **3, 4 y 5** | **No existían.** Solo estaba el informe único |

Los issues #41, #42 y #43 —ensamblar y entregar las semanas 3, 4 y 5— estaban abiertos y asignados a
M0 desde el principio. No era trabajo nuevo: era trabajo que la D22 había dado por innecesario.

### Sobre la fecha

La D22 fijó el **8 de septiembre** para todo, porque el calendario nunca se confirmó. Esta decisión
**no la cambia**, por el mismo argumento que la D22 dio: si la fecha real de la Semana 5 fuera el 15,
entregar antes no perjudica; al revés no hay remedio.

**Evidencia:** `docs/entregas/semana-3/`, `docs/entregas/semana-4/`, `docs/entregas/semana-5/`

**Origen:** el profesor, sobre los avances del caso. Es la primera vez que una suposición declarada
por escrito en este documento se retira porque llegó la respuesta que esperaba, y no por haber
cambiado de opinión.
