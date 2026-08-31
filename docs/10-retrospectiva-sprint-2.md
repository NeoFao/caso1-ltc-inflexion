# Retrospectiva del Sprint 2

**Del 18 al 31 de agosto de 2026** · Escrita por Fabrizio Espinoza (M0)

Se entregaron los dos avances. Pero lo que este sprint enseñó no fue sobre modelos.

---

## Lo que pasó, en números medidos

| | |
|---|---|
| PR fusionados | **28** — 15 de M2, 11 de M3, 2 de M1 |
| Issues cerrados | 23 |
| Decisiones registradas | 18 |
| Pruebas al cerrar | 262, más 9 que se saltan sin el grupo `modelos` |
| Evaluaciones sobre el bloque de prueba | **0.** La reserva sigue intacta |

Los dos entregables salieron completos y verificados: 421 números en las entregas y 219 en el material de defensa, todos respaldados por una medición.

---

## El hallazgo del sprint no es técnico

Encontramos **nueve defectos** que compartían una sola forma. No nueve errores distintos: **un patrón con nueve apariciones**, que es como lo planteó Alejandro y tiene razón, porque el arreglo también es uno solo.

> **Algo dejó de funcionar, no falló de forma visible, y siguió pareciendo correcto desde afuera.**

Ninguno se encontró leyendo código. **Todos aparecieron ejecutando un control o buscando el patrón a propósito.**

### Los nueve

| # | Qué | Cómo se veía | Quién lo encontró |
|---|---|---|---|
| 1 | La autocorrelación comparaba la estimación contra su propio límite superior | Daba cero, y cero es un resultado plausible | Un control que tenía que reproducir «3 de 40» |
| 2 | Cinco atribuciones falsas en `main` | Un mensaje firmado se dio por bueno | M2, leyendo su propio módulo |
| 3 | El ensamblador descartaba en silencio los bloques pendientes | El documento salía «completo» | M0, al revisar por qué faltaban las conclusiones |
| 4 | `m2-ablacion.json` medía dos representaciones sin decirlo | **Ninguna línea de código cambió** | M2, comparando dos mitades del mismo archivo |
| 5 | El estudio de `w` y `h` heredaba un default que había cambiado | El guion corría igual | M0 y M2, por separado, con el mismo barrido |
| 6 | El backend truncaba la marca de tiempo | La app funcionaba, con **una sexta parte de los datos** | M0, al levantar la app por primera vez |
| 7 | Un import fallido abortaba la suite entera | **Cero pruebas ejecutadas**, y se ve igual que verde | M2, yendo a comprobar un «cero abiertos» |
| 8 | El verificador aprobaba sobre cero archivos, con salida 0 | «Todos respaldados por una medición» | M2, verificando sus propios documentos |
| 9 | `evaluar_modelo()` tenía `conjunto="prueba"` por omisión | Nadie lo omitía, pero era una trampa esperando | M0, al conectar el pestillo |

### Los tres que más enseñan

**El 6 y el 7 son de la misma familia y en direcciones opuestas.** En el 6, M1 detectó el síntoma y lo compensó en su capa con un filtro; la vista funcionaba, así que nadie miró debajo, y **el 84,4 % de los puntos de inflexión no se dibujaba**. En el 7, el defecto estaba en mi archivo y M2 verificó varios PR contra una suite que no arrancaba.

> **Un parche que compensa un defecto ajeno es la forma más difícil de detectarlo, porque todo parece funcionar.**

**El 8 es el peor, y es mío.** El verificador de números es el instrumento que produce el «421 números respaldados» que cité en cada informe de estado de este sprint. Aprobaba sobre cero archivos y salía con código 0.

> **El mecanismo de verificación mismo puede ser lo que falle en silencio.**

---

## Lo que funcionó, y conviene repetir

### El control que reproduce un número conocido

Es la regla 2, y es la que atrapó los defectos 1, 4 y 5. Su forma más fuerte la escribió M2 en el PR #61: **los valores de control se copian del documento entregado, no del JSON**. Un JSON regenerado por accidente pasaría el control comparándose consigo mismo.

### Fijar el criterio antes de mirar el resultado

Funcionó dos veces de forma comprobable:

- **La rejilla del modelo avanzado.** La celda `48/32` daba 0,346696 contra 0,345129 de la por defecto: era mejor. El criterio de la D15, escrito antes, decía que el ruido entre semillas superaba la señal entre celdas. **M3 no la coronó.**
- **La hora del día.** La tasa de giros va de 8,15 % a 10,49 %, con el máximo cuando abre Estados Unidos. Se ve como un patrón. El contraste da p = 0,083 y no lo es.

### Dos mediciones independientes que coinciden

Pasó tres veces sin que nadie lo planeara: el F1 del bosque, `0.390497720487045`, lo obtuvieron M2 y M3 por separado con código distinto. La información mutua de la hora la medimos M2 y yo hasta el sexto decimal. **Salió de que cada uno aplicara la regla 2 por su lado.**

### Reportar el resultado que no queríamos

Tres veces, y las tres se sostienen mejor que si hubieran salido bien:

- Los cinco activos de apoyo **no se puede afirmar que aporten**, y su efecto es del mismo tamaño que añadir columnas duplicadas que por construcción no informan nada.
- **iTransformer es peor que el bosque clásico**, y es la única desventaja distinguible de las tres.
- **Ajustar hiperparámetros no mejora de forma distinguible**, ni en el fundacional ni en el avanzado.

M3 pudo titular el aporte multivariante con el `+0,0212` de la semilla 0, que excluía el cero y cruzaba el umbral. Usó la vista de cinco semillas, que da `+0,0126` y no alcanza. **Eligió la cifra menos favorable.**

---

## Lo que no funcionó

### Verifiqué números con rigor y acepté los enunciados que los rodeaban

Dos veces, y las dos se propagaron:

- **Las cinco atribuciones falsas.** Un mensaje sin contexto se dio por bueno y quedó escrito en el código.
- **«La Semana 2 ya se entregó».** Lo escribió M3 en el PR #64. Revisé los nueve valores de esa tabla contra la evidencia y miré con lupa el cambio a `test_decisiones.py`. **No abrí el README que estaba al lado.** Quedó en `DECISIONES.md`, y M2 construyó una decisión encima.

Bajo esa premisa, la cuarta conclusión de la Semana 2 era intocable. Como era falsa, **íbamos a entregar una conclusión que ya sabíamos que no se sostenía.**

### Dejé sin responder una consulta de método mientras el equipo avanzaba

M3 planteó en el #37 cómo hacer la búsqueda de hiperparámetros con un modelo cuyo ruido de semilla supera el umbral. Fusioné su PR parcial **sin responderla** y le devolví el issue. Él avanzó dejando escrito que procedía con su propuesta y no con un acuerdo, que es lo correcto — pero el que falló fui yo.

### M1 arrancó tarde

Su primer PR de código entró el 24 de agosto, seis semanas después del inicio. Hasta entonces el código de ese módulo lo había escrito yo entero, lo que funcionó para llegar a las entregas y no funciona como forma de trabajar.

### Dos hashes de commit citados mal

Los dos en el mismo día, los dos corregidos. Escribí la referencia antes de tener el commit hecho — la regla 1 aplicada a algo que no parece un número.

---

## Lo que cambia para el Sprint 3

**Lo que ya está hecho, no propuesto:**

1. **Las decisiones viven en `docs/DECISIONES.md`**, y las que se pueden romper en silencio están fijadas por pruebas. Van 18.
2. **Hay plantilla de PR** con los tres controles.
3. **El verificador falla** en vez de aprobar sobre cero archivos.
4. **Un import fallido no aborta la suite**, y la versión de Python está fijada al parche exacto, también en CI.
5. **Hay una prueba que cruza capas**, y otra que impide que un artefacto nuevo quede sin vigilar.
6. **El bloque de prueba tiene protocolo (D18) y pestillo**: la primera corrida deja constancia y las siguientes fallan sin motivo declarado.

**Lo que hay que hacer y no está hecho:**

- **Enviar la consulta al profesor.** Lleva tres semanas y bloquea la tercera prueba de detección.
- **Nombrar las dos configuraciones que van a prueba**, antes de correr nada. Le toca a M3.
- **Decidir cuándo se congela el código.** Con nueve defectos en dos semanas, gastar la reserva antes de eso es apostar a que no aparezca el décimo.

---

## La regla que resume el sprint

Las dos primeras reglas del proyecto salieron de errores de medición. La tercera, de las atribuciones falsas. Este sprint agrega una cuarta, y sale de los nueve:

> **Un control que nunca se vio fallar no es un control.**

Se aplicó a propósito en todo lo que se escribió después: las pruebas del contrato se rompieron a propósito para verlas fallar, la prueba de detección se comprobó corriendo la etiqueta una posición —de 187/187 a 0/187—, y la prueba entre capas se comprobó falseando una cifra del panel.

**Es más barato que descubrir a posteriori que llevabas dos semanas verificando contra nada.**
