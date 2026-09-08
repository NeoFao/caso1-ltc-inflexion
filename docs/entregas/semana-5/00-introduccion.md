# Introducción

**Autor:** Fabrizio Espinoza (M0) · **Revisa:** el equipo · **Todas las cifras salen de
`docs/evidencias/`.**

---

## Qué se construyó

Un sistema que clasifica cada vela de Litecoin en tres estados —**máximo local**, **mínimo local**
o **continuidad**— y una aplicación web que muestra esas predicciones sobre el precio.

El enunciado pedía un modelo fundacional y un Transformer. Hay los dos, y hay además un tercero que
el enunciado no pedía y que resultó ser el que mejor funciona:

| Modelo | Qué es | Por qué está |
|---|---|---|
| **Bosque aleatorio** | Clásico, `scikit-learn` | Referencia obligatoria: sin él, «el modelo profundo funciona» no significa nada |
| **Chronos-Bolt** | Fundacional, *zero-shot* | Lo pide el enunciado (D12) |
| **iTransformer** | Transformer entrenado | Lo pide el enunciado (S4-M3-01) |

Y tres modelos de referencia —trivial, mayoritario y aleatorio— que existen para que ningún
resultado se pueda leer como bueno sin compararlo contra no hacer nada.

---

## Qué se puede afirmar hoy, y qué no

Esta es la parte incómoda del informe, y va al principio a propósito.

**Se puede afirmar:**

- El circuito completo **funciona y no tiene fuga**. Las cuatro pruebas de detección pasan, incluida
  la que alimenta el modelo vela a vela y comprueba que predice **exactamente lo mismo** que
  procesando el bloque entero: 500 velas, **cero discrepancias** (sección 4).
- **El bosque detecta las dos clases extremas mejor que el azar**, con el criterio fijado antes de
  medir. Sobre validación: F1 máximo 0,108108 contra 0,051813 del azar, F1 mínimo 0,140351 contra
  0,053763 (sección 5). Y sobre 7 311 mediciones independientes, con intervalos que **excluyen el
  cero en las dos clases** (conclusiones).
- **El modelo fundacional también supera al azar** de forma distinguible, cuando se lo mide con
  muestra suficiente.
- **Ningún modelo profundo mejora al bosque clásico.** Ni el fundacional ni el avanzado, y el
  avanzado queda por debajo en los **nueve** períodos medidos.

**No se puede afirmar:**

- Que el sistema sirva para operar. La precisión direccional del mejor modelo sobre validación es
  **0,103627**. Es mejor que el azar y sigue siendo baja.
- **Que detecte mejor que el azar sobre el bloque de prueba.** Es la única medición limpia del
  informe, se hizo una sola vez, y cumple **dos de las tres** condiciones que el equipo fijó de
  antemano (sección 5). Que con más datos la misma ventaja sí se distinga **no cambia esa cifra**:
  la explica.
- Que los cinco activos de apoyo aporten de forma distinguible (secciones 2 y 6).
- Que el **iTransformer** supere al azar. No lo hace ni con cuatro veces más mediciones — ahí no
  falta muestra.

> **La tensión entre las dos listas es real y no se esconde.** El resultado que se reporta como
> oficial es el del bloque de prueba, y es el más conservador. Todo lo demás se midió **después**,
> sobre datos que sí se pueden volver a mirar, y sirve para explicar por qué ese resultado salió
> como salió — no para reemplazarlo. Las conclusiones lo desarrollan.

---

## Lo que este proyecto trató de hacer bien, y por qué se cuenta

El riesgo de un trabajo así no es que el modelo salga mal. Es que **salga bien por la razón
equivocada** y nadie se entere: una fuga de información, un criterio elegido después de ver el
resultado, una cifra copiada de una corrida que ya no existe.

Contra eso el proyecto adoptó tres reglas, y el informe las declara porque explican por qué sus
números se pueden creer:

1. **Nada se afirma sin medir**, y cada cifra publicada tiene que existir en `docs/evidencias/`. Un
   verificador recorre los documentos y falla si encuentra un número sin respaldo. Atrapó errores
   reales, incluidos varios propios.
2. **Los criterios se fijan antes de mirar el resultado**, por escrito, en `docs/DECISIONES.md`. Y
   se dejan escritos aun cuando después haya que corregirlos.
3. **El bloque de prueba se mide una sola vez** (D18), con un pestillo que hace comprobable esa
   afirmación en vez de solo declararla.

El documento incluye los errores que se cometieron aplicándolas. No por franqueza decorativa: un
informe que solo cuenta lo que salió bien no da forma de saber si lo que cuenta es cierto.

---

## Cómo leer este informe

| Sección | Qué responde |
|---|---|
| **1. Diseño** | Qué se predice exactamente, sobre qué datos, y por qué esos parámetros y no otros |
| **2. Ingeniería de características** | Qué ve el modelo, y qué usa de verdad |
| **3. Los dos modelos** | Qué son el fundacional y el avanzado, y qué costaron |
| **4. Pruebas de detección** | Las cuatro pruebas que el enunciado pide, y qué demuestra cada una |
| **5. Rendimiento** | La comparación sobre validación y la medición única sobre el bloque de prueba |
| **6. Limitaciones** | Lo que el enfoque no puede, incluido el análisis con datos estáticos |
| **Conclusiones** | Lo que se sostiene y lo que no |

Las secciones 1 a 4 se pueden leer sueltas. Las 5 y 6 dependen de la 1: sin saber qué es un punto de
inflexión aquí, las métricas no significan nada.
