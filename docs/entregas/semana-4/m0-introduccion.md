# Introducción

Esta entrega cubre la **Semana 4** del enunciado: el desarrollo del **modelo avanzado** —un
Transformer—, la ingeniería de características que reciben los tres modelos y la comparación entre
ellos sobre validación.

> **Las pruebas de detección no se repiten aquí, y conviene decir por qué.** Las cuatro son pruebas
> **del circuito**, no de un modelo: comprueban que el etiquetado es correcto, que el camino de
> datos no tiene fuga y que alimentar el sistema vela a vela da lo mismo que procesar el bloque
> entero. Se corrieron con el **modelo clásico** y se reportan en la **Semana 3**.
>
> Correrlas de nuevo sobre el avanzado mediría otra vez el mismo circuito. Sería una mejora tenerlas
> también sobre los dos modelos profundos —el enunciado las nombra en las dos semanas— y **no se
> hizo**: decirlo es más barato que insinuar que están.

Se entrega por separado, como avance propio, además de estar integrada en el informe final.

---

## Qué se entrega esta semana

| Pieza | Estado |
|---|---|
| Modelo avanzado entrenado | **Hecho** — iTransformer, `src/modelos/avanzado.py` |
| Ingeniería de características | **Hecha** — 63 columnas, ninguna en nivel de precio |
| Comparación de los tres modelos sobre validación | **Hecha** — con intervalos pareados |
| Pruebas de detección | **En la Semana 3** — son del circuito, no de un modelo, y se corrieron con el clásico |

---

## Lo que esta semana añade a la anterior, y por qué el orden importa

La Semana 3 demostró que el circuito es correcto. Esta semana lo usa para **comparar**, que es una
pregunta distinta y más difícil.

Comparar exige tres cosas que no son negociables, y las tres estaban decididas antes de medir:

1. **La misma partición y el mismo arnés para todos.** Un resultado obtenido fuera del arnés de
   evaluación no entra al documento. Si dos modelos se miden con particiones distintas, la
   comparación mide la partición y no los modelos.
2. **Un piso obligatorio.** Todos los modelos se comparan contra un `baseline_aleatorio`, no solo
   entre ellos. Sin ese piso, «el Transformer alcanza 0,35 de F1 macro» no significa nada.
3. **Intervalos, no medias sueltas.** Una diferencia entre dos modelos puede venir de que uno sea
   mejor o de qué velas cayeron en el bloque. El remuestreo pareado separa las dos cosas.

---

## El capítulo de características va primero, y no es relleno

El modelo avanzado recibe las mismas **63 columnas** que el clásico. Qué son esas columnas —y sobre
todo qué **no** son— condiciona lo que cualquier modelo puede aprender, así que el capítulo va antes
que la comparación.

El punto que más importa de ese capítulo: **el modelo no ve el precio.** Ninguna de las 63 columnas
es un nivel de precio. Y no se hizo bien de entrada: hubo 24 columnas de precio rezagado en nivel,
que en una serie con tendencia funcionan como un indicador de *cuándo* se está mirando en vez de
*qué* se está mirando. El cambio a variación relativa está medido, con intervalo que excluye el cero.

---

## Lo que esta entrega permite afirmar, y lo que no

**Permite afirmar cuál de los tres modelos es mejor sobre validación**, con el criterio fijado de
antemano. El resultado no es el que el enunciado sugiere esperar, y se reporta tal cual.

**No permite afirmar rendimiento sobre datos no vistos.** Sobre validación se tomaron decisiones —se
compararon modelos y se eligió— y por eso mismo esas cifras no son una estimación honesta de lo que
haría el sistema con datos nuevos. Esa medición es la Semana 5, y se hace **una sola vez**.
