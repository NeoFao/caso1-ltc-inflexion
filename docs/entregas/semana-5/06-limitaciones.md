# 6. Limitaciones

**Autor:** Fabrizio Espinoza (M0) · **Fuente del material:** `docs/06-aporte-multivariante.md`,
D14, D15, D16, D20, D24, D25 · **Todas las cifras salen de `docs/evidencias/`.**

El enunciado pide explícitamente **«un análisis de las limitaciones del enfoque con datos
estáticos»**. Esta sección lo da, y añade dos limitaciones más que aparecieron midiendo.

Ninguna de las cuatro es una opinión: las cuatro están medidas, y de tres de ellas se conoce el
**mecanismo**, que es lo que las vuelve útiles en vez de una lista de disculpas.

---

## 6.1 Los activos de apoyo aportan poco, y no lo mismo en las dos familias

**La limitación se declara por familia, no en general** (D24, D25).

| Familia | ¿El aporte se distingue del azar? |
|---|---|
| **Bosque** | **No.** Diferencia de 0,00078 en F1 macro, con el signo cambiando entre semillas y del mismo tamaño que un control que añade columnas duplicadas |
| **Avanzado** | **Tampoco se puede afirmar.** La diferencia es positiva en las cinco semillas de dos barridos independientes, pero la condición del intervalo **no se reproduce** (6.3) |

**El mecanismo está medido, y es lo que hace útil esta limitación.** El profesor señaló en clase que
una variable exógena aporta si es proporcional o **inversamente** proporcional a la objetivo: una
que se mueve igual trae poco; una que se mueve al revés trae información que la objetivo no tiene.

Se midió: **entre los seis activos no hay ninguna relación inversa.** Los quince pares van de
**+0,5175 a +0,8300**, y con LTC en particular de **+0,5831** (SOL) a **+0,7528** (ETH).

No es que los cinco activos sean malas variables. Es que son **redundantes** con LTC, y la
redundancia no informa (D20).

**Se intentó construir una variable decorrelacionada con los mismos datos**, antes de concluir que
haría falta traer un activo de fuera. Criterio fijado antes de mirar: decorrelacionada si
`|correlación| < 0,3`. De seis candidatas, **dos** lo cumplen — la fuerza relativa LTC/SOL
(**+0,1903**) y LTC/ADA (**+0,2763**).

**La limitación real, entonces, no es «las exógenas no sirven».** Es más precisa: *estos seis
activos* no sirven porque se mueven juntos, y la vía para arreglarlo es traer información de otra
naturaleza —no otra criptomoneda—, o construir cocientes que rompan la proporcionalidad.

---

## 6.2 Ningún modelo profundo mejora al bosque clásico

Es la limitación más incómoda porque contradice lo que el enunciado sugiere esperar.

- **Chronos-Bolt** queda 0,021908 por debajo del bosque, con intervalo que incluye el cero: no se
  distingue de él.
- **iTransformer** queda por debajo del bosque **en las cinco semillas** — 0,345357 de media contra
  0,380975.
- **Ninguno de los dos supera al `baseline_aleatorio` de forma distinguible** (tabla 5.2).

**Lo que no se afirma:** que el iTransformer sea distinguiblemente **peor** que el bosque. El
intervalo que decía eso no se reproduce (6.3). Lo que sostiene la fila es el signo estable, no el
intervalo de una corrida.

**Y ese signo resultó ser mucho más estable de lo que se pensaba.** Medido después de la corrida
sobre nueve tramos consecutivos, con validación walk-forward: el iTransformer queda por debajo del
bosque en **9 de 9**, con diferencia media **−0,031591** y sin quedar por encima en ninguno. Es
exactamente la forma de evidencia que la [D25](../../DECISIONES.md) dijo que debía llevar el peso
cuando el intervalo no aplica — y nueve períodos pesan más que cinco semillas sobre un solo bloque.
Ver las conclusiones.

**Una hipótesis honesta sobre por qué.** Estos modelos están construidos para pronosticar **valores**
de una serie, y aquí se les pide **clasificar** un estado definido por catorce comparaciones
estrictas sobre los vecinos. La sección 6.4 mide por qué ese puente es caro. No es una explicación
verificada; es la lectura que la evidencia sugiere, y se declara como hipótesis.

---

## 6.3 Un criterio del proyecto no se puede aplicar a uno de los modelos

Esta limitación no es del enfoque: es **del instrumento de medición**, y apareció ensayando la
corrida final el día antes de la entrega.

El proyecto fijó de antemano (D16) tres condiciones para afirmar que una diferencia se distingue del
azar: media positiva, **intervalo pareado que excluya el cero**, y signo estable en cinco semillas.

**La segunda condición no se reproduce cuando entra el iTransformer.** Volviendo a medir validación
con el mismo código y los mismos datos, el intervalo cruzó el cero en las dos corridas del ensayo,
mientras la corrida comprometida lo excluía por menos de una milésima.

**El diagnóstico, que es lo que lo vuelve útil:** el remuestreo pareado resamplea las **filas**
condicionando en **un solo sorteo del entrenamiento**; la condición del signo mira **cinco sorteos**.
Cuando el sorteo del entrenamiento es la fuente dominante de variación, el intervalo de una corrida
no es un instrumento frágil — **es el instrumento equivocado**, porque su supuesto de predicciones
fijas no se cumple.

**Se midió si el modelo se podía hacer reproducible**, antes de descartar esa vía. Tres palancas, las
tres fallan: hilos fijos con algoritmos deterministas, semilla de *hash* fija, y semilla fija — con
las tres, la pérdida final sigue cambiando entre procesos.

**Y hay una segunda mitad de esta limitación, que es de tamaño y no de instrumento.** Aun cuando la
condición se puede aplicar, hace falta muestra suficiente para que signifique algo. La Figura 1 lo
cuantifica: con las **1 960 velas** del bloque de prueba, un efecto como el que este sistema tiene se
detecta **el 80 % de las veces**. Es el umbral convencional — defendible, pero sin margen.

![Curva de potencia](../../evidencias/informe-f4-curva-potencia.png)

**Figura 1.** Cuánta muestra hacía falta para ver el efecto que hay. El bloque que se usó cae
exactamente sobre el 80 %. Fuente: `docs/evidencias/informe-f4-curva-potencia.png`.

**Y el alcance está acotado, también medido:** el bosque y el `baseline_aleatorio` reproducen **bit a
bit entre procesos**, con la misma huella SHA-256 de las 1 959 predicciones. La comparación de la que
depende el veredicto del proyecto no está afectada.

La **D25** decide en consecuencia, **antes** de tocar el bloque de prueba: donde entre un modelo que
no reproduce, el intervalo se reporta pero no decide.

> **Lo que haríamos distinto**, y queda escrito porque es la parte reutilizable: aplicar la condición
> del intervalo **dentro de cada semilla** y leer en cuántas de las cinco excluye el cero. Respeta el
> supuesto del remuestreo en vez de violarlo y cuesta poco, porque las cinco semillas ya se corren.
> No se adoptó a dos días de la entrega: cambiar el guion otra vez y repetir el ensayo tenía más
> riesgo que beneficio.

---

## 6.4 El puente de trayectoria a etiqueta amplifica diferencias mínimas

El etiquetador exige que los `2w` vecinos sean **estrictamente** menores que el centro: con `w = 7`,
**catorce comparaciones estrictas** encadenadas.

Sobre un pronóstico suave, un vecino que difiere del centro en 10⁻¹¹ decide la clase. Y ese orden de
magnitud es exactamente el de las diferencias de reducción en punto flotante entre dos corridas.

**Medido:** dos corridas del modelo avanzado **con la misma semilla** dan 0,341851 y 0,346685. La
diferencia no viene de la semilla —está fija— sino de que el etiquetador amplifica ruido numérico
hasta el nivel de la clase (D15).

**La consecuencia práctica** llega hasta el método: el rango entre cinco semillas del modelo avanzado
es **0,030377**, que **supera el umbral de decisión de 0,02** fijado en la D5. Con esa dispersión,
elegir la mejor celda de una rejilla no selecciona la mejor configuración: selecciona **la celda a la
que le tocó la semilla más afortunada**. Por eso la D15 obliga a promediar cinco semillas por celda y
a comparar de forma pareada.

Es la limitación con la consecuencia más amplia del informe: no cambia una cifra, cambia **cómo se
puede elegir** entre configuraciones.

---

## 6.5 El análisis con datos estáticos, que es lo que el enunciado pide

Las cuatro limitaciones anteriores tienen un origen común, y conviene decirlo junto.

**El sistema se entrena y se evalúa sobre un panel congelado**: 13 114 velas, del 11/08/2020 al
05/08/2026, descargadas una vez. De ahí se siguen cuatro cosas:

**1. No hay adaptación a régimen.** El bloque de entrenamiento cubre casi seis años. La partición es
cronológica, así que el modelo se entrena con el pasado y se evalúa con el futuro —eso está bien—,
pero **el modelo no se reentrena**. Si el comportamiento del mercado cambia, nada lo detecta ni lo
corrige.

**2. Un solo período es una sola muestra.** Todas las cifras salen de una ventana temporal concreta.
No hay forma, con datos estáticos, de distinguir «el modelo detecta puntos de inflexión» de «el
modelo detecta puntos de inflexión **en este período**». Sería necesario evaluar sobre períodos
independientes, y la historia común disponible no da para eso: la acota Solana, y bajar la
granularidad **subdivide** la historia, no la añade.

**3. La cola nunca está confirmada.** Las últimas 8 velas —**32 horas**— no tienen etiqueta real
todavía. En un panel estático se ve como un detalle del final; en producción es **permanente**: el
sistema opera siempre con las últimas 8 predicciones sin verificar. La D21 obliga a mostrarlas
marcadas, porque ocultarlas haría parecer el sistema mejor de lo que es.

**4. Los activos de apoyo se eligieron de un universo estático.** Los seis son criptomonedas
grandes, y la 6.1 midió que se mueven juntas. Un enfoque con datos vivos podría **buscar**
variables decorreladas en vez de fijar seis de antemano.

**En una frase:** con datos estáticos se puede demostrar que el circuito es correcto y que el modelo
detecta mejor que el azar sobre un período. **No** se puede demostrar que siga haciéndolo, y este
informe no lo afirma.

---

## 6.6 Resumen

**Tabla 1.** Las cuatro limitaciones.

| # | Limitación | ¿Medida? | ¿Se conoce el mecanismo? |
|---|---|---|---|
| 1 | Los activos de apoyo aportan poco, y no igual en las dos familias | sí | sí — proporcionalidad, sin relación inversa |
| 2 | Ningún modelo profundo mejora al bosque | sí | hipótesis, no verificada |
| 3 | La condición del intervalo no aplica al modelo no reproducible | sí | sí — el supuesto del remuestreo no se cumple |
| 4 | El puente de trayectoria a etiqueta amplifica ruido numérico | sí | sí — catorce comparaciones estrictas |

Las cuatro se encontraron **midiendo**, y tres de ellas **contradiciendo lo que el equipo esperaba o
había afirmado antes**. Ese es el argumento de que la lista está completa hasta donde se pudo mirar:
no es una lista de precauciones escritas al final, es lo que quedó después de que cada afirmación
cómoda se cayera al comprobarla.

---

## Referencias

Ansari, A. F., Stella, L., Turkmen, C., Zhang, X., Mercado, P., Shen, H., Shchur, O.,
Rangapuram, S. S., Pineda Arango, S., Kapoor, S., Zschiegner, J., Maddix, D. C.,
Wang, H., Mahoney, M. W., Torkkola, K., Wilson, A. G., Bohlke-Schneider, M., &
Wang, Y. (2024). *Chronos: Learning the language of time series* (Preprint). arXiv.
https://doi.org/10.48550/arXiv.2403.07815

Breiman, L. (2001). Random forests. *Machine Learning, 45*(1), 5–32.
https://doi.org/10.1023/A:1010933404324

Liu, Y., Hu, T., Zhang, H., Wu, H., Wang, S., Ma, L., & Long, M. (2023). *iTransformer:
Inverted transformers are effective for time series forecasting* (Preprint). arXiv.
https://doi.org/10.48550/arXiv.2310.06625

Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, L.,
& Polosukhin, I. (2017). *Attention is all you need* (Preprint). arXiv.
https://doi.org/10.48550/arXiv.1706.03762

Wang, P. (2024). *iTransformer* (Versión 0.8.1) [Software]. GitHub.
https://github.com/lucidrains/iTransformer

Zeng, A., Chen, M., Zhang, L., & Xu, Q. (2023). Are Transformers effective for time
series forecasting? *Proceedings of the AAAI Conference on Artificial Intelligence,
37*(9), 11121–11128. https://doi.org/10.1609/aaai.v37i9.26317

> **Sobre esta lista.** Son las fuentes que el informe **usa**, no las que revisó: el marco
> teórico completo está en los avances 1 y 2, con veintitantas referencias verificadas contra
> Crossref. Aquí van solo las que sostienen una afirmación de este documento.
>
> **Por qué el iTransformer aparece dos veces.** Se cita el **artículo** (Liu et al., 2023),
> que es la arquitectura, y el **software** (Wang, 2024), que es la implementación que de verdad
> se ejecutó. No son la misma fuente y el proyecto ejecutó la segunda.
>
> El artículo estuvo fuera de esta lista hasta que M3 lo verificó contra la página del propio
> artículo, con el DOI comprobado: mientras no lo estuvo, no se añadió de memoria. **Se cita por
> su DOI de arXiv y no como ICLR 2024**, que es como suele verse, porque la página del artículo
> no declara sede de publicación y eso no se verificó.
