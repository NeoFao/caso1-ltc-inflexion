# Marco teórico: métricas de evaluación para puntos de inflexión

**Autor:** Alejandro Zamora · **Issue:** [S1-M2-06](https://github.com/NeoFao/caso1-ltc-inflexion/issues/33)

Es el noveno punto del bloque de criptoactivos del enunciado. Va en archivo aparte porque tiene evidencia propia y da para una sección completa.

> **Esqueleto.** Los números están medidos y son citables. Falta tu texto.

---

## El problema que hace falta explicar antes que nada

![Figura A](../../evidencias/mt-09a-balance-clases.png)

**Figura A.** Distribución de las tres clases en LTC con `w = 5` sobre velas diarias.

Las clases están desbalanceadas **por construcción, no por accidente**: como mucho 1 de cada `w+1` velas puede ser máximo, así que la clase Continuidad domina inevitablemente.

> **ESCRIBÍ ACÁ.** Explicá por qué el desbalance es estructural y no un problema de los datos. Conectá con la cota aritmética de la sección 7 de tu otro archivo.

---

## Por qué la exactitud no sirve: medido, no argumentado

![Figura B](../../evidencias/mt-09b-confusion-baseline.png)

**Figura B.** Matriz de confusión del *baseline* trivial, un modelo que siempre responde "Zona de Continuidad".

**Medido sobre LTC, `w = 5`, velas diarias:**

| Métrica | Baseline trivial |
|---|---|
| Exactitud | **0,869** |
| F1 macro | **0,310** |
| Precisión direccional | **0,000** |

> **ESCRIBÍ ACÁ.** Este es el mejor argumento de toda tu sección y hay que exprimirlo.
>
> Un modelo que **no detecta ni un solo punto de inflexión** — que es literalmente lo único que el proyecto tiene que hacer — alcanza 86,9 % de exactitud. Si reportáramos exactitud, ese modelo parecería bueno.
>
> F1 macro lo desenmascara: 0,310. Y la precisión direccional lo hace evidente: 0,000, porque no acertó ningún giro, ya que no anunció ninguno.
>
> Es el tipo de resultado que conviene poner nosotros antes de que lo pregunten.

---

## Las métricas que sí usamos

> **ESCRIBÍ ACÁ.** Una subsección por cada una. `contracts/metrics.py` documenta cada decisión con su razón; usalo como fuente, pero explicalo con tus palabras.

### F1-Score por clase

> Precisión y exhaustividad, y por qué su media armónica es más exigente que el promedio simple.

### F1 macro y por qué no ponderado

> El macro promedia las tres clases con igual peso. El ponderado premia acertar la clase mayoritaria, que es justo lo que hace bien un modelo inútil. Elegimos macro a propósito y hay que justificarlo.

### Precisión direccional

> **Definición provisional nuestra:** de todas las velas que de verdad fueron máximo o mínimo, qué fracción anunciamos con el tipo correcto. Se ignoran las de Continuidad, porque acertar "aquí no pasa nada" no es acertar una dirección.
>
> **Decilo explícitamente:** el enunciado pide Precisión Direccional sin precisar qué significa en un problema de tres clases y no de regresión. Adoptamos esta definición y está consultada con el profesor. Declarar una ambigüedad y cómo la resolvimos suma; dejarla tapada, resta.

### Matriz de confusión

> Por qué es la única que muestra **qué tipo** de error comete el modelo. No es lo mismo confundir un máximo con un mínimo que confundirlo con continuidad: el primero es un error de dirección y el segundo, de detección.

---

## El baseline como piso obligatorio

> **ESCRIBÍ ACÁ.** Cerrá con el criterio de decisión del proyecto: todo modelo se compara contra el baseline trivial, y si no lo supera en F1 macro, no aporta nada por mucho que su exactitud impresione. Están implementados tres baselines — trivial, mayoritario y aleatorio — para poder distinguir si un modelo aprendió algo o si solo está acertando por frecuencia de clase.

---

## Referencias

> **ESCRIBÍ ACÁ.** APA. Al menos una fuente sobre evaluación con clases desbalanceadas y una sobre F1 macro contra ponderado.

---

> **Nota sobre los números.** Todos salen de `docs/evidencias/marco-teorico.json`, medidos con `w = 5` sobre velas diarias, que es el valor **provisional**. Si el equipo congela `w = 7` sobre 4 horas, estos tres números cambian: se regeneran con `uv run python scripts/figuras_marco_teorico.py` y se actualizan. El argumento no cambia; los números sí. Citalos siempre indicando el `w` usado.
