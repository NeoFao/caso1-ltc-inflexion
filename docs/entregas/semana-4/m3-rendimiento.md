# Rendimiento comparado y lo que no se puede afirmar

**Autor:** Isaac Fallas (M3) · **Ensamblado por** Fabrizio Espinoza (M0) desde la sección
de M3 del informe final, sin reescribir su contenido. **Todas las cifras salen de
`docs/evidencias/`.**

---

## Rendimiento sobre validación

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

- Sobre **este bloque**, ninguno de los dos modelos profundos supera al `baseline_aleatorio` de
  forma distinguible: le ganan en la media y el intervalo incluye el cero. **Esa lectura cambió al
  medir con más potencia**, y hay que decirlo aquí para que la tabla no se lea sola: sobre las 7 311
  filas agregadas de los nueve tramos, **Chronos-Bolt sí supera al azar** —+0,027769, intervalo
  [0,011976 , 0,045189], que excluye el cero— mientras que el **iTransformer sigue sin superarlo**
  —+0,006386, intervalo [−0,008267 , 0,019878]— **ni con cuatro veces más observaciones**. Lo que
  era «ninguno de los dos» resultó ser uno de cada.
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

---

## Lo que no se puede afirmar, y por qué

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

---

## Por clase: lo que el bloque de prueba sugirió y lo que la potencia confirmó

Aquí hay dos mediciones y **la segunda corrige a la primera**. Van juntas porque la diferencia entre
ellas es el hallazgo, no un detalle de método.

### Lo que se vio en el bloque de prueba

**Tabla 1.** F1 por clase extrema sobre el bloque de prueba, contra el piso del azar.

| Modelo | F1 Máximo | F1 Mínimo |
|---|---|---|
| `baseline_aleatorio` (el piso, D7) | 0,077778 | 0,044944 |
| `bosque_aleatorio_rezagos_relativos` | 0,046154 | **0,165746** |
| `chronos_bolt` | 0,062992 | 0,070707 |
| `itransformer` | **0,116071** | 0,032432 |

Leído solo, dice que **ningún modelo supera al azar en las dos clases** y que el bosque queda por
debajo del azar en Máximo. Con 86 ejemplos por clase, esa lectura era la más severa posible del
resultado.

### Lo que dice la agregación de los nueve tramos

Sobre **7 311 filas**, con intervalo pareado en cada celda:

**Tabla 2.** Diferencia contra el azar por clase, y si el intervalo excluye el cero.

| Modelo | Máximo | ¿Excluye el cero? | Mínimo | ¿Excluye el cero? |
|---|---|---|---|---|
| Bosque | +0,043611 | **sí** | +0,048673 | **sí** |
| Chronos-Bolt | +0,025181 | no | +0,045992 | **sí** |
| iTransformer | +0,034007 | **sí** | +0,003412 | no |

**El bosque sí supera al azar en las dos clases.** Lo que parecía el resultado más severo del informe
—que ninguno detectara las dos— era un **artefacto de tener 86 ejemplos por clase**, no un hecho
sobre los modelos. Con cuatro veces más observaciones, la clase Máximo del bosque pasa de estar por
debajo del azar a superarlo con intervalo que excluye el cero.

**Lo que sí sobrevive, y ahora con intervalo:** los dos modelos profundos detectan **clases
opuestas**. El iTransformer supera al azar en Máximo y no en Mínimo; Chronos-Bolt, al revés. No es la
lectura de un bloque: se sostiene con potencia.

### Por qué esto importa más allá de la tabla

Es la segunda vez en este informe que una lectura por clase sobre un solo bloque no aguanta al
volver a medirla —la primera fue la asimetría picos/valles, **5 de 9** tramos— y las dos veces el
tamaño de la clase rara fue la causa. En **dos** de los nueve tramos una de las dos clases dio
**0,000000** exacto: con menos de cien ejemplos, la métrica por clase puede colapsar entera.

**La lección es del método y es reutilizable:** una métrica por clase sobre 86 ejemplos no distingue
un modelo que no detecta de uno que no tuvo con qué demostrarlo. Y como la regla de decisión del
proyecto miraba el F1 macro, no habría atrapado ninguna de las dos cosas — ni el falso negativo por
clase, ni que un modelo compense una clase con la otra.

No se saca de aquí ninguna configuración nueva ni se propone combinar modelos: la sección 7 del
protocolo lo prohíbe, y la cifra oficial sigue siendo la del bloque de prueba.

---

---

## Cómo se regenera cada cifra

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
