# Pronóstico de puntos de inflexión en el precio de Litecoin

Caso N.º 1 — Señales y Sistemas — 3.er Trimestre 2026
Tecnologías de la Información y Comunicación Empresarial · Universidad Invenio
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

### Lo que la medición NO respalda, y hay que decirlo en el informe

El planteamiento del caso supone que BTC, ETH, SOL, XRP y ADA dicen algo sobre los puntos de inflexión de LTC. **Medido, no se puede afirmar que aporten.** Sobre el bosque de M3 y validación, con rezagos relativos, la diferencia entre usar los seis activos y usar solo LTC es de **+0,0090** en F1 macro: su intervalo de confianza del 95 % incluye el cero, está por debajo del umbral de decisión de 0,02, y cambia de signo al reentrenar con otra semilla.

No invalida el proyecto —cambia la conclusión, no el método—, pero **ninguna sección puede afirmar que los activos de apoyo aportan**. El estudio completo, y por qué la cifra de la ablación lineal no respondía esta pregunta, están en [`docs/06-aporte-multivariante.md`](docs/06-aporte-multivariante.md).

**Congelado el 18 de agosto de 2026:** `4h`, `w = 7`, `h = 1`. Los tres salen de medición y cada uno de un criterio distinto fijado antes de mirar el resultado — decisiones [D1](docs/DECISIONES.md), [D2](docs/DECISIONES.md) y [D3](docs/DECISIONES.md), con el estudio completo en [`docs/04-decision-w-h-granularidad.md`](docs/04-decision-w-h-granularidad.md).

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

## Cómo se organiza el trabajo

| | |
|---|---|
| [Issues](https://github.com/NeoFao/caso1-ltc-inflexion/issues) | El backlog. Cada uno lleva por qué existe, qué hacer y su criterio de aceptación |
| [Milestones](https://github.com/NeoFao/caso1-ltc-inflexion/milestones) | Un hito por sprint, con la fecha de la entrega semanal |
| Etiquetas `M0`–`M3` | De quién es. Filtrá por la tuya y ese es tu trabajo |
| Etiqueta `bloquea` | Alguien más no puede avanzar hasta que cierre. Tienen prioridad sobre todo lo demás |
| Etiqueta `contrato` | Toca `contracts/`. Requiere revisión explícita de quien lo consume |

Filtrá lo tuyo así:

```bash
gh issue list --label M2-features --milestone "Sprint 1 — Marco teorico y datos"
```

Las tareas se escriben con criterios **INVEST**: independiente de las demás, negociable en el
cómo, valiosa por sí sola, estimable, pequeña para caber en una semana, y testeable con un
criterio escrito antes de empezar.

Una tarea está terminada cuando existen las cuatro cosas: código con pruebas, un número
obtenido ejecutando, la sección del documento, y el slide. Las cuatro.

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

## Las decisiones del equipo

**[`docs/DECISIONES.md`](docs/DECISIONES.md) es la única fuente de verdad sobre qué decidió el equipo.** Si alguien dice "esto lo acordamos", tiene que poder señalar una fila de ahí. Una decisión que no está en ese archivo no es una decisión del equipo.

Las que se pueden romper en silencio están **fijadas por pruebas** en `tests/test_decisiones.py`, así que cambiar un valor acordado sin pasar por el documento hace fallar el CI. Es deliberado.

---

## Reglas que no se negocian

1. **Ningún número que no hayas obtenido ejecutando.** Ni conteos, ni porcentajes, ni tiempos. Si no lo corriste, escribí "no lo he medido".
2. **Ninguna conclusión a partir de una salida cortada.** Si un log se truncó, pedilo de nuevo.
3. **Verificá la fecha de todo artefacto** antes de usarlo como evidencia. Las figuras se guardan con su `.generado.txt` al lado justamente por esto.
4. **Distinguí lo medido de lo construido.** Una serie sintética que armaste vos no es lo que está pasando en los datos reales.
5. **Decí en la misma frase lo que no está verificado.** "Corre" y "funciona" no son lo mismo.
6. **Fijá el criterio antes de mirar el resultado.** Si no, se llama justificar lo que ya querías hacer.
7. **Una tarea está terminada** cuando hay código, evidencia medida, sección del documento y slide. Las cuatro.
8. **Todo número nuevo reproduce uno conocido antes de publicarse.** Los cinco errores de medición de la Semana 2 los atrapó un control que reproducía un valor ya sabido, no releer el código.
9. **Toda decisión que se cite como acordada tiene que poder señalar dónde se acordó**, y una decisión se acuerda en el repositorio, nunca en un mensaje suelto.

---

## Documentos

| | |
|---|---|
| [PRD](docs/01-prd.md) · [versión Word](docs/) | Qué construimos, alcance, requisitos, riesgos, plan |
| [Definición del punto de inflexión](docs/00-definicion-punto-inflexion.md) | Qué son `w` y `h` y por qué de ellos depende todo lo demás |
| [Consulta al profesor](docs/02-consulta-profesor.md) | Guion de la reunión del equipo y el texto listo para enviar |
| [Backlog](docs/03-backlog.md) | Quién hace qué, en qué orden. Generado desde los issues |
| **[Decisiones del equipo](docs/DECISIONES.md)** | **Qué se decidió, por qué, y con qué evidencia. Fuente única de verdad** |
| [Decisión de `w`, `h` y granularidad](docs/04-decision-w-h-granularidad.md) | El estudio medido que sustenta los tres valores |
| [¿Aportan los activos de apoyo?](docs/06-aporte-multivariante.md) | El resultado negativo, medido con bootstrap pareado sobre el bosque de M3 |
| [`docs/evidencias/`](docs/evidencias/) | Mediciones y figuras, todas regenerables |
| [`docs/entregas/`](docs/entregas/) | Los cinco entregables semanales |

Los entregables en Word se generan con:

```bash
npm install --prefix scripts && npm run ensamblar --prefix scripts
```

`ensamblar` une las secciones de la Semana 1, renumera figuras y tablas de corrido y avisa qué bloques quedan sin redactar. `npm run prd --prefix scripts` regenera el PRD.

**Un paso manual que no se puede automatizar desde el generador:** la tabla de contenido se escribe como campo de Word sin resultado calculado, así que abre en blanco. Antes de entregar hay que abrir el `.docx`, seleccionar el índice y pulsar F9. El propio comando lo recuerda al terminar.

La primera vez instala `docx`; después basta la segunda mitad. Si falla con `EBUSY`, hay un proceso reteniendo el archivo — normalmente Word abierto, o una instancia sin ventana que quedó de una conversión previa.
