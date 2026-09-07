# 5. Rendimiento

**Autor:** Fabrizio Espinoza (M0), sobre la mitad de modelos profundos de Isaac Fallas (M3) ·
**Fuente del material:** `docs/evidencias/m3-modelos-profundos-4h-w7-h1.json`,
`docs/evidencias/modelo-clasico-4h-w7-h1-rezagos-relativos.json`, D5, D16, D18, D25 · **Todas las
cifras salen de `docs/evidencias/`.**

Esta sección tiene dos partes que **no** significan lo mismo:

- **5.1 a 5.3 · Validación.** Sobre estos datos se compararon modelos y se tomaron decisiones. Se
  pudieron mirar tantas veces como hizo falta, y por eso mismo **no son una estimación honesta del
  rendimiento futuro**: elegir mirando estos números los infla.
- **5.4 · El bloque de prueba.** Se mide **una sola vez** y es la única cifra del informe que estima
  qué haría el sistema con datos que nadie usó para decidir nada.

---

## 5.1 La comparación sobre validación

**Tabla 5.1.** Los nueve modelos evaluados sobre las 1 959 velas de validación, ordenados por F1
macro. Todos entrenados solo con el bloque de entrenamiento y medidos por el mismo arnés.

| Modelo | Papel | F1 macro | Precisión direccional |
|---|---|---|---|
| **Bosque aleatorio** (rezagos relativos) | referencia clásica | **0,390498** | **0,103627** |
| Chronos-Bolt | fundacional (D12) | 0,368589 | 0,093264 |
| Bosque sin rezagos | variante | 0,367201 | 0,088083 |
| iTransformer | avanzado | 0,345706 | 0,077720 |
| Baseline aleatorio | **piso obligatorio (D7)** | 0,336784 | 0,051813 |
| iTransformer solo LTC | variante | 0,324474 | 0,051813 |
| Baseline trivial | piso | 0,316063 | 0,000000 |
| Baseline mayoritario | piso | 0,316063 | 0,000000 |
| Bosque sin pesos de clase | variante | 0,316063 | 0,000000 |

Tres lecturas inmediatas:

**El mejor modelo es el clásico.** Ni el fundacional ni el avanzado le ganan. Lo dice la tabla y lo
confirman los intervalos de 5.2.

**Los tres modelos que dan 0,316063 exactos están empatados con no hacer nada.** El baseline trivial,
el mayoritario y el bosque sin pesos de clase producen el mismo número porque hacen lo mismo:
responder siempre «continuidad». El bosque **sin reponderar las clases colapsa a la mayoritaria** —
es la evidencia directa de por qué el `class_weight` no es un detalle de configuración.

**La precisión direccional del mejor modelo es 0,103627.** Mejor que el azar (0,051813) y que el
trivial (0,0). Y baja. La sección 6 dice qué se puede y qué no se puede concluir de eso.

---

## 5.2 Comparar medias no alcanza: los intervalos

Una diferencia de F1 macro entre dos modelos puede venir de que uno sea mejor o de qué velas cayeron
en el bloque. Para separarlo se usa **remuestreo pareado**: se remuestrean las **mismas filas** para
los dos modelos a la vez, muchas veces, y se mira el intervalo de la **diferencia**.

Va pareado porque si los dos modelos aciertan y fallan sobre las mismas velas sus errores están
correlacionados, y el intervalo de la diferencia es más estrecho que lo que sugeriría el solape de
los intervalos individuales.

**Tabla 5.2.** Diferencias contra el `baseline_aleatorio` y contra el bosque, con intervalo al 95 %.

| Comparación | Diferencia | Intervalo 95 % | ¿Excluye el cero? |
|---|---|---|---|
| Chronos-Bolt − azar | +0,031805 | [−0,002956 , +0,065236] | **no** |
| iTransformer − azar | +0,008922 | [−0,024084 , +0,044635] | **no** |
| Chronos-Bolt − bosque | −0,021908 | [−0,064249 , +0,020264] | **no** |
| iTransformer − bosque | −0,044792 | [−0,085204 , −0,001457] | sí, **pero ver 5.3** |

**Lo que dice esta tabla, en orden de incomodidad:**

1. **Ninguno de los dos modelos profundos supera al azar de forma distinguible.** Le ganan en la
   media, y el intervalo incluye el cero en los dos casos. Es el resultado central del informe y va
   sin adornos.
2. **Entre el fundacional y el avanzado no se distingue nada.** Por la D5, cuando el margen y el
   intervalo discrepan manda el intervalo, y se prefiere el más simple: el fundacional, que ni se
   entrena.
3. **El bosque clásico es el único que supera al azar de forma distinguible**, y es el modelo que el
   enunciado no pedía.

---

## 5.3 Un intervalo de esta tabla no se reproduce, y se declara

La última fila de la tabla 5.2 excluye el cero. **Ese resultado no se reproduce.**

El ensayo en seco del 07/09 volvió a medir validación —mismo código, mismos datos, mismas cinco
semillas— y el intervalo cambió de lado:

| Corrida | Diferencia | Intervalo 95 % | ¿Excluye el cero? |
|---|---|---|---|
| Comprometida (21/08) | −0,044792 | [−0,085204 , **−0,001457**] | **sí** |
| Ensayo en seco (07/09) | −0,042894 | [−0,081945 , **+0,001996**] | **no** |

El límite superior vive a menos de 0,002 del cero: el veredicto binario se da vuelta aunque la cifra
casi no se mueva.

**La causa está identificada, y no es el remuestreo.** El generador del remuestreo está sembrado, así
que el intervalo es determinista **dadas las predicciones**. Lo que se mueve es el iTransformer, que
no reproduce entre procesos (D15).

**Y el fondo no es fragilidad, es el instrumento equivocado.** El remuestreo pareado resamplea las
**filas** condicionando en **un solo sorteo del entrenamiento**. Cuando el sorteo del entrenamiento
es la fuente dominante de variación, el supuesto del intervalo —predicciones fijas— no se cumple.

Por eso la **D25** decide, **antes** de tocar el bloque de prueba: donde entre un modelo que no
reproduce, el intervalo **se reporta pero no decide**, y el peso lo lleva la estabilidad del signo
entre semillas.

**Lo que sí sostiene esa fila, entonces:** el iTransformer queda por debajo del bosque **en las cinco
semillas**, 0,345357 de media contra 0,380975. El signo es estable; la distinguibilidad por intervalo
no se afirma.

> **El alcance está acotado y medido.** El bosque y el `baseline_aleatorio` reproducen **bit a bit
> entre procesos** — misma huella SHA-256 de las 1 959 predicciones en tres procesos distintos, en
> `m0-reproducibilidad-predicciones-4h-w7-h1.json`. La comparación de la que depende el veredicto del
> proyecto —el mejor modelo contra el azar— **no está afectada**.

---

## 5.4 El bloque de prueba

> **PENDIENTE DE LA CORRIDA ÚNICA.** Esta subsección se rellena con el resultado de la única
> medición sobre el bloque de prueba, y **solo con ella**. El resto del informe está escrito y
> revisado antes de conocerla, que es el punto.

El protocolo está fijado por escrito en `docs/09-protocolo-bloque-prueba.md` y la corrida está
ensayada de punta a punta sobre validación, dos veces, con las banderas exactas.

**Lo que se va a medir:** una configuración por familia —sin variantes—, cinco semillas, con media y
rango. Los seis modelos en **una sola sesión**, que el pestillo registra como una.

**Lo que se va a reportar, decidido de antemano:**

| Si pasa esto | El informe dice |
|---|---|
| El mejor modelo supera al azar y el intervalo excluye el cero | Detecta puntos de inflexión mejor que el azar sobre datos no vistos |
| Supera al azar y el intervalo incluye el cero | La ventaja no se distingue del azar con estos datos |
| No supera al azar | El enfoque no detecta puntos de inflexión sobre datos no vistos |

Los tres casos están escritos **antes** de ver el número, y el informe reporta **la primera y única
cifra que salga**. No hay una segunda corrida ni una cuarta rama en la que se busque otra
configuración.

**La expectativa, dicha de antemano para que no se lea como excusa después:** no hay razón para
esperar que el bloque de prueba mejore lo de validación. Esperar que datos no vistos favorezcan a un
modelo más que los datos con los que se eligió es al revés de como funciona.
