# El modelo avanzado

**Autor:** Isaac Fallas (M3) · **Ensamblado por** Fabrizio Espinoza (M0) desde la sección
de M3 del informe final, sin reescribir su contenido. **Todas las cifras salen de
`docs/evidencias/`.**

---

## iTransformer

**iTransformer, lookback 96, dimensión 64, profundidad 2, 8 épocas.**

Es la arquitectura que atiende **entre series** en vez de entre instantes, que es justamente la
propiedad que interesa cuando se tienen seis activos.

### Por qué no es Informer

El enunciado nombraba a los dos. **Informer no se pudo instalar**, y eso está medido y no supuesto:
la ruta obvia era `neuralforecast`, que trae los dos, y su resolución falla en este proyecto porque
depende de `ray`, que **no publica ruedas** para la versión de Python que el proyecto fija — el
resolutor las busca con la etiqueta `cp314` sobre `win_amd64` y solo encuentra `cp310` a `cp313`.
Queda registrado en la D14 con la salida literal del resolutor.

### Lo que cuesta

| | |
|---|---|
| Parámetros | 141 656 |
| Entrenamiento | 27,0 s |
| Presupuesto de la RNF-4 | 7 200 s |

Cabe con holgura de dos órdenes de magnitud. **El modelo avanzado no fracasa por falta de
presupuesto**, y conviene decirlo antes de mostrar sus cifras.

| | F1 macro | Precisión Direccional | Exactitud |
|---|---|---|---|
| iTransformer | **0,345706** | 0,077720 | 0,805513 |

Ese valor es **una corrida**. El modelo se entrena, así que la cifra comparable es la media de
cinco semillas: **0,342604**, con un rango de **0,023207**. La tabla del protocolo declara la
media, no la corrida.

---

---

## Por qué no se ajustaron hiperparámetros

Las dos rejillas se corrieron y **las dos concluyeron que no hay de dónde mejorar**. En los dos
casos la regla estaba escrita antes de mirar el resultado.

**Fundacional — 18 celdas.** La mejor da 0,387269 contra los 0,368589 de la configuración por
omisión. Esa ganancia de **+0,018680 tiene un intervalo de [−0,017599 , 0,059620]**, que incluye el
cero: no se distingue del efecto de haber elegido el máximo de la rejilla mirando el mismo bloque de
validación con el que se elige.

**Avanzado — 6 celdas.** Aquí la regla la había fijado la D15 de antemano, y se disparó: la
dispersión **entre semillas** dentro de una celda, 0,026073, **supera** la dispersión **entre
celdas**, 0,020981. La rejilla no está distinguiendo configuraciones, está midiendo ruido de
entrenamiento. La ganancia media del ajuste es +0,001567 y **cambia de signo**: favorece a 3 de 5
semillas.

En los dos casos queda la configuración por omisión. **Es un resultado negativo y es información:**
dice que el margen de este problema no está en los hiperparámetros.

---
