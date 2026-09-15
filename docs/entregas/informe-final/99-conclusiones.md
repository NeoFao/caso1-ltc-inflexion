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

**Que el sistema sirva para operar — y tampoco lo contrario.** Operar exige entradas, salidas y
costos, y **ninguna de las tres se ha simulado en este proyecto**: no hay una sola cifra sobre
rentabilidad. Por eso el informe no afirma utilidad práctica, y por la misma razón **no afirma que
no la tenga**: negarlo estaría igual de infundado que afirmarlo, solo que en la dirección cómoda.

Lo que sí se puede sostener es lo que se midió: la precisión direccional del mejor modelo sobre
validación es **0,103627**, mejor que el azar y baja; y con el umbral 0,40, **más de un tercio de los
avisos cae a menos de cuatro horas de un giro real**.

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
la reserva —ya gastada— y midiendo todo sobre datos que sí se pueden volver a mirar.

Salieron dos investigaciones distintas, y conviene leerlas por separado:

| | Qué preguntaba | Qué respondió |
|---|---|---|
| **A** | ¿Por qué el bloque de prueba no lo mostró? | **Era potencia.** El efecto existe y se distingue con muestra suficiente |
| **B** | ¿Se puede mejorar el modelo? | **Siete intentos, ninguno se sostiene.** El límite está en los datos |

---

# A. Por qué el bloque de prueba no alcanzó

### El diagnóstico

Medimos **por cuánto le gana cada extremo a su vecino más cercano**, que es qué tan pronunciado es:

**Tabla C.1.** Margen del extremo sobre su vecino más cercano.

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

### Lo que sí resolvió la pregunta: medir muchas veces en vez de una

El cuello de botella no era el modelo ni el criterio: era que **una sola medición sobre 86 ejemplos
de cada clase no puede dar un intervalo estrecho**.

Se probó la alternativa correcta para series de tiempo: **validación walk-forward**. En vez de un
bloque medido una vez, se avanza por la serie entrenando con lo anterior y midiendo en el tramo
siguiente, con el mismo embargo en cada frontera. El procedimiento se fijó antes de correrlo y no se
tocó después.

**Tabla C.2.** Nueve tramos consecutivos, sobre entrenamiento y validación.

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

**Tabla C.3.** El iTransformer contra el bosque, en los mismos nueve tramos.

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

### La medición que cierra la pregunta: era potencia, y ahora está demostrado

Contar «9 de 9» o «6 de 9» tira a la basura la magnitud de cada tramo y se queda solo con el signo.
Y cada tramo evalúa sobre unas 810 filas con ~40 ejemplos por clase extrema: el mismo problema de
potencia que hizo fallar la condición 2 sobre el bloque de prueba, un piso más abajo.

Lo correcto es **juntar las predicciones de los nueve tramos** —que son de períodos distintos y no se
solapan— y medir una sola vez sobre el conjunto completo.

**Tabla C.4.** Las predicciones de los nueve tramos, juntas: **7 311 filas**, con 347 máximos y 345
mínimos reales. Cuatro veces el bloque de prueba.

| Comparación | Diferencia | Intervalo 95 % | ¿Excluye el cero? |
|---|---|---|---|
| **El modelo del proyecto − el azar** | **+0,051285** | **[+0,033296 , +0,070146]** | **SÍ** |
| Los seis apilados − el azar | +0,061545 | [+0,042448 , +0,079764] | **Sí** |
| Los seis apilados − solo LTC | +0,010260 | [−0,007997 , +0,027271] | no |

**La primera fila es el resultado más importante de esta investigación.**

Sobre el bloque de prueba, con **1 960 filas**, la ventaja del modelo sobre el azar era positiva y
su intervalo **incluía** el cero. Sobre **7 311 filas**, la misma ventaja —de tamaño casi idéntico,
+0,051285 contra +0,035021— tiene un intervalo que **excluye** el cero con holgura.

**El efecto no cambió. Cambió cuánta evidencia había para verlo.** El resultado negativo de la
corrida única era un problema de **potencia estadística**, y ahora está demostrado en vez de
conjeturado.

Y la tercera fila adelanta algo que la **parte B** desarrolla: **el apilado de los seis activos
sigue sin establecerse** ni siquiera con cuatro veces más datos. Su intervalo incluye el cero.

> **Lo que esto NO cambia.** La cifra que el informe reporta en la sección 5 **sigue siendo la del
> bloque de prueba**, y sigue siendo la única estimación limpia: estos 7 311 casos vienen de
> períodos que el modelo y las características usaron para desarrollarse. Lo que esta medición
> establece no es *cuánto* detecta el sistema, sino **que la ausencia de detección que reportó la
> corrida única se explica por el tamaño de la muestra y no por la ausencia del efecto**.

### La corrección más grande: el bosque sí detecta las dos clases

El bloque de prueba dejó la lectura más dura de todo el trabajo: **ningún modelo supera al azar en
las dos clases extremas.** El bosque ganaba en Mínimo y quedaba **por debajo del azar en Máximo**.

Pero el F1 de una clase con **86 ejemplos** es la cifra más ruidosa del informe — en dos de los
nueve tramos del walk-forward una clase dio **0,000000** exacto. Así que esa lectura podía ser un
hecho o podía ser lo que 86 casos dejan ver.

**Tabla C.5.** Cada modelo contra el azar, por clase, sobre las 7 311 filas agregadas.

| Modelo | Clase | Diferencia | Intervalo 95 % | ¿Excluye el cero? |
|---|---|---|---|---|
| **Bosque** | **Máximo** | **+0,043611** | [+0,009983 , +0,083107] | **Sí** |
| **Bosque** | **Mínimo** | **+0,048673** | [+0,006744 , +0,092239] | **Sí** |
| Chronos-Bolt | Máximo | +0,025181 | [−0,003307 , +0,053815] | No |
| Chronos-Bolt | Mínimo | +0,045992 | [+0,009795 , +0,087301] | Sí |
| iTransformer | Máximo | +0,034007 | [+0,007096 , +0,060425] | Sí |
| iTransformer | Mínimo | +0,003412 | [−0,025806 , +0,032277] | No |

**El bosque supera al azar de forma distinguible en las dos clases.** Sobre el bloque de prueba
salía *peor que el azar* detectando máximos; sobre 7 311 filas le gana por +0,043611 con un
intervalo que excluye el cero.

**La lectura más severa del informe era un artefacto de muestra pequeña.**

Y los otros dos siguen repartidos, cada uno con una sola clase: el fundacional detecta mínimos, el
avanzado detecta máximos. Esa asimetría entre ellos **sí** sobrevive a la potencia — no así la del
bosque.

> Las cifras del iTransformer salen de un modelo que **no reproduce entre procesos** (D15, D25).
> Las del bosque y Chronos-Bolt sí reproducen.

> **Y esto tampoco cambia lo que la sección 5 reporta.** El veredicto se aplicó como estaba escrito
> sobre el bloque de prueba, y ahí el bosque quedó por debajo del azar en Máximo. Eso pasó y queda
> reportado. Lo que esta tabla añade es **qué significa**: no que el modelo no detecte máximos, sino
> que 86 ejemplos no alcanzan para verlo.

### Y lo que la potencia corrige de un resultado central del informe

La misma pregunta se le puede hacer a los modelos profundos. El informe afirma que **ninguno de los
dos supera al azar de forma distinguible** — y eso se midió sobre 1 960 filas, con la potencia que
la tabla C.12 acaba de mostrar.

**Tabla C.6.** Los tres modelos contra el azar, sobre las 7 311 filas agregadas.

| Modelo | Diferencia | Intervalo 95 % | ¿Excluye el cero? |
|---|---|---|---|
| Bosque aleatorio | +0,038699 | [+0,019699 , +0,058595] | **Sí** |
| **Chronos-Bolt** (fundacional) | **+0,027769** | **[+0,011976 , +0,045189]** | **Sí** |
| iTransformer (avanzado) | +0,006386 | [−0,008267 , +0,019878] | **No** |

**Con potencia suficiente los dos modelos profundos dejan de comportarse igual, y esa frase del
informe resulta medio falsa: el fundacional sí supera al azar de forma distinguible.**

Sobre el bloque de prueba los dos parecían lo mismo —ninguno se distinguía— y no lo eran. Chronos-
Bolt tenía una ventaja real que 1 960 filas no alcanzaban a mostrar.

**Y el resultado del iTransformer se vuelve mucho más fuerte, no más débil.** No se distingue del
azar **ni con cuatro veces más datos**. Ahí no es un problema de muestra: es que la ventaja, si
existe, es demasiado pequeña para importar.

> La cifra del iTransformer sale de una corrida de un modelo que **no reproduce entre procesos**
> (D15, D25): repetir el experimento mueve ese número en la tercera cifra decimal. **El intervalo
> incluye el cero en las dos corridas que se hicieron**, así que la conclusión no depende de cuál se
> tome — pero el valor exacto sí, y por eso se declara en vez de presentarlo como fijo.

**Esto no cambia lo que la sección 5 reporta.** El veredicto del protocolo se aplicó como estaba
escrito, sobre el bloque de prueba, y esa sigue siendo la única estimación limpia. Lo que cambia es
qué se puede decir **sobre por qué** salió así, y en un caso —el fundacional— la explicación es que
faltaba muestra y no efecto.

### La prueba que no dependía de nuestra disciplina

Todo lo anterior —el bloque de prueba, el walk-forward, la curva de potencia— depende de que el
equipo se haya comportado: de que nadie mirara la reserva antes de tiempo, de que las
características se eligieran sin espiar. Hay una forma de evidencia que **no depende de eso**:
medir sobre datos que **no existían** cuando se tomaron las decisiones.

El panel del proyecto termina el **05/08/2026**. El 08/09 se descargaron las velas que el mercado
produjo desde entonces —**200 velas, 192 evaluables**— y se le pidieron al modelo **sin
reentrenarlo**.

**Tabla C.7.** El bloque fresco: velas posteriores a la construcción del modelo.

| | F1 macro | F1 máximo | F1 mínimo | Precisión direccional |
|---|---|---|---|---|
| **Bosque** | **0,390152** | **0,125000** | **0,125000** | **0,117647** |
| Azar | 0,323971 | 0,000000 | 0,086957 | 0,058824 |

**La diferencia es +0,066181**, la mayor de todas las que este informe reporta: mayor que la del
bloque de prueba (+0,035021) y que la del agregado de nueve tramos (+0,051285). Le gana al azar en
**las dos clases**, y **duplica** la precisión direccional.

**Y su intervalo incluye el cero:** [−0,043087 , +0,194589]. Con 192 velas y nueve ejemplos de cada
clase extrema no podía ser de otra manera — la curva de potencia de la Figura C.1 dice que ni siquiera
con mil velas se llega al 50 % de probabilidad de detectarlo.

> **Lo que esta prueba podía hacer y lo que no.** No podía confirmar detección: no tiene tamaño para
> eso, y se dijo **antes** de mirar el resultado. Lo que sí podía era **desmentirla** — si el modelo
> hubiera salido claramente por debajo del azar sobre datos frescos, habría sido informativo y
> habría que reportarlo.
>
> No la desmintió. Sobre datos que nadie pudo haber usado para ajustar nada, el modelo se comporta
> **al menos tan bien como en todo lo demás**.

---

# B. Qué intentamos para mejorar el modelo, y qué pasó

### Los arreglos que probamos

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

**Los tres empeoran o no cambian nada**, y por la misma razón: filtrar o fusionar no arregla que
haya pocos ejemplos de la clase rara. Filtrar reduce los máximos de validación de 99 a 27.

Visto con lo que la **parte A** midió, el fracaso tiene más sentido: los dos arreglos atacaban una
asimetría entre picos y valles que **no es estable** —aparece en 5 de 9 tramos, que es una moneda—.
Se diseñaron a partir de una lectura del bloque de prueba que las nueve mediciones no confirman.

### El cuarto arreglo: la única vía que sí mejora, y por qué aun así no se afirma

Si el cuello de botella es la cantidad de ejemplos, la vía directa es conseguir más. Los puntos de
inflexión de BTC, ETH, SOL, XRP y ADA son **el mismo fenómeno** que los de LTC: si se construyen las
mismas familias de características centradas en cada activo, cada uno aporta su propia tanda de
ejemplos etiquetados.

Se probó. Seis tandas apiladas, **54 990 filas de entrenamiento en vez de 9 165**, prediciendo sobre
LTC como siempre.

**Tabla C.8.** Entrenar solo con LTC contra entrenar con los seis, sobre validación.

| | F1 macro | F1 máximo | F1 mínimo | Ventaja sobre el azar |
|---|---|---|---|---|
| Solo LTC | 0,3815 | 0,1158 | 0,1350 | +0,0447 |
| **Los seis apilados** | **0,4047** | **0,1455** | **0,1667** | **+0,0679** |

**Mejora las dos clases extremas**, que era exactamente lo que fallaba. Es el único de los cuatro
arreglos que mejora algo.

> ⚠️ **Y aun así no se afirma, por el criterio del propio proyecto.** Repetido sobre los nueve
> tramos del walk-forward, el apilado mejora en **6 de 9**, con una mejora media de **+0,010678** y
> un rango que va de **−0,022268** a **+0,036688**.
>
> La tercera condición de la [D16](../../DECISIONES.md) pide que **el signo no cambie**. Aquí cambia
> en tres de nueve. **Seis de nueve es lo que el azar produce con facilidad.**
>
> Reportar solo el resultado de la partición única —que es claro y favorable— sería exactamente el
> error que este informe dedica seis páginas a describir. Se reporta con las dos cifras: la que
> favorece y la que no.

Lo que sí se puede decir: **es la vía más prometedora de las cuatro**, tiene un mecanismo claro, y su
efecto medio sobre los nueve tramos es positivo — la ventaja sobre el azar sube de **+0,049712** a
**+0,060391**. Es la recomendación principal para quien continúe.

Y notar una decisión que hubo que tomar: **la correlación cruzada queda fuera del juego común**. Sus
columnas nombran a los otros activos, así que «correlación con BTC» significa algo distinto según de
quién sea la tanda. Apilarlas mezclaría cosas que no son la misma.

### El quinto arreglo, que la propia evidencia sugirió

Que Chronos-Bolt detecte mínimos y el iTransformer detecte máximos **no lo dijo nadie de antemano**:
salió de medir. Si es real, combinarlos debería detectar las dos cosas. Es la única hipótesis nueva
que los datos propusieron, y se probó de tres formas.

**Tabla C.9.** Las combinaciones, sobre las 7 311 filas agregadas.

| | F1 macro | F1 de las dos clases extremas |
|---|---|---|
| Azar | 0,330286 | 0,045729 |
| **Bosque** (el mejor individual) | **0,368985** | 0,091871 |
| Voto por mayoría | 0,334500 | 0,030791 |
| **Unión de extremos** | 0,346469 | **0,111972** |
| Especialistas | 0,356348 | 0,084194 |

**Ninguna se establece.** Las tres empeoran el F1 macro, y la unión de extremos —que es la mejor
medida sobre las dos clases que importan— tiene un intervalo que **incluye el cero por muy poco**:
+0,020101, con límite inferior en −0,000047.

> Las cifras de F1 macro de esta tabla dependen del iTransformer, que **no reproduce entre
> procesos** (D15, D25): repetir el experimento las mueve en la tercera decimal. **Ninguna
> conclusión cambia** — las tres siguen por debajo del bosque — pero los valores exactos sí, y por
> eso se dice.

**Van cinco arreglos y ninguno se establece.** Eso ya no es una serie de intentos fallidos: es
evidencia consistente de que el límite está en los datos y no en el modelado.

### Los dos últimos: otra familia de modelo, y pesar en vez de filtrar

**Sexto: cambiar de familia.** Todo lo anterior cambia la etiqueta, la decisión o los datos, pero
siempre con un bosque aleatorio. Se probó *gradient boosting* por histogramas, que suele ir mejor
en datos tabulares y no se había probado ni una vez.

**Séptimo: pesar los extremos por su margen, en vez de filtrarlos.** El primer arreglo falló porque
filtrar quitaba ejemplos de una clase ya diminuta —de 99 máximos a 27—. Pero la intuición de fondo
seguía en pie: un extremo que gana por 0,05 % es menos fiable que uno que gana por 3 %. La forma
correcta de usar eso no es tirar la fila, es **decirle al modelo cuánto confiar en ella**. Es el
arreglo 1 sin su defecto.

**Tabla C.10.** Los dos últimos, sobre las 7 311 filas agregadas.

| | F1 macro | Contra el bosque | ¿Excluye el cero? |
|---|---|---|---|
| Bosque (lo actual) | 0,368985 | — | — |
| Gradient boosting | 0,361496 | −0,007489 | No |
| Bosque pesado por margen | **0,370087** | +0,001101 | No |

**Ninguno se establece.** El boosting queda por debajo y el pesado empata.

### El octavo eje: dejar que el sistema se calle

Los siete intentos anteriores comparten algo que no se hizo explícito hasta el final: **los siete
miden con el sistema respondiendo en todas las velas.** `predecir()` elige siempre la clase más
probable, así que el sistema **nunca se calla**. El intento 3 cambió *qué clase* gana; ninguno probó
**no contestar**.

Ese es un eje distinto, y es el único que dio algo.

#### La pregunta que el informe no tenía respondida

La precisión direccional de este informe —**0,103627** sobre validación— responde: *de los giros que
ocurrieron, ¿a cuántos les acertó el tipo?* Es una medida sobre los giros.

Falta el complemento, que es lo que le importaría a cualquiera que usara esto: **de las veces que el
sistema avisa, ¿cuántas acierta?** Sobre los nueve tramos, con **6 550 observaciones**:

**Tabla C.12.** Precisión del aviso al subir el umbral, y cobertura que cuesta.

| Umbral | Avisos | Cobertura | Precisión del aviso | Azar a esa cobertura | Tramos a favor |
|---|---|---|---|---|---|
| 0,00 *(hoy)* | 6 550 | 100,00 % | **0,081374** | 0,048244 | 9 de 9 |
| 0,25 | 5 015 | 76,56 % | 0,094317 | 0,049452 | 9 de 9 |
| 0,30 | 4 083 | 62,34 % | 0,095518 | 0,044575 | 9 de 9 |
| 0,35 | 2 915 | 44,50 % | 0,098456 | 0,046998 | 9 de 9 |
| **0,40** | **1 766** | **26,96 %** | **0,099660** | **0,049830** | **9 de 9** |
| 0,45 | 831 | 12,69 % | 0,115523 | 0,050542 | 8 de 9 |
| 0,50 | 285 | 4,35 % | 0,129825 | 0,059649 | 9 de 9 |

*Nota.* La frecuencia base de giros es **0,093740**. El criterio, escrito antes de correr, exigía
superarla, superar al azar a la misma cobertura y que el signo aguantara en los nueve tramos.

#### Lo primero que hay que decir es incómodo

**Tal como funciona hoy, el aviso es peor que inútil como alarma.** Avisando en todas las velas
acierta el **8,1 %**, y la frecuencia base de giros es **9,4 %**: quien reaccionara a cada aviso lo
haría peor que reaccionando al azar con la misma frecuencia. Que supere al `baseline_aleatorio`
—0,081374 contra 0,048244— no lo arregla, porque ese piso también nombra el tipo al azar.

Eso no contradice nada de lo medido antes. Dice que **la métrica que el informe reporta y la que un
usuario necesita no son la misma**, y que la segunda faltaba.

#### Callarse sí funciona, y aguanta el criterio

La precisión sube de forma sostenida al subir el umbral, y desde **0,25** en adelante cumple las
tres condiciones. **El punto defendible es 0,40:**

- Avisa en el **26,96 %** de las velas y acierta el **0,099660**, que es **exactamente el doble** del
  azar a esa misma cobertura (0,049830).
- Gana en **los nueve tramos**, con entre **150 y 225 avisos por tramo**: suficientes para que el
  resultado no dependa de un puñado de casos.

**Y no elegimos 0,50 aunque su cifra sea más alta.** Da 0,129825, pero con **285 avisos en total** y
entre 20 y 46 por tramo; su «9 de 9» incluye un tramo donde gana solo porque al azar le tocó
**exactamente cero aciertos**. Con esos conteos, una racha no es un resultado. El umbral 0,45, que
está en medio, ya falla el criterio con **8 de 9**.

Esa no monotonía entre 0,40, 0,45 y 0,50 es la señal de que ahí el ruido manda, y es la razón de
quedarse en el punto con más datos y no en el de la cifra mayor.

#### Qué cambia esto, y qué no

**Cambia lo que el sistema puede ofrecer.** En vez de un aviso en cada vela que acierta el 8 %, un
aviso en una de cada cuatro velas que acierta el 10 % y dobla al azar. Es un cambio de **punto de
operación**, no de modelo: el bosque es el mismo y no se reentrenó nada.

**No cambia ninguna cifra de este informe.** La comparación de modelos, el bloque de prueba y las
tres condiciones de la D16 se miden con cobertura del 100 %, como estaban.

**Y no convierte esto en un sistema con el que operar.** Acertar 1 de cada 10 avisos, doblando al
azar, sigue siendo un margen pequeño; lo que cambia es que ahora está medido por el lado que
importa y que existe una perilla —el umbral— que hace explícito el canje entre avisar mucho y
acertar poco, o poco y acertar algo más.

**La Tabla C.11 pasa a tener ocho filas, y la octava es la primera que se sostiene.** Y refuerza, no
contradice, lo que las otras siete dijeron: el límite sigue estando en los datos. Lo que se ganó no
salió de modelar mejor, sino de **admitir que el sistema no tiene nada que decir en tres de cada
cuatro velas**.

#### Los avisos que fallan, ¿fallan por mucho o por una vela?

Hasta aquí todo se midió con la definición **exacta**: un aviso acierta solo si **esa vela** era el
giro. Errar por una vela cuenta igual que errar por diez.

Para medir el modelo eso es lo correcto y no se toca. Pero **no es la pregunta de quien mira el
gráfico**: un aviso una vela antes del giro real no se lee como un fallo, se lee como un aviso a
tiempo. Son cuatro horas. Y esa pregunta no estaba medida.

**Tabla C.13.** Precisión del aviso en el umbral 0,40, admitiendo una tolerancia de `k` velas.

| Tolerancia | Horas | Precisión | Azar, misma tolerancia | Ventaja | Veces el azar | Tramos |
|---|---|---|---|---|---|---|
| 0 velas | 0 | 0,099660 | 0,048697 | +0,050963 | 2,05 | 9 de 9 |
| **1 vela** | **4** | **0,364100** | 0,135334 | **+0,228766** | **2,69** | 9 de 9 |
| 2 velas | 8 | 0,472254 | 0,236693 | +0,235561 | 2,00 | 9 de 9 |
| 3 velas | 12 | 0,553794 | 0,344281 | +0,209513 | 1,61 | 9 de 9 |

#### Dónde estaba la trampa, y por qué el piso se mueve con la ventana

Ampliar la tolerancia sube la precisión **de cualquiera**, incluido el azar: con tres velas de
margen cada aviso tiene siete oportunidades de acertar en vez de una. Reportar la precisión con
tolerancia **sin mover el piso** habría sido inflar el número — y se ve en la tabla: el azar pasa de
0,048697 a 0,344281.

Por eso el `baseline_aleatorio` se mide con **la misma tolerancia y la misma cobertura**, y el
criterio escrito de antemano no pedía que el número subiera, sino que **la ventaja sobre el azar
creciera**.

#### Lo que dice el resultado

**La ventaja crece, y mucho.** De **+0,050963** con la vela exacta a **+0,228766** admitiendo una
vela: **cuatro veces y media más**, con el signo estable en los nueve tramos.

**Los fallos del modelo no son aleatorios: están concentrados alrededor del giro real.** Si el
modelo se equivocara al azar, ensanchar la ventana habría ayudado igual a los dos y la ventaja se
habría quedado quieta. No es lo que pasa.

**Y la ventaja tiene un máximo.** En veces-el-azar el mejor punto es **1 vela** (2,69×); a partir de
ahí la tolerancia beneficia más al azar que al modelo, y a 3 velas la ventaja relativa ya bajó a
1,61×. Ensanchar la ventana más allá de eso no mide mejor el modelo: **mide peor el azar**.

#### Qué frase queda, y cuál hay que dejar de decir

**Hay que dejar de decir «nueve de cada diez avisos están mal».** Es cierto solo bajo la exigencia de
la vela exacta, y esa exigencia es del instrumento de medición, no del usuario.

Lo que se sostiene, medido:

> Con el umbral 0,40 el sistema avisa en **una de cada cuatro velas**. De esos avisos, **más de un
> tercio cae a menos de cuatro horas de un giro real de ese tipo** —0,364100—, casi **tres veces**
> lo que consigue avisar al azar con la misma frecuencia y el mismo margen.

#### Y lo que sigue sin poder afirmarse

**Nada de esto dice que el sistema sirva para operar**, y conviene ser explícito porque es la
conclusión que la tabla invita a sacar.

Operar exige entradas, salidas y costos, y **en este proyecto no se ha simulado ninguna de las
tres**. No hay una sola cifra sobre rentabilidad. Medir detección con tolerancia sigue siendo medir
**detección**.

Decir «sirve para operar» sería afirmar algo no medido. Y decir «no sirve para operar» —como este
informe llegó a insinuar— **también lo sería**: es igual de infundado, solo que en la dirección
cómoda. Lo que se puede sostener es lo único que se midió: **detecta, con un margen pequeño pero
estable, y sus errores caen cerca.**

#### El noveno eje, y el que más mueve: preguntarle otra cosa

La medición de tolerancia dejó una consecuencia que había que probar. Si los errores del modelo caen
**alrededor** del giro, entonces el modelo ya contesta bien *«¿estamos cerca de un giro?»* — y este
proyecto lo ha estado puntuando durante cinco semanas por *«¿es **esta** vela el giro?»*.

Así que se le cambió la pregunta: **una vela es Máximo si hay un máximo real a `k` velas o menos.**
Con `k = 0` es exactamente la etiqueta de siempre, lo que sirve de control del experimento.

**Tabla C.14.** Entrenar y evaluar con el objetivo de proximidad, nueve tramos.

| Margen | Horas | Velas con giro | F1 macro del modelo | F1 macro del azar | Ventaja | Tramos |
|---|---|---|---|---|---|---|
| 0 velas | 0 | 9,29 % | 0,381008 | 0,336389 | +0,044619 | 9 de 9 |
| **1 vela** | **4** | 27,47 % | **0,567778** | 0,337697 | **+0,230081** | 9 de 9 |
| 2 velas | 8 | 44,13 % | 0,553873 | 0,338043 | +0,215829 | 9 de 9 |
| 3 velas | 12 | 58,13 % | 0,538214 | 0,338467 | +0,199747 | 9 de 9 |

#### Por qué esto no es hacer la tarea más fácil y llamarlo mejora

Es la objeción obvia y hay que contestarla con la tabla, no con palabras: **predecir «hay giro cerca»
es más fácil que predecir «es aquí»**, así que el F1 tenía que subir de todos modos.

**Lo que decide es la columna del azar.** El `baseline_aleatorio` se entrena y se mide sobre la misma
etiqueta, y va de **0,336389** a **0,338467**: se mueve **dos milésimas** mientras el modelo sube
**diecinueve centésimas**.

Si la tarea se hubiera vuelto más fácil *para todos*, el azar habría subido con él. No lo hace. **La
mejora es del modelo, no de la tarea.**

Y por eso el criterio escrito de antemano no pedía que el F1 subiera —eso estaba garantizado— sino
que **la ventaja sobre el azar creciera**. Crece de **+0,044619** a **+0,230081**: **más de cinco
veces**, con el signo estable en los nueve tramos y positiva en las dos clases extremas.

#### Dónde está el óptimo, y por qué no es el margen más ancho

**El mejor punto es una vela: cuatro horas.** A partir de ahí la ventaja **baja** —+0,230081, luego
+0,215829, luego +0,199747— aunque el F1 absoluto siga pareciendo alto.

La razón es que a `k = 3` el **58,13 %** de las velas ya cuentan como «cerca de un giro». La clase
deja de ser rara, la pregunta deja de ser interesante y responder «sí» casi siempre empieza a ser una
estrategia. **Un margen más ancho no es un modelo mejor: es una pregunta más floja.**

#### Qué significa, y qué no

**Significa que el sistema tiene bastante más señal de la que este informe le atribuía**, y que buena
parte de lo que parecía error del modelo era **exigencia del instrumento**. Con la pregunta a cuatro
horas, el F1 macro pasa de 0,381008 a **0,567778**.

**No significa que el resultado del informe cambie.** El enunciado define el punto de inflexión como
la vela exacta, y esa es la medición que este informe reporta, incluida la del bloque de prueba.
Esto es un **problema distinto**, se reporta al lado y no en su lugar.

**Y no se puede validar como se validó aquello.** El bloque de prueba se gastó el 07/09 y no vuelve:
esta medición vive sobre nueve tramos de validación deslizante. Es evidencia fuera de muestra y con
potencia, pero **no es una medición limpia de un solo disparo**, y esa distinción no se puede
recuperar.

> **La lectura honesta de los nueve ejes.** Siete intentos de mejorar el modelo no dieron nada. El
> octavo —dejar que se calle— dio algo. El noveno —cambiar la pregunta— dio cinco veces más que
> todos los anteriores juntos.
>
> Los tres que funcionaron tienen algo en común y vale la pena decirlo: **ninguno toca el modelo.**
> Cambian qué se le pregunta y cuándo se le hace caso. El límite nunca estuvo en el modelado, y las
> primeras siete intervenciones lo estaban buscando en el sitio equivocado — incluidas las mías.

#### El décimo eje: el volumen, que estaba ahí sin usar

Revisando qué no se había probado apareció un hueco de los que dan vergüenza: **el panel trae el
volumen de los seis activos y ninguna de las 63 columnas lo usa.** Todas derivan del precio.

Y el volumen es la señal de manual para giros: **agotamiento** en techos —el precio sigue subiendo
con volumen cada vez menor— y **capitulación** en suelos —la caída termina con un pico—.

Se probaron **seis columnas**, solo sobre LTC: volumen sobre su media a 7 y a 24 velas, su
`z`-score, su variación, su posición dentro del rango reciente, y la correlación entre retorno y
volumen. Seis y no sesenta por la razón que el propio módulo de características documenta: con
**420 ejemplos** de la clase minoritaria, cien columnas nuevas garantizan el sobreajuste.

**Tabla C.15.** El bosque con y sin las seis columnas de volumen, nueve tramos.

| Objetivo | Sin volumen | Con volumen | Diferencia | Tramos a favor |
|---|---|---|---|---|
| Exacto | 0,381008 | 0,371025 | **−0,009983** | 3 de 9 |
| Proximidad a 1 vela | 0,567778 | 0,567984 | +0,000206 | 5 de 9 |

**No aporta, y en el objetivo exacto empeora.** Con la etiqueta de proximidad la diferencia es de
dos diezmilésimas y gana en cinco tramos de nueve, que es una moneda.

**La expectativa estaba escrita antes y era esta**, por dos razones que ya estaban medidas: los dos
únicos ejes que funcionaron no tocaban las características, y la importancia por permutación ya
había medido que **17 de las 63 columnas actuales no superan el piso de ruido**. El problema nunca
pareció ser falta de columnas, y el volumen lo confirma.

Sirve para cerrar la pregunta. Deja de ser «algo que no probamos» y pasa a ser **algo que probamos y
no está**.

#### El undécimo eje: cuatro veces más velas, y por qué no sirvieron de nada

El informe concluye que **el límite está en los datos**. Esa conclusión se sacó sin probar la forma
más obvia de tener más datos: **bajar la granularidad**. El estudio de parámetros comparó **solo 1
día y 4 horas**; 1 hora nunca se descargó.

Se descargó. Y para que la comparación signifique algo, la ventana se fijó **en tiempo de reloj**:
`w = 28` a una hora son las mismas **±28 horas** que `w = 7` a cuatro. El mismo fenómeno, cuatro
veces más resolución.

**Tabla C.16.** El mismo fenómeno, muestreado a 4 horas y a 1 hora.

| Granularidad | Velas | Giros reales | F1 macro | F1 del azar | Ventaja | Tramos |
|---|---|---|---|---|---|---|
| **4 horas**, w=7 | 13 114 | **1 217** | 0,381008 | 0,336389 | **+0,044619** | 9 de 9 |
| **1 hora**, w=28 | 53 395 | **1 243** | 0,346692 | 0,332961 | +0,013731 | 7 de 9 |

#### La cifra que lo explica todo está en la tercera columna

**Cuatro veces más velas produjeron 26 giros más.** 1 217 contra 1 243.

Y tiene que ser así, aunque no lo habíamos pensado: **los puntos de inflexión que ocurrieron en seis
años son los que ocurrieron.** Muestrear el eje del tiempo más fino no crea eventos nuevos — crea
más filas de **continuidad** entre los mismos eventos.

El desbalance, que ya era el problema, **empeora**: de **9,29 %** de velas con giro a **2,33 %**. Se
cuadruplicó el pajar y el número de agujas quedó igual.

#### Por eso la ventaja no sube: baja

De **+0,044619** a **+0,013731**, y el signo deja de ser estable —de **9 de 9** a **7 de 9**—. No es
que 1 hora no ayude: **perjudica.**

#### Lo que esto convierte de conjetura en medición

El informe venía diciendo que «el límite está en los datos» apoyándose en que siete intentos de
modelado no dieron nada. Era un argumento por eliminación.

**Ahora está medido, y es más preciso que la frase original:** el límite no es el número de
observaciones, es **el número de eventos**. Son unos **1 220 giros en seis años**, y de esos seis
años **no se pueden extraer más** por mucho que se afine el muestreo.

> **Y eso dice dónde habría que buscar si hubiera más tiempo**, que es más útil que la frase vieja.
> No en más resolución sobre el mismo período —eso está medido y no está—, sino en **más período** o
> en **más activos**: las dos únicas formas de que ocurran más giros. Es coherente con que el
> apilado multiactivo fuera el único de los siete primeros intentos que mostró algo, con 6 de 9.

**Se esperaba que 1 hora ayudara** —está escrito antes de correrlo— precisamente porque era la
carencia que el informe declaraba. Salió al revés, y el resultado es **más fuerte** que si hubiera
salido como esperábamos.

#### El duodécimo eje: doce activos en vez de seis

La medición de granularidad dejaba una salida: si el límite es el **número de eventos**, y de seis
años no se pueden sacar más, entonces hay que traerlos de **otros activos**. Cada activo nuevo aporta
sus propios ~1 200 giros.

Se descargaron seis más —DOGE, LINK, TRX, BCH, XLM y ATOM— elegidos por un criterio único y
declarado de antemano: **cotizar en Binance contra USDT desde antes de agosto de 2020**, que es donde
empieza el panel. No por rendimiento, que sería elegir la respuesta. Los seis cubren el **100 %** del
panel.

Se entrena apilando las filas de N activos y **se evalúa siempre sobre LTC**.

**Tabla C.17.** Apilar más activos, evaluando siempre sobre LTC.

| Apilado | Filas de entrenamiento | F1 macro | F1 del azar | Ventaja | Tramos |
|---|---|---|---|---|---|
| Solo LTC | 12 358 | 0,383911 | 0,336389 | +0,047522 | 8 de 9 |
| **Los 6 del panel** | 74 148 | **0,388672** | 0,336282 | **+0,052391** | **9 de 9** |
| Los 12 | 148 296 | 0,380690 | 0,335295 | +0,045396 | 9 de 9 |

#### Seis ayuda. Doce estorba.

**Pasar de uno a seis sube la ventaja** —de +0,047522 a +0,052391— y además la vuelve estable en los
nueve tramos. Eso confirma, con un montaje más limpio, lo único que había mostrado señal entre los
siete primeros intentos.

**Pasar de seis a doce la baja**, a +0,045396, **por debajo incluso de entrenar solo con LTC**. Se
duplicaron las filas de entrenamiento —de 74 148 a 148 296— y el resultado empeoró.

#### Por qué, y estaba escrito antes de correrlo

Porque **los criptoactivos grandes se mueven juntos**. La correlación entre los quince pares del
panel va de **+0,517489** a **+0,829963**, y no hay un solo par inversamente proporcional. Los seis
nuevos son más de lo mismo: sus giros ocurren **en los mismos instantes**.

**Mil doscientos giros repetidos no son dos mil cuatrocientos giros distintos.** Son los mismos
mil doscientos vistos seis veces más, y lo que aportan es peso —más filas diciendo lo mismo— sin
información nueva. A partir de cierto punto eso deja de ayudar y empieza a sesgar el modelo hacia el
comportamiento medio del sector, que no es el de LTC.

#### La conclusión, afilada por tercera vez en el día

El argumento del informe ha ido estrechándose a base de medirlo:

| Se decía | Después de medir |
|---|---|
| «El límite está en los datos» | Por eliminación: siete intentos de modelado sin resultado |
| «El límite es el número de **eventos**, no de observaciones» | 4× velas → 26 giros más, y la ventaja **baja** |
| **«El límite es el número de eventos INDEPENDIENTES»** | 2× activos → 2× filas, y la ventaja **baja** |

**Esa última frase es la que el proyecto puede defender**, y es bastante más útil que la primera:
dice que para mejorar esto no hacen falta ni mejores modelos, ni más resolución, ni más
criptoactivos. Hacen falta **más años**, o activos que **giren en momentos distintos** — y esos, por
definición, no son cripto.

#### El decimotercer eje: quitarle el handicap al modelo avanzado

Queda una objeción que el informe arrastraba sin responder, y es razonable: **el iTransformer recibe
seis series de cierre y nada más**, mientras el bosque recibe las **63 columnas** que construyó M2.
Concluir que «ningún modelo profundo mejora al clásico» comparando eso con aquello deja la sospecha
de que los profundos nunca jugaron con las mismas cartas.

Se le dieron. Seis indicadores de LTC además de los seis cierres —volatilidad, RSI, MACD, posición en
el rango, distancia a la media móvil y %B de Bollinger—, **uno por familia de las que exige la
RF-F1** y elegidos por familia, no por importancia medida: lo segundo habría sido elegir la
respuesta.

**Tabla C.18.** El mismo iTransformer con seis series y con doce.

| Entrada | Series | F1 macro | F1 del azar | Ventaja | Tramos |
|---|---|---|---|---|---|
| Seis cierres *(lo de hoy)* | 6 | 0,340066 | 0,336389 | +0,003678 | 5 de 9 |
| **Seis cierres + seis indicadores** | 12 | 0,316936 | 0,336389 | **−0,019453** | **0 de 9** |

#### Empeora, y cae por debajo del azar en los nueve tramos

No es un empate ni un resultado ambiguo: con los indicadores dentro, el modelo avanzado **pierde
contra el azar en los nueve tramos**.

**Y la razón estaba escrita antes de correrlo.** El iTransformer no clasifica: se entrena a
**pronosticar todas sus series de entrada** minimizando un error cuadrático común. Con seis series
más, buena parte de ese error pasa a ser **pronosticar RSI y MACD** — que no es lo que nos interesa y
consume la capacidad del modelo.

Por eso la conclusión correcta no es «las características no sirven». Es más estrecha: **no se le
pueden dar a este modelo por esta vía**, porque su función de pérdida las convierte en objetivos y no
en información.

#### Lo que esto cierra

La objeción de que los profundos jugaban atados era legítima y ahora está respondida: **desatarlo lo
empeora**. La conclusión del informe no dependía del handicap.

**Y queda dicho lo que no se probó**, porque también era parte de la objeción. **Chronos-Bolt no
entra en esta medición**: es *zero-shot* y pronostica una serie a partir de su propio pasado, así que
no hay dónde inyectarle características sin reentrenarlo, y reentrenar un modelo fundacional es otro
proyecto. Su handicap es **estructural**, se declara y no se corrige.

#### El decimotercero, y el último hueco declarado: el avanzado también estaba atado

Quedaba una objeción legítima contra la conclusión de que **ningún modelo profundo mejora al
clásico**: nunca les dimos lo mismo. El bosque recibe **63 columnas**; el iTransformer recibe **seis
series de cierre** y nada más.

Se le dieron seis indicadores de LTC además de los cierres —volatilidad, RSI, MACD, posición en el
rango, distancia a la media y %B de Bollinger—, **uno por familia de las que exige la RF-F1 y
elegidos por familia, no por importancia medida**, que sería elegir la respuesta.

**Tabla C.18.** El iTransformer con seis series y con doce.

| Entrada | Series | F1 macro | F1 del azar | Ventaja | Tramos |
|---|---|---|---|---|---|
| Seis cierres *(lo de siempre)* | 6 | 0,340066 | 0,336389 | +0,003678 | 5 de 9 |
| **Más seis indicadores** | 12 | 0,316936 | 0,336389 | **-0,019453** | **0 de 9** |

**Empeora, y lo deja por debajo del azar en los nueve tramos.**

> **Y aquí apareció, sin buscarla, una segunda confirmación de la limitación 3.** La corrida se
> relanzó porque la primera se cortó, y al terminar había dos resultados que comparar.
>
> **La fila de doce series reproduce bit a bit:** −0,019453 y 0 de 9 en las dos. **La de seis se
> mueve:** +0,003678 y 5 de 9 en la primera, **+0,004849 y 6 de 9** en la segunda.
>
> Es exactamente lo que la sección 5 documenta del iTransformer: **no reproduce entre procesos**, así
> que una cifra suya de una sola corrida es un sorteo y no una medición. Aquí no cambia nada —el
> veredicto es el mismo en las dos— pero **se publica la primera, que es la que se midió antes**.
> Sustituirla por la segunda, que sale algo mejor, sería elegir la corrida más favorable después de
> verla.

#### Y el porqué estaba escrito antes de correrlo

El iTransformer no es un clasificador al que se le añaden columnas: es un **pronosticador**, y se
entrena a predecir **todas las series de entrada** con un error cuadrático común.

Con seis series más, buena parte de esa pérdida pasa a ser **pronosticar RSI y MACD** —que no es lo
que interesa— en vez de pronosticar el precio, que es lo único de lo que sale la etiqueta. Darle más
información por esa puerta **le cambia el objetivo**, no se la añade.

Esto se declaró como riesgo en el propio guion antes de medir, precisamente para no poder leer el
resultado como «las características no sirven». **No es eso: es que esa arquitectura no las recibe
por ahí.**

#### Qué cierra

**La objeción del handicap, que era razonable.** Se podía decir que la comparación era injusta porque
el clásico veía más. Ahora está medido: **quitarle el handicap al avanzado lo empeora**, y la
conclusión del informe —que ningún modelo profundo mejora al bosque— **no dependía de esa
desventaja**.

**Chronos-Bolt queda fuera de esta prueba y hay que decirlo.** Es *zero-shot*: pronostica una serie a
partir de su propio pasado y **no hay dónde inyectarle características** sin reentrenarlo, que es
otro proyecto. Su handicap es **estructural**, se declara, y no se corrige.

#### Las dos que funcionan, juntas: el mejor resultado del trabajo

De trece ejes probados, dos se sostienen —**dejar que el sistema se calle** y **preguntarle si hay un
giro cerca**— y se habían medido **por separado**. La abstención, sobre el objetivo exacto; la
proximidad, con el modelo respondiendo en todas las velas. **Componerlas era lo obvio y estaba sin
hacer.**

**Tabla C.19.** El umbral de confianza aplicado sobre el objetivo de proximidad a una vela.

| Umbral | Avisos | Cobertura | Precisión del aviso | Azar a esa cobertura | Veces el azar | Tramos |
|---|---|---|---|---|---|---|
| 0,00 | 6 550 | 100,00 % | 0,244885 | 0,137710 | 1,78 | 9 de 9 |
| 0,30 | 4 673 | 71,34 % | 0,302803 | 0,135673 | 2,23 | 9 de 9 |
| 0,40 | 3 334 | 50,90 % | 0,368326 | 0,139172 | 2,65 | 9 de 9 |
| 0,50 | 2 571 | 39,25 % | 0,414625 | 0,130299 | 3,18 | 9 de 9 |
| **0,60** | **1 827** | **27,89 %** | **0,440066** | 0,133005 | **3,31** | **9 de 9** |
| 0,70 | 772 | 11,79 % | 0,462435 | 0,137306 | **3,37** | 9 de 9 |

*Nota.* Frecuencia base de este objetivo: **0,277557**. El mejor cociente que consigue el objetivo
exacto con el mismo barrido es **2,18**.

#### La comparación que importa no es la precisión

**El 0,440066 no se puede presentar a secas**, y conviene decirlo antes de que alguien lo señale:
acertar «hay un giro en ±1 vela» es más fácil que acertar la vela exacta, y la frecuencia base de
este objetivo es **0,277557** en vez de 0,093740. Una parte del número viene de que la pregunta es
más blanda.

**Por eso el criterio, escrito antes de correrlo, no mira la precisión sino cuánto le gana al azar** —
medido sobre esa misma etiqueta y a esa misma cobertura. Eso es inmune a que un objetivo sea más
fácil que el otro.

Y ahí el resultado no admite discusión: **3,31 veces el azar** contra **2,18** del mejor punto del
objetivo exacto.

#### Lo que hace este resultado más sólido que todos los anteriores

**Nueve de nueve tramos en todos los umbrales.** El objetivo exacto solo alcanzaba su 2,18 en el
umbral 0,50, con **285 avisos** y **6 de 9** tramos. Aquí el mismo cociente se supera con **1 827
avisos** y el signo aguanta en los nueve.

**Y la curva del azar es plana**: se queda entre 0,130 y 0,143 en todos los umbrales, como debe ser
—un aviso al azar no sabe nada, así que filtrar por confianza no lo mejora—. **Todo el ascenso de
0,245 a 0,462 es información del modelo.**

#### A igual cobertura, cuatro veces mejor

La comparación más limpia es a **cobertura comparable**. El mejor punto que reportaba el objetivo
exacto avisaba en el **26,96 %** de las velas acertando **0,099660**. Aquí, avisando en el
**27,89 %** —prácticamente lo mismo— se acierta **0,440066**.

> **La frase medida que el sistema puede sostener hoy:** avisa en **una de cada cuatro velas**, y de
> esos avisos **cuatro de cada diez caen a menos de cuatro horas de un giro real de ese tipo** —
> contra **algo más de uno** de avisar al azar con la misma frecuencia. En los nueve tramos.

#### Y una cautela sobre los decimales

El piso del azar es **un sorteo**: se anuncia en tantas velas al azar como anunció el modelo. Eso
significa que los cocientes cargan algo de ruido propio del sorteo —unas centésimas entre corridas—,
y por eso la comparación se hace sobre la **diferencia grande** (3,31 contra 2,18) y no sobre
hundredths. La misma medición anterior daba 2,02 en el umbral 0,40 donde esta da 2,65: **la
diferencia entre objetivos es del orden de una unidad, y el ruido del sorteo de unas centésimas.**

**Sigue sin poder afirmarse que sirva para operar**, por lo mismo de siempre: eso exige entradas,
salidas y costos, y no se ha simulado. Lo que cambia es que el sistema ya tiene una descripción
honesta y útil de lo que hace.

### El balance de los siete intentos

**Tabla C.11.** Todo lo que se probó, y en qué eje.

| # | Qué se cambió | Eje | Resultado |
|---|---|---|---|
| 1 | Umbral de margen mínimo | la etiqueta | peor |
| 2 | Juntar máximos y mínimos | la estructura de clases | peor |
| 3 | Corregir por frecuencia base | la regla de decisión | no cambia |
| 4 | Apilar los seis activos | el volumen de datos | mejora, **6 de 9** |
| 5 | Combinar los tres modelos | la agregación | no se establece |
| 6 | Gradient boosting | la familia de modelo | no se establece |
| 7 | Pesar por margen | la confianza por ejemplo | no se establece |
| **8** | **Dejar que se calle** | **el punto de operación** | **se sostiene, 9 de 9** |
| **9** | **Preguntarle «hay giro cerca»** | **la pregunta** | **se sostiene, y da 5× más** |
| 10 | Añadir el volumen | las características | **no aporta**, y empeora el exacto |
| 11 | Bajar a velas de 1 hora | el volumen de datos | **perjudica**: +0,013731 contra +0,044619 |
| 12 | Apilar doce activos en vez de seis | el número de eventos | **perjudica**: +0,045396 contra +0,052391 |
| 13 | Dar indicadores al avanzado | lo que el modelo ve | **perjudica**: -0,019453, 0 de 9 |
| 13 | Darle indicadores al avanzado | lo que el modelo ve | **perjudica**: −0,019453, pierde 0 de 9 |
| **14** | **Las dos que funcionan, juntas** | **pregunta + punto de operación** | **el mejor resultado: 3,31× el azar, 9 de 9** |

**Once de las catorce intervenciones no producen una mejora que se sostenga.** Las dos que sí tienen
algo en común, y es lo que más dice de todo el proyecto: **ninguna toca el modelo.** Una cambia
**cuándo contesta** y la otra **qué se le pregunta**.

El límite nunca estuvo en el modelado. Las siete primeras intervenciones lo estaban buscando en el
sitio equivocado.

Eso ya no es una lista de intentos fallidos. Es evidencia consistente de que **el límite de este
sistema no está en el modelado**: está en cuánta señal hay en estos datos, con esta definición de
punto de inflexión y esta cantidad de ejemplos.

Y encaja con todo lo demás que se midió hoy: el efecto **existe** y es **estable** —el bosque le
gana al azar en los nueve tramos y con intervalos que excluyen el cero— pero es **pequeño**, y
ningún cambio de modelado lo agranda.

### Y una observación sobre la métrica, que sí queda

La unión de extremos se ve **mal** en F1 macro y **mejor que todo lo demás** en las dos clases
extremas. La diferencia no está en el modelo: está en que **el F1 macro promedia las tres clases, y
«continuidad» es el 90,7 % de las velas y no es lo que el enunciado pide detectar.**

Una métrica que promedie **solo las dos clases extremas** habría ordenado los modelos de otro modo.
No se cambia —está fijada desde la Semana 1 y cambiarla ahora sería elegir la métrica después de ver
los resultados, que es exactamente lo que este informe no hace— pero **queda anotado que la elección
de métrica no fue neutral**, y esa es una decisión que conviene tomar mirándola de frente.

---

### Lo que se aprende de esto

**El diseño de un solo bloque medido una vez es correcto contra el autoengaño y débil contra el
ruido.** Protege perfectamente de elegir mirando el resultado —que es el riesgo grande— al precio de
no poder distinguir un efecto pequeño de la nada.

Y ahora se puede poner número a ese precio, midiéndolo en vez de afirmarlo. Tomando submuestras de
tamaño *n* de las predicciones agregadas y contando en cuántas el intervalo excluye el cero (ver la **Figura 6.1** de la sección 6):

**Tabla C.12.** Curva de potencia: probabilidad de detectar el efecto, según el tamaño del bloque.

| Velas en el bloque | Probabilidad de detectarlo |
|---|---|
| 1 000 | 42 % |
| **1 960** — *el tamaño que usamos* | **80 %** |
| 3 000 | 100 % |
| 5 000 | 100 % |

**Y esto corrige lo que parecía la conclusión obvia.** El bloque de prueba **no era insuficiente**:
1 960 velas dan un **80 %** de probabilidad de detectar este efecto, que es exactamente el umbral
convencional. El diseño era defendible.

Lo que no tenía era **margen**. Con un 80 % de potencia, una de cada cinco veces el resultado sale
negativo aunque el efecto exista — y nos tocó esa. Con **3 000 velas**, un 50 % más, la detección
habría sido segura.

> **Un matiz que hay que decir:** esta curva se calcula con el efecto que se observa en el agregado
> (≈ +0,051). El bloque de prueba observó **+0,035021**, más chico, así que su potencia real fue
> **menor** que ese 80 %. O tuvo mala suerte con el efecto, o el efecto en ese período era
> genuinamente más débil; con una sola medición no se puede separar.

**La lección, entonces, no es «apartamos poco».** Es que **el tamaño del bloque se puede calcular
antes de apartarlo**, a partir del efecto que uno espera detectar, y nosotros lo elegimos por
proporción —un tercio de los datos— sin hacer esa cuenta. Salió razonable por suerte, y sin margen.

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

