# Introducción

Esta entrega cubre la **Semana 4** del enunciado: el desarrollo del **modelo avanzado** —un
Transformer—, la ingeniería de características que reciben los tres modelos, la comparación entre
ellos sobre validación y **las pruebas de detección corridas sobre los modelos profundos**.

> **Esa última sección es nueva, y antes esta introducción decía lo contrario.** Decía que las
> pruebas de detección se habían corrido solo con el modelo clásico y que repetirlas sobre los
> profundos sería una mejora **no hecha**. El enunciado las pide en las semanas 3 **y** 4, así que se
> hicieron. Están en la sección 4 de este documento, con su criterio fijado por escrito antes de
> correrlas.
>
> Lo que encontraron no es lo que esperábamos: **Chronos-Bolt pasa las tres**, y el **iTransformer
> falla la sintética** con cero máximos detectados. Y las tres confirman que el contexto que los dos
> profundos leen de la serie de precios es **causal**, que hasta ahora no estaba comprobado.

Se entrega por separado, como avance propio, además de estar integrada en el informe final.

---

## Qué se entrega esta semana

| Pieza | Estado |
|---|---|
| Modelo avanzado entrenado | **Hecho** — iTransformer, `src/modelos/avanzado.py` |
| Ingeniería de características | **Hecha** — 63 columnas, ninguna en nivel de precio |
| Comparación de los tres modelos sobre validación | **Hecha** — con intervalos pareados |
| Pruebas de detección sobre los profundos | **Hechas** — las tres que dependen del modelo, sobre el fundacional y el avanzado |

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
