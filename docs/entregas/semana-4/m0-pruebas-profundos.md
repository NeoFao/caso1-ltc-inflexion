# Pruebas de detección sobre los modelos profundos

**Autor:** Fabrizio Espinoza (M0) · **Fuente del material:**
`docs/evidencias/pruebas-deteccion-profundos.json` · **Todas las cifras salen de
`docs/evidencias/`.**

El enunciado pide pruebas de detección en las semanas 3 **y** 4. Las de la Semana 3 se corrieron con
el **modelo clásico**, y durante un tiempo esta entrega dijo que repetirlas sobre los profundos sería
una mejora que no estaba hecha. **Ya está hecha, y esta sección la reporta.**

---

## 1. Qué se repitió, qué no, y con qué criterio

La **prueba 1** —el etiquetador solo, 187 de 187 vértices— **no se repite**: no interviene ningún
modelo, solo la función que etiqueta. Correrla con otro modelo mediría exactamente lo mismo.

Las **pruebas 2, 3 y 4** sí dependen del modelo, y se corrieron para los tres.

> **El criterio y la expectativa se escribieron antes de correr nada**, en el encabezado de
> `scripts/pruebas_deteccion_profundos.py`, y ese archivo se versionó **en un commit propio, sin
> resultados**, antes de la corrida. No es un detalle de forma: si el criterio se fijara después, la
> prueba no probaría nada.
>
> **El criterio** es el mismo que se le aplicó al clásico, sin aflojarlo: superar al
> `baseline_aleatorio` **de la misma corrida** en el F1 de **las dos** clases extremas.
>
> **La expectativa declarada fue que los dos profundos fallaran la 2 o la 3.** Se cumplió a medias, y
> la mitad que falló es la nuestra: **Chronos-Bolt pasó las tres.** Eso se cuenta en la sección 4.

El **modelo clásico entró como control del propio guion**: si hubiera dado algo distinto de lo que ya
dice `pruebas-deteccion.json`, el defecto estaría en el guion nuevo y no en los modelos. Dio
**idéntico** —0,540146 en sintético y 0,953353 en entrenamiento—, así que el instrumento es el mismo.

---

## 2. Los resultados

**Tabla 1.** Prueba 2 — el circuito completo sobre la serie construida, 442 observaciones evaluadas.

| Modelo | F1 macro | F1 Máximo | F1 Mínimo | ¿Supera? |
|---|---|---|---|---|
| `bosque_aleatorio` (control) | 0,540146 | 0,411765 | 0,333333 | **sí** |
| `chronos_bolt` | 0,526095 | 0,409091 | 0,254545 | **sí** |
| `itransformer` | 0,324180 | **0,000000** | 0,080000 | **no** |
| `baseline_aleatorio` | 0,308567 | 0,000000 | 0,000000 | — |

**Tabla 2.** Prueba 3 — sobre el bloque de entrenamiento, 9 165 observaciones.

| Modelo | F1 macro | F1 Máximo | F1 Mínimo | ¿Supera? |
|---|---|---|---|---|
| `bosque_aleatorio` (control) | 0,953353 | 0,961098 | 0,906414 | **sí** |
| `chronos_bolt` | 0,352284 | 0,050370 | 0,089157 | **sí** |
| `itransformer` | 0,351343 | 0,087452 | 0,067836 | **sí** |
| `baseline_aleatorio` | 0,331638 | 0,049704 | 0,037825 | — |

**Tabla 3.** Prueba 4 — las velas de a una frente al bloque entero, 200 velas.

| Modelo | Discrepancias | ¿Supera? |
|---|---|---|
| `bosque_aleatorio` | 0 | **sí** |
| `chronos_bolt` | 0 | **sí** |
| `itransformer` | 0 | **sí** |

---

## 3. La prueba 4 es la que más aporta, y es nueva para los profundos

Sobre el clásico, esta prueba comprobaba que el circuito se comporta igual vela a vela que por
bloques. Sobre los profundos comprueba algo que antes no estaba comprobado en ninguna parte.

**Los dos modelos profundos no leen sus datos de la tabla de características: los leen de la serie de
precios, por posición.** Chronos-Bolt toma los 512 cierres que terminan en la vela actual;
el iTransformer toma los 96 últimos de los seis activos. Ese acceso por posición es exactamente
donde una fuga entraría sin que ninguna métrica lo delatara: bastaría con que el contexto tomara
**una vela de más hacia adelante** para que los resultados subieran y siguieran pareciendo normales.

**Cero discrepancias en los tres.** Las predicciones de a una son idénticas a las del bloque, así que
el contexto de los dos profundos es **causal**.

> **Se simularon 200 velas y no las 500 del clásico**, porque Chronos-Bolt infiere vela a vela sobre
> el panel completo. No cambia lo que la prueba responde: **una sola discrepancia la haría fallar**, y
> no hubo ninguna.

---

## 4. Lo que estas pruebas dicen, incluido lo que nos corrigió

### Chronos-Bolt pasa las tres, y no lo esperábamos

La expectativa escrita era que los dos profundos fallaran la prueba 2 o la 3. **Chronos-Bolt pasó las
tres**, y en la sintética casi empata con el clásico: **0,409091** contra **0,411765** en el F1 de
máximos.

Eso acota una afirmación que esta entrega hace en otra sección. Que el fundacional no supere al azar
*de forma distinguible sobre validación* con 1 959 observaciones **no es lo mismo** que no detectar:
sobre una serie donde la señal existe por construcción, detecta, y casi tan bien como el bosque.

**Y hay que decir por dónde pasa raspando.** En el bloque de entrenamiento su F1 de máximos es
**0,050370** contra **0,049704** del azar: cumple el criterio por **0,000666**. Cumplirlo por seis
diezmilésimas es cumplirlo, y también es el tipo de margen que no se debe presentar como holgura.

### El iTransformer falla la 2, y el modo en que falla señala dónde está el problema

No falla por quedar por debajo del azar. Falla con un **F1 de máximos de exactamente 0,000000**:
sobre la serie construida **no identifica un solo máximo**. El azar también da 0,000000 ahí, así que
el criterio —que exige superarlo **estrictamente**— no se cumple por un empate en cero. Mínimos sí
los detecta, 0,080000 contra 0,000000.

> **Aquí había una explicación nuestra que resultó ser falsa, y la desmontó M3 midiendo.**
>
> Esta sección decía que una trayectoria suave **nunca produce un máximo estricto**, y que por eso
> el resultado era cero máximos. Sonaba bien y no se había comprobado.
>
> **El iTransformer predice 29 máximos** sobre esas 442 velas, y **36 mínimos**, que exigen las
> mismas catorce desigualdades. **El puente sí produce extremos estrictos.** Lo que pasa es otra
> cosa: **ninguno de los 29 cae sobre un máximo real.**

**Tabla 4.** Dónde caen los máximos que cada modelo anuncia, sobre 14 máximos reales.

| Modelo | Máximos predichos | Exactos | A una vela o menos |
|---|---|---|---|
| `bosque_aleatorio` | 54 | **14** | **38** |
| `chronos_bolt` | 30 | 9 | 21 |
| `itransformer` | 29 | **0** | **1** |

*Nota.* Medido por M3 en `docs/evidencias/m3-desfase-puente-sintetico.json`, reproduciendo la prueba
2 con las funciones de este mismo guion y **deteniéndose si el F1 recalculado no coincidiera con el
publicado**. Coincidió en los tres modelos.

**Lo que la medición sí sostiene** es más preciso y más útil que lo que habíamos escrito: los fallos
del bosque y de Chronos **caen cerca del giro** —38 de 54 y 21 de 30 a una vela o menos— y los del
iTransformer **no**: **1 de 29**. Marca giros, pero lejos, y tiende a marcarlos **después** del real.

**Y una cautela sobre el propio cero.** Con **14 máximos reales**, acertar cero contra acertar dos no
son situaciones distinguibles. El F1 de 0,000000 es exacto como cifra, pero **no autoriza a decir
«nunca»**: autoriza a decir que no acertó ninguno de catorce.

> **Por qué se cuenta el error en vez de corregirlo en silencio.** Porque la explicación falsa era
> **nuestra y cómoda**: cerraba la sección con una causa elegante. La medición que la desmonta la
> pidió M0 y la hizo M3 sobre su propio módulo, buscando confirmarla. Es el mismo patrón que las
> cuatro limitaciones de la sección 6: lo que corrige este informe aparece **midiendo**, no
> revisando la redacción.

### Lo que no dicen

**Ninguna de las tres mide si el sistema sirve.** La 2 y la 3 usan datos construidos o ya vistos; la
4 no mide rendimiento en absoluto, mide coherencia. El rendimiento sobre datos no vistos está en la
comparación sobre validación, y la medición única sobre el bloque de prueba en la Semana 5.

Y **nada de esto tocó el bloque de prueba**, que se midió una sola vez el 07/09 y cuya cifra el
informe reporta sin cambios. Estas pruebas son sintético, entrenamiento y validación: datos que sí se
pueden volver a mirar.

---

## 5. Reproducirlo

```bash
uv run python scripts/pruebas_deteccion_profundos.py
```

Necesita el entorno con `torch` y `chronos`. Deja la constancia completa —con el criterio y la
expectativa escritos antes— en `docs/evidencias/pruebas-deteccion-profundos.json`.
