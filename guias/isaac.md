# Guía de Isaac — M3 · Modelo fundacional y modelo avanzado

## Qué es tuyo

```
src/modelos/         todos los modelos del proyecto
```

**Qué no tocás:** `contracts/`, `src/panel/`, `src/features/`, `src/diagnostico/`, `src/evaluacion/`, `src/api/`, `app/`.

## Antes que nada, algo que tenés que saber

**Tu módulo es el más pesado del proyecto y está sobre vos solo.** Está dicho en el PRD como riesgo R2, y hay un punto de decisión explícito el lunes de la semana 4: si el modelo avanzado no arranca, entra Fabrizio a apoyar.

Eso no es desconfianza. Es planificación. Lo que sí necesito de vos es que **avises temprano**, no en la semana 4. Si en la semana 2 ves que algo no cierra, decilo entonces.

---

## Instalación aparte

Vos sos el único que necesita torch y transformers. Pesan varios GB, por eso no están en la instalación base:

```bash
uv sync --group dev --group modelos
```

Verificá que quedó en CPU y anotá qué te dice:

```bash
uv run python -c "import torch; print(torch.__version__, 'cuda:', torch.cuda.is_available())"
```

---

## La interfaz que tenés que cumplir

Todo modelo tuyo hereda de `Modelo` en `src/modelos/base.py` y expone dos métodos:

```python
from src.modelos.base import Modelo

class MiModelo(Modelo):
    nombre = "mi_modelo"

    def entrenar(self, X, y):
        ...
        return self

    def predecir(self, X):
        ...  # array de códigos de Clase, uno por fila
```

**Esto es lo que te da libertad.** Mientras cumplas la interfaz, adentro hacés lo que quieras, y la aplicación de Jose Pablo y el arnés de evaluación funcionan con tu modelo sin que nadie cambie nada. También significa que él puede construir la app antes de que vos tengas modelo, contra el baseline.

Para evaluar, nunca calcules métricas a mano:

```python
from src.evaluacion.arnes import evaluar_modelo, guardar_resultado
from contracts.splits import particionar

particion = particionar(n=len(y), w=7, h=5)
resultado = evaluar_modelo(MiModelo(), X, y, particion, conjunto="validacion")
guardar_resultado(resultado)
```

---

## Semana 1 — cuatro tareas

### T3.1 — Un modelo clásico que funcione de punta a punta

**Por qué primero esto y no el fundacional:** porque necesitás recorrer el circuito completo — cargar el panel, construir características, particionar, entrenar, evaluar — con algo que sabés que va a andar. Si el primer modelo que intentás es un transformer de Hugging Face, cuando falle no vas a saber si el problema es el modelo, las características, la partición o la interfaz.

**Qué hacer:** un `RandomForestClassifier` de scikit-learn envuelto en la interfaz `Modelo`, en `src/modelos/clasico.py`.

**Criterio de aceptación:** una fila en `docs/evidencias/resultados.csv` con su F1 macro sobre validación, al lado de las de los tres baselines. Si no supera al `BaselineTrivial` en F1 macro, algo está mal y hay que averiguar qué antes de seguir.

Ese número es tu punto de referencia para todo el resto del proyecto.

### T3.2 — Verificá si CryptoMamba es viable

**Por qué:** es el riesgo R3 del PRD. Sospecho que CryptoMamba depende de `mamba-ssm`, que compila contra CUDA y es problemático en Windows. **No lo he verificado.** Si es cierto, hay que saberlo ahora y no en la semana 4.

**Qué hacer:** buscá el repositorio, mirá sus dependencias, intentá instalarlo en un entorno aparte. Media hora, no un día.

**Criterio de aceptación:** una respuesta de una línea — se puede o no se puede en nuestras máquinas — con la evidencia de por qué. Si no se puede, iTransformer es el candidato más benigno en CPU, aunque **eso tampoco está medido**.

### T3.3 — Inventario de modelos fundacionales candidatos

**Por qué:** RF-M1 pide que la elección se justifique según las características medidas de los datos, no por popularidad. Eso significa que tenés que comparar, no elegir el más nombrado.

**Qué hacer:** elegí dos o tres candidatos de Hugging Face y para cada uno medí, en tu máquina: tiempo de descarga, memoria en RAM, y tiempo de inferencia sobre una ventana de nuestro tamaño.

**El punto difícil, y quiero que lo pienses desde ahora:** los modelos fundacionales de series de tiempo **pronostican, no clasifican**. Devuelven una trayectoria futura de precios, y nosotros necesitamos tres clases. Hay dos formas de cruzar ese puente:

1. **Usar el modelo congelado como extractor de representaciones** y ponerle encima una cabeza de clasificación entrenada por nosotros.
2. **Pronosticar la trayectoria** y derivar la etiqueta aplicándole el mismo `etiquetar()` del contrato.

Son dos proyectos distintos con métricas distintas. La opción 2 es más simple y más honesta con el espíritu del enunciado; la 1 suele rendir más. **No decidas solo: traelo a la reunión del lunes.**

**Criterio de aceptación:** una tabla con los candidatos y sus tiempos medidos, y una recomendación con su razón.

### T3.4 — Tu sección teórica

Modelos fundacionales de series de tiempo (TSFMs), VTA (Verbal Technical Analysis), FinLSPM y CryptoMamba.

Escribila mientras hacés T3.2 y T3.3: vas a estar leyendo esos papers de todos modos, y escribir después significa leerlos dos veces.

**Cita en APA.** Es un criterio entero de la rúbrica, vale lo mismo que todo el contenido técnico.

---

## Semanas 2 a 5

- **Semana 2:** entorno de entrenamiento listo, decisión de modelo fundacional tomada y justificada.
- **Semana 3:** modelo fundacional funcionando y evaluado. Pruebas con datos sintéticos, de entrenamiento y tiempo real.
- **Semana 4:** modelo avanzado, mismas pruebas.
- **Semana 5:** tu parte del reporte.

---

## Dos datos medidos que condicionan tu trabajo

1. **El panel de 4 horas tiene 13 114 filas**, con 9 165 en entrenamiento.
2. **La clase minoritaria tiene 420 ejemplos en entrenamiento con `w=7`.**

Cuatrocientos veinte ejemplos es poco para un transformer entrenado desde cero. Eso empuja fuerte hacia usar un modelo preentrenado y ajustarlo, en vez de entrenar una arquitectura grande desde el principio. Es un argumento medido, no una opinión, y va al informe tal cual.

**Presupuesto de tiempo (RNF-4):** si entrenar el modelo avanzado supera las dos horas en la máquina más lenta del equipo, se reduce el alcance del modelo. No aceptamos que solo una persona pueda entrenarlo, porque eso convierte a esa persona en un cuello de botella para todos.

---

## Si te trabás

- **Un modelo de Hugging Face que no carga:** copiá el traceback entero al grupo, sin resumir.
- **La instalación de torch tarda muchísimo:** es normal la primera vez. Si pasa de una hora, decilo.
- **El F1 te da sospechosamente alto:** desconfiá antes de festejar. Casi siempre es fuga de información. Pedile a Alejandro que corra `verificar_sin_fuga` sobre las características que estás usando.
- **Más de un día trabado:** decilo.
