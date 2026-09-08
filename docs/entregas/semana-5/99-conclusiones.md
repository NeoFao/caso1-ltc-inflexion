# Conclusiones

**Autor:** Fabrizio Espinoza (M0) · **Revisa:** el equipo · **Todas las cifras salen de
`docs/evidencias/`.**

---

## Lo que se sostiene

**1. El circuito es correcto y no tiene fuga.** Es la conclusión mejor respaldada del informe. El
etiquetador recupera 187 de 187 vértices plantados; el sistema alimentado vela a vela produce
predicciones **idénticas** a las del bloque completo sobre 500 velas, con **cero discrepancias**. Esa
última prueba es la única que podía detectar que algo mirara filas posteriores, y no lo detectó.

**2. El bosque clásico detecta las dos clases extremas mejor que el azar sobre validación**, con el
criterio fijado antes de medir: F1 máximo 0,108108 contra 0,051813, F1 mínimo 0,140351 contra
0,053763. Es el único modelo del que se puede afirmar eso.

**3. Ningún modelo profundo mejora al bosque.** El fundacional no se distingue de él; el avanzado
queda por debajo en las cinco semillas. Y **ninguno de los dos supera al `baseline_aleatorio` de
forma distinguible**.

**4. Los cinco activos de apoyo no aportan de forma que se pueda afirmar**, y se sabe por qué: los
seis se mueven juntos —de +0,5175 a +0,8300— y **no hay ninguna relación inversa**. Son redundantes
con LTC, y la redundancia no informa.

---

## Lo que no se sostiene

**Que el sistema sirva para operar.** La precisión direccional del mejor modelo sobre validación es
**0,103627**. Es mejor que el azar y sigue siendo baja. El informe no afirma utilidad práctica y no
hay medición que la respalde.

**Que el modelo avanzado sea distinguiblemente peor que el bosque.** Lo decía un intervalo que **no
se reproduce**. Lo que sostiene esa afirmación es el signo estable en cinco semillas, que es una
evidencia más débil y se reporta como tal.

**Que estos resultados se mantengan fuera de este período.** Con un panel estático no hay forma de
separar «el modelo detecta puntos de inflexión» de «los detecta en esta ventana temporal».

---

## Lo que el proyecto aprendió sobre cómo trabajar, que es lo que se lleva

Estas conclusiones importan más que las cifras, porque las cifras valen para un activo y un período,
y esto vale para el próximo trabajo.

**1. Un control que nunca se vio fallar no es un control.** Se adoptó como regla: cada prueba nueva
se rompe a propósito para comprobar que falla. Encontró defectos reales —incluida una prueba que,
al romperle la guarda que protegía, **gastó el bloque de prueba** en una copia local.

**2. El camino que se recorre una sola vez se ensaya entero antes.** La corrida final se ensayó dos
veces sobre validación, en una copia del repositorio. El ensayo encontró tres defectos, uno de los
cuales —un fallo de entorno por el límite de longitud de rutas— **habría reventado la corrida real a
mitad de camino, con la reserva ya gastada y sin poder repetirla**.

**3. Aplicar la regla correcta importa tanto como medir bien.** Una decisión del proyecto concluyó
que un aporte no era distinguible aplicando un umbral que se había fijado para **elegir** entre
modelos, no para responder si algo se distingue del azar. Los números estaban bien; la regla no era
la que correspondía.

**4. Un criterio se decide antes de ver el número, incluso cuando decidirlo tarde sería más cómodo.**
El día antes de la entrega se descubrió que una de las tres condiciones del proyecto no se reproducía
para uno de los modelos. Se decidió qué hacer **antes** de tocar el bloque de prueba. Después de ver
el resultado, cualquier decisión sobre el criterio habría estado contaminada.

**5. Los errores propios se corrigen por escrito y sin reescribir el pasado.** Las decisiones que
resultaron mal leídas siguen en el documento, marcadas como corregidas, con la corrección al lado. Un
documento que se reescribe para parecer que siempre tuvo razón no sirve para aprender de él.

---

## Lo que hicimos después de medir, y qué salió

La corrida sobre el bloque de prueba dejó una pregunta abierta: la ventaja sobre el azar era
positiva y estable en signo, pero su intervalo incluía el cero. **Investigamos por qué**, sin tocar
la reserva —ya gastada— y midiendo todo sobre validación.

### El diagnóstico

Medimos **por cuánto le gana cada extremo a su vecino más cercano**, que es qué tan pronunciado es:

**Tabla 1.** Margen del extremo sobre su vecino más cercano.

| Bloque | Máximos | Mínimos |
|---|---|---|
| Entrenamiento | 0,6372 % | **0,7498 %** |
| Validación | 0,6129 % | **0,8334 %** |
| Prueba | **0,4500 %** | **0,4822 %** |

**Los mínimos ganan por más margen que los máximos en los tres bloques.** Los suelos de este activo
son más pronunciados que los techos, y esa diferencia es consistente.

**Y en prueba los extremos ganan por un tercio menos**: son extremos marginales, decididos por una
diferencia de precio pequeña, y por eso intrínsecamente menos predecibles.

> ⚠️ **Lo que esta tabla NO explica, y conviene decirlo porque es tentador concluirlo.** Es natural
> saltar de «los suelos son más pronunciados» a «por eso el modelo detecta valles mejor que picos».
> **Ese salto no se sostiene.** Comprobado sobre los nueve tramos del walk-forward: el F1 de mínimos
> supera al de máximos en **5 de 9** — que es lo que daría una moneda.
>
> La diferencia de margen es real y consistente. **Que se traduzca en mejor detección, no.** Lo que
> se observó en el bloque de prueba —valles bien, picos por debajo del azar— es un resultado de ese
> bloque, no una propiedad estable del activo.
>
> Y hay una señal de cuán ruidoso es esto: en **dos** de los nueve tramos el F1 de mínimos dio
> exactamente **0,0000**. Con menos de cien ejemplos por clase, la métrica por clase puede colapsar
> a cero por completo. Es la forma más clara del cuello de botella.

### Los tres arreglos que probamos, y por qué fallaron

**Exigir un margen mínimo** para llamar extremo a una vela — si un extremo que gana por 0,05 % es
indistinguible del ruido, etiquetarlo igual que uno que gana por 3 % le pide al modelo aprender algo
que no está ahí:

| Umbral | Ventaja sobre el azar |
|---|---|
| **0 % (lo publicado)** | **+0,0537** |
| 0,1 % | +0,0339 |
| 0,3 % | +0,0310 |
| 0,8 % | +0,0116 |

**Juntar picos y valles** en una sola clase «punto de inflexión», que duplica los ejemplos de la
clase rara y elimina la asimetría de raíz: la ventaja pasa de **+0,0537** a **−0,0293**.

**Corregir la regla de decisión, no el entrenamiento.** `predecir()` elige la clase más probable, y
con un 90,7 % de «continuidad» esa clase casi siempre gana aunque el modelo tenga información útil
sobre las raras. Se probó elegir la clase que más se aparta de su frecuencia base —el arreglo
estándar para clases desbalanceadas— con un solo parámetro, **elegido mirando únicamente datos de
entrenamiento** y aplicado después a validación una sola vez.

**El procedimiento eligió no cambiar nada.** Corregir por frecuencia al decidir hace caer el F1
macro de 0,3672 a 0,1023 sobre los datos de calibración, así que el parámetro óptimo resultó ser
cero. La razón es que `class_weight="balanced"` **ya** corrige por frecuencia al entrenar: hacerlo
otra vez al decidir duplica la corrección y destruye la precisión de las clases raras.

Es un resultado útil aunque sea negativo: dice que la elección de `class_weight` que el proyecto
hizo en la Semana 2 ya estaba haciendo ese trabajo, y que ahí no queda margen.

**Los tres empeoran o no cambian nada**, y por la misma razón: filtrar o fusionar no arregla que haya pocos ejemplos de
la clase rara. Filtrar reduce los máximos de validación de 99 a 27.

Visto con lo del recuadro de arriba, el fracaso tiene más sentido: los arreglos atacaban una
asimetría que **no es estable**. Se diseñaron a partir de una lectura del bloque de prueba que las
nueve mediciones no confirman.

### Lo que sí resolvió la pregunta: medir muchas veces en vez de una

El cuello de botella no era el modelo ni el criterio: era que **una sola medición sobre 86 ejemplos
de cada clase no puede dar un intervalo estrecho**.

Se probó la alternativa correcta para series de tiempo: **validación walk-forward**. En vez de un
bloque medido una vez, se avanza por la serie entrenando con lo anterior y midiendo en el tramo
siguiente, con el mismo embargo en cada frontera. El procedimiento se fijó antes de correrlo y no se
tocó después.

**Tabla 2.** Nueve tramos consecutivos, sobre entrenamiento y validación.

| | |
|---|---|
| Tramos en que el bosque supera al azar | **9 de 9** |
| Ventaja media | **+0,035046** |
| Ventaja mínima / máxima | +0,005380 / +0,072690 |
| Probabilidad de 9 de 9 si no hubiera efecto | **1 en 512** |

Los nueve tramos cubren regímenes opuestos, desde uno que cayó un **35,5 %** hasta uno que subió un
**88,8 %**. **El bosque gana en todos.**

**Y el mismo procedimiento resuelve la limitación 2**, que había quedado debilitada porque su
intervalo no se reproducía:

**Tabla 3.** El iTransformer contra el bosque, en los mismos nueve tramos.

| | |
|---|---|
| Tramos en que el avanzado queda **por debajo** del bosque | **9 de 9** |
| Diferencia media | **−0,031591** |
| Diferencia mínima / máxima | −0,054415 / −0,017886 |

**Nunca queda por encima, en ningún tramo.** La D25 había establecido que, donde entra un modelo no
reproducible, el peso lo lleva la estabilidad del signo y no el intervalo. Nueve períodos con el
mismo signo es una forma mucho más fuerte de esa condición que cinco semillas sobre un solo bloque.

Y hay una coincidencia que importa: la ventaja media del walk-forward (**+0,035046**) y la que dio
el bloque de prueba (**+0,035021**) coinciden hasta la cuarta cifra decimal. **La reserva no tuvo
mala suerte** — el efecto era del mismo tamaño en los nueve tramos y en el bloque no visto, y lo que
faltaba era poder estadístico para distinguirlo del azar.

> **Lo que esto NO demuestra, y hay que decirlo.** El walk-forward **no es una estimación insesgada**:
> los tramos posteriores entrenan con datos de los anteriores, y el modelo se desarrolló mirando
> validación. **La única estimación limpia sigue siendo la del bloque de prueba**, y esa es la que el
> informe reporta en la sección 5. Lo que el walk-forward muestra es que **la ventaja es consistente
> en signo** a lo largo de nueve períodos y de regímenes opuestos.
>
> Por eso **no reemplaza el resultado**: lo explica.

### Lo que se aprende de esto

**El diseño de un solo bloque medido una vez es correcto contra el autoengaño y débil contra el
ruido.** Protege perfectamente de elegir mirando el resultado —que es el riesgo grande— al precio de
no poder distinguir un efecto pequeño de la nada.

Un diseño walk-forward con el procedimiento fijado de antemano da las dos cosas: nadie puede elegir
mirando, y hay potencia suficiente para ver un efecto de este tamaño. **Es la corrección de método
más importante que salió de este trabajo.**

---

## Lo que haríamos distinto

**Traer una variable de otra naturaleza.** El problema de los activos de apoyo no es que sean malos
predictores, es que son redundantes. Otra criptomoneda grande volvería a serlo. Se midió que dos
cocientes construidos —LTC/SOL y LTC/ADA— sí decorrelacionan, y esa es la vía barata que quedó sin
explorar.

**Aplicar la condición del intervalo dentro de cada semilla**, y leer en cuántas de las cinco excluye
el cero, en vez de calcular un intervalo sobre un único sorteo del entrenamiento. Respeta el supuesto
del método en vez de violarlo, y cuesta poco porque las cinco semillas ya se corren.

**Suavizar el puente de trayectoria a etiqueta.** Catorce comparaciones estrictas convierten
diferencias de 10⁻¹¹ en cambios de clase. Una definición con margen —o una etiqueta con grados en vez
de categórica— haría que el modelo profundo se midiera por su pronóstico y no por el redondeo.

**Reentrenar.** Nada de este trabajo dice qué pasa cuando cambia el régimen, porque el panel es
estático.

---

## Una última cosa, sobre el resultado que el enunciado esperaba

El enunciado sugiere que un modelo fundacional y un Transformer son las herramientas para este
problema. **Medido, ninguno de los dos le gana a un bosque aleatorio, y ninguno supera al azar de
forma distinguible.**

Ese resultado se podría haber presentado de otra manera: eligiendo la semilla afortunada, comparando
contra un baseline más flojo, o reportando el 0,953353 del bloque de entrenamiento sin la advertencia
de que ahí el modelo ya vio las respuestas.

No se hizo, y las reglas que lo impidieron están escritas y son comprobables. **El aporte de este
trabajo no es el modelo: es poder decir con precisión qué no se puede afirmar con él.**
