# Guía de Alejandro — M2 · Etiquetado, sintéticos y características

## Qué es tuyo

```
src/features/        ingeniería de características
src/sintetico/       generador de series con giros conocidos
```

**Qué no tocás:** `contracts/`, `src/panel/`, `src/diagnostico/`, `src/modelos/`, `src/api/`, `app/`.

Ojo con una cosa: **`contracts/labeling.py` no es tuyo aunque el etiquetado sea tu tema.** Es un contrato, y lo consumen los cuatro módulos. Si creés que está mal, lo decís y se discute; no lo editás.

## Tu papel en una frase

Sos el que convierte precios en algo de lo que un modelo puede aprender. Si tus características no aportan, no hay modelo que salve el proyecto.

Y sos el dueño de la única prueba del proyecto donde la verdad no está en discusión: las series sintéticas.

---

## Lo primero: entendé la trampa

Toda tu carpeta se rige por una sola regla:

> **Una característica en el instante `t` solo puede usar información hasta `t`.**

Suena obvio. No lo es. Ejemplos reales de cómo se rompe sin querer:

| Lo que escribís | Por qué está mal |
|---|---|
| `serie.rolling(11, center=True).mean()` | La ventana centrada incluye 5 velas del futuro |
| `serie.shift(-1)` | Trae el valor de mañana |
| `serie.fillna(method="bfill")` | Rellena hacia atrás: copia un precio futuro sobre un instante pasado |
| `scaler.fit(todo_el_dataset)` | El escalador aprende la media y la desviación de datos de prueba |

El problema es que estos errores **no se notan**: producen métricas excelentes y un sistema inservible. Es el riesgo R4 del PRD y el peor de todos.

Por eso hay una prueba automática. Antes de meter cualquier característica nueva al pipeline:

```python
from src.evaluacion.fuga import verificar_sin_fuga
from src.features.base import construir

verificar_sin_fuga(construir, panel)
```

Si no lanza nada, tu función no mira al futuro. Si lanza `FugaDetectada`, te dice exactamente qué columna y en qué fila.

Probá cómo se siente que falle — vale la pena ver la máquina funcionando:

```bash
uv run pytest tests/test_fuga.py -v
```

---

## Semana 1 — cuatro tareas

### T2.1 — Medí a qué nivel de ruido se rompe el etiquetador

**Por qué:** es un resultado que nadie tiene y que vale oro en la exposición. El etiquetador encuentra los giros perfectamente en una serie limpia. ¿Y con ruido? ¿Cuánto ruido tolera antes de empezar a inventar giros que no existen?

Esto responde de antemano la pregunta incómoda: *"¿cómo saben que sus etiquetas no son ruido?"*

**Qué hacer:** `serie_zigzag()` en `src/sintetico/generador.py` acepta un parámetro `ruido`. Con `ruido=0` los giros son exactamente los vértices que pusimos. Subí el ruido de a poco y medí qué fracción de los vértices verdaderos sigue detectando el etiquetador, y cuántos giros falsos aparece.

```python
from src.sintetico.generador import serie_zigzag
from contracts.labeling import etiquetar

serie, giros_verdaderos = serie_zigzag(n=800, w=7, semilla=0, ruido=0.5)
etiquetas = etiquetar(serie, w=7)
```

**Criterio de aceptación:** una tabla con niveles de ruido contra (giros detectados / giros verdaderos) y giros falsos, más una figura. El número que buscás es el ruido a partir del cual la detección se degrada.

**Decilo bien en el documento:** esta serie la construiste vos. No es lo que pasa en LTC. Es un experimento controlado para caracterizar la sensibilidad del etiquetado, y hay que presentarlo como tal.

### T2.2 — Indicadores técnicos

**Por qué:** el enunciado los pide explícitamente (RF-F1), y son las características con más historia en este dominio.

**Qué hacer:** agregá a `src/features/base.py` al menos: medias móviles simple y exponencial, RSI, MACD, y bandas de Bollinger. Todos con ventanas hacia atrás.

Seguí el patrón que ya está en el archivo — mirá cómo están escritas `retornos()` y `volatilidad()` y copiá la forma.

**No agregues `ta-lib` ni `pandas-ta` sin justificarlo.** Un RSI son seis líneas de pandas, y una dependencia nueva es una decisión, no un detalle. Si querés meter una librería, traé el argumento de qué hace que no podamos hacer nosotros.

**Criterio de aceptación:** las características nuevas están en `construir()`, `verificar_sin_fuga()` pasa, y hay una figura que muestra un indicador sobre el precio para que se vea que está bien calculado.

### T2.3 — Características de ventana deslizante

**Por qué:** RF-F1 pide cuatro familias y esta falta.

**Qué hacer:** estadísticos sobre ventanas móviles del cierre y de los retornos: mínimo, máximo, rango, posición del precio actual dentro del rango de la ventana, asimetría, curtosis.

La **posición dentro del rango** es la más prometedora para este problema concreto: un precio cerca del máximo de sus últimas 20 velas está estructuralmente más cerca de ser un máximo local. Vale la pena que la midas y la comentes.

### T2.4 — Tu sección teórica

Criptoactivos: definición, características principales, tipos, mercado cripto, factores que afectan el precio, correlación y dependencia entre activos. Más: definición de punto de inflexión y cómo encontrarlos.

Para la parte de punto de inflexión, tenés material propio: el documento [`docs/00-definicion-punto-inflexion.md`](../docs/00-definicion-punto-inflexion.md) y tus mediciones de T2.1.

---

## Semanas 2 a 5

- **Semana 2:** escalado (RF-F3 — el escalador se ajusta **solo** con datos de entrenamiento) y la sección del pipeline en el documento.
- **Semana 3:** medición de importancia de características (RF-F4). Cuáles aportan y cuáles no, con número.
- **Semana 4:** ablaciones. Qué pasa con el F1 si sacás la familia de correlación cruzada — eso mide si el enfoque multivariante del enunciado realmente sirve, y es de lo mejor que podés llevar al reporte final.
- **Semana 5:** tu parte del reporte.

---

## Un dato que ya está medido y te ahorra tiempo

Con el panel de 4 horas y `w=7`, la clase minoritaria tiene **420 ejemplos en entrenamiento**. Con `w=10` bajan a 299. No son muchos.

Eso significa que **más características no es mejor**. Con 420 ejemplos de una clase, meter 200 columnas garantiza sobreajuste. Tu trabajo no es generar todas las características posibles: es generar las que aportan y demostrar cuáles son.

---

## Si te trabás

- **`verificar_sin_fuga` falla y no entendés por qué:** el mensaje dice la columna y la fila. Mirá esa función en aislamiento y preguntate qué información usa.
- **No sabés si una característica tiene sentido financiero:** preguntá antes de escribirla. Es más barato.
- **Más de un día trabado:** decilo.
