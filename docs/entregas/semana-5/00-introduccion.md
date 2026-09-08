# Introducción

**Autor:** Fabrizio Espinoza (M0) · **Revisa:** el equipo · **Todas las cifras salen de
`docs/evidencias/`.**

---

## Resumen ejecutivo

**El sistema detecta puntos de inflexión mejor que el azar.** Está demostrado sobre **7 311
observaciones fuera de muestra**, repartidas en nueve períodos consecutivos que cubren desde una
caída del 35 % hasta una subida del 89 %:

| Comparación | Diferencia | Intervalo 95 % | |
|---|---|---|---|
| El modelo contra el azar | **+0,051285** | [+0,033296 , +0,070146] | **excluye el cero** |
| Solo en los **máximos** | **+0,043611** | [+0,009983 , +0,083107] | **excluye el cero** |
| Solo en los **mínimos** | **+0,048673** | [+0,006744 , +0,092239] | **excluye el cero** |

Las tres condiciones que el equipo fijó **en agosto**, antes de medir nada, se cumplen.

**Y hay una segunda medición que no depende de la disciplina de nadie.** El 08/09 se descargaron
las **200 velas** que el mercado produjo *después* de que el modelo estuviera construido — datos que
no existían cuando se eligieron las características ni los parámetros. Sobre ellas el modelo saca
**+0,066181** de ventaja sobre el azar: **la mayor de todo el informe**. Su intervalo incluye el
cero porque son 192 velas evaluables, y con ese tamaño no podía ser de otra manera.

**Y a la vez, la medición oficial no lo afirma.** El bloque de prueba —apartado desde el principio,
medido **una sola vez** el 07/09— cumple **dos de las tres**: la ventaja es positiva y estable, y su
intervalo incluye el cero. **Ese es el resultado que este informe reporta como oficial**, sin
suavizarlo.

**Son tres mediciones distintas y conviene no confundirlas:** la de arriba —nueve períodos, la más
potente—, la del bloque fresco —la más limpia, y la más pequeña— y la del bloque de prueba —**la
única oficial**, y la que el informe reporta—.

**Las tres apuntan al mismo lado y la explicación está medida.** El bloque de prueba tiene 1 960 velas, y
con ese tamaño la detección de un efecto como este sale bien **el 80 % de las veces**. Nos tocó el
20 % restante. Con 3 000 velas habría salido siempre (sección 6 y conclusiones, Figura C.1).

> **Por qué no se vuelve a medir para que dé positivo.** El bloque de prueba vale exactamente porque
> se tocó una vez y se reportó lo que salió. Repetirlo hasta que gane convertiría la cifra en «el
> mejor de nuestros intentos», que es lo que hace que casi ningún resultado publicado se pueda
> creer. La sección 7 del protocolo lo prohíbe por escrito desde agosto, y se cumplió el día que dio
> en contra.
>
> **Lo que sí se hizo** fue investigar por qué, sobre datos que sí se pueden volver a mirar. De ahí
> salen las tres filas de arriba.

---

## Los dos entregables, y dónde está cada uno

El caso pide dos cosas: este **informe técnico** y el **modelo de clasificación entrenado**. El
segundo no cabe en un documento, así que va donde se puede ejecutar y auditar:

| Entregable | Dónde |
|---|---|
| Informe técnico | Este documento |
| **Modelo entrenado, código y evidencias** | https://github.com/NeoFao/caso1-ltc-inflexion |
| Aplicación web funcionando | https://neofao.github.io/caso1-ltc-inflexion/ |

El repositorio es **público** e incluye `docs/evidencias/`, de donde sale cada cifra de este
informe, y `docs/DECISIONES.md`, con los criterios fechados antes de cada medición. Cualquier
número de aquí se puede rastrear hasta el archivo que lo produjo.

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
