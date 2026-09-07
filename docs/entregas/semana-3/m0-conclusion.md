# Conclusión

## Lo que la Semana 3 deja demostrado

**El circuito es correcto y no tiene fuga.** Es la conclusión mejor respaldada de esta entrega. El
etiquetador recupera **187 de 187** vértices plantados en una serie construida; el sistema alimentado
vela a vela produce predicciones **idénticas** a las del bloque completo sobre **500 velas**, con
**cero discrepancias**.

Esa última prueba es la única de las cuatro capaz de detectar que algo mire filas posteriores —las
otras tres tienen el bloque entero disponible— y no lo detectó.

**El modelo fundacional está entrenado y medido.** Chronos-Bolt es *zero-shot*: no se entrena sobre
estos datos. Eso lo hace barato y reproducible, y a la vez limita lo que puede aprender del problema
concreto.

---

## Lo que la Semana 3 no demuestra, y conviene decirlo antes de que se lea de más

**Nada sobre si el sistema sirve.** Ninguna de las cuatro pruebas mide rendimiento sobre datos no
vistos. La comparación entre modelos llega en la Semana 4 y la medición sobre el bloque de prueba en
la 5.

**Y la cifra más alta de esta entrega es la menos informativa.** El F1 macro de **0,953353** sobre el
bloque de entrenamiento es lo esperable de un modelo que vio esas etiquetas. Esa prueba solo tiene
valor **si falla**: un resultado bajo indicaría que el problema está antes del ajuste, en las
características o en las etiquetas. Que salga alto no dice que el modelo detecte puntos de inflexión.

Se reporta con esa advertencia al lado porque una tabla con 0,953353 sin ese párrafo sería el número
más engañoso del documento.

---

## Una decisión de producto que se toma en esta semana

La prueba de tiempo real mide algo que no es un defecto sino una propiedad del problema: como la
etiqueta necesita `w` velas posteriores, una predicción hecha ahora **no se puede confirmar hasta 32
horas después**. Al final de la serie quedan siempre **8 predicciones sin confirmar**.

Se decidió **mostrarlas, marcadas como pendientes**. Ocultarlas dejaría una vista donde todo lo
mostrado parece verificado, y haría parecer el sistema mejor de lo que es.

---

## Lo que sigue

La Semana 4 desarrolla el modelo avanzado y compara los tres —clásico, fundacional y avanzado— sobre
el mismo bloque de validación y con el mismo arnés. La Semana 5 mide una sola vez sobre el bloque de
prueba, con el protocolo escrito de antemano.
