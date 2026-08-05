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

Sos el que hace que los otros tres nunca estén bloqueados, y el que une todo. Tu trabajo no se mide por líneas de código sino por cuántas veces alguien te tuvo que esperar.

---

## Estado actual, medido el 5 de agosto de 2026

| | |
|---|---|
| Panel diario | 2 185 filas, 2020-08-11 → 2026-08-04, cero huecos |
| Panel de 4 horas | 13 114 filas, 2020-08-11 → 2026-08-05 |
| Activo que limita la ventana | SOL, listado el 2020-08-11 |
| Recomendación del criterio | `w=7`, `h=5`, intervalo 4h — 420 ejemplos de la clase minoritaria |
| Suite de pruebas | 44 pruebas pasando |

**El resultado que importa:** con velas diarias **ninguna** combinación de `(w, h)` alcanza el piso de 300 ejemplos que fijamos antes de medir. El mejor caso es `w=3` con 149. Por eso el panel de trabajo es el de 4 horas.

Esto es el riesgo R1 materializándose en la semana 1 en vez de la semana 4, que es exactamente para lo que servía medir antes de repartir tareas.

---

## Esta semana — en orden

### 1. Enviar la consulta al profesor

Está redactada y lista en la sección 9 de [`docs/00-definicion-punto-inflexion.md`](../docs/00-definicion-punto-inflexion.md). Cuatro preguntas: si `w` y `h` son decisión nuestra, qué granularidad espera, qué entiende por "tiempo real", y cómo interpretar la Precisión Direccional en tres clases.

**Es lo primero porque tiene latencia.** Todo lo demás depende de vos; esto depende de otro.

Agregale una quinta pregunta que salió de la medición: que ahora tenés el argumento medido para justificar velas de 4 horas, y conviene confirmarlo antes de construir cinco semanas encima.

### 2. Preguntar qué máquina tiene cada uno

Riesgo R3. Una línea en el grupo: procesador, RAM, y si tienen GPU NVIDIA. Sin eso, la elección de modelo avanzado de Isaac es a ciegas.

### 3. Publicar el repo y repartir las guías

```bash
git init
git add .
git commit -m "Estructura del proyecto, contratos y primera medicion de datos"
gh repo create caso1-ltc-inflexion --public --source=. --push
```

Después, a cada uno su guía. No mandes el repo entero y que se arreglen: mandá el enlace directo a `guias/<su-nombre>.md`.

### 4. Reunión para congelar `w`, `h` y granularidad

Con la tabla de `docs/evidencias/spike-datos-4h.json` proyectada. La medición recomienda `w=7`, pero la decisión es del equipo y el criterio ya estaba fijado de antemano, así que la discusión es corta.

Cuando se decida, cambiás `contracts/config.py`, quitás `PROVISIONAL = True`, y avisás por escrito.

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
- **`uv python install` falló en Windows** con un error de enlace de versión, pero `uv sync` funcionó igual. Si a alguien le pasa, que corra `uv sync` directamente y siga.
