# PRD — Sistema de Pronóstico de Puntos de Inflexión en LTC

**Documento de Requisitos de Producto**
Caso N°1 — Señales y Sistemas — 3er Trimestre 2026

| | |
|---|---|
| **Versión** | 1.0 |
| **Fecha** | 5 de agosto de 2026 |
| **Autor** | Fabrizio Espinoza Arce (Project Manager) |
| **Equipo** | Alejandro Zamora, Jose Pablo Monestel, Isaac Morun, Fabrizio Espinoza Arce |
| **Programa** | Tecnologías de la Información y Comunicación Empresarial, Universidad Invenio |
| **Entrega a** | Roberto Calvo Arias |
| **Entrega final** | 8 de septiembre de 2026 |
| **Estado** | Borrador para revisión del equipo |

---

## Cómo leer este documento

No hace falta leerlo entero de una sentada. Está ordenado así:

- **Secciones 1 a 4** — qué estamos construyendo y por qué. Léanlas todos.
- **Secciones 5 a 8** — cómo está partido el trabajo y qué le toca a cada uno. Lean la suya con cuidado y las demás por encima, para saber a quién preguntarle qué.
- **Secciones 9 a 12** — cómo se trabaja semana a semana y cuándo algo cuenta como terminado.
- **Secciones 13 a 15** — lo que todavía no está decidido, lo que puede salir mal y lo que estamos suponiendo sin haber verificado.

Si algo no se entiende, no es culpa de quien lee. Escríbanlo en el grupo y lo corrijo en la versión siguiente.

---

## 1. Qué estamos construyendo

Un sistema que mira el precio de Litecoin y avisa cuándo está por dar la vuelta.

Más preciso: un modelo de aprendizaje automático que, para cada momento del tiempo, clasifica el precio de LTC en una de tres etiquetas — **Máximo**, **Mínimo** o **Zona de Continuidad** — usando como información de apoyo el comportamiento de Bitcoin, Ethereum, Solana, XRP y Cardano.

Alrededor del modelo construimos tres cosas más:

1. Una **aplicación web** que permite ver el modelo funcionando sobre datos sintéticos, históricos y en vivo.
2. Un **informe técnico** que documenta el diseño, el rendimiento medido y las limitaciones del enfoque.
3. Una **presentación semanal** del avance.

## 2. Por qué existe el problema

Los precios de criptomonedas son series difíciles: no son estacionarias (sus propiedades estadísticas cambian con el tiempo), son muy volátiles, y su volatilidad tampoco es constante (heterocedasticidad). Los modelos estadísticos clásicos como ARIMA o GARCH asumen estructuras lineales y estables, y por eso rinden mal acá.

Además, LTC no se mueve solo. Su precio responde al mercado general de criptomonedas, y en particular a los activos de mayor capitalización, que funcionan como transmisores de riesgo y de sentimiento. Un modelo que ignore eso está tirando información útil.

De ahí el planteamiento: **problema multivariante** (seis series, no una) y **enfoque de aprendizaje profundo** (no estadística clásica).

## 3. Objetivos y criterios de éxito

Hay dos tipos de éxito y conviene no confundirlos.

### 3.1 Éxito académico

El trabajo se califica con seis criterios, todos del mismo peso (16.66% cada uno):

| Criterio | Qué mide |
|---|---|
| Contenido | Profundidad y precisión en la descripción de equipos, tecnologías y sistemas |
| Análisis | Capacidad de relacionar los conceptos técnicos con su aplicación, con ejemplos prácticos |
| Calidad de las fuentes | Uso de referencias académicas y cumplimiento del formato APA |
| Estructura y redacción | Organización clara, coherencia y uso correcto del idioma |
| Calidad de la exposición | Que la presentación sea clara, dinámica y mantenga la atención |
| Comunicación efectiva | Que la comunicación sea clara, concisa y adaptada al público |

**Léanlo dos veces: cuatro de los seis criterios no hablan del modelo.** Hablan de cómo escribimos, cómo citamos y cómo exponemos. Eso es el 66% de la nota. Un modelo brillante con un documento apurado saca menos que un modelo decente con un documento impecable.

Esto no es un detalle de cierre. Es la razón por la que en este proyecto **escribir la sección del documento es parte de terminar la tarea**, no algo que se hace después.

### 3.2 Éxito técnico

El proyecto es exitoso técnicamente si:

1. El modelo supera de forma medible a un **baseline trivial**. El baseline trivial es un modelo que siempre responde "Zona de Continuidad". Como las clases van a estar desbalanceadas, ese modelo tonto va a tener buena exactitud, y si no lo superamos en F1 no tenemos nada.
2. Existen **dos modelos** funcionando y comparados con la misma métrica y la misma partición de datos: uno fundacional de Hugging Face y uno avanzado.
3. Todo resultado del informe se puede **regenerar con un comando**. Si un número no se puede volver a producir, no entra al informe.

### 3.3 Criterio de decisión, fijado de antemano

Para no terminar justificando lo que ya queríamos hacer, dejamos escrito ahora — antes de medir nada — cómo se elige el modelo que va al reporte final:

> Gana el modelo con mayor **F1 macro** sobre el conjunto de prueba. Si la diferencia entre el fundacional y el avanzado es **menor a 0.02 absoluto**, se recomienda el fundacional por ser más simple, y el avanzado se documenta igual con su resultado.

El umbral de 0.02 es una propuesta del PM, no un número sacado de un paper. Si alguien tiene un criterio mejor, se cambia **ahora**. Después de ver los resultados ya no se puede cambiar sin decirlo explícitamente en el informe.

## 4. Alcance

### 4.1 Dentro del alcance

- Descarga y limpieza de series históricas de las seis criptomonedas.
- Análisis exploratorio y diagnóstico estadístico de las series.
- Definición operativa del punto de inflexión y generación de etiquetas.
- Ingeniería de características (indicadores técnicos, rezagos, ventanas, volatilidad, correlación).
- Un modelo fundacional de Hugging Face.
- Un modelo avanzado (iTransformer, CryptoMamba, Informer, VTA o FinLSPM).
- Arnés de evaluación con métricas comunes y partición temporal fija.
- Generador de series sintéticas con puntos de inflexión conocidos.
- Aplicación web con tres modos de prueba.
- Cinco documentos semanales y cinco presentaciones.

### 4.2 Fuera del alcance

Esto no se construye, y si a alguien se le ocurre a mitad de camino, se discute antes de escribir una línea:

- Ejecución de operaciones reales, conexión a un exchange, gestión de órdenes.
- Recomendaciones de inversión de cualquier tipo.
- Autenticación, usuarios, base de datos, despliegue en producción.
- Reentrenamiento automático o pipelines de MLOps.
- Más criptomonedas que las seis del enunciado.
- Análisis de sentimiento, noticias o redes sociales.

---

## 5. El producto

### 5.1 Quién lo usa

Seamos honestos sobre esto, porque cambia las decisiones de diseño: **el usuario real es quien evalúa el proyecto, y nosotros mismos.** No hay un inversionista esperando esta herramienta. Diseñar para un usuario imaginario nos llevaría a construir cosas que nadie va a mirar.

Por eso la aplicación tiene una sola misión: **hacer visible y comprensible, en segundos, lo que el modelo hace bien y lo que hace mal.**

### 5.2 Los tres modos

El enunciado exige pruebas de detección "con datos sintéticos, de entrenamiento y tiempo real". La aplicación tiene exactamente esos tres modos, ni uno más:

**Modo Sintético.** Se genera una serie artificial con giros que nosotros mismos pusimos, así que sabemos con certeza absoluta dónde están. El modelo la analiza y se ve si los encuentra. Es la única prueba donde la verdad no está en discusión. Sirve para detectar errores de implementación que en datos reales pasarían desapercibidos.

**Modo Histórico.** Se elige un rango de fechas del panel real. Se muestran las etiquetas verdaderas y las predichas sobre el mismo gráfico, más las métricas del período. Es la evaluación formal del enunciado, hecha visible.

**Modo Tiempo Real.** Se descargan las velas más recientes y el modelo predice sobre datos que todavía no tienen etiqueta conocida. Muestra siempre la fecha y hora del dato que está usando.

Más: selector de criptomoneda, comparación lado a lado del modelo fundacional contra el avanzado, y un panel de métricas.

### 5.3 Requisitos funcionales

Numerados para poder rastrearlos después. Cada tarea del backlog va a apuntar a uno de estos.

**Datos**

- **RF-D1** — El sistema obtiene velas OHLCV de las seis criptomonedas desde una única fuente documentada.
- **RF-D2** — Cada descarga queda registrada con fuente, fecha y hora, rango de fechas y hash del archivo. Sin ese registro el dato no se usa.
- **RF-D3** — Los huecos y valores anómalos se tratan con una regla escrita y auditable. Nada se corrige "a ojo".
- **RF-D4** — El panel combinado se guarda versionado y es idéntico para las cuatro personas.

**Etiquetado**

- **RF-E1** — Una única función pura asigna las tres clases a partir del precio de cierre, `w` y `h`. Ningún módulo implementa su propia versión.
- **RF-E2** — Ninguna característica usa información posterior al instante de predicción. Esto se verifica con una prueba automática, no con buena fe.
- **RF-E3** — La partición entrenamiento / validación / prueba es temporal y está fija. Nunca aleatoria.

**Características**

- **RF-F1** — Se generan características de al menos cuatro familias: indicadores técnicos, rezagos, ventana deslizante y volatilidad.
- **RF-F2** — Se generan características de correlación cruzada entre LTC y las otras cinco criptomonedas.
- **RF-F3** — Todas las características se calculan sobre la misma escala documentada, y el escalado se ajusta solo con datos de entrenamiento.
- **RF-F4** — Se documenta qué características quedaron y por qué, con una medición de importancia.

**Modelos**

- **RF-M1** — Un modelo fundacional de Hugging Face, con su elección justificada según las características medidas de los datos, no por popularidad.
- **RF-M2** — Un modelo avanzado de la lista del enunciado, con código disponible públicamente.
- **RF-M3** — Ambos modelos exponen la misma interfaz de predicción, para que el arnés de evaluación y la aplicación no sepan cuál están usando.
- **RF-M4** — Ambos entrenan con semilla fija y el proceso es reproducible.

**Evaluación**

- **RF-V1** — Todas las métricas salen de una única función compartida: Precisión Direccional, F1 macro, F1 por clase y matriz de confusión.
- **RF-V2** — Todo reporte de resultados incluye el baseline trivial como punto de comparación obligatorio.
- **RF-V3** — Los resultados se guardan en un archivo versionado con la fecha de ejecución.

**Aplicación**

- **RF-U1** — Modo sintético operativo.
- **RF-U2** — Modo histórico operativo con selección de rango.
- **RF-U3** — Modo tiempo real operativo, mostrando siempre la fecha del dato.
- **RF-U4** — Comparación de los dos modelos sobre el mismo período.
- **RF-U5** — La aplicación arranca y es usable **sin conexión a internet**, con el último dato cacheado, indicando su antigüedad.
- **RF-U6** — La aplicación no contiene lógica de negocio. Ninguna métrica, etiqueta o predicción se calcula dentro de ella.

**Documentación**

- **RF-I1** — Cada módulo entrega su sección del documento en la misma semana en que entrega su código.
- **RF-I2** — Toda figura lleva número, pie, y está referenciada en el texto.
- **RF-I3** — Toda cita sigue formato APA.
- **RF-I4** — Toda figura y toda tabla se regenera con un script commiteado. Nada de capturas pegadas.

### 5.4 Requisitos no funcionales

- **RNF-1 — Todo corre en CPU.** Si algo exige GPU, tiene que existir un camino en CPU aunque sea más lento. Todavía no sabemos qué máquinas tiene el equipo.
- **RNF-2 — Reproducibilidad.** Cualquier número del informe se regenera con un comando. Semillas fijas en todo.
- **RNF-3 — Entorno idéntico.** Las cuatro máquinas instalan exactamente las mismas versiones desde un archivo de bloqueo.
- **RNF-4 — Presupuesto de entrenamiento.** El tiempo de entrenamiento del modelo avanzado se mide en la semana 3. Si supera **dos horas** en la máquina más lenta del equipo, se reduce el alcance del modelo en vez de aceptar que solo una persona pueda entrenarlo.

---

## 6. Arquitectura

```
   FUENTE DE DATOS (API pública)
            |
            v
   [ M0 ] descarga y consolidación
            |
            v
   data/processed/panel_v1.parquet  <-- artefacto congelado, igual para los cuatro
            |
      +-----+------------------+------------------+
      |                        |                  |
      v                        v                  v
  [ M1 ] EDA y           [ M2 ] etiquetas    [ M3 ] modelos
  diagnóstico            y características    fundacional
      |                        |               y avanzado
      |                        |                  |
      +------------------------+------------------+
                               |
                               v
                    [ M0 ] arnés de evaluación
                               |
                               v
                    [ M0 ] API del backend
                               |
                               v
                    [ M1 ] aplicación web
```

**La idea central:** el artefacto de datos y los contratos se congelan primero. A partir de ahí, los tres módulos de abajo trabajan en paralelo sin esperarse entre sí, porque todos dependen del contrato y ninguno depende del trabajo en curso de otro.

### 6.1 Pila tecnológica

| Capa | Elección | Por qué |
|---|---|---|
| Lenguaje | Python 3.14 | Ultima estable. Se midio que resuelve identico a 3.13 con torch 2.13 y transformers 5.14; 3.15 se descarta porque ningun torch tiene ruedas para esa version |
| Entorno | `uv` con archivo de bloqueo | Un solo comando instala todo, incluido el intérprete. Elimina los cuatro puntos de falla habituales del setup |
| Datos | pandas + parquet | El dataset son miles de filas, no millones. pandas es lo que van a encontrar en cualquier tutorial cuando se traben |
| Modelos | PyTorch (CPU) + transformers | Requisito del enunciado |
| Backend | FastAPI | Expone las funciones que ya existen como JSON. Delgado, sin lógica propia |
| Frontend | Vite + React + TypeScript + Tailwind | El equipo ya entregó un producto con esta pila |
| Gráficos | TradingView Lightweight Charts | Es la librería que hace que un gráfico de cripto se vea profesional, con marcadores sobre puntos concretos |
| Figuras del informe | matplotlib con estilo compartido | Consistencia entre los cinco documentos |

**Lo que deliberadamente no usamos:** MLflow, DVC, Weights & Biases, Docker. Cada una es una semana de aprendizaje que no tenemos, y el problema que resuelven — trazabilidad de experimentos — lo cubrimos con un parquet versionado y un CSV de resultados commiteado.

---

## 7. Módulos y responsables

**Regla base: nadie comparte tarea con nadie.** Cada persona tiene sus carpetas, y nadie edita archivos ajenos sin avisar por escrito.

### M0 — Infraestructura, contratos y evaluación · *Fabrizio Espinoza (PM)*

Monta el repositorio, el entorno, la integración continua y las guías. Produce el dataset canónico. Define y congela los contratos. Construye el arnés de evaluación y el backend. Ensambla los documentos semanales y los decks. Es quien une todo.

**Carpetas:** `contracts/`, `src/evaluacion/`, `src/api/`, `data/`, `.github/`
**Su marco teórico:** métricas de evaluación para puntos de inflexión.

### M1 — Datos, diagnóstico y aplicación · *Jose Pablo Monestel*

**Semanas 1-2:** análisis exploratorio y diagnóstico estadístico de las seis series — estacionariedad, volatilidad, autocorrelación, correlación cruzada. Es el módulo que responde "¿cómo son realmente estos datos?".
**Semanas 3-5:** la aplicación web completa, con los tres modos.

Arranca el frontend en la semana 2 contra datos falsos. **No espera a que exista el modelo.**

**Carpetas:** `src/datos/`, `src/visual/`, `app/`
**Su marco teórico:** definición y componentes de una serie temporal, estacionariedad, no estacionariedad, heterocedasticidad, volatilidad, autocorrelación, correlación cruzada.

### M2 — Etiquetado y características · *Alejandro Zamora*

Implementa la función de etiquetado según la definición que congele el equipo. Construye el generador de series sintéticas con giros conocidos. Diseña y mide las características. Reporta cuáles aportan y cuáles no.

**Carpetas:** `src/features/`, `src/sintetico/`
**Su marco teórico:** criptoactivos, sus características y tipos, factores que afectan el precio, correlación y dependencia entre activos, definición de punto de inflexión y cómo encontrarlos.

### M3 — Modelado · *Isaac Morun*

**Semanas 1-2:** estudio comparado de los modelos candidatos y montaje del entorno de entrenamiento.
**Semana 3:** modelo fundacional de Hugging Face funcionando y evaluado.
**Semana 4:** modelo avanzado funcionando y evaluado.

Es el módulo con más riesgo del proyecto. Si en la semana 4 el modelo avanzado no arranca, el PM entra a apoyar. Eso está previsto y no es un fracaso: es el plan.

**Carpetas:** `src/modelos/`
**Su marco teórico:** modelos fundacionales de series de tiempo, VTA, FinLSPM, CryptoMamba.

### 7.1 Por qué este reparto

No es al azar. Cada quien está donde ya demostró que rinde: en el proyecto anterior del equipo, Jose Pablo llevó interfaz y visualización, Isaac llevó la parte de inteligencia artificial, y Alejandro llevó el núcleo y la integración — que acá corresponde a los contratos de etiquetado.

### 7.2 Sobre exponer

Cada semana, **cada persona expone el módulo de otro**, rotando. Esto no es trabajo compartido: cada quien sigue construyendo solo lo suyo. Es un ensayo.

La razón es concreta: dos de los seis criterios de la rúbrica evalúan la exposición y la comunicación, y suman lo mismo que contenido y análisis juntos. Si llegamos a la semana 5 con cuatro especialistas que solo saben defender su parte, perdemos ahí. Además, si alguien falta el día de la presentación, no se cae el avance.

---

## 8. Los contratos congelados

Un contrato es una definición que varios módulos usan y que **nadie cambia por su cuenta**. Son la razón por la que se puede trabajar en paralelo sin pisarse.

Se congelan al cierre de la Semana 1 y viven en `contracts/`.

| Contrato | Qué fija | Quién lo consume |
|---|---|---|
| `schema.py` | Columnas exactas del panel, tipos, zona horaria | M1, M2, M3 |
| `labeling.py` | La función que asigna Máximo / Mínimo / Continuidad | M2, M3, M0 |
| `splits.py` | Las fechas exactas de entrenamiento, validación y prueba | M3, M0 |
| `metrics.py` | Las firmas de todas las métricas | M3, M0, M1 |

**Cómo se cambia un contrato:** se propone por escrito, con la razón y qué se rompe. Lo aprueban el PM y quien lo consume. Se cambia en un solo lugar y se vuelve a correr todo. Nunca se parcha en cuatro archivos distintos.

**Por qué esto importa tanto:** si en la semana 3 Alejandro está etiquetando con una ventana de 5 e Isaac entrenó con una de 10, los resultados no son comparables entre sí y no hay forma de saber cuál modelo es mejor. Peor: no nos vamos a dar cuenta hasta que los números no cuadren, probablemente en la semana 4, cuando ya no hay tiempo para rehacer.

### 8.1 Estándar de figuras

`src/visual/estilo.py` contiene la paleta, la hoja de estilo y las funciones de ayuda. **Cada módulo genera sus propias figuras llamando a eso.** Nadie espera a nadie, y salen consistentes porque comparten el código, no porque alguien se acuerde de una convención.

La aplicación web usa la misma paleta que las figuras del informe. El demo y el documento tienen que parecer el mismo proyecto.

---

## 9. Plan por semanas

La fecha de la Semana 1 la confirmó el profesor. Las demás están por confirmar.

| Semana | Cierre estimado | Entregable del enunciado | Qué se construye en paralelo |
|---|---|---|---|
| **1** | **18/08** | Marco teórico: series temporales y criptoactivos — **documento, sin presentación** | Repo, entorno, dataset canónico, contratos congelados |
| **2** | ~25/08 | Marco teórico: modelos y definición del pipeline — documento | Características, entorno de entrenamiento, esqueleto de la app contra datos falsos |
| **3** | ~01/09 | Modelo fundacional + pruebas de detección — **documento y presentación** | App conectada al modelo real, modos sintético e histórico |
| **4** | ~08/09 | Modelo avanzado + pruebas de detección — documento y presentación | Modo tiempo real, comparación de modelos |
| **5** | ~15/09 | Reporte final — documento y presentación | Cierre, ensayo, evidencias |

**Solo la fecha de la Semana 1 está confirmada.** El profesor dijo que la primera entrega es el
martes 18 de agosto. Las demás son cadencia semanal supuesta, y hay un conflicto: si la entrega
final fuera el 8 de septiembre, no caben cinco entregas semanales empezando el 18 de agosto.
Está como consulta 6 al profesor.

**Decisión clave del plan:** el enunciado pide que las semanas 1 y 2 sean solo teoría. No lo hacemos así. Escribimos la teoría **y** construimos el pipeline en paralelo desde la primera semana. Si esperamos a la semana 3 para tocar código, las semanas 4 y 5 se convierten en una carrera y no queda margen para probar de verdad ni para ensayar la presentación.

El entregable semanal se respeta tal cual lo pide el enunciado. El código adicional es nuestro colchón, no un cambio de alcance.

---

## 10. Cadencia semanal

| Cuándo | Qué |
|---|---|
| **Lunes** | Reunión de 30 minutos. Cada uno dice qué entrega esta semana y qué lo puede bloquear. Se cierra el alcance de la semana. |
| **Todos los días** | Cada quien sube su trabajo a su rama, aunque esté incompleto. Un día sin subir nada es una señal de alarma, no un problema de disciplina. |
| **Jueves** | Corte. Cada módulo entrega su sección del documento y sus figuras. |
| **Viernes** | El PM ensambla el documento y el deck. Ensayo con exposición cruzada. |

**Regla de desbloqueo:** si alguien está trabado más de un día, lo dice. No hay premio por sufrir en silencio, y en un proyecto de cinco semanas un día perdido es el 3% del tiempo total.

**Regla de datos que no existen:** si alguien va a construir algo que depende de datos, de una API o de un archivo que todavía no existe, lo avisa **antes de empezar**. Esa es la forma más cara de perder tiempo en este tipo de proyecto.

---

## 11. Cuándo una tarea está terminada

Una tarea no está terminada cuando el código corre. Está terminada cuando existen estas cuatro cosas:

1. **Código** en la rama, con sus pruebas pasando.
2. **Evidencia medida** — un número que salió de ejecutar algo, no de estimarlo. Si no se ejecutó, se dice "no lo he medido".
3. **Sección del documento** escrita, con sus figuras numeradas y referenciadas.
4. **Slide** con lo esencial de ese avance.

Las cuatro. Una tarea con código y sin documento no cuenta como avance, porque el 66% de la nota está en el documento y la presentación.

### 11.1 Cómo se escriben las tareas

Cada tarea del backlog cumple estos seis criterios:

| | Qué significa acá |
|---|---|
| **I**ndependiente | Se puede hacer sin esperar a que otro termine. Los contratos existen justamente para esto |
| **N**egociable | El *qué* está fijo, el *cómo* lo decide quien la hace |
| **V**aliosa | Produce algo que se puede mostrar: un número, una figura, una pantalla. No "avanzar en el módulo" |
| **E**stimable | Quien la hace puede decir si le toma horas o días. Si no puede, está mal descrita |
| **S**mall (pequeña) | Cabe en una semana. Si no cabe, se parte |
| **T**esteable | Hay una forma clara de saber si quedó bien, escrita antes de empezar |

---

## 12. Reglas de honestidad

Estas no son formalismos. Cada una evita un error concreto que en un proyecto así se paga caro.

1. **Ningún número que no se haya obtenido ejecutando.** Ni conteos, ni porcentajes, ni tiempos. Si no se corrió, se escribe "no lo he medido". Un número inventado en un documento entregado es peor que un espacio en blanco.
2. **Ninguna conclusión a partir de una salida cortada.** Si un log o un archivo se truncó, se pide de nuevo. No se completa con suposiciones.
3. **Verificar la fecha de todo artefacto generado** antes de usarlo como evidencia — figuras, archivos de datos, resultados. Es fácil pasar horas mirando un resultado viejo que no se regeneró.
4. **Distinguir lo medido de lo construido.** Si alguien arma un caso sintético para ilustrar un riesgo, lo dice. No se presenta como algo que está pasando en los datos reales.
5. **Decir en la misma frase lo que no está verificado.** "Compila" y "funciona" no son lo mismo. "Las pruebas pasan" y "lo probé de verdad" tampoco.
6. **Fijar el criterio antes de mirar el resultado.** Si hay que elegir entre dos opciones, se define primero qué número decide. Al revés se llama justificar lo que ya se quería hacer.
7. **Desconfiar de las listas de estado.** Se desactualizan en las dos direcciones. La fuente de verdad es el código y lo que se ejecuta.

---

## 13. Decisiones abiertas

| # | Decisión | Quién decide | Cuándo |
|---|---|---|---|
| D1 | Granularidad de las velas: diaria, 4 horas u horaria | Equipo, con la medición del spike de datos en la mano | Semana 1 |
| D2 | Valor de la ventana `w` | Equipo | Semana 1 |
| D3 | Valor del horizonte `h` | Equipo | Semana 1 |
| D4 | Qué se considera "tiempo real": detección con retraso confirmado o predicción en el momento | Profesor | Pendiente de respuesta |
| D5 | Cómo interpretar la Precisión Direccional en un problema de tres clases | Profesor | Pendiente de respuesta |
| D6 | Qué máquina tiene cada integrante | Equipo | Esta semana |
| D7 | Qué modelo fundacional y qué modelo avanzado | Isaac, justificado con datos medidos | Semanas 2 y 3 |
| D8 | Pila del frontend: React/Vite o Streamlit | PM, propuesta React/Vite | Esta semana |

El contexto completo de D1, D2, D3, D4 y D5 está en [`docs/00-definicion-punto-inflexion.md`](00-definicion-punto-inflexion.md), que además contiene la consulta al profesor redactada para enviarse.

---

## 14. Riesgos

Ordenados del más grave al menos grave.

| # | Riesgo | Impacto | Qué hacemos |
|---|---|---|---|
| R1 | **Los datos no alcanzan.** La ventana histórica común de las seis criptomonedas puede dar pocas filas, y las clases de interés van a ser raras por construcción | Puede invalidar la elección de modelo y obligar a rediseñar | Spike de datos esta semana, antes de repartir tareas. Si en velas diarias no alcanza, se pasa a granularidad menor |
| R2 | **El modelo avanzado no arranca.** Es el módulo más pesado y está sobre una sola persona | Se cae el entregable de la semana 4 | Punto de decisión explícito el lunes de la semana 4. El PM entra a apoyar. Está previsto |
| R3 | **Cómputo insuficiente.** Todavía no sabemos qué máquinas hay. CryptoMamba puede depender de CUDA — hay que verificarlo | Elimina modelos de la lista del enunciado | Confirmar máquinas esta semana. Verificar la dependencia antes de que alguien elija ese modelo |
| R4 | **Fuga de información.** Como la etiqueta de un instante requiere ver el futuro, es fácil contaminar las características sin darse cuenta | Resultados excelentes y falsos. Es el peor caso porque no se nota | Prueba automática obligatoria (RF-E2). Se implementa antes que las características |
| R5 | **La aplicación consume el tiempo del modelado.** Ahora es un módulo completo | Se llega a la semana 5 con la app linda y el informe flojo | El alcance está cerrado en tres modos. La app no lleva lógica de negocio |
| R6 | **Carga documental.** Cinco documentos y cinco exposiciones en cinco semanas, con la rúbrica pesando 66% en forma | Documentos apurados, que es exactamente donde más se pierde nota | La sección del documento es parte de la definición de terminado, no una tarea aparte |
| R7 | **La respuesta del profesor cambia el alcance.** En particular D4, sobre qué es tiempo real | Puede redefinir la app y las pruebas de las semanas 3 y 4 | Enviar la consulta ya, no la semana que viene |

---

## 15. Supuestos no verificados

Esta sección existe porque es más honesto que dejarlos escondidos en el texto. **Nada de lo que sigue está medido.**

1. Que existe una fuente pública y gratuita con velas OHLCV de las seis criptomonedas, accesible desde Costa Rica. No se ha probado.
2. Que la ventana histórica común arranca alrededor de 2020, limitada por Solana, que es la de listado más reciente. Creo que es así, pero no lo he confirmado.
3. Que en velas diarias hay alrededor de 2.000 observaciones desde 2020. Es aritmética sobre días transcurridos, no un conteo sobre datos reales.
4. Que las clases Máximo y Mínimo van a estar por debajo del 17% cada una con una ventana de 5. Esto sí es una cota aritmética demostrable, pero el valor real será menor y no se ha medido.
5. Que existe un modelo fundacional en Hugging Face que corre en CPU en tiempo razonable para este problema. No se ha probado ninguno.
6. Que CryptoMamba depende de CUDA y es problemático en Windows. Es una sospecha, no una verificación.
7. Que las fechas de cierre semanal son los martes. Está por confirmar con el profesor.

**Cada uno de estos supuestos se convierte en una medición o se retira del documento antes del cierre de la Semana 1.**

---

## 16. Glosario

**Vela (candle):** una observación de precio agrupada en un intervalo de tiempo — un día, una hora. Trae apertura, máximo, mínimo, cierre y volumen. Nosotros usamos el cierre.

**OHLCV:** apertura, máximo, mínimo, cierre y volumen. Los cinco campos de una vela.

**Etiqueta:** la respuesta correcta que el modelo debe aprender a dar. Acá: Máximo, Mínimo o Continuidad.

**Serie estacionaria:** una serie cuyas propiedades estadísticas no cambian con el tiempo. Los precios de cripto no lo son, y ese es parte del problema.

**Heterocedasticidad:** que la volatilidad no sea constante. Hay períodos tranquilos y períodos agitados.

**Clases desbalanceadas:** cuando una etiqueta aparece muchísimo más que las otras. Rompe la exactitud como medida de calidad.

**F1-Score:** medida que combina cuántos de los giros anunciados eran de verdad giros con cuántos de los giros reales logramos anunciar. No se deja engañar por el desbalance.

**F1 macro:** el promedio del F1 de las tres clases, dándoles el mismo peso. Es duro con los modelos que ignoran las clases raras, que es justo lo que queremos.

**Baseline trivial:** un modelo tonto que siempre responde lo mismo. Sirve como piso: si no lo superamos, no tenemos nada.

**Fuga de información (data leakage):** cuando el modelo recibe sin querer información del futuro que en la práctica no tendría. Produce resultados excelentes y falsos.

**Modelo fundacional:** un modelo grande preentrenado sobre muchísimas series de tiempo, que se puede usar sin entrenarlo desde cero.

**Contrato congelado:** una definición acordada que varios módulos consumen y que nadie cambia por su cuenta.

**Mock (dato falso):** una versión simulada de algo que todavía no existe, para poder trabajar sin esperar a que exista.

---

*Este documento se actualiza. Si algo cambia, cambia acá primero y después en el código.*
