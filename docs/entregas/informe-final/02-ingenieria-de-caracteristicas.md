# 2. Ingeniería de características

**Autor:** Alejandro Zamora (M2) · **Fuente del material:** `docs/07-importancia-caracteristicas.md`,
`docs/06-aporte-multivariante.md`, D5, D6, D16, D20 · **Todas las cifras salen de
`docs/evidencias/`.**

El modelo recibe **63 columnas** construidas por `src/features/base.py`. Esta sección dice qué son,
por qué ninguna es precio crudo, cuáles el modelo usa de verdad, y qué no se puede afirmar sobre
ellas.

---

## 2.1 Las seis familias

**Tabla 2.1.** Las 63 columnas, por familia.

| Familia | Columnas | Qué mide |
|---|---|---|
| Rezagos | 24 | Variación relativa del cierre a 1–7 velas, de los seis activos |
| Retornos | 17 | Retornos a 1 y 3 velas |
| Indicadores técnicos | 10 | RSI, MACD, Bollinger, distancia a medias móviles |
| Correlación cruzada | 5 | Correlación móvil de LTC contra cada activo de apoyo |
| Ventana deslizante | 4 | Posición dentro del rango, rango relativo |
| Volatilidad | 3 | Desviación móvil de los retornos |

Ninguna familia se eligió por costumbre: los órdenes de rezago salen de medir la autocorrelación y
la correlación cruzada (S1-M2-04), y la ventana de los indicadores está fijada por el contrato
—`w = 7`, `h = 1`, velas de 4 horas— para que ninguna columna use información posterior a `t`.

---

## 2.2 Cero columnas en nivel de precio, y lo que costó llegar ahí

**El modelo no ve el precio.** Lo verifiqué de dos formas sobre el `main` de hoy:

```
columnas construidas                                63
rezagos en nivel de precio (`_rezago_` sin `_rel_`)   0
```

Las dos únicas columnas cuya magnitud supera la decena son `LTC_rsi_14` —acotado entre 0 y 100 por
definición— y `LTC_curtosis_retornos_20`, que es un cuarto momento y no tiene cota superior.
**Ninguna de las dos es un nivel de precio**, y ninguna columna alcanza el orden de magnitud en que
cotiza LTC en el período.

**Y no se hizo bien de entrada.** Hasta el PR #58 había 24 columnas de precio rezagado *en nivel*,
que en una serie con tendencia funcionan como un indicador de posición dentro de la serie y no como
una señal: el modelo puede aprender *cuándo* está mirando en vez de *qué* está mirando. Se cambiaron
a variación relativa `p(t−k)/p(t) − 1` (D6).

**Lo que compró ese cambio está medido**, con remuestreo pareado sobre las mismas filas de
validación:

```
bosque con rezagos relativos  vs  bosque con rezagos en nivel
  diferencia   +0,046191
  IC 95 %      [+0,014060 , +0,080520]      excluye el cero
```

Y el efecto sobre lo que el proyecto puede afirmar es más grande que ese número: con rezagos en
nivel, el bosque **no se distinguía del azar** (+0,007522, IC [−0,025712, +0,039088], incluye el
cero); con rezagos relativos sí (+0,053714, IC [+0,013658, +0,092854]).

Es decir: **la representación no mejoró un modelo que ya funcionaba — es lo que hizo que hubiera un
resultado que reportar.**

---

## 2.3 Qué usa el modelo, medido por permutación

La importancia que devuelve el bosque se calcula sobre entrenamiento y favorece a las variables de
alta cardinalidad: describe de qué se colgó el modelo para ajustar lo que ya vio. La pregunta útil
es otra —si el modelo necesita la columna para predecir lo que no vio—, y se responde permutando la
columna sobre **validación** y midiendo cuánto cae el F1 macro.

Las dos ordenaciones coinciden en lo grueso y no en el detalle: **correlación de rangos de Spearman
0,6086**. Elegir una u otra cambia qué columnas se conservarían.

**Tabla 2.2.** Las cinco columnas de mayor caída (F1 macro base: 0,390498).

| Columna | Caída media |
|---|---|
| `LTC_posicion_rango_7` | 0,0422 |
| `LTC_dist_sma_7` | 0,0343 |
| `ADA_cierre_rezago_rel_5` | 0,0258 |
| `LTC_cierre_rezago_rel_5` | 0,0255 |
| `LTC_cierre_rezago_rel_6` | 0,0224 |

**Tabla 2.3.** Agregado por familia.

| Familia | Columnas | Caída total | Máxima | Mediana |
|---|---|---|---|---|
| Rezagos | 24 | 0,2773 | 0,0258 | 0,0105 |
| Retornos | 17 | 0,1287 | 0,0195 | 0,0083 |
| Indicadores técnicos | 10 | 0,1218 | 0,0343 | 0,0098 |
| Ventana deslizante | 4 | 0,0700 | **0,0422** | 0,0109 |
| Correlación cruzada | 5 | 0,0386 | 0,0147 | 0,0077 |
| Volatilidad | 3 | 0,0242 | 0,0103 | 0,0081 |

**Ventana deslizante es la familia más eficiente por columna:** cuatro columnas, y la mayor caída
de todas.

---

## 2.4 El piso de ruido: qué hace que la tabla signifique algo

Una tabla de importancias sin piso no se puede leer. Una caída de 0,004 puede ser información o
puede ser lo que da cualquier columna al permutarla.

Por eso el experimento añade **cinco columnas centinela** —ruido puro, con semilla fija— y mide su
caída con el mismo procedimiento. **El piso es la mayor de las cinco: 0,006500**, de
`centinela_ruido_3`.

Con ese piso, **46 de las 63 columnas lo superan** y 17 no.

El propio experimento cuantifica lo que cuestan las columnas que no informan. Añadir **cinco**
centinelas casi no mueve el modelo —F1 macro 0,389590 contra 0,390498 del real—, pero con **quince**
el modelo auxiliar sí se degrada: **0,366391**. Con 420 ejemplos de la clase minoritaria, cada
columna que no aporta es superficie de sobreajuste (RF-F4).

Se citan las dos cifras y no su resta a propósito: una diferencia calculada en prosa es un valor
derivado sin evidencia propia, que es lo que el equipo acordó no hacer.

---

## 2.5 Recortar las 17: medido, no opinado

La tabla dice de qué se apoya el modelo. **No dice qué pasa si se le quitan las que no usa** — eso
hay que entrenarlo. Se entrenó, con las 63 y con las 46, sobre cinco semillas:

**Tabla 2.4.** Efecto de quitar las 17 que no superan el piso.

| Semilla | 63 columnas | 46 columnas | Diferencia |
|---|---|---|---|
| 0 | 0,3905 | 0,3936 | +0,0031 |
| 1 | 0,3739 | 0,3751 | +0,0012 |
| 2 | 0,3814 | 0,3852 | +0,0038 |
| 3 | 0,3854 | 0,3898 | +0,0044 |
| 4 | 0,3737 | 0,3865 | +0,0128 |
| | | **media** | **+0,005063** |

**Mejora en las cinco y el signo nunca cambia**, que es la condición de la D16 y la que en el
análisis multivariante no se cumplió.

Dos precisiones que el informe tiene que hacer explícitas:

1. **+0,0051 está por debajo del umbral de decisión del equipo (0,02).** Por la D5 esto **no**
   autoriza a decir que el modelo recortado sea mejor. Autoriza a decir que quitarlas no cuesta
   nada y que el signo es consistente.
2. **El argumento principal no es el +0,0051, es la superficie de sobreajuste.** El +0,0051 es la
   confirmación de que recortar no daña, no la razón para recortar.

---

## 2.6 La tensión con el resultado multivariante, y por qué no es una contradicción

`ADA_cierre_rezago_rel_5` aparece **tercera** en la tabla de importancias, y otros cuatro activos de
apoyo están en el top 15. Y sin embargo quitar **todos** los activos de apoyo no cambia el
resultado de forma distinguible: diferencia media **+0,00078**, con el signo cambiando en 2 de 5
semillas.

**Las dos cosas son ciertas, y miden preguntas distintas:**

- **Permutar** pregunta *«¿de qué depende este modelo ya ajustado?»*. Respuesta: entre otras cosas,
  del rezago 5 de ADA.
- **Ablacionar** pregunta *«¿qué pasa si entreno sin esa familia?»*. Respuesta: nada apreciable.

La explicación es la **redundancia**, y está medida (D20): los quince pares entre los seis activos
correlacionan de **+0,5175 a +0,8300**, y **no hay ninguna relación inversa**. Si el rezago de ADA
está, el modelo lo usa; si no está, usa el de LTC y llega parecido.

**Permutar mide dependencia; ablacionar mide información única.** Es la misma razón por la que no
superar el piso no prueba que una columna sea inútil: con columnas correlacionadas, la permutación
reparte el crédito entre ellas y subestima a las dos.

---

## 2.7 Lo que esta sección no puede afirmar

- **Que las 17 descartadas sean inútiles.** Lo medido es que *esta* medición no las distingue del
  ruido, sobre *este* modelo y con 1 959 velas de validación.
- **Que las 46 sean las mejores 46 posibles.** No se probó ningún otro corte. El piso de ruido es
  un criterio defendible, no un óptimo.
- **Que el orden columna por columna sea estable.** Varias caídas medias están dentro de una
  desviación de sus vecinas: lo estable es la separación entre bloques, no el puesto exacto.

---

> **Reproducibilidad.** Todo sale de `uv run python -m src.features.importancia`, que deja el JSON,
> el CSV y la figura. El guion **no escribe nada** si el bosque no reproduce antes el F1 macro
> `0.390497720487045` que M3 y M2 midieron por separado con código distinto.
