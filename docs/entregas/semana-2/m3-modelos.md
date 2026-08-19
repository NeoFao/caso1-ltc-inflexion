# Marco teórico: modelos estadísticos y de aprendizaje automático para series temporales

**Autor:** Isaac Felipe Morún Moreira · **Issues:** [S2-M3-02](https://github.com/NeoFao/caso1-ltc-inflexion/issues/17) y [S2-M3-03](https://github.com/NeoFao/caso1-ltc-inflexion/issues/36)

> **Este archivo es un esqueleto.** Cada sección trae la evidencia ya medida donde
> la hay. Lo que falta es el texto. Borrá los bloques `> ESCRIBÍ ACÁ` a medida que
> los completes.
>
> Todos los números que aparecen abajo salen de `docs/evidencias/` y ya están
> verificados. No hay que volver a medirlos.

---

## 1. Modelos fundacionales de series de tiempo (TSFMs)

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

> **ESCRIBÍ ACÁ.** Qué es un modelo fundacional de series de tiempo: un modelo
> preentrenado sobre muchas series de dominios distintos que puede pronosticar una
> serie nueva sin haber sido entrenado en ella —*zero-shot*—. Explicá en qué se
> diferencia de entrenar un modelo desde cero con nuestros datos, y por qué eso
> importa cuando se tienen 13 114 observaciones y no millones.
>
> Después conectá con la tabla: los tres son viables en CPU, pero la diferencia
> práctica es de tres órdenes de magnitud. **Chronos-T5 queda fuera por 96,3 minutos
> de sola inferencia sobre el bloque de validación**, sin entrenar nada. Ese es el
> número que decide.
>
> **Cuidado con la redacción:** los tres aparecen como `viable: true` en la
> evidencia porque *corren*. Que corran y que sirvan no es lo mismo, y conviene que
> lo digas vos.

---

## 2. VTA (Verbal Technical Analysis)

> **ESCRIBÍ ACÁ.** Qué propone: traducir el estado de la serie a descripciones en
> lenguaje natural para que un modelo de lenguaje razone sobre ellas, en lugar de
> alimentarlo con números crudos.
>
> Lo que hay que responder para nuestro caso: **¿aplica a un problema de
> clasificación de tres clases sobre seis series simultáneas?** Y si aplica, ¿qué
> costo tiene traducir 13 114 velas a texto?
>
> Si no lo medimos, se dice que no se midió. No hace falta implementarlo para
> descartarlo, pero sí decir con qué criterio se descarta.

---

## 3. FinLSPM (Large Stock Predict Model)

> **ESCRIBÍ ACÁ.** Qué es y para qué se diseñó. El punto de análisis: está pensado
> para **acciones**, y la sección de criptoactivos de la Semana 1 midió que las
> criptomonedas carecen del anclaje de valoración fundamental que sí tienen las
> acciones. Preguntate en voz alta si eso lo hace transferible o no.
>
> Verificá si el código está disponible: el enunciado exige **usar un modelo cuyo
> código esté disponible**, y ese es un criterio de descarte tan válido como el
> rendimiento.

---

## 4. CryptoMamba

**Medido:** no se puede instalar sin CUDA en las máquinas del equipo.

`mamba-ssm` publica en PyPI una única distribución de código fuente y **ninguna
rueda precompilada**, de modo que todo se compila desde fuente. Sin `nvcc`, el
`setup.py` de `causal-conv1d` avisa y después falla contra su propia variable
indefinida: `NameError: name 'bare_metal_version' is not defined`. Probado en un
entorno desechable, nunca en el del proyecto. Fuente:
[`m3-spike-cryptomamba.json`](../../evidencias/m3-spike-cryptomamba.json).

> **ESCRIBÍ ACÁ.** Explicá qué es un modelo de espacio de estados y en qué se
> diferencia de un Transformer: coste lineal con la longitud de la secuencia frente
> a cuadrático, y estado recurrente frente a atención sobre toda la ventana.
>
> **Y acá está el punto fuerte de tu sección, que conviene decir nosotros primero:**
> el enunciado pide *"primero un modelo fundacional y segundo un Transformer"* y
> menciona CryptoMamba entre las opciones para el segundo. **CryptoMamba no es un
> Transformer**, es un modelo de espacio de estados; son familias distintas. Sumado
> a que no se puede instalar sin CUDA, son dos razones independientes para no
> elegirlo. Está en la consulta al profesor.

---

## 5. Transformer

> **ESCRIBÍ ACÁ.** El punto que la asignación añadió y que no estaba en la tabla
> original del enunciado, así que hay que cubrirlo bien.
>
> Qué es el mecanismo de atención y por qué se propuso para series temporales.
> Después el matiz que importa: existe literatura que cuestiona su ventaja real en
> pronóstico de series largas frente a alternativas mucho más simples, y también
> variantes diseñadas específicamente para series —Informer, iTransformer— que el
> enunciado nombra. Elegí una posición y sostenela con una cita.
>
> Conectá con nuestros datos: con clases desbalanceadas y **420 ejemplos de la clase
> minoritaria en entrenamiento**, ¿es razonable entrenar un modelo con atención desde
> cero? Esa pregunta es la que enlaza con la sección 6.

---

## 6. Justificación de la elección de modelo

> **ESCRIBÍ ACÁ.** Es el punto que más pesa, porque es donde se ve si las cinco
> secciones anteriores sirvieron para decidir o solo para describir.
>
> La estructura que funciona: **criterios primero, candidatos después.** Declará los
> criterios antes de aplicarlos —que corra en CPU, que el código esté disponible, que
> el tiempo de inferencia quepa en el bloque de validación, que no obligue a cambiar
> el entorno del equipo— y recién entonces pasá cada candidato por ellos.
>
> Tenés medido lo suficiente para que la decisión no sea una opinión: la Tabla 1 para
> el coste, el spike de CryptoMamba para la viabilidad, y el modelo clásico de
> referencia como piso contra el que comparar.
>
> **Y decí también qué queda sin resolver.** Un modelo fundacional pronostica la
> trayectoria del precio, no la etiqueta de tres clases: hay que explicar cómo se
> pasa de lo uno a lo otro, y que aplicar `etiquetar()` sobre la trayectoria
> pronosticada cuesta 12 segundos sobre todo el bloque. Es una decisión de diseño,
> no un detalle.

---

## Referencias

> **ESCRIBÍ ACÁ.** Formato APA 7, con DOI. Mínimo una fuente por modelo: TSFMs,
> VTA, FinLSPM, CryptoMamba y Transformer.
>
> Verificalas antes de entregar:
> `uv run python scripts/verificar_referencias.py docs/entregas/semana-2/*.md`
>
> El script comprueba contra Crossref que existan y que **ninguna esté retractada**.
> En la Semana 1 encontró una que sí lo estaba.
