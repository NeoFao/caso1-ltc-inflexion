# Guía de Fabrizio — M0 · Infraestructura, contratos, evaluación e integración

## Qué es tuyo

```
contracts/           los cuatro contratos congelados
src/panel/           descarga y consolidación del panel canónico
src/evaluacion/      arnés de evaluación y verificador de fuga
src/api/             backend de la aplicación
scripts/             mediciones y utilidades
.github/             integración continua
docs/                ensamblaje de los cinco documentos y los cinco decks
```

## Tu papel

**Vos no escribís contenido técnico.** Juntás lo que escribió cada uno, lo unificás en un solo
documento, armás el guion de exposición y entregás.

La infraestructura ya está montada; de aquí en adelante tu trabajo es integración y
documentación. Cada semana tenés un issue propio de ensamblaje con su lista de verificación.

Tu trabajo no se mide por líneas de código sino por cuántas veces alguien te tuvo que esperar,
y por si el documento entregado se lee como escrito por una sola persona.

---

## Estado actual, medido el 5 de agosto de 2026 (revisado el 11)

| | |
|---|---|
| Panel diario | 2 185 filas, 2020-08-11 → 2026-08-04, cero huecos |
| Panel de 4 horas | 13 114 filas, 2020-08-11 → 2026-08-05 |
| Activo que limita la ventana | SOL, listado el 2020-08-11 |
| Recomendación del criterio | `w=7`, `h=5`, intervalo 4h — 420 ejemplos de la clase minoritaria |
| Suite de pruebas | 57 pruebas pasando |
| Entrega 1 | **martes 18 de agosto**, documento sin presentacion |

**El resultado que importa:** con velas diarias **ninguna** combinación de `(w, h)` alcanza el piso de 300 ejemplos que fijamos antes de medir. El mejor caso es `w=3` con 149. Por eso el panel de trabajo es el de 4 horas.

Esto es el riesgo R1 materializándose en la semana 1 en vez de la semana 4, que es exactamente para lo que servía medir antes de repartir tareas.

---

## Esta semana — en orden

Quedan siete días para la primera entrega y el equipo todavía no arrancó: 0 de 43 issues cerrados.

### 1. Congelar `w`, `h` y granularidad — hoy

Es lo único que **no depende de nadie más**. Mientras `PROVISIONAL = True`, M2 y M3 están bloqueados por igual.

La medición recomienda `w=7`, `h=5`, velas de 4 horas, con el criterio fijado antes de mirar los resultados. La Parte A de [`docs/02-consulta-profesor.md`](../docs/02-consulta-profesor.md) es el guion de esa reunión, con las tablas.

Después: cambiás `contracts/config.py`, quitás `PROVISIONAL`, corrés `uv run python scripts/exportar_estatico.py` y avisás por escrito.

### 2. Enviar la consulta al profesor

La Parte B se copia y se manda. Seis preguntas, no cuatro: se sumaron la del Transformer contra CryptoMamba, y la del calendario.

### 3. Repartir el trabajo

A cada uno el enlace directo a `guias/<su-nombre>.md` y a sus issues:

```bash
gh issue list --label M1-datos-app --milestone "Sprint 1 — Marco teorico y datos"
```

Pediles el usuario de GitHub para asignarlos, y las especificaciones de su máquina.

### 4. Ensamblar la Semana 1

Tu issue propio, con la lista de verificación. El corte con los demás es el jueves 13; entrega el martes 18.

**Documento, no presentación.** El profesor lo dijo explícitamente.

---

## Lo que sigue siendo tuyo cada semana

**Lunes:** reunión de 30 minutos. Cada uno dice qué entrega y qué lo puede bloquear.

**Jueves:** corte. Cada módulo entrega su sección en `docs/entregas/semana-N/<modulo>.md` y sus figuras en `docs/evidencias/`.

**Viernes:** ensamblás el documento Word y el deck, y se ensaya con exposición cruzada — cada quien expone el módulo de otro.

El generador del PRD en Word está en el scratchpad de la sesión; para los documentos semanales conviene que armes un script propio en `scripts/` que tome los markdown de `docs/entregas/semana-N/` y produzca el Word con el mismo estilo. Así el ensamblaje semanal deja de ser trabajo manual.

---

## Lo que tenés que vigilar

**Que nadie calcule una métrica fuera de `contracts/metrics.py`.** En el momento en que aparezca un F1 calculado a mano en un notebook, dejan de ser comparables.

**Que las figuras del informe tengan su `.generado.txt` reciente.** `estilo.guardar()` lo escribe solo, pero si alguien guarda una figura a mano se pierde el rastro.

**Que Isaac avise temprano.** El riesgo R2 es que el modelo avanzado no arranque, y el peor escenario no es que falle: es que falle en silencio hasta la semana 4.

**Que la app no calcule nada.** Es la regla que más fácil se rompe, porque siempre es más rápido calcular algo en el frontend que agregar un endpoint.

---

## Deudas conocidas del repo

Cosas que están montadas pero incompletas, para que no las descubras tarde:

- **`src/api/main.py` sirve predicciones del `BaselineTrivial`**, no de un modelo real. Es a propósito: permite que Jose Pablo construya la app desde la semana 2. Hay que cambiarlo cuando Isaac tenga modelo.
- **Falta el endpoint de tiempo real** (RF-U3). Depende de resolver antes qué significa "tiempo real", que es la consulta 3 al profesor.
- **`src/features/base.py` tiene cuatro familias de características de las que pide RF-F1**; faltan indicadores técnicos y ventana deslizante. Son de Alejandro.
- **No hay escalado todavía** (RF-F3).
- **El frontend está montado pero vacío**: compila y levanta, no muestra datos. Es de Jose Pablo desde la semana 2.
- **`uv` puede fallar al instalar Python en Windows** con `Missing expected target directory for Python minor version link`. Pasó en esta máquina con 3.11, 3.14 y 3.15. Se arregla borrando el enlace corto y volviendo a sincronizar:

  ```bash
  rm -rf "$APPDATA/uv/python/cpython-3.14-windows-x86_64-none" && uv sync --group dev
  ```

  Está en el README de las guías porque les va a pasar a ellos también.
