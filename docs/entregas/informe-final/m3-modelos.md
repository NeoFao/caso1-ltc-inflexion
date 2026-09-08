# Los dos modelos: fundacional y avanzado

**Módulo M3 — Isaac Morún.** Material para la sección 3 del informe, la mitad de modelos de la
sección 5, y las limitaciones 2 y 3.

Las cifras de las secciones 1 a 6 son de **validación**; la sección 7 trae lo del bloque de prueba,
medido **una sola vez** el 07/09 (D18, D23). Todas salen de un archivo de evidencia que se regenera
con un comando.

---

## 1. El puente, que es lo que hace comparables a los dos

Ni Chronos-Bolt ni iTransformer clasifican. Los dos **pronostican una trayectoria**, y el problema
pide tres clases. Entre una cosa y la otra hay un puente, y está construido igual para los dos:

1. Estando en `t`, se pronostican `w + h` velas — con `w = 7` y `h = 1`, ocho velas.
2. Con ellas se arma una ventana de `2w + 1` centrada en `t + h`.
3. Se le aplica `etiquetar()` **del contrato**, el mismo que produjo las etiquetas reales.
4. Se lee el centro.

**Que los dos crucen igual no es un detalle de implementación: es lo que permite restar sus F1.**
Si cada uno cruzara a su manera, la diferencia entre ambos mezclaría el modelo con el puente y no
mediría lo que dice medir.

El puente está probado contra fuga con la misma prueba en las dos familias: se perturba el futuro
posterior al corte y se exige que la predicción de instantes anteriores **no se mueva**.

---

## 2. Modelo fundacional — Chronos-Bolt

**`amazon/chronos-bolt-small`, contexto 512, cuantil 0,5, cero entrenamiento** (D12).

Es un modelo de series temporales preentrenado que se usa **zero-shot**: no ve ni una vela de
nuestro conjunto de entrenamiento. Eso lo hace determinista —cinco semillas dan idéntico— y explica
por qué su fila del protocolo no lleva rango.

De las 1 959 filas de validación, **0 quedaron sin historia suficiente** para el contexto de 512,
así que la cifra no está calculada sobre un subconjunto cómodo.

| | F1 macro | Precisión Direccional | Exactitud |
|---|---|---|---|
| Chronos-Bolt | **0,368589** | 0,093264 | 0,830015 |

---

## 3. Modelo avanzado — iTransformer

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

## 4. Rendimiento sobre validación

| Modelo | F1 macro | PD | Exactitud |
|---|---|---|---|
| `bosque_aleatorio_rezagos_relativos` | **0,390498** | 0,103627 | 0,858091 |
| `chronos_bolt` | 0,368589 | 0,093264 | 0,830015 |
| `itransformer` | 0,345706 | 0,077720 | 0,805513 |
| `baseline_aleatorio` | 0,336784 | 0,051813 | 0,822358 |
| `itransformer_solo_ltc` | 0,324474 | 0,051813 | 0,794793 |
| `baseline_trivial` | 0,316063 | 0,000000 | 0,901480 |

**La exactitud del baseline trivial es la más alta de la tabla.** Predecir siempre Continuidad
acierta el 90,148 % de las veces y no detecta ni un solo giro. Por eso la métrica que decide es el
F1 macro y no la exactitud — y por eso el informe pone el F1 como número grande.

### Las comparaciones que deciden

Remuestreo **pareado** a 1 000 remuestras: las dos predicciones se remuestrean sobre las mismas
filas, porque los dos modelos aciertan y fallan sobre las mismas velas.

| Comparación | Diferencia | IC 95 % | ¿Excluye el cero? |
|---|---|---|---|
| Chronos-Bolt − trivial | +0,052527 | [0,025310 , 0,080845] | **sí** |
| Chronos-Bolt − aleatorio | +0,031805 | [−0,002956 , 0,065236] | no |
| Chronos-Bolt − bosque | −0,021908 | [−0,064249 , 0,020264] | no |
| iTransformer − trivial | +0,029643 | [0,006959 , 0,056009] | **sí** |
| iTransformer − aleatorio | +0,008922 | [−0,024084 , 0,044635] | no |
| iTransformer − bosque | −0,044792 | [−0,085204 , −0,001457] | sí, **pero no se reproduce** |
| iTransformer − Chronos-Bolt | −0,022884 | [−0,060774 , 0,018986] | no |

> **Las cuatro filas donde entra el iTransformer se leen con la [D25](../../DECISIONES.md#d25).**
> Ese modelo no es reproducible entre procesos, así que el intervalo pareado de una corrida no
> decide: el peso lo lleva el signo entre semillas. Las filas de Chronos-Bolt no están afectadas,
> porque es *zero-shot* y sus predicciones sí reproducen.

**Lo que esto dice, en orden de incomodidad:**

- Ninguno de los dos modelos profundos supera al `baseline_aleatorio` de forma distinguible.
  Le ganan en la media y el intervalo incluye el cero.
- **El iTransformer queda por debajo del bosque en las cinco semillas** — 0,345357 de media contra
  0,380975 del bosque.
  El intervalo pareado de *esta* corrida excluye el cero, pero **ese intervalo no se reproduce**:
  el ensayo en seco volvió a medirlo y dio [−0,081366 , 0,003154]. Lo que sostiene esta fila es el
  signo estable en las cinco, no el intervalo de una corrida — ver la sección 6 y la
  [D25](../../DECISIONES.md#d25).
- Entre fundacional y avanzado **no se distingue nada**. Por la D5, cuando el margen y su intervalo
  discrepan manda el intervalo, así que se prefiere el más simple: el fundacional, que ni se
  entrena.

---

## 5. Por qué no se ajustaron hiperparámetros

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

## 6. Lo que no se puede afirmar, y por qué

### Los activos de apoyo: signo estable en las cinco, sin distinguibilidad afirmable

El informe declara como limitación que los activos de apoyo no aportan de forma distinguible. **Se
midió sobre el bosque, y sobre el avanzado hay que decirlo con más cuidado**, porque la arquitectura
elegida existe justamente para atender entre series y es donde uno esperaría ver el aporte si lo
hay.

Esta sección pasó por dos correcciones y conviene que se lean juntas. La **D24** corrigió el
criterio de la D14 —mía—, que había respondido una pregunta de **distinguibilidad** con el umbral de
la D5, que es una convención para **elegir entre configuraciones**. Esa corrección sigue en pie. La
**D25** retiró el veredicto que la D24 sacó de ahí, porque la condición que lo sostenía no se
reproduce. **La conclusión vuelve a coincidir con la D14 por una razón distinta de la que la D14
dio**, y eso no vuelve correcto el argumento de entonces.

| Semilla | Completo | Solo LTC | Diferencia |
|---|---|---|---|
| 0 | 0,341440 | 0,329116 | +0,012324 |
| 1 | 0,333265 | 0,330431 | +0,002834 |
| 2 | 0,339446 | 0,331057 | +0,008389 |
| 3 | 0,356472 | 0,331717 | +0,024755 |
| 4 | 0,342398 | 0,339107 | +0,003291 |

Media **+0,010319**, mínima +0,002834, máxima +0,024755, y **el signo no cambia en ninguna de las
cinco**. Un barrido independiente lo repitió: positivo otra vez en las cinco, con el completo en
0,345357 de media contra 0,330523 del que usa solo LTC.

**Y aun así no se puede afirmar que el aporte sea distinguible.** La segunda condición de la D16
—que el intervalo pareado excluya el cero— **no se reproduce**: la corrida comprometida dio
[0,000434 , 0,044067] y el ensayo en seco [−0,001736 , 0,045490]. El límite de la primera vivía a
menos de una milésima del cero. Está en la [D25](../../DECISIONES.md#d25), decidido **antes** de
tocar el bloque de prueba.

Lo que sí sostiene el signo: el ruido de punto flotante **no tiene signo**, y las cinco semillas
caen del mismo lado en dos barridos independientes. Si no hubiera efecto, que las cinco coincidan
tiene probabilidad 1 en 16. Es evidencia de que algo hay; no alcanza el estándar que el equipo fijó
para afirmarlo.

**Y aun así no rescataría nada.** El iTransformer *con* los cinco activos de apoyo sigue quedando
por debajo del bosque *sin* ellos. Las dos cosas son ciertas a la vez y hay que decirlas juntas:

> El aporte de los activos de apoyo al modelo avanzado tiene **signo estable en las cinco semillas
> de dos barridos independientes**, y **no se puede afirmar que sea distinguible del azar** por el
> estándar que el equipo fijó. La D20 explica por qué sería pequeño aunque lo fuera: los seis son
> fuertemente proporcionales entre sí y **no hay ninguna relación inversa**, así que lo que traen es
> en buena parte lo que LTC ya tenía.

### La dispersión no es pareja, y es peor donde más importa

Las seis métricas que publica el panel, medidas sobre cinco semillas:

| Métrica | Media | Rango |
|---|---|---|
| F1 macro | 0,342604 | 0,023207 |
| Exactitud | 0,778765 | 0,058703 |
| F1 Continuidad | 0,876340 | 0,035500 |
| Precisión Direccional | 0,097409 | 0,046632 |
| F1 Mínimo | 0,077887 | 0,048659 |
| **F1 Máximo** | **0,073585** | **0,075013** |

**El F1 de la clase Máximo recorre más que su propia media.** Una media suelta en esa columna no
significa gran cosa, y por eso las tres métricas por clase se reportan siempre con su rango.

Y sobre el bloque de prueba es peor, porque hay menos de donde medir. Los conteos, que **no son
simétricos** y conviene no redondearlos:

| Bloque | Máximos | Mínimos |
|---|---|---|
| Validación | **99** | 94 |
| Prueba | **86** | 86 |

Para la clase Máximo —la de la fila conflictiva— se pasa de 99 a 86. Que la métrica por clase pueda
colapsar con esos tamaños no es una precaución retórica: el walk-forward lo midió, y en **2** de sus
nueve tramos una de las dos clases dio **0,000000** exacto.

### El puente amplifica diferencias que no deberían importar

**Dos procesos con la misma semilla no dan el mismo número.** Las diferencias en la pérdida son del
orden de 10⁻¹¹ —orden de reducción en punto flotante de la CPU— y aun así mueven el F1 de forma
visible.

La causa no está en el modelo sino en el puente: `etiquetar()` decide con desigualdades
**estrictas**, así que sobre una trayectoria pronosticada casi plana una diferencia mínima alcanza
para voltear la etiqueta. Está registrado en la D15, y es la razón por la que ninguna cifra del
avanzado se reporta como valor puntual.

---

## 7. Sobre el bloque de prueba: los dos modelos fallan en clases opuestas

Esto no aparece al mirar el F1 macro, y es lo más preciso que se puede decir del resultado final.

**Tabla.** F1 por clase extrema sobre el bloque de prueba, contra el piso del azar.

| Modelo | F1 Máximo | F1 Mínimo |
|---|---|---|
| `baseline_aleatorio` (el piso, D7) | 0,077778 | 0,044944 |
| `bosque_aleatorio_rezagos_relativos` | 0,046154 | **0,165746** |
| `chronos_bolt` | 0,062992 | 0,070707 |
| `itransformer` | **0,116071** | 0,032432 |

Dos lecturas que conviene no separar:

**Ningún modelo supera al azar en las dos clases extremas.** El bosque le gana holgadamente en
Mínimo y queda **por debajo del azar** en Máximo; el fundacional queda por debajo en Máximo; y el
avanzado queda por debajo en Mínimo. Es la forma más exacta del resultado negativo, y más severa que
mirar solo el F1 macro: no es que el sistema detecte poco, es que **ningún modelo detecta las dos
cosas que hay que detectar**.

**Y el único que supera al azar en Máximo es el avanzado**, que es el que pierde en F1 macro. La
clase donde el mejor modelo falla es justamente donde el modelo que el enunciado pedía no falla.
Decirlo importa en las dos direcciones: es un punto a favor del profundo que el F1 macro esconde, y
es la razón por la que promediar las dos clases en una sola métrica puede hacer parecer que un
modelo detecta cuando lo que hace es compensar.

No se saca de aquí ninguna configuración nueva ni se propone combinarlos: la sección 7 del protocolo
lo prohíbe y esto se reporta como lo que es, una lectura de la única corrida.

**Y hay que decir cuánto pesa esa advertencia, porque está medida.** El walk-forward de los nueve
tramos comprobó, sobre el bosque, que la asimetría entre las dos clases extremas **no es estable**:
el F1 de mínimos supera al de máximos en **5 de 9** tramos, que es lo que daría una moneda. En **dos**
de los nueve, una de las dos clases dio **0,000000** exacto — con menos de cien ejemplos por clase, la
métrica por clase puede colapsar entera.

Los modelos profundos **no se midieron por clase en los nueve tramos**, así que no hay forma de saber
si el patrón de esta tabla se repetiría. Lo que dice esta sección es qué pasó **en el bloque de
prueba**, que es la única estimación limpia que tenemos y también un solo bloque. Leerlo como una
propiedad de los modelos —«el avanzado detecta máximos y el bosque mínimos»— sería exactamente el
salto que la corrección de la sección de conclusiones tuvo que deshacer: de una diferencia medida a
una explicación que suena bien.

---

## 8. La celda que faltaba, y las tres lecturas escritas de antemano

Sobre el bloque de prueba se mide **una configuración por familia**, congelada antes de correr nada:
`chronos_bolt` por omisión y `itransformer` con lookback 96 y dimensión 64. Sin variantes.

Las tres lecturas posibles ya están escritas en la sección 6 del protocolo, **antes de conocer el
resultado**, y el informe reporta la primera y única cifra que salga en los tres casos. No hay una
cuarta rama en la que se busque otra configuración.

Dicho sin adornos: sobre validación **ninguno de los dos modelos de M3 supera al azar de forma
distinguible**, y el avanzado queda por debajo del bosque clásico en las cinco semillas.

**La expectativa se escribió antes y se cumplió.** Aquí decía que esperar que el bloque de prueba
mejorara lo de validación sería esperar que datos no vistos favorezcan a un modelo más que los datos
con los que se eligió. La corrida del 07/09 dio el mismo orden que validación, y de las tres
condiciones se cumplieron dos. Que la predicción incómoda se cumpliera no es un consuelo, pero sí es
la comprobación de que el criterio no se acomodó al resultado.

---

## 9. Cómo se regenera cada cifra

```bash
uv sync --group dev --group modelos

# Tabla de rendimiento y comparaciones pareadas
uv run python -m src.modelos.experimento --con-fundacional --con-avanzado

# Las seis metricas por semilla del avanzado
uv run python -m src.modelos.sensibilidad_avanzado

# Las dos rejillas
uv run python -m src.modelos.hiperparametros
uv run python -m src.modelos.hiperparametros_avanzado
```

| Evidencia | Qué contiene |
|---|---|
| `m3-modelos-profundos-4h-w7-h1.json` | Tabla de rendimiento, comparaciones pareadas, costos |
| `m3-sensibilidad-avanzado-completa-4h-w7-h1.json` | Seis métricas × cinco semillas × dos variantes |
| `m3-hiperparametros-fundacional-4h-w7-h1.json` | Las 18 celdas y la ganancia con su intervalo |
| `m3-hiperparametros-avanzado-4h-w7-h1.json` | Las 6 celdas y el veredicto de la D15 |
| `m3-inventario-tsfm.json`, `m3-inventario-avanzado.json` | Qué se pudo instalar y qué no |
