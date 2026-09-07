# El modelo fundacional

**Autor:** Isaac Fallas (M3) · **Ensamblado por** Fabrizio Espinoza (M0) desde la sección
de M3 del informe final, sin reescribir su contenido. **Todas las cifras salen de
`docs/evidencias/`.**

---

## El puente, que es lo que hace comparables a los dos

Ni Chronos-Bolt ni iTransformer clasifican. Los dos **pronostican una trayectoria**, y el problema
pide tres clases. Entre una cosa y la otra hay un puente, y está construido igual para los dos:

1. Estando en `t`, se pronostican `w + h` velas — con `w = 7` y `h = 1`, ocho velas.
2. Con ellas se arma una ventana de `2w + 1` centrada en `t + h`.
3. Se le aplica `etiquetar()` **del contrato**, el mismo que produjo las etiquetas reales.
4. Se lee el centro.

**Que los dos crucen igual no es un detalle de implementación: es lo que permite restar sus F1.**
Si cada uno cruzara a su manera, la diferencia entre ambos mezclaría el modelo con el puente y no
mediría lo que dice medir.

El puente está probado contra fuga con la misma prueba en las dos familias: se perturba el futuro
posterior al corte y se exige que la predicción de instantes anteriores **no se mueva**.

---

---

## Chronos-Bolt

**`amazon/chronos-bolt-small`, contexto 512, cuantil 0,5, cero entrenamiento** (D12).

Es un modelo de series temporales preentrenado que se usa **zero-shot**: no ve ni una vela de
nuestro conjunto de entrenamiento. Eso lo hace determinista —cinco semillas dan idéntico— y explica
por qué su fila del protocolo no lleva rango.

De las 1 959 filas de validación, **0 quedaron sin historia suficiente** para el contexto de 512,
así que la cifra no está calculada sobre un subconjunto cómodo.

| | F1 macro | Precisión Direccional | Exactitud |
|---|---|---|---|
| Chronos-Bolt | **0,368589** | 0,093264 | 0,830015 |

---
