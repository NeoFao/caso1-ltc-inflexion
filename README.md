# Pronóstico de puntos de inflexión en el precio de Litecoin

Caso N.º 1 — Señales y Sistemas — 3.er Trimestre 2026
Entrega final: 8 de septiembre de 2026

Clasificación multiclase de puntos de inflexión (Máximo / Mínimo / Continuidad) en el precio de LTC, usando como variables de apoyo BTC, ETH, SOL, XRP y ADA.

---

## Arrancar en tres comandos

```bash
pip install uv
```

```bash
uv sync --group dev
```

```bash
uv run pytest
```

Si las pruebas pasan, tu entorno está bien y podés empezar. `uv` descarga el Python correcto solo, no hace falta instalarlo aparte.

**Después, leé tu guía**: [`guias/`](guias/) tiene una por persona, con el paso a paso de lo que te toca.

---

## Qué hay medido (no supuesto)

Ejecutado el 5 de agosto de 2026 con `scripts/spike_datos.py`. Los números completos están en [`docs/evidencias/`](docs/evidencias/).

| | Velas diarias | Velas de 4 horas |
|---|---|---|
| Ventana común a las 6 criptos | 2020-08-11 → 2026-08-04 | 2020-08-11 → 2026-08-05 |
| Observaciones del panel | 2 185 | 13 114 |
| Activo que limita la ventana | SOL (listado 2020-08-11) | SOL |
| Máximos con w=7 | 4,47 % | 4,63 % |
| Ejemplos de clase minoritaria en entrenamiento (w=7) | 67 | 420 |
| ¿Cumple el piso de 300 acordado? | **No, en ninguna combinación** | Sí, hasta w=7 |

Por eso el panel de trabajo es el de 4 horas. La granularidad diaria no da suficientes ejemplos de las clases que importan, y eso se midió antes de escribir una línea de modelo.

**Los valores de `w` y `h` siguen marcados como PROVISIONAL en [`contracts/config.py`](contracts/config.py).** La medición recomienda `w=7`, pero la decisión es del equipo. El contexto para decidir está en [`docs/00-definicion-punto-inflexion.md`](docs/00-definicion-punto-inflexion.md).

---

## Cómo está partido el trabajo

Nadie comparte tarea con nadie. Cada quien tiene sus carpetas y nadie edita archivos ajenos sin avisar por escrito.

| Módulo | Responsable | Carpetas propias |
|---|---|---|
| **M0** Infraestructura, contratos, evaluación, backend, integración | Fabrizio Espinoza | `contracts/` `src/panel/` `src/evaluacion/` `src/api/` `scripts/` |
| **M1** Datos, diagnóstico y aplicación web | Jose Pablo Monestel | `src/diagnostico/` `src/visual/` `app/` |
| **M2** Etiquetado, series sintéticas y características | Alejandro Zamora | `src/features/` `src/sintetico/` |
| **M3** Modelo fundacional y modelo avanzado | Isaac Morun | `src/modelos/` |

El detalle completo — alcance, requisitos numerados, riesgos y plan semanal — está en el [PRD](docs/01-prd.md).

---

## Los contratos

`contracts/` es la razón por la que se puede trabajar en paralelo sin pisarse. Son definiciones que varios módulos consumen y **nadie cambia por su cuenta**.

| Archivo | Qué fija |
|---|---|
| [`config.py`](contracts/config.py) | Activos, granularidad, `w`, `h`, umbrales de decisión |
| [`schema.py`](contracts/schema.py) | Columnas exactas del panel y su validación |
| [`labeling.py`](contracts/labeling.py) | La función que asigna Máximo / Mínimo / Continuidad |
| [`splits.py`](contracts/splits.py) | Partición temporal fija, con embargo entre bloques |
| [`metrics.py`](contracts/metrics.py) | Precisión Direccional, F1 macro, F1 por clase, confusión |

**Para cambiar un contrato:** se propone por escrito con la razón y qué se rompe, lo aprueban el PM y quien lo consume, se cambia en un solo lugar y se vuelve a correr todo.

---

## Comandos que vas a usar

```bash
uv run pytest -q
```

```bash
uv run ruff check .
```

```bash
uv run python scripts/spike_datos.py --intervalo 4h --sin-descargar
```

```bash
uv run uvicorn src.api.main:app --reload --port 8000
```

---

## Reglas que no se negocian

1. **Ningún número que no hayas obtenido ejecutando.** Ni conteos, ni porcentajes, ni tiempos. Si no lo corriste, escribí "no lo he medido".
2. **Ninguna conclusión a partir de una salida cortada.** Si un log se truncó, pedilo de nuevo.
3. **Verificá la fecha de todo artefacto** antes de usarlo como evidencia. Las figuras se guardan con su `.generado.txt` al lado justamente por esto.
4. **Distinguí lo medido de lo construido.** Una serie sintética que armaste vos no es lo que está pasando en los datos reales.
5. **Decí en la misma frase lo que no está verificado.** "Corre" y "funciona" no son lo mismo.
6. **Fijá el criterio antes de mirar el resultado.** Si no, se llama justificar lo que ya querías hacer.
7. **Una tarea está terminada** cuando hay código, evidencia medida, sección del documento y slide. Las cuatro.

---

## Documentos

| | |
|---|---|
| [PRD](docs/01-prd.md) · [versión Word](docs/) | Qué construimos, alcance, requisitos, riesgos, plan |
| [Definición del punto de inflexión](docs/00-definicion-punto-inflexion.md) | Qué son `w` y `h`, por qué importan, y la consulta al profesor |
| [`docs/evidencias/`](docs/evidencias/) | Mediciones y figuras, todas regenerables |
| [`docs/entregas/`](docs/entregas/) | Los cinco entregables semanales |
