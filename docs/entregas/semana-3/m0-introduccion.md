# Introducción

Esta entrega cubre la **Semana 3** del enunciado: el desarrollo del **modelo fundacional** y las
**pruebas de detección** con datos sintéticos, de entrenamiento y en tiempo real.

Se entrega por separado, como avance propio, además de estar integrada en el informe final. Las dos
formas contienen el mismo material medido; lo que cambia es el alcance: aquí se puede seguir un solo
tema hasta el fondo sin la comparación entre modelos, que llega en la Semana 4.

---

## Qué se entrega esta semana

| Pieza | Estado |
|---|---|
| Modelo fundacional entrenado | **Hecho** — Chronos-Bolt, `src/modelos/fundacional.py` |
| Prueba de detección con datos sintéticos | **Hecha** — 187 de 187 vértices recuperados |
| Prueba de detección sobre entrenamiento | **Hecha** — F1 macro 0,953353 contra 0,331638 del azar |
| Prueba de detección en tiempo real | **Hecha** — 500 velas, cero discrepancias |

---

## Por qué el diseño va antes que el modelo

El documento empieza por el **diseño** y no por el modelo, aunque el enunciado pida el modelo. La
razón es que sin la definición operativa de punto de inflexión ninguna métrica del resto significa
algo: el F1 macro de un clasificador de tres clases depende por completo de cómo se construyeron esas
tres clases.

El capítulo de diseño responde tres preguntas —qué se predice, sobre qué datos, y cómo se separan
para que las cifras se puedan creer— y las tres se decidieron **midiendo**, antes de entrenar nada.

---

## Lo que esta entrega permite afirmar, y lo que no

**Permite afirmar que el circuito es correcto.** Las cuatro pruebas de detección pasan, y la de
tiempo real —que alimenta el sistema vela a vela y comprueba que predice exactamente lo mismo que
procesando el bloque entero— es la única capaz de detectar fuga de información desde filas
posteriores. Dio **cero discrepancias sobre 500 velas**.

**No permite afirmar que el modelo fundacional sirva.** Ninguna de las cuatro pruebas mide
rendimiento sobre datos no vistos. La prueba sobre entrenamiento da la cifra más alta del documento
—0,953353— y es la que menos vale, porque ahí el modelo ya vio las respuestas; el capítulo
correspondiente lo explica en vez de dejar la tabla sola.

Esa distinción —**«corre» y «funciona» no son lo mismo**— es la que organiza toda la entrega.
