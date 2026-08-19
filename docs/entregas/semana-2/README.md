# Semana 2 — Modelos y procedimiento

**Vence el martes 25 de agosto a las 13:00. Documento, no presentación. Se permiten varios envíos.**

---

## Qué pide la asignación, textual

**Marco teórico Modelos Estadísticos y de Machine Learning para Series Temporales**

1. Modelos fundacionales de series de tiempo (TSFMs)
2. VTA (Verbal Technical Analysis)
3. FinLSPM (Large Stock Predict Model)
4. CryptoMamba
5. Transformer

**Justificar elección de modelo**

> **Ojo con dos cosas.** La página de la asignación añade **Transformer**, que no
> estaba en la tabla semanal del enunciado original, y añade **justificar la
> elección de modelo**. Y la tabla del enunciado incluía además el **marco teórico
> del procedimiento** —los ocho pasos, de extracción de datos a evaluación—, que la
> página no menciona. Lo incluimos igual: si sobra no resta, y si el profesor lo
> esperaba, no llegar sin él.

---

## Quién entrega qué

| Archivo | Quién | Puntos |
|---|---|---|
| [`m3-modelos.md`](m3-modelos.md) | Isaac | Los 5 modelos + la justificación |
| [`m0-procedimiento.md`](m0-procedimiento.md) | Fabrizio | Los 8 pasos del procedimiento |
| [`m0-introduccion.md`](m0-introduccion.md) · [`m0-conclusion.md`](m0-conclusion.md) | Fabrizio | Marco y cierre |

Alejandro y Jose Pablo tienen tareas de código este sprint (#20, #35, #19), no de
documento. Si su trabajo produce un número citable, va a `docs/evidencias/` y se
cita desde aquí.

**Corte: sábado 22.** Deja tres días de margen.

---

## Evidencia que ya existe y hay que citar

**No hay que volver a medir nada de esto.** Isaac lo produjo en el Sprint 1 y está
verificado.

| Archivo | Qué contiene |
|---|---|
| [`m3-inventario-tsfm.json`](../../evidencias/m3-inventario-tsfm.json) | Los tres candidatos fundacionales medidos en CPU: disco, RAM pico, segundos por ventana y extrapolación al bloque de validación |
| [`m3-spike-cryptomamba.json`](../../evidencias/m3-spike-cryptomamba.json) | Por qué CryptoMamba no se puede instalar sin CUDA, con el error exacto |
| [`modelo-clasico-4h-w7-h1.json`](../../evidencias/modelo-clasico-4h-w7-h1.json) | El modelo clásico de referencia contra los tres baselines |

---

## El contrato ya está congelado

`contracts/config.py` dejó de estar `PROVISIONAL` el 18 de agosto:

```
GRANULARIDAD = "4h"    VENTANA_W = 7    HORIZONTE_H = 1
```

**Todo número nuevo se mide con esos valores.** Los de la Semana 1 se midieron con
velas diarias y `w = 5`, y así quedan declarados en aquel documento; no se
regeneran. Si una sección de esta entrega compara con un número de la anterior, hay
que decir con qué configuración se midió cada uno.

---

## Reglas de escritura

Las mismas de la Semana 1, que funcionaron:

1. **Ningún número que no salga de `docs/evidencias/` o que no hayas medido vos.**
   Si hace falta uno que no está, se corre el script y se agrega; no se estima.
2. **Toda figura y toda tabla llevan número, pie y mención en el texto.**
3. **Lo construido por nosotros se declara como tal** en el pie.
4. **Citas en APA 7**, con DOI. Se verifican con
   `uv run python scripts/verificar_referencias.py docs/entregas/semana-2/*.md`.
5. **Escribí el porqué, no solo el qué.** Un dato es un dato; el análisis es decir
   qué decisión del proyecto se sigue de él.
6. **Lo que no se midió se declara como no medido**, en la misma frase.

---

## Cómo se arma el entregable

```bash
uv run python scripts/verificar_numeros.py
```

```bash
CARPETA_ENTREGA=semana-2 npm run ensamblar --prefix scripts
```

El ensamblador avisa qué bloques quedan sin redactar y renumera figuras y tablas de
corrido entre archivos. **Antes de entregar hay que abrir el `.docx`, seleccionar el
índice y pulsar F9**, o sale en blanco.
