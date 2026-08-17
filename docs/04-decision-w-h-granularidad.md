# Decisión de `w`, `h` y granularidad

**Estudio y justificación** — 17 de agosto de 2026

Reproducible con `uv run python scripts/estudio_w_h_granularidad.py`.
Números en [`docs/evidencias/estudio-w-h.json`](evidencias/estudio-w-h.json).

---

## Resumen

| Parámetro | Valor | Se decidió por |
|---|---|---|
| Granularidad | **4 horas** | Es la única con suficientes ejemplos de las clases raras |
| `w` | **7** | El mayor que cumple el piso acordado antes de medir |
| `h` | **1** | La información sobre el objetivo cae 4,2× al pasar de h=1 a h=3 |

**`h = 1` corrige la recomendación previa de `h = 5`**, que se había elegido por criterio y no por medición. La medición apunta al lado contrario.

---

## 1. Granularidad: por qué 4 horas

El criterio se fijó **antes** de medir, para no justificar lo que ya queríamos:

> Se elige la combinación que deje **al menos 300 ejemplos de la clase minoritaria en el conjunto de entrenamiento**.

Razón del piso: con menos ejemplos, un modelo no tiene de dónde aprender la clase que importa. El valor de 300 es una propuesta del equipo, no un umbral de la literatura, y así se reporta.

| `w` | Velas diarias | Velas de 4 h |
|---|---|---|
| 3 | 149 ✗ | 884 ✓ |
| 5 | 97 ✗ | 557 ✓ |
| 7 | 67 ✗ | **420 ✓** |
| 10 | 53 ✗ | 299 ✗ |
| 15 | 32 ✗ | 189 ✗ |

Con velas diarias **ninguna** combinación llega. El mejor caso es la mitad del piso.

Las dos granularidades cubren **exactamente el mismo período**: del 11 de agosto de 2020 al presente. La ventana la limita Solana, que es la de listado más reciente, y un panel multivariante exige que las seis series existan a la vez. Bajar la granularidad no añade historia; **subdivide la que hay**: de 2 185 observaciones a 13 114.

**Lo que se pierde.** Las velas de 4 h incorporan más ruido de microestructura y son menos legibles en una figura. Es un costo aceptado a cambio de que las clases raras tengan representación suficiente.

---

## 2. `w`: por qué 7

`w` es la ventana a cada lado que define si una vela fue un giro. Hay una tensión directa:

- `w` pequeño detecta muchos giros, y muchos son ruido de mercado.
- `w` grande detecta solo giros estructurales, pero deja poquísimos ejemplos.

Existe además una **cota aritmética**: dos máximos no pueden estar a menos de `w+1` velas, porque cada uno caería en la ventana del otro y cada uno tendría que ser mayor que el otro. Por lo tanto, a lo sumo 1 de cada `w+1` velas puede ser máximo. Con `w=7` el techo teórico es 12,5 % y lo medido es 4,63 %.

La regla acordada fue **el mayor `w` que cumpla el piso**, porque un `w` grande produce etiquetas más significativas. Sobre el panel de 4 horas eso da **`w = 7`**, con 420 ejemplos.

Que `w = 10` quede en 299 —uno por debajo— es casualidad, pero muestra que el criterio discriminó de verdad en lugar de aprobar cualquier cosa.

---

## 3. `h`: la decisión que hubo que rehacer

`h` es cuántas velas hacia adelante se pronostica. **No afecta el balance de clases**: es un desplazamiento del objetivo, no un cambio en su definición. Los 420 ejemplos son los mismos para `h = 1`, `3` o `5`.

Eso significa que el criterio de la sección 1 **no lo discrimina**, y la elección inicial de `h = 5` se hizo por juicio: más anticipación es más útil y parecía no costar nada.

### Primer intento de medirlo, que falló

Se midió un baseline de persistencia —predecir que la etiqueta de `t+h` será la de `t`— esperando que se degradara al alejar el horizonte. No se degradó: el F1 macro se mantuvo entre 0,28 y 0,33 para todo `h`.

La explicación es que, con las clases tan desbalanceadas, ese baseline responde casi siempre «Continuidad» y se comporta como el baseline trivial sin importar `h`. El experimento no discriminó, pero deja un dato propio: **la etiqueta actual no informa sobre la futura a ninguna distancia**.

### La medición que sí discriminó

Se calculó la **información mutua** entre las características disponibles en `t` y la etiqueta en `t+h`, sobre el conjunto de entrenamiento:

| `h` | Información mutua media |
|---|---|
| **1** | **0,004606** |
| 3 | 0,001094 |
| 5 | 0,000821 |
| 8 | 0,000949 |
| 12 | 0,000976 |

La caída de `h=1` a `h=3` es de **4,2 veces**, y a partir de ahí la curva se aplana. El patrón se repite en las cuatro configuraciones medidas —dos granularidades por dos valores de `w`—, y esa consistencia es lo que lo hace creíble.

**Interpretación:** lo observable en `t` informa sobre la vela inmediatamente siguiente y prácticamente nada más allá. Predecir a `h = 5` con estas características sería pronosticar sobre algo que los datos no anticipan.

### Advertencia honesta sobre este resultado

El **nivel absoluto** de información mutua es bajo para todo `h`, incluido `h = 1`. Lo que se interpreta es la **forma** de la curva, no su magnitud. Y esa magnitud pequeña es en sí misma un aviso: el problema es difícil con las características actuales, y conviene decirlo en el reporte final antes de que lo pregunten.

---

## 4. Lo que hay que reportar sobre la anticipación real

La anticipación efectiva del sistema **no es `h`**: es `h + w`. Para saber si la vela `t+h` fue un máximo hay que observar las `w` posteriores.

Con `w = 7` y `h = 1` son **8 velas de 4 horas, es decir 32 horas**. Reportar «predice una vela adelante» sin aclarar esto sería engañoso.

---

## 5. Cuándo se aplica

El cambio de valores en `contracts/config.py` **no se aplicó antes de la entrega de la Semana 1**, por dos razones:

1. Ningún argumento del marco teórico depende de estos valores. La estacionariedad, la autocorrelación, la correlación cruzada y la volatilidad se calculan sobre precios y retornos, no sobre etiquetas.
2. La sección de criptoactivos y métricas ya estaba redactada citando `w = 5` sobre velas diarias, y declarándolo explícitamente. Reescribirla horas antes de entregar introduciría más riesgo de error que beneficio.

Por el enunciado, la **extracción de datos y la definición del pipeline son entregables de la Semana 2**, que es donde corresponde aplicar y documentar esta decisión.

**Para aplicarla:** editar `contracts/config.py` con `GRANULARIDAD = "4h"`, `VENTANA_W = 7`, `HORIZONTE_H = 1`, `PROVISIONAL = False`, y regenerar:

```bash
uv run python scripts/figuras_marco_teorico.py && npm run ensamblar --prefix scripts
```
