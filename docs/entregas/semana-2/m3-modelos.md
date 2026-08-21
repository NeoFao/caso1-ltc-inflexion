# Marco teórico: modelos estadísticos y de aprendizaje automático para series temporales

**Autor:** Isaac Felipe Morún Moreira · **Issues:** [S2-M3-02](https://github.com/NeoFao/caso1-ltc-inflexion/issues/17) y [S2-M3-03](https://github.com/NeoFao/caso1-ltc-inflexion/issues/36)

---

## 1. Modelos fundacionales de series de tiempo (TSFMs)

Un modelo fundacional de series de tiempo (*Time Series Foundation Model*, TSFM) es un modelo preentrenado sobre un corpus masivo de series de dominios distintos —tráfico, energía, ventas, clima, finanzas— capaz de pronosticar una serie nueva sin haber visto un solo ejemplo suyo durante el entrenamiento: pronóstico *zero-shot*. Chronos, por ejemplo, tokeniza el valor de cada instante en un vocabulario discreto y reutiliza directamente una arquitectura de lenguaje entrenada para predecir el siguiente token, tratando el pronóstico como un problema de lenguaje (Ansari et al., 2024). TimesFM sigue el mismo espíritu con un decodificador entrenado sobre cerca de 100 mil millones de puntos temporales reales y sintéticos (Das et al., 2023).

La diferencia con entrenar un modelo desde cero es la que importa para este proyecto: un modelo entrenado desde cero solo puede aprender de los datos que le damos, y nuestro panel tiene 13 114 velas de 4 horas, de las cuales apenas 420 son ejemplos de la clase minoritaria en entrenamiento (`docs/04-decision-w-h-granularidad.md`). Un TSFM ya trajo su noción de tendencia, estacionalidad y ruido de miles de series ajenas; lo único que le pedimos es que la aplique a la nuestra. Eso lo vuelve el candidato natural para el requisito RF-M1 del PRD, que exige justificar la elección con las características medidas de los datos y no por popularidad.

**Medido sobre las máquinas del equipo, en CPU, con contexto de 512 velas reales:**

| Candidato | Familia | Disco (MB) | RAM pico (MB) | s/ventana en lote | Bloque de validación (min) |
|---|---|---|---|---|---|
| **chronos-bolt-small** | Chronos-Bolt (Amazon) | **182,05** | **695,0** | **0,0061** | **0,2** |
| chronos-t5-small | Chronos-T5 (Amazon) | 176,08 | 4 805,6 | 2,9546 | 96,3 |
| timesfm-2.5-200m | TimesFM (Google) | 882,32 | 1 264,6 | 0,1836 | 6,0 |

**Tabla 1.** Inventario de modelos fundacionales que corren en CPU. Medido con
`src/modelos/inventario_tsfm.py`. Fuente:
[`m3-inventario-tsfm.json`](../../evidencias/m3-inventario-tsfm.json).

**Descartado antes de instalarse:** IBM `granite-tsfm` (TinyTimeMixer), porque su
resolución degrada `torch` de 2.13.0 a 2.10.0 y un entorno distinto al del resto del
equipo rompe el requisito no funcional de reproducibilidad. Comprobado con
`uv pip install --dry-run`, sin llegar a instalarlo.

Los tres candidatos que sí se instalaron son viables en CPU: los tres cargan, los tres infieren, los tres devuelven un pronóstico. Pero la diferencia práctica entre ellos es de tres órdenes de magnitud, y ahí está el número que decide. **Chronos-T5 queda descartado por 96,3 minutos de sola inferencia sobre el bloque de validación**, sin entrenar nada — contra el techo de dos horas que RNF-4 fija para el modelo avanzado completo. Es autorregresivo y muestrea 20 trayectorias por ventana; Chronos-Bolt predice sus 9 cuantiles de una sola pasada, lo que explica la diferencia de casi 500 veces en tiempo por ventana.

**Cuidado con la lectura de la Tabla 1.** Los tres aparecen como `viable: true` en la evidencia porque *corren*: cargan sin error y producen un pronóstico con la forma esperada. Que corran y que sirvan para nuestro problema no es lo mismo — esa pregunta es la de la sección 6, y ahí es donde entra el candidato que sí recomendamos: Chronos-Bolt.

---

## 2. VTA (Verbal Technical Analysis)

VTA es un marco reciente (Koa et al., 2025) que combina dos formas de razonamiento sobre una serie de precios: convierte el histórico en anotaciones textuales —un resumen en lenguaje natural del comportamiento reciente del precio— y usa un modelo de lenguaje para razonar verbalmente sobre esas anotaciones, mientras condiciona un modelo de series de tiempo separado sobre la salida de ese razonamiento. En vez de alimentar al modelo con números crudos, primero los traduce a una descripción que un modelo de lenguaje puede interpretar, y el objetivo de entrenamiento combina la calidad del pronóstico numérico con la coherencia del razonamiento textual. El código está disponible públicamente (`github.com/chen-jan/VTA`), lo que satisface RF-M2 si se lo considerara para el modelo avanzado.

Dos preguntas hay que responder para nuestro caso, y ninguna de las dos es favorable.

**¿Aplica a una clasificación de tres clases sobre seis series simultáneas?** El diseño original de VTA pronostica la trayectoria de un solo activo a la vez y se evalúa sobre mercados de acciones de Estados Unidos, China y Europa (Koa et al., 2025) — no está pensado para razonar sobre seis series correlacionadas al mismo tiempo, que es justamente lo que el enunciado exige al pedir que BTC, ETH, SOL, XRP y ADA entren como variables de apoyo de LTC. Extenderlo a un caso multivariante exigiría diseñar de cero el prompt que describa las seis series a la vez, algo que el trabajo original no aborda.

**¿Qué costo tiene traducir 13 114 velas a texto?** No lo hemos medido, y no lo escondemos: no llegamos a implementar el paso de textificación para cronometrarlo. Pero el orden de magnitud del problema es claro sin necesidad de medirlo con precisión — VTA anota por activo y por ventana, así que aplicado a nuestro panel implica generar y procesar una anotación textual por cada una de las 13 114 velas y por cada uno de los seis activos, y después pasarlas por un modelo de lenguaje para razonar. Es un costo de cómputo de un orden completamente distinto al de los TSFMs de la sección 1, que procesan la serie numérica directamente.

**Se descarta.** No porque el enfoque sea malo — el propio equipo de VTA reporta resultados de vanguardia en sus mercados de prueba —, sino porque el punto de entrada al problema (una sola serie, no seis; texto, no números) no calza con lo que tenemos que resolver, y adaptarlo tiene un costo que no está dentro del presupuesto de cinco semanas del proyecto.

---

## 3. FinLSPM (Large Stock Predict Model)

FinLSPM adapta un modelo de lenguaje general en un predictor financiero mediante dos piezas: una tokenización numérica voraz (*Numerical Greedy Tokenization*) que mapea los valores de entrada a un subconjunto de símbolos numéricos, aprovechando las relaciones numéricas que el modelo de lenguaje ya aprendió durante su preentrenamiento sobre texto, y una función de pérdida MR-MAE ajustada para capturar patrones de volatilidad (Guo et al., 2026). Está diseñado y ajustado principalmente sobre el índice NASDAQ en frecuencia diaria, donde reduce el error absoluto medio en 69,8 % frente a un modelo lineal de referencia.

Acá hay que corregir una suposición razonable antes de usarla como argumento: el propio artículo evalúa FinLSPM también sobre S&P 500 y sobre **Bitcoin**, como prueba de generalización (Guo et al., 2026). Es decir, sus autores ya lo probaron sobre un criptoactivo — así que el argumento de "está pensado para acciones, que tienen anclaje fundamental, y las criptomonedas no" no sostiene por sí solo el descarte, aunque sea un punto de análisis válido para explicar por qué su arquitectura principal se ajustó sobre un índice diario y no sobre un panel multivariante de 4 horas como el nuestro.

El criterio que sí decide es otro, y es verificable: **el enunciado exige un modelo con código disponible públicamente** (RF-M2). Buscamos un repositorio público de FinLSPM y no lo encontramos —ni en el artículo, ni en una búsqueda dirigida—. No es una prueba de que no exista, es lo que pudimos verificar hasta ahora: "no lo hemos encontrado", no "no existe". Mientras eso siga así, FinLSPM no cumple un requisito no negociable del enunciado, y ese es el motivo de descarte, no la transferencia de acciones a criptoactivos.

---

## 4. CryptoMamba

**Medido:** no se puede instalar sin CUDA en las máquinas del equipo.

`mamba-ssm` publica en PyPI una única distribución de código fuente y **ninguna
rueda precompilada**, de modo que todo se compila desde fuente. Sin `nvcc`, el
`setup.py` de `causal-conv1d` avisa y después falla contra su propia variable
indefinida: `NameError: name 'bare_metal_version' is not defined`. Probado en un
entorno desechable, nunca en el del proyecto. Fuente:
[`m3-spike-cryptomamba.json`](../../evidencias/m3-spike-cryptomamba.json).

Un modelo de espacio de estados (*state space model*, SSM) como Mamba procesa la secuencia con un estado interno que se actualiza vela a vela, de manera recurrente, y cuyo costo de cómputo crece **linealmente** con la longitud de la secuencia — a diferencia de un Transformer, cuyo mecanismo de atención compara cada posición contra todas las demás y crece **cuadráticamente** (Gu & Dao, 2023). Mamba además hace que ese estado sea *selectivo*: los parámetros que gobiernan qué información retener o descartar dependen de la entrada en cada paso, en vez de ser fijos, lo que le permite mantener memoria relevante sobre secuencias largas sin pagar el costo cuadrático de la atención. CryptoMamba aplica esa arquitectura al pronóstico del precio de Bitcoin, y reporta mejoras frente a LSTM, Bi-LSTM, GRU y S-Mamba (Sepehri et al., 2025).

**Y acá está el punto que conviene decir nosotros primero.** El apartado de entregables del enunciado pide *"primero un modelo fundacional y segundo un Transformer"*, y menciona CryptoMamba entre las opciones para el segundo. **CryptoMamba no es un Transformer**, es un modelo de espacio de estados: son dos familias arquitectónicas distintas, con mecanismos de cómputo distintos (recurrencia lineal contra atención cuadrática), y agruparlas bajo el mismo nombre no es correcto técnicamente. Elegirlo cumpliría con la lista de opciones del procedimiento, pero no con el requisito literal del entregable. Sumado a que no se puede instalar sin CUDA en nuestras máquinas, son **dos razones independientes** para no elegirlo, y las dos están reportadas por escrito en la consulta al profesor (`docs/02-consulta-profesor.md`, punto 5).

---

## 5. Transformer

El mecanismo de atención, introducido por Vaswani et al. (2017) para traducción automática, permite que cada posición de una secuencia se compare directamente contra todas las demás y pondere cuánto le importa cada una, sin la limitación de una recurrencia paso a paso como la de un SSM o una LSTM. Esa capacidad de mirar toda la secuencia a la vez es lo que motivó adaptarlo a series temporales: en principio, un punto lejano en el pasado puede influir tanto como uno reciente si la atención le asigna peso, algo que una recurrencia tiene que propagar paso a paso y puede perder por el camino.

Pero el matiz importa, y conviene decirlo con la misma honestidad con la que reportamos que el bosque aleatorio del Sprint 1 casi no detectaba extremos: hay literatura que cuestiona la ventaja real de la atención en pronóstico de series **largas**. Zeng et al. (2023) muestran que un modelo lineal simple (DLinear) supera a varios pronosticadores basados en Transformer en las pruebas estándar de pronóstico a largo plazo, y argumentan que la naturaleza *permutation-invariant* de la atención — que no distingue el orden temporal salvo por una codificación posicional añadida aparte — puede ser una desventaja, no una ventaja, cuando lo que importa es precisamente el orden. Esa crítica motivó variantes diseñadas específicamente para series y no adaptadas desde el lenguaje: Informer reduce el costo cuadrático con atención dispersa (*ProbSparse*), e iTransformer invierte qué es lo que se atiende — en vez de atender entre instantes de tiempo, atiende entre series completas, tratando cada serie (LTC, BTC, ETH...) como un token —, que es la forma que corresponde a un panel de seis series como el que exige el enunciado.

**Con una advertencia que hay que hacer acá y no al final.** Que el panel sea multivariante por construcción no significa que las cinco series de apoyo aporten información sobre los giros de LTC, y eso se midió: la diferencia entre usar los seis activos y usar solo LTC es de **+0,0090** en F1 macro, con un intervalo de confianza del 95 % de **[−0,0229, +0,0417]** que incluye el cero, por debajo del umbral de decisión de 0,02, y con dos de cinco semillas dando diferencia negativa (`docs/06-aporte-multivariante.md`). **No se puede afirmar que aporten.** Una arquitectura que atiende entre series encaja con la *forma* de nuestros datos; si además le sirve de algo es una pregunta abierta, y elegir iTransformer por su carácter multivariante sería justificarlo con un supuesto que nuestra propia medición no sostiene.

Nuestros propios datos refuerzan la cautela. Con **420 ejemplos de la clase minoritaria en entrenamiento**, entrenar una arquitectura con atención desde cero —que típicamente necesita mucho más volumen de datos que un modelo recurrente o uno lineal para no sobreajustar— es pedirle a los datos algo que ya medimos que no tienen: el estudio de `w` y `h` encontró que la información mutua entre lo observable y la etiqueta cae 4,2 veces solo entre `h=1` y `h=3` (`docs/04-decision-w-h-granularidad.md`), así que la señal disponible es escasa incluso antes de pensar en el tamaño del modelo. Esa es exactamente la pregunta que enlaza con la sección 6: si atención sí, pero no entrenada desde cero.

---

## 6. Justificación de la elección de modelo

La estructura que sostiene esta sección es **criterios primero, candidatos después**, para que la elección no sea una opinión leída en retrospectiva sobre los números.

**Los criterios, declarados antes de aplicarlos:**

1. Corre en CPU (RNF-1) — no sabíamos qué máquinas tenía el equipo al empezar, y confirmamos `cuda_disponible: False` en la nuestra.
2. El código está disponible públicamente (RF-M2).
3. El tiempo de inferencia cabe dentro del presupuesto de dos horas para el modelo avanzado completo, entrenamiento incluido (RNF-4) — y por extensión, no debería consumir buena parte de ese presupuesto solo en inferir sobre validación.
4. No obliga a cambiar el entorno del resto del equipo (RNF-3).

**Modelo fundacional (RF-M1).** De los tres TSFMs medidos, los tres cumplen 1, 2 y 4. Solo Chronos-Bolt cumple 3 con margen: 0,2 minutos contra el bloque de validación entero, frente a los 96,3 de Chronos-T5 y los 6,0 de TimesFM. Ninguno de los dos números descarta a TimesFM de plano, pero Chronos-Bolt es la elección que deja más presupuesto de tiempo disponible para el modelo avanzado y para la optimización de hiperparámetros de la Semana 4 (issue #37). **Recomendación: Chronos-Bolt**, justificada por el criterio 3 medido y no por ser el más nombrado.

**Modelo avanzado (RF-M2).** De los candidatos del enunciado, CryptoMamba falla los criterios 1 y 2 a la vez —no corre en nuestras máquinas y, siendo estrictos con el entregable, no es un Transformer—; VTA falla el criterio 3 de facto por el costo no medido pero cualitativamente alto de textificar 78 684 valores (13 114 velas × 6 activos); FinLSPM falla el criterio 2 porque no encontramos su código público. Eso deja, entre las opciones que sí son Transformers de verdad, a **iTransformer** e **Informer**, ambos con código disponible y ambos diseñados para series y no adaptados desde el lenguaje — la sección 5 explica esa distinción, y también por qué no conviene apoyarla en el supuesto multivariante. La decisión entre los dos exige medirlos en nuestras máquinas, cosa que todavía no se hizo, así que **no se resuelve aquí**: es la tarea S4-M3-01 (issue [#27](https://github.com/NeoFao/caso1-ltc-inflexion/issues/27)). Elegir sin medir es exactamente lo que RF-M1 prohíbe.

**Y lo que queda sin resolver, porque es una decisión de diseño y no un detalle.** Un modelo fundacional de series de tiempo pronostica una trayectoria de precios, no una etiqueta de tres clases: hay que decidir cómo se cruza ese puente. Hay dos formas: usar el modelo congelado como extractor de representaciones y entrenar una cabeza de clasificación encima, o pronosticar la trayectoria y aplicarle directamente la función `etiquetar()` del contrato. La segunda es más simple, reutiliza código que ya está probado y verificado contra fuga, y —esto sí lo medimos— aplicar `etiquetar()` sobre la trayectoria que pronostica Chronos-Bolt cuesta apenas 12 segundos sobre las 1 959 filas del bloque de validación completo. Eso cambia el cálculo: la opción "simple" deja de ser la más barata pero la peor, y pasa a ser prácticamente gratis. La opción del extractor de representaciones sigue sobre la mesa, pero ahora tiene que justificar su costo adicional de entrenar una cabeza propia contra una alternativa que ya casi no cuesta nada. Esta es la decisión que se lleva al lunes, con el número puesto sobre la mesa y no solo el argumento.

---

## Referencias

Ansari, A. F., Stella, L., Turkmen, C., Zhang, X., Mercado, P., Shen, H., Shchur, O.,
Rangapuram, S. S., Pineda Arango, S., Kapoor, S., Zschiegner, J., Maddix, D. C.,
Wang, H., Mahoney, M. W., Torkkola, K., Wilson, A. G., Bohlke-Schneider, M., &
Wang, Y. (2024). *Chronos: Learning the language of time series* (Preprint). arXiv.
https://doi.org/10.48550/arXiv.2403.07815

Das, A., Kong, W., Sen, R., & Zhou, Y. (2023). *A decoder-only foundation model for
time-series forecasting* (Preprint). arXiv. https://doi.org/10.48550/arXiv.2310.10688

Gu, A., & Dao, T. (2023). *Mamba: Linear-time sequence modeling with selective state
spaces* (Preprint). arXiv. https://doi.org/10.48550/arXiv.2312.00752

Guo, H., Kwok, P. Y., Guo, Y., Zhao, J., & Gu, D. (2026). FinLSPM: Large stock
predict model via numerical prior knowledge from LLM. *Expert Systems with
Applications*. https://doi.org/10.1016/j.eswa.2025.130294

Koa, K. J. L., Chen, J., Ma, Y., Zheng, H., & Chua, T.-S. (2025). *Reasoning on
time-series for financial technical analysis* (Preprint). arXiv.
https://doi.org/10.48550/arXiv.2511.08616

Sepehri, M. S., Mehradfar, A., Soltanolkotabi, M., & Avestimehr, S. (2025). CryptoMamba:
Leveraging state space models for accurate Bitcoin price prediction. *2025 IEEE
International Conference on Blockchain and Cryptocurrency (ICBC)*, 1–3.
https://doi.org/10.1109/icbc64466.2025.11114565

Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, L.,
& Polosukhin, I. (2017). *Attention is all you need* (Preprint). arXiv.
https://doi.org/10.48550/arXiv.1706.03762

Zeng, A., Chen, M., Zhang, L., & Xu, Q. (2023). Are Transformers effective for time
series forecasting? *Proceedings of the AAAI Conference on Artificial Intelligence,
37*(9), 11121–11128. https://doi.org/10.1609/aaai.v37i9.26317

> **Nota sobre verificación.** Las ocho referencias se comprobaron contra Crossref con
> `scripts/verificar_referencias.py`. Cinco DOI (Ansari et al., Das et al., Gu & Dao,
> Koa et al. y Vaswani et al.) son *preprints* de arXiv, registrados en DataCite y no
> en Crossref: el script de verificación de este proyecto solo consulta la API de
> Crossref, así que los reporta como `NO EXISTE en Crossref` aunque son DOI reales y
> resuelven correctamente contra `doi.org` (comprobado con `curl -I`, HTTP 302 en los
> cinco). Es una limitación conocida del script y no un problema de estas referencias;
> queda avisado por escrito para quien lo revise, y como posible mejora para M0 —
> agregar una consulta de respaldo contra la API de DataCite— sin tocar el archivo
> nosotros mismos, porque `scripts/` no es carpeta de M3.
