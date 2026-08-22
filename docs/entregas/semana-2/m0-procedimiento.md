# Procedimiento para desarrollar el modelo de puntos de inflexión

**Autor:** Fabrizio Espinoza Arce · **Issue:** [S2-M0-02](https://github.com/NeoFao/caso1-ltc-inflexion/issues/22)

> **Nota de verificación.** Los valores citados salen de
> `docs/evidencias/modelo-clasico-4h-w7-h1-rezagos-en-nivel.json` y `docs/evidencias/estudio-w-h.json`,
> y se comprueban con `scripts/verificar_numeros.py`. Salvo indicación expresa,
> todos corresponden a la configuración congelada: **velas de 4 horas, `w = 7`,
> `h = 1`**.

El enunciado plantea un procedimiento genérico de ocho etapas y pide adaptarlo al
proyecto. Esta sección lo recorre entera, y en cada etapa declara qué está
construido y medido, y qué queda pendiente. La diferencia entre las dos cosas se
señala en cada caso, porque un procedimiento descrito y un procedimiento ejecutado
no son lo mismo.

---

## 1. Extracción de datos

Los precios provienen de la interfaz pública de Binance, de las seis parejas contra
USDT. La descarga deja un manifiesto con la suma de verificación de cada archivo, de
modo que dos personas pueden comprobar que trabajan sobre el mismo panel sin
compararlo fila por fila.

**La decisión de granularidad se resolvió midiendo, y el criterio se fijó antes de
mirar el resultado:** elegir el `w` más grande que deje al menos **300 ejemplos** de
la clase minoritaria en entrenamiento.

| Granularidad | Mejor caso medido | ¿Cumple el piso? |
|---|---|---|
| Velas diarias | 149 ejemplos con `w = 3` | **No, en ninguna combinación** |
| Velas de 4 horas | 420 ejemplos con `w = 7` | Sí, hasta `w = 7` |

**Tabla 1.** Disponibilidad de la clase minoritaria por granularidad. Fuente:
[`estudio-w-h.json`](../../evidencias/estudio-w-h.json).

Las dos granularidades cubren exactamente el mismo período, del 11 de agosto de 2020
al presente, porque la ventana la acota Solana y un panel multivariante exige que
las seis series existan a la vez. Bajar la granularidad no añade historia:
**subdivide la que hay**, de 2 185 observaciones a **13 114**.

El costo aceptado es que las velas de 4 horas incorporan más ruido de microestructura
y son menos legibles en una figura.

---

## 2. Limpieza de datos

La cobertura del panel de 4 horas está medida y es prácticamente completa: sobre los
13 114 instantes esperados para Solana no hay ningún hueco, y los de los demás
activos en su historia completa van de 9 a 16 velas, menos del 0,1 %.

**La política es no imputar en el panel.** Un hueco en el precio es información —el
mercado no cotizó, o el exchange no publicó— y rellenarlo inventa una observación que
después alimenta una etiqueta. Los nulos que sí aparecen son los que introducen las
ventanas móviles al principio de la serie, **30 filas**, y se tratan dentro del
modelo y no antes de particionar, por la razón que se explica en la etapa 5.

El panel se valida contra un esquema explícito antes de cualquier uso: columnas
exactas, tipos e índice temporal. Un panel que no cumple el esquema falla al cargarse
en lugar de propagar el defecto.

---

## 3. Análisis exploratorio

Es lo que constituyó la entrega de la Semana 1, y sus resultados condicionan todas
las etapas siguientes. Los tres que más pesan:

**Los precios no son estacionarios y los retornos sí.** Ninguna de las seis series
rechaza la raíz unitaria sobre precios; las seis la rechazan sobre retornos. De ahí
que las características se construyan sobre retornos.

**Los retornos no tienen autocorrelación lineal aprovechable.** De cuarenta rezagos,
tres superan la banda de confianza. Es el argumento medido a favor de modelos no
lineales y multivariantes.

**La volatilidad conmuta entre regímenes**, con un cociente de 8,8 entre extremos.
Descarta los métodos que asumen varianza constante.

> Esos números se midieron sobre velas diarias con `w = 5`, que era la configuración
> vigente en aquella entrega, y así quedan declarados. No se regeneraron al congelar
> el contrato porque ninguno depende de la etiqueta: se calculan sobre precios y
> retornos.

---

## 4. Ingeniería de características

El conjunto actual tiene **63 columnas**, de las cuales **24 son precios rezagados en
nivel**. Cubre cinco familias: retornos y rezagos de los seis activos, indicadores
técnicos, estadísticos de ventana deslizante, medidas de volatilidad y medidas de
correlación entre activos.

**Las que más pesan, medidas por permutación sobre el conjunto de validación:**

| Característica | Caída del F1 macro al permutarla |
|---|---|
| `LTC_posicion_rango_7` | 0,0422 |
| `LTC_dist_sma_7` | 0,0343 |
| `ADA_cierre_rezago_rel_5` | 0,0258 |
| `LTC_cierre_rezago_rel_5` | 0,0255 |
| `LTC_cierre_rezago_rel_6` | 0,0224 |

**Tabla 2.** Las cinco características de mayor importancia por permutación, con el
modelo de referencia sobre validación. Fuente:
[`m2-importancia-4h-w7-h1.json`](../../evidencias/m2-importancia-4h-w7-h1.json).

**La medida es por permutación y no la que trae el bosque, y la diferencia importa.**
La importancia por impureza que devuelve `scikit-learn` se calcula sobre entrenamiento
y favorece a las variables de alta cardinalidad, de modo que describe de qué se colgó
el modelo para ajustar lo que ya vio. Permutar una columna sobre validación y medir
cuánto cae el F1 macro responde otra pregunta: si el modelo la necesita para predecir
lo que no vio. Las dos ordenaciones coinciden en lo grueso —correlación de rangos de
0,61— y se separan en el detalle, que es lo esperable si esos sesgos son reales.

**Y la tabla sola no significaría nada sin su control.** Cualquier lista ordenada por
importancia se puede leer, aunque las 63 columnas fueran ruido: alguna quedaría
primera. Por eso se entrena un segundo modelo con cinco columnas de ruido puro
añadidas, y la mayor importancia que alcanza una de ellas fija el piso: **0,0065**.
Toda característica por debajo de ese valor es indistinguible de una columna
inventada. **Diecisiete de las sesenta y tres lo están.**

Que encabecen medidas de **posición relativa dentro de una ventana** es coherente con
el hallazgo de la Semana 1: lo que informa es dónde está el precio respecto de su
vecindad reciente, no cuánto vale.

**Una cautela que la propia medición obliga a declarar:** que una columna no supere el
piso no prueba que sea inútil, sino que esta medición no la distingue del ruido. Con
columnas correlacionadas entre sí, permutar reparte el crédito entre ellas y
subestima a las dos.

**Toda característica se verifica contra fuga de información** antes de entrar: se
perturba el futuro de la serie y se comprueba que los valores del pasado no cambian.
Es obligatorio porque la fuga no se manifiesta como un error, sino como métricas
excelentes.

---

## 5. Partición temporal

No se usa validación cruzada aleatoria. Sobre una serie temporal, mezclar filas
permite que el modelo se entrene con información posterior a la que predice.

La partición es **cronológica y con embargo**:

| Bloque | Observaciones |
|---|---|
| Entrenamiento | 9 171 |
| Validación | 1 959 |
| Prueba | 1 968 |
| **Embargo, descartado** | **16** |

**Tabla 3.** Partición temporal del panel de 4 horas. Fuente:
[`modelo-clasico-4h-w7-h1-rezagos-en-nivel.json`](../../evidencias/modelo-clasico-4h-w7-h1-rezagos-en-nivel.json).

**El embargo son `w + h` velas descartadas en cada frontera.** Sin él, las últimas
observaciones de entrenamiento y las primeras de validación comparten las velas que
se usaron para construir sus etiquetas, y los dos bloques dejan de ser
independientes. Son 16 observaciones de 13 114: un costo despreciable frente al
riesgo que elimina.

De aquí sale también la razón por la que la imputación va **dentro** del modelo. Si
se imputara antes de particionar, la mediana se calcularía con datos de validación y
de prueba, que es fuga de información por la puerta de atrás.

El balance de clases en entrenamiento queda en **4,58 % de máximos, 4,70 % de mínimos
y 90,72 % de continuidad**, muy por debajo de la cota aritmética del 12,5 % que
impone `w = 7`.

---

## 6. Selección del modelo

Se aborda en dos pasos, como pide el enunciado, y con un piso obligatorio antes de
los dos.

**Primero el piso.** Tres *baselines* deliberadamente triviales —el que responde
siempre lo mismo, el que responde la clase mayoritaria y uno aleatorio— y un **modelo
de referencia**, un bosque aleatorio, que recorre el circuito completo. En todo este
documento *baseline* designa a los tres triviales y **modelo de referencia** designa
al bosque; no se usan como sinónimos. Sirven para descartar
explicaciones alternativas: si un modelo elaborado no supera al azar, no aprendió
nada.

**Después los dos que pide el enunciado:** un modelo fundacional disponible
públicamente, y un modelo más avanzado. La comparación entre ambos es la conclusión
central del proyecto, y por eso las dos se miden con la misma función de evaluación,
la misma partición y el mismo criterio.

**El criterio de decisión está fijado desde antes de medir:** un modelo solo se
declara mejor si supera al mejor de los baselines en F1 macro por al menos **0,02**.
Cualquier diferencia menor se reporta como no concluyente.

La justificación concreta de qué modelo fundacional se elige, con el inventario
medido de candidatos, está en [`m3-modelos.md`](m3-modelos.md).

---

## 7. Entrenamiento y optimización de hiperparámetros

**Están separados a propósito y en ese orden.**

El entrenamiento del modelo de referencia ya se ejecutó de punta a punta y es
reproducible con un comando. Sus hiperparámetros se fijaron **antes** de mirar ningún
resultado, y la razón de cada uno está escrita junto al valor, de modo que
"lo elegimos antes de medir" es auditable y no una afirmación nuestra.

**La búsqueda de hiperparámetros no se hace todavía.** Ajustarlos mirando validación
antes de que exista el modelo fundacional gastaría el único conjunto no visto que
queda para comparar los dos modelos. Es una tarea del Sprint 4, y hasta entonces
cualquier valor que se toque se declara como cambio.

Hay un cambio ya declarado: la ponderación de clases del modelo de referencia se
modificó **después** de ver que la opción prerregistrada colapsaba a la clase
mayoritaria. Queda escrito en la evidencia como corrección de variante, no como
búsqueda.

**El conjunto de prueba no se toca.** El guion de experimentos exige una bandera
explícita para evaluar sobre él, precisamente para que no ocurra por descuido.

---

## 8. Evaluación y despliegue

**Las métricas están fijadas y viven en una sola implementación compartida:** F1 por
clase, F1 macro, Precisión Direccional y matriz de confusión. La exactitud se reporta
únicamente para mostrar por qué no sirve. El desarrollo completo del argumento está
en la sección de métricas de la Semana 1.

**Lo que hay que reportar sobre la anticipación real.** La latencia efectiva del
sistema es `h + w`, no `h`: con `w = 7` y `h = 1` sobre velas de 4 horas son **8
velas, es decir 32 horas**. Para saber si la vela `t+h` fue un máximo hay que
observar las `w` posteriores. Reportar "predice una vela adelante" sin aclararlo
sería engañoso.

**Despliegue.** El backend expone las predicciones y la evidencia por una interfaz
pública, y la aplicación web las consume. Está construido y funciona en local; la
publicación para uso público es una tarea abierta.

---

## Lo que este procedimiento todavía no resuelve

Dos cuestiones abiertas, que se declaran aquí para que no aparezcan como sorpresa
más adelante. Una tercera, que figuraba en este mismo lugar, se resolvió mientras se
redactaba el documento y se deja anotada por lo que ilustra.

**Resuelta: cómo se pasa de un pronóstico de trayectoria a una etiqueta de tres
clases.** Un modelo fundacional pronostica el precio, no la clase. Se aplica el
etiquetador del contrato sobre la trayectoria pronosticada, en lugar de entrenar una
cabeza de clasificación sobre representaciones congeladas. Lo decidió una medición:
etiquetar la trayectoria cuesta unos doce segundos sobre el bloque de validación
entero, así que la vía más simple resultó ser también la más barata.

**Qué se entiende por prueba en tiempo real.** El enunciado la pide para las semanas
3 y 4. Como la etiqueta de un instante no se conoce hasta `w` velas después, caben
dos lecturas —confirmación tardía pero verificable, o anuncio en el momento— y son
dos productos distintos. Está en la consulta al profesor.

**Cuánta señal hay realmente.** La información mutua entre lo observable y la etiqueta
es baja para todo horizonte, incluido `h = 1`. Lo que sustenta la elección de `h` es
la forma de la curva y no su magnitud, y esa magnitud pequeña es en sí misma un aviso:
el problema es difícil con las características actuales.
