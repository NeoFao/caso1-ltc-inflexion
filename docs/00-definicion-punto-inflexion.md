# Definición operativa del punto de inflexión

**Qué hay que decidir, por qué importa, y qué le vamos a preguntar al profesor**

Documento de contexto para la decisión del equipo — Caso N°1, Semana 1
Fecha: 5 de agosto de 2026
Autor: Fabrizio Espinoza Arce (PM)
Estado: **abierto — pendiente de decisión del equipo y de respuesta del profesor**

---

## 1. Para qué es este documento

El enunciado nos pide construir un modelo que clasifique el precio de Litecoin en tres etiquetas: **Máximo**, **Mínimo** o **Zona de Continuidad**.

Lo que el enunciado **no** dice es *cómo se decide* cuál es cuál. Dice textualmente:

> Máximo local: punto en el que el precio de cierre de LTC en una ventana temporal `w` deja de aumentar y comienza a disminuir.

Nombra una ventana `w` pero nunca dice cuánto vale. Tampoco dice cuánto vale el horizonte `h` de predicción. Esos dos números los tenemos que elegir nosotros.

No son un detalle de configuración. **De ellos dependen las etiquetas de entrenamiento, y de las etiquetas depende absolutamente todo lo demás**: qué aprende el modelo, qué features tienen sentido, y qué significan las métricas del reporte final. Si los elegimos tarde o los elegimos distinto cada uno, tiramos trabajo.

Este documento existe para que los cuatro entendamos qué estamos decidiendo antes de decidirlo, y para dejar por escrito qué le consultamos al profesor.

---

## 2. Por qué "máximo" no es una pregunta obvia

Intuitivamente, un máximo es "donde el precio deja de subir y empieza a bajar". El problema es que un precio sube y baja **todo el tiempo**, a todas las escalas. Un máximo solo existe *en relación con un vecindario*: depende de cuánto mires a los lados.

Un ejemplo para verlo. **Esta serie me la inventé para ilustrar el punto — no son datos reales de LTC:**

| Día | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Cierre | 100 | 102 | **105** | 103 | 106 | **110** | 108 | 104 | **101** | 103 | 107 |

- Si solo miramos **un día a cada lado**, el día 3 es un máximo: 105 es mayor que 102 (día 2) y que 103 (día 4). También lo es el día 6.
- Si miramos **cinco días a cada lado**, el día 3 ya no es máximo: dentro de esa vecindad está el día 6 con 110, que es más alto. Solo sobrevive el día 6.

El día 3 no cambió. Lo que cambió es la lupa. Y las dos lecturas son correctas: el día 3 *es* un giro local pequeño, y *no es* un giro importante.

**Ese es el punto entero del documento.** No estamos buscando "la definición verdadera" de máximo, porque no existe. Estamos eligiendo a qué escala queremos que el modelo trabaje, y esa elección hay que justificarla.

---

## 3. Qué es `w` (la ventana)

`w` es **cuántas velas miramos a cada lado** para decidir si una vela es un giro.

> Una vela `t` es **Máximo** si su cierre es mayor que el cierre de todas las velas entre `t-w` y `t+w`.
> Es **Mínimo** si su cierre es menor que todas ellas.
> En cualquier otro caso es **Zona de Continuidad**.

Qué implica elegir uno u otro:

| | `w` chico (ej. 2) | `w` grande (ej. 10) |
|---|---|---|
| Cuántos giros detecta | Muchos | Pocos |
| Qué tipo de giros | Incluye ruido de mercado | Solo giros estructurales |
| Ejemplos para entrenar | Bastantes | Muy pocos |
| Riesgo | El modelo aprende ruido | El modelo no tiene de dónde aprender |

Hay un límite aritmético que conviene tener claro desde ya, porque condiciona todo el proyecto:

> **Dos máximos no pueden estar a menos de `w+1` velas de distancia.**
> Si dos velas fueran ambas máximo y estuvieran a menos de `w`, cada una caería dentro de la ventana de la otra, y cada una tendría que ser mayor que la otra. Imposible.

Consecuencia directa: como mucho **1 de cada `w+1` velas** puede ser Máximo, y lo mismo para Mínimo. Con `w=5`, los máximos son a lo sumo el 16.7% de los datos y los mínimos otro 16.7%; el resto — al menos el 66% — es Continuidad. Y eso es una **cota superior**: en la práctica va a ser bastante menos.

**Esto es aritmética, no una medición.** Todavía no hemos descargado los datos, así que no sabemos el porcentaje real. Pero la cota ya nos dice que vamos a tener un problema de **clases desbalanceadas**, y que hay que tenerlo en cuenta desde el diseño y no descubrirlo en la semana 4.

### Por qué el desbalance importa tanto

Si el 85% de las velas son Continuidad, un modelo que responda siempre "Continuidad" y nunca detecte un solo giro acierta el 85% de las veces. Un 85% de exactitud suena bien en una presentación y es un modelo completamente inútil.

Por eso el enunciado no pide exactitud: pide **Precisión Direccional** y **F1-Score**. Son métricas que no se dejan engañar por el desbalance. Este es exactamente el tipo de pregunta incómoda que nos pueden hacer en la exposición, así que conviene que lo tengamos claro y lo digamos nosotros primero.

---

## 4. Qué es `h` (el horizonte)

`h` es **cuánto hacia adelante pronosticamos**. El modelo ve la información disponible hasta el momento `t` y responde: ¿qué etiqueta le va a corresponder a la vela `t+h`?

- `h = 1`: predecir la vela siguiente. Más fácil, menos útil en la práctica.
- `h = 5`: predecir cinco velas adelante. Mucho más útil, mucho más difícil.

`w` y `h` son independientes: `w` define *qué* es un giro, `h` define *con cuánta anticipación* lo queremos anunciar.

---

## 5. La trampa: la etiqueta llega tarde

Este es el punto que más fácil se pasa por alto y el que más nos puede costar en la evaluación.

Para saber si la vela `t` fue un máximo, hay que comparar su cierre con el de las `w` velas **posteriores**. Es decir: **la etiqueta de la vela `t` no se conoce hasta la vela `t+w`.**

Ahora juntemos las dos cosas. Si estamos parados en `t` y queremos predecir la etiqueta de `t+h`, esa etiqueta no existirá hasta `t+h+w`. En términos prácticos: **la anticipación real del sistema es `h+w` velas, no `h`.**

De acá salen dos riesgos concretos:

1. **Fuga de información (data leakage).** Si al construir las features no tenemos cuidado, podemos meter sin querer información de velas futuras — las mismas que se usaron para calcular la etiqueta. El modelo daría resultados excelentes en las pruebas y sería inservible con datos reales. Es el error más común en este tipo de proyecto y es invisible si no se busca a propósito.
2. **Qué significa "tiempo real".** El enunciado pide, en las semanas 3 y 4, "pruebas de detección con datos sintéticos, de entrenamiento y **tiempo real**". Hay que definir qué cuenta como tiempo real acá: ¿el sistema anuncia el giro `w` velas después de que ocurrió (confirmación tardía pero certera), o tiene que anunciarlo en el momento (predicción genuina, más difícil y más valiosa)? **Son dos productos distintos.**

Este segundo punto va directo a la consulta al profesor.

---

## 6. Qué se rompe si no congelamos esto ya

La definición de la etiqueta es la **interfaz compartida** del proyecto. Todo lo demás la consume:

- El módulo de **features** construye variables pensando en predecir *esa* etiqueta.
- El módulo de **modelado** entrena contra *esa* etiqueta.
- El módulo de **evaluación** reporta métricas calculadas sobre *esa* etiqueta.

Si en la semana 3 alguien está trabajando con `w=5` y otro con `w=10`, los resultados no son comparables entre sí y no hay forma de saber cuál de los dos modelos es mejor. Peor: no nos vamos a dar cuenta hasta que los números no cuadren, probablemente en la semana 4, cuando ya no haya tiempo.

Por eso `w` y `h` se deciden **esta semana**, se escriben en `contracts/labeling.py` como una única función que usan los cuatro módulos, y **no se cambian sin acuerdo explícito de todo el equipo**.

Si más adelante encontramos una razón medida para cambiarlos, se cambian — pero se cambian en un solo lugar y se re-corre todo, no se parcha en cuatro archivos distintos.

---

## 7. Lo que ya está decidido por el enunciado

No todo está abierto. Dos cosas ya vienen fijadas y no las discutimos:

- **La etiqueta se calcula sobre el precio de cierre**, no sobre el máximo ni el mínimo de la vela. El enunciado lo dice explícitamente ("el precio de cierre de LTC en una ventana temporal `w`").
- **Son tres clases**, no dos ni cinco: Máximo, Mínimo y Zona de Continuidad.

---

## 8. Lo que el equipo tiene que decidir

Cuatro decisiones. Las tres primeras son nuestras; la cuarta depende de lo que responda el profesor.

### Decisión 1 — Granularidad de las velas

Cuánto dura cada vela. Es la decisión de mayor impacto de las cuatro, porque determina cuántos datos vamos a tener.

| Opción | Datos aproximados desde 2020 | A favor | En contra |
|---|---|---|---|
| **Diaria** | ~2.000 velas | Menos ruido, series más limpias, más fácil de interpretar y de explicar | Pocos datos para un Transformer; los giros van a ser escasos |
| **Horaria** | ~48.000 velas | Veinticuatro veces más ejemplos; hace viable entrenar un modelo grande | Mucho más ruido de microestructura; archivos más pesados; más difícil de justificar cada giro |
| **4 horas** | ~12.000 velas | Punto intermedio razonable | Menos convencional, hay que justificarlo mejor |

> **Advertencia sobre las cifras de esta tabla:** son estimaciones aritméticas (días transcurridos desde 2020 hasta hoy), **no mediciones**. No hemos descargado ningún dato todavía. Además, la ventana histórica común de las seis criptomonedas está limitada por la más joven — creo que es SOL, listada alrededor de 2020, **pero eso hay que verificarlo, no lo he confirmado**.

### Decisión 2 — Valor de `w`

Propuesta para discutir, con velas diarias:

| Opción | `w` | Qué captura | Máximo teórico de giros |
|---|---|---|---|
| A | 3 | Oscilaciones cortas | 25% máx + 25% mín |
| B | 5 | Giros de escala semanal | 16.7% + 16.7% |
| C | 10 | Solo cambios de tendencia importantes | 9% + 9% |

Recordar que son **cotas superiores**, no lo que va a pasar de verdad.

### Decisión 3 — Valor de `h`

Propuesta: `h` entre 1 y 5 velas. A mayor `h`, más útil y más difícil. Conviene fijar un valor principal para el proyecto y, si sobra tiempo, reportar cómo se degrada el rendimiento al aumentarlo — eso es material de análisis para el reporte final y suma en el criterio de Análisis de la rúbrica.

### Decisión 4 — Qué significa "tiempo real"

Depende de la respuesta del profesor a la consulta 3 de la sección siguiente.

### Cómo proponemos decidir

Para no elegir a ciegas y para no justificar después lo que ya queríamos hacer, el criterio se fija **antes** de mirar los resultados:

1. Se descargan los datos y se mide, para cada combinación candidata de `(granularidad, w, h)`, el porcentaje real de cada clase y el total de ejemplos de las clases minoritarias.
2. **Criterio fijado de antemano:** se elige la combinación con el `w` más grande que deje **al menos 300 ejemplos de la clase minoritaria en el conjunto de entrenamiento**. Preferimos el `w` más grande porque detecta giros más significativos; el piso de 300 es para que el modelo tenga de dónde aprender.
3. El equipo revisa el resultado de esa medición y confirma o ajusta.

> El umbral de 300 es una propuesta, no un número medido ni sacado de un paper. Está para que la discusión tenga un criterio explícito en vez de resolverse por intuición. Si alguien tiene un argumento mejor, se cambia **ahora**, antes de medir — no después de ver los resultados.

---

## 9. Consulta al profesor

*Esta sección está redactada para poder enviarse tal cual.*

---

Estimado profesor Roberto Calvo,

Somos el equipo del Caso N°1 (pronóstico de puntos de inflexión en LTC). Antes de fijar el diseño del modelo queremos consultarle cuatro puntos del enunciado que admiten más de una lectura, para no avanzar sobre un supuesto equivocado.

**1. Sobre la ventana `w` y el horizonte `h`.**
El enunciado define el máximo local en función de una ventana temporal `w`, pero no fija su valor, ni el del horizonte de predicción `h`. Entendemos que la elección es nuestra y que debe quedar justificada en el informe a partir de las características de los datos. ¿Es correcta esa interpretación, o hay valores o un criterio que usted espere que utilicemos?

**2. Sobre la granularidad y la ventana histórica.**
El enunciado no especifica la frecuencia de los datos. Estamos evaluando velas diarias, de 4 horas u horarias; la diferencia es de aproximadamente 2.000 a 48.000 observaciones, lo que condiciona qué modelos son viables. Además, la ventana histórica común a las seis criptomonedas está acotada por la de listado más reciente. ¿Tiene alguna preferencia de granularidad o de período mínimo?

**3. Sobre qué se considera "tiempo real".**
Para determinar si una vela fue un máximo local hay que observar las `w` velas siguientes, de modo que la etiqueta de un instante `t` solo se conoce en `t+w`. Las pruebas "en tiempo real" que pide el enunciado para las semanas 3 y 4 admiten entonces dos interpretaciones:

- **(a)** El sistema confirma el giro con `w` velas de retraso: detección tardía pero verificable.
- **(b)** El sistema anuncia el giro en el momento, sin esperar confirmación: predicción genuina, considerablemente más difícil.

¿Cuál de las dos espera que implementemos? ¿O deberíamos reportar ambas?

**4. Sobre la métrica de decisión.**
El enunciado solicita Precisión Direccional y F1-Score. Dado que el problema es de tres clases y que estarán fuertemente desbalanceadas por construcción, quisiéramos confirmar cómo interpretarlas: ¿F1 macro (que da igual peso a las tres clases) o F1 ponderado? ¿Y cómo debe entenderse la Precisión Direccional en un problema de clasificación multiclase y no de regresión?

Quedamos atentos. Muchas gracias.

Fabrizio Espinoza Arce — por el equipo (Alejandro Zamora, Jose Pablo Monestel, Isaac Morun)

---

## 10. Resumen para quien tenga tres minutos

- El enunciado deja abiertos dos números, `w` y `h`, y de ellos depende todo lo demás.
- `w` = cuánto miramos a los lados para decidir si algo fue un giro. `h` = con cuánta anticipación lo queremos predecir.
- Como mucho 1 de cada `w+1` velas puede ser un máximo, así que las clases van a estar desbalanceadas sí o sí. Por eso medimos con F1 y no con exactitud.
- La etiqueta de la vela `t` recién se conoce en `t+w`. Eso abre dos riesgos: fuga de información al construir features, y ambigüedad sobre qué significa "tiempo real".
- Se congelan esta semana, viven en un solo archivo, y no se cambian sin acuerdo de los cuatro.
- Al profesor le consultamos seis cosas, y el texto vive en [`02-consulta-profesor.md`](02-consulta-profesor.md): si `w` y `h` son decisión nuestra, qué granularidad espera, qué entiende por tiempo real, cómo interpretar las métricas, si el segundo modelo debe ser un Transformer de verdad, y cómo queda el calendario de entregas.

---

## Anexo — Términos usados

**Vela (candle):** una observación de precio agrupada en un intervalo (un día, una hora). Trae apertura, máximo, mínimo, cierre y volumen. Nosotros usamos el cierre.

**Etiqueta:** la respuesta correcta que el modelo tiene que aprender a dar. Acá: Máximo, Mínimo o Continuidad.

**Clases desbalanceadas:** cuando una etiqueta aparece muchísimo más que las otras. Rompe la exactitud como medida de calidad.

**F1-Score:** medida que combina cuántos de los giros anunciados eran de verdad giros (precisión) con cuántos de los giros reales logramos anunciar (recall). No se deja engañar por el desbalance.

**Fuga de información (data leakage):** cuando el modelo recibe, sin que nos demos cuenta, información del futuro que en producción no tendría. Produce resultados excelentes y falsos.

**Interfaz congelada:** una definición acordada que varios módulos consumen y que nadie cambia por su cuenta.
