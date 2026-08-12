# Semana 1 — Marco teórico

**Entrega: martes 18 de agosto. Documento, no presentación.**

El profesor fue explícito: *"Presentación no, tiene que ser documento para avanzar en documento"*. Nadie hace láminas esta semana.

---

## Qué entrega cada uno

| Archivo | Quién | Puntos del enunciado |
|---|---|---|
| [`m1-series-temporales.md`](m1-series-temporales.md) | Jose Pablo | Los 8 de series de tiempo |
| [`m2-criptoactivos.md`](m2-criptoactivos.md) | Alejandro | Los 8 de criptoactivos |
| [`m2-metricas.md`](m2-metricas.md) | Alejandro | El 9.º: métricas de evaluación |

Fabrizio los une, unifica la voz y entrega.

**Corte: jueves 13.** Deja un día de margen. Si el jueves falta una sección, se avisa el jueves, no el lunes siguiente.

---

## La evidencia ya está generada

No tienen que producir las figuras: ya existen. Su trabajo es **escribir el análisis alrededor de ellas**.

```bash
uv run python scripts/figuras_marco_teorico.py
```

Deja en [`docs/evidencias/`](../../evidencias/):

| Archivo | Para qué punto |
|---|---|
| `mt-01-serie-temporal.png` | Definición de serie temporal |
| `mt-02-componentes.png` | Componentes: tendencia, estacionalidad, residuo |
| `mt-03-estacionariedad.png` + los dos `.csv` | Estacionariedad y no estacionariedad |
| `mt-04-volatilidad.png` | Volatilidad |
| `mt-05-heterocedasticidad.png` | Heterocedasticidad |
| `mt-06-autocorrelacion.png` | Autocorrelación |
| `mt-07-correlacion.png` + `.csv` | Correlación cruzada |
| `mt-08a-giros-construidos.png` · `mt-08b-giros-ltc.png` | Punto de inflexión y cómo encontrarlos |
| `mt-09a-balance-clases.png` · `mt-09b-confusion-baseline.png` | Métricas de evaluación |
| **`marco-teorico.json`** | **Todos los números medidos, para citar sin recalcular** |

---

## El patrón que hay que seguir en cada concepto

El profesor pidió construir series sintéticas con volatilidad y correlación controladas. La razón no es decorativa:

> **Primero la serie construida, donde la respuesta correcta la pusimos nosotros. Después LTC real.**

Así el lector ve que el método detecta lo que tiene que detectar **antes** de creerle sobre datos donde nadie sabe la verdad. Eso es exactamente lo que pide el criterio de Análisis de la rúbrica: relacionar el concepto con su aplicación mediante un ejemplo práctico.

Las figuras ya vienen pareadas así.

---

## Reglas de escritura

1. **Ningún número que no esté en `marco-teorico.json` o que no hayas medido vos.** Si necesitás uno que no está, corré el script y agregalo; no lo estimes.
2. **Toda figura lleva número, pie, y se menciona en el texto.** Una figura que aparece sin que el texto la nombre resta en Estructura y redacción.
3. **Las series construidas se declaran como tales en el pie.** No son Litecoin y no dicen nada del mercado.
4. **Citas en APA.** Es un criterio entero de la rúbrica, vale lo mismo que todo el contenido técnico.
5. **Escribí el porqué, no solo el qué.** "El p-valor es 0.179" es un dato; "no podemos rechazar la raíz unitaria, lo que es compatible con una serie no estacionaria, y por eso las características se construyen sobre retornos" es análisis.

---

## Advertencia sobre los números que dependen de `w`

`contracts/config.py` todavía dice `PROVISIONAL = True`, con `w=5`, `h=3` y velas diarias. La medición recomienda `w=7` y velas de 4 horas.

**Los números que NO cambian si se congela otro valor** — porque son sobre precios y retornos, no sobre etiquetas:

- Estacionariedad (ADF), autocorrelación, correlación cruzada, volatilidad, componentes.

**Los que SÍ van a cambiar:**

- Balance de clases, métricas del baseline, cantidad de puntos de inflexión detectados.

Escriban esos últimos citando el valor de `w` usado, así: *"con w = 5 sobre velas diarias, ..."*. Cuando se congele, se regeneran las figuras con un comando y solo hay que actualizar los números, no reescribir el argumento.
