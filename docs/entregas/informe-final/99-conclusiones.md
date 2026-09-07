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
