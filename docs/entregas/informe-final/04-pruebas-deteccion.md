# 4. Pruebas de detección

**Autor:** Fabrizio Espinoza (M0) · **Fuente del material:**
`docs/evidencias/pruebas-deteccion.json`, D21 · **Todas las cifras salen de `docs/evidencias/`.**

El enunciado pide, en las semanas 3 y 4, **pruebas de detección con datos sintéticos, de
entrenamiento y en tiempo real**. Son tres; aquí hay **cuatro**, porque la sintética se partió en
dos: una que prueba el etiquetador solo y otra que prueba el circuito completo. Sin esa separación,
un fallo en la sintética no dice dónde está el problema.

**Cada prueba tiene su criterio escrito antes de correrla.** Están en el propio archivo de evidencia,
en el campo `criterio_preregistrado`, no en un documento aparte donde se pudieran ajustar después.

> **Con qué modelo se corrieron, y qué queda fuera.** Las cuatro son pruebas **del circuito** —
> etiquetado, camino de datos, ausencia de fuga — y se corrieron con el **modelo clásico**: en
> `pruebas-deteccion.json` las claves son `f1_macro_bosque`, `f1_maximo_bosque` y `f1_minimo_bosque`.
>
> **No se repitieron sobre los dos modelos profundos.** El enunciado las nombra en las semanas 3 y 4,
> así que tenerlas también sobre el fundacional y el avanzado sería una mejora — y no está hecha. Lo
> que las cuatro verifican no cambia por el modelo que las corra, pero eso es un argumento, no una
> medición, y por eso queda declarado aquí en vez de resuelto en silencio.

---

## 4.1 Qué demuestra cada una

Las cuatro no son cuatro intentos de lo mismo: cada una puede fallar por una razón que las otras no
verían.

**Tabla 4.1.** Las cuatro pruebas, qué aísla cada una y qué pasó.

| # | Prueba | Qué puede detectar que las otras no | Resultado |
|---|---|---|---|
| 1 | Sintética · etiquetador | Que el etiquetador esté corrido respecto de la serie | **187/187** |
| 2 | Sintética · circuito completo | Que el circuito no detecte ni sobre datos donde la señal existe por construcción | **supera** |
| 3 | Entrenamiento | Que el problema esté **antes** del ajuste | **supera** |
| 4 | Tiempo real | **Fuga de información de filas posteriores** | **0 discrepancias** |

---

## 4.2 Prueba 1 · El etiquetador, sobre una serie construida

**Qué prueba.** Que el etiquetador recupera los vértices que se plantaron a propósito, en una serie
sin ruido y con los vértices separados más de `w + 1`, de modo que cada uno sea un extremo estricto.

**Criterio fijado antes:** recuperación del **100 %**. Con una serie construida así, fallar uno solo
significa que algo está corrido.

| | |
|---|---|
| Observaciones | 3 000 |
| Giros plantados | **187** |
| Giros recuperados | **187** |
| Recuperación | **1,0** |

El criterio es exigente a propósito: aquí no hay lugar para «casi». Si el etiquetador se saltara uno,
todas las etiquetas del proyecto estarían desplazadas y ninguna métrica posterior significaría nada.

---

## 4.3 Prueba 2 · El circuito completo, sobre datos sintéticos

**Qué prueba.** Que el circuito entero —características, partición, modelo— detecta los giros de una
serie construida, **pasando por el mismo canal que los datos reales**.

**Criterio fijado antes:** el bosque tiene que superar al baseline aleatorio en el F1 de **las dos**
clases extremas. Con un guardarraíl explícito: **no basta con que sea mayor que cero.**

**Tabla 4.2.** Prueba 2, sobre serie sintética.

| Métrica | Bosque | Azar |
|---|---|---|
| F1 macro | **0,540146** | 0,308567 |
| F1 máximo | **0,411765** | 0,0 |
| F1 mínimo | **0,333333** | 0,0 |

Que el azar dé **0,0** en las dos clases extremas es lo esperable: acertar un extremo por casualidad
en una serie limpia es muy improbable. Lo informativo es que el bosque no dé cero.

> **Por qué el guardarraíl.** «Mayor que cero» aprueba a un modelo que acierta un extremo de
> quinientos. El criterio exige superar al azar **de la misma corrida**, que es un piso que se mueve
> con los datos en vez de un número fijo elegido por conveniencia.

---

## 4.4 Prueba 3 · Sobre el bloque de entrenamiento

**Qué prueba.** Que el modelo detecta sobre datos reales.

**Tabla 4.3.** Prueba 3, sobre entrenamiento (9 165 velas etiquetadas).

| Métrica | Bosque | Azar |
|---|---|---|
| F1 macro | **0,953353** | 0,331638 |
| F1 máximo | **0,961098** | — |
| F1 mínimo | **0,906414** | — |

**Y aquí hay que ser explícito, porque es la cifra más alta del informe y la que menos vale.** La
advertencia está en el propio archivo de evidencia:

> Un resultado alto aquí **NO es evidencia de que el modelo sirva**: es lo esperable de un modelo que
> vio estas etiquetas. Lo informativo sería un resultado **bajo**, que indicaría que el problema está
> antes del ajuste.

O sea: esta prueba solo tiene valor **si falla**. Un 0,95 en entrenamiento no dice que el modelo
detecte puntos de inflexión; dice que el circuito puede aprender cuando se le dan las respuestas. Si
hubiera salido 0,4, sabríamos que el problema no está en el modelo sino en las características o en
las etiquetas.

El enunciado la pide, y se reporta con esa advertencia al lado. Una tabla con 0,953353 sin ese
párrafo sería el número más engañoso del documento.

---

## 4.5 Prueba 4 · Tiempo real, y por qué es la única que busca fuga

Las tres anteriores procesan un bloque entero de datos de una vez. Esta alimenta el sistema **vela a
vela**, como funcionaría en producción.

**Criterio fijado antes:** las predicciones vela a vela tienen que ser **idénticas** a las del
bloque. Cualquier discrepancia significa que algo usa información de filas posteriores — **fuga que
las otras tres pruebas no pueden ver**, porque todas tienen el bloque completo disponible.

**Tabla 4.4.** Prueba 4, tiempo real.

| | |
|---|---|
| Velas simuladas | **500** |
| Predicciones idénticas | **sí** |
| Discrepancias | **0** |

Cero discrepancias sobre 500 velas es la evidencia más fuerte del informe de que **el circuito no
mira hacia adelante**. No es una revisión de código ni un argumento: es una comprobación que fallaría
si hubiera fuga.

### La cola sin confirmar, y por qué se muestra

Esta prueba mide algo más, que no es un defecto sino una propiedad del problema.

Como la etiqueta necesita `w` velas posteriores, una predicción hecha en `t` **no se puede confirmar
hasta `t + 8`** — ocho velas de 4 horas, o sea **32 horas**. Al final de la serie quedan siempre
**8 predicciones sin confirmar**.

La **D21** decide qué hacer con ellas: **se muestran, marcadas como pendientes.** El argumento está
en el archivo de evidencia:

> En producción el sistema está parado al final de la serie, y las últimas 8 velas todavía no tienen
> etiqueta real. La D21 obliga a mostrarlas igual, marcadas como pendientes, porque **ocultarlas
> haría parecer el sistema mejor de lo que es**.

Es una decisión de honestidad de producto: esconder lo que aún no se sabe deja una vista donde todo
lo mostrado parece verificado. La aplicación las declara.

---

## 4.6 Lo que las cuatro juntas permiten decir

**Que el circuito es correcto.** El etiquetador no está corrido, el canal detecta cuando hay algo que
detectar, el modelo aprende cuando ve las respuestas, y no hay fuga temporal.

**Y nada sobre si el sistema sirve.** Ninguna de las cuatro mide rendimiento sobre datos no vistos.
Eso es la sección 5, y da números mucho más modestos que el 0,953353 de la prueba 3.

Esa distinción —**«corre» y «funciona» no son lo mismo**— es la razón por la que estas pruebas están
antes que las métricas y no después.
