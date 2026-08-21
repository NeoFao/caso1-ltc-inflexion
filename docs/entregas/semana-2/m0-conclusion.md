# Conclusiones

**Autor:** Fabrizio Espinoza Arce · Ensamblaje

Cuatro conclusiones cierran esta entrega. Como en la anterior, ninguna proviene únicamente de la literatura consultada: todas se apoyan en mediciones realizadas sobre las máquinas y los datos del proyecto.

**Primera. Los tres parámetros que definen el problema dejaron de ser provisionales, y cada uno se fijó con un criterio distinto declarado antes de medir.** La granularidad, por el piso de ejemplos de la clase minoritaria; la ventana, por ser la mayor que lo cumple; y el horizonte, por la caída de la información mutua entre lo observable y la etiqueta. Que sean tres criterios y no uno importa: fijar los tres con el mismo argumento habría sido justificar una decisión ya tomada.

**Segunda. La elección del modelo fundacional se resolvió por coste medido y no por preferencia.** Los tres candidatos evaluados corren en CPU, pero el tiempo de inferencia sobre el bloque de validación los separa por tres órdenes de magnitud, y el descarte más costoso se decidió con ese número. Merece señalarse que el criterio que elimina a FinLSPM no es técnico sino de disponibilidad: el enunciado exige código público y no logramos encontrarlo, lo que se reporta como lo que es —no lo hemos encontrado— y no como una afirmación sobre su inexistencia.

**Tercera. CryptoMamba queda descartado por dos razones independientes, y una obliga a consultar al profesor.** No puede instalarse sin CUDA en ninguna de las máquinas del equipo, lo que se comprobó en un entorno desechable, y además no es un Transformer sino un modelo de espacio de estados, mientras que el enunciado pide expresamente un Transformer como segundo modelo. La primera razón es nuestra limitación; la segunda es una ambigüedad del enunciado que preferimos plantear antes que resolver por cuenta propia.

**Cuarta. El procedimiento está construido de punta a punta, y el modelo de referencia supera al azar de forma distinguible, pero no gracias a los activos de apoyo.** Las dos mitades de esa frase se midieron por separado y conviene enunciarlas juntas, porque cada una sola induce a error.

El modelo de referencia aventaja al baseline aleatorio en **0,0537** de F1 macro, con un intervalo de confianza del 95 % de **[0,0137 , 0,0929]** que excluye el cero y supera el umbral de decisión de 0,02 que el equipo fijó de antemano. La ventaja sobrevive al reentrenamiento: sobre cinco semillas, la menor diferencia observada es de 0,0296 y ninguna cae por debajo del umbral. Frente al baseline trivial la diferencia es de **0,0744**, con intervalo **[0,0418 , 0,1077]**.

Buena parte de ese margen procede de una decisión concreta y medible. Expresar los rezagos como variación relativa al precio actual, en lugar de como precio en nivel, aporta por sí solo **0,0462** de F1 macro, con intervalo **[0,0141 , 0,0805]**. Medido con la representación anterior, el mismo modelo aventajaba al azar en apenas 0,0075, con un intervalo que incluía el cero: la mejora no proviene de un modelo distinto, sino de haber alineado la construcción de las características con la evidencia de estacionariedad reportada en la Semana 1.

Lo que no se sostiene es el supuesto multivariante. La diferencia entre emplear los seis criptoactivos y emplear únicamente Litecoin es de **0,0090**, con un intervalo de **[−0,0229 , 0,0417]** que incluye el cero, por debajo del umbral, y con dos de cinco semillas arrojando diferencia negativa. **No puede afirmarse que las cinco series de apoyo aporten información sobre los puntos de inflexión de Litecoin.** El planteamiento multivariante era razonable a la vista de las correlaciones medidas en la Semana 1, y esa justificación de diseño se mantiene; lo que la medición añade es que dicha estructura no se traduce, con este modelo y a esta resolución, en poder predictivo distinguible del ruido.

Preferimos declararlo así, con sus intervalos, antes que presentar un margen que la evidencia no respalda o silenciar uno que sí respalda.

## Limitaciones

Cuatro advertencias que conviene explicitar.

**La señal disponible es escasa.** La información mutua entre lo observable y la etiqueta es baja para todo horizonte, incluido el elegido. Lo que sustenta la decisión es la forma de la curva y no su magnitud, y esa magnitud pequeña es en sí misma un aviso sobre la dificultad del problema con las características actuales.

**El conjunto de validación no tiene resolución suficiente.** Con 99 máximos y 94 mínimos, y un F1 macro que pesa esas dos clases a dos tercios, unos pocos aciertos mueven el resultado de forma apreciable. Cualquier comparación entre modelos que no venga acompañada de un intervalo debe leerse con reserva.

**Una fracción de los puntos de inflexión es impredecible por construcción.** Los saltos inducidos por anuncios regulatorios son exógenos a la serie, y ninguna característica construida sobre el histórico de precios puede anticiparlos.

**El paso de un pronóstico de trayectoria a una etiqueta de tres clases quedó resuelto, y conviene decir cómo.** Un modelo fundacional pronostica el precio, no la clase. Se optó por aplicar el etiquetador del contrato sobre la trayectoria pronosticada, en lugar de entrenar una cabeza de clasificación sobre representaciones congeladas. Lo que inclinó la decisión fue una medición y no una preferencia: aplicar el etiquetador cuesta unos doce segundos sobre el bloque de validación completo, de modo que la alternativa más simple resultó ser además la más barata, y la opción del extractor de representaciones habría tenido que justificar un costo adicional frente a algo que prácticamente no cuesta.

## Sobre el umbral de decisión

El proyecto fijó antes de medir que un modelo solo se declara mejor si supera al mejor de los baselines en F1 macro por al menos 0,02. Conviene precisar qué es y qué no es ese umbral: **es una convención del equipo acordada de antemano, no un contraste estadístico.** Fijarlo antes de mirar los resultados fue lo correcto, porque impide elegir el criterio después de conocer el desenlace; presentarlo como si fuera una prueba de significancia no lo sería. Cuando el margen y su intervalo discrepen, manda el intervalo.

## Trabajo siguiente

La tercera entrega desarrolla el modelo fundacional y las pruebas de detección con datos sintéticos, de entrenamiento y en tiempo real. Conviene declarar que qué se entiende por "tiempo real" está consultado con el profesor y pendiente de respuesta: como la etiqueta de un instante no se conoce hasta `w` velas después, caben dos lecturas —confirmación tardía pero verificable, o anuncio en el momento— que producen dos productos distintos.
