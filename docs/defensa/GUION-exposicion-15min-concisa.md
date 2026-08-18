# Guion de exposición — Marco Teórico, 15 minutos (versión concisa)

> **Caso N.º 1 — Señales y Sistemas — Prof. Roberto Calvo Arias**
> Universidad Invenio · Tecnologías de la Información y Comunicación Empresarial

> **Este guion acompaña al Word de la carpeta `semana-1-concisa`**, el de 54
> páginas. El texto hablado es **idéntico** al de la versión extensa, y no por
> descuido: las dos versiones del documento tienen el mismo contenido y difieren
> solo en la densidad de la redacción. Se comprobó una por una que las ocho figuras
> que el guion proyecta llevan el mismo número y el mismo pie en las dos, y que
> ningún dato mencionado en voz alta desapareció de la versión concisa. Si se
> corrige una frase del guion, hay que corregirla también en el otro archivo.

**Cada persona habla una sola vez, de corrido.** Nadie vuelve a tomar la palabra
después. El orden está pensado para que cada bloque prepare el siguiente.

| Quién | Reloj | Duración | De qué habla |
|---|---|---|---|
| **Fabrizio Espinoza Arce** | 0:00 – 3:20 | 3 min 20 s | El problema y el criterio de trabajo |
| **Jose Pablo Monestel** | 3:20 – 7:25 | 4 min 05 s | Series de tiempo: qué medimos y qué salió |
| **Alejandro Josué Rodríguez Zamora** | 7:25 – 11:30 | 4 min 05 s | Criptoactivos y definición del punto de inflexión |
| **Isaac Felipe Morún Moreira** | 11:30 – 15:30 | 4 min 05 s | Métricas de evaluación y plan del proyecto |

**Instrucciones:**

- Los tiempos están contados a **140 palabras por minuto**, que es ritmo pausado, e incluyen las pausas y los cambios de lámina. Así da **15 minutos 31 segundos**. A 150, que sigue siendo un ritmo cómodo, baja a **14 minutos 30**. Cronometrate en el ensayo y ajustá con los recortes del anexo.
- Donde dice **[FIGURA n]**, cambiá la lámina y esperá dos segundos antes de seguir.
- Donde dice **(pausa)**, contá hasta dos en silencio.
- Los números en **negrita** decilos con claridad. Todos son medidos por nosotros.
- Si te trabás, seguí. No vuelvas atrás a corregir.

---
---

# 1. FABRIZIO ESPINOZA ARCE — 0:00 a 3:20

## El problema y el criterio de trabajo

Buenas tardes. Somos el equipo del Caso número uno y presentamos el marco teórico, que es la primera de las cinco entregas.

**[FIGURA 1 — el precio de Litecoin]**

El problema que tenemos que resolver se enuncia en una frase: **clasificar cada momento del precio de Litecoin en una de tres categorías**. Máximo local, cuando el precio deja de subir y empieza a bajar. Mínimo local, cuando deja de bajar y empieza a subir. Y zona de continuidad, que es todo lo demás.

A lo largo del trimestre tenemos que construir un modelo que aprenda a hacer esa clasificación. Esta primera entrega es el sustento teórico de ese modelo. (pausa)

Es difícil por tres razones concretas, y las tres las verificamos hoy con datos nuestros.

La primera: **el precio no tiene un valor de referencia al que regrese**. Litecoin llegó a valer **cuarenta dólares** y también **trescientos ochenta y siete**. Eso invalida buena parte de las herramientas estadísticas clásicas, que asumen que los datos oscilan alrededor de un valor estable.

La segunda: **la intensidad del movimiento cambia con el tiempo**. Hay períodos largos de calma y períodos de movimientos muy bruscos, y no hay aviso previo de cuándo se pasa de uno al otro.

La tercera es la más incómoda del caso: **para confirmar que un punto fue un máximo hay que observar lo que viene después**. Si el precio sigue subiendo, no era máximo. La respuesta correcta solo se conoce con retraso, y eso condiciona todo el diseño. (pausa)

Litecoin además no se mueve de forma aislada, y por eso el enunciado pide incorporar las cinco criptomonedas de mayor capitalización: **Bitcoin, Ethereum, Solana, XRP y Cardano**.

Sobre cómo trabajamos, dos criterios que le dan forma a todo el documento.

**El primero: ningún concepto se expone solo como definición.** Cada propiedad que afirmamos la verificamos sobre nuestros datos y reportamos el valor obtenido. Y cuando algo no lo medimos, lo decimos en vez de omitirlo. Son **dos mil ciento ochenta y cinco días** de precios de las seis criptomonedas, entre agosto de dos mil veinte y agosto de este año.

**El segundo criterio lo sugirió usted en la sesión de trabajo: construir nosotros mismos series artificiales**, fijando de antemano la volatilidad y la correlación.

La razón es directa. Si aplico un procedimiento a los datos reales y obtengo un número, no puedo distinguir si describe el mercado o si es un artefacto del procedimiento. Si antes lo aplico a una serie donde el valor correcto lo fijamos nosotros y lo recupera, entonces sí puedo interpretar lo que mida sobre datos reales. (pausa)

Lo hicimos en las cuatro condiciones que usted mencionó, y mis compañeros les muestran los resultados. Le dejo la palabra a Jose Pablo.

---
---

# 2. JOSE PABLO MONESTEL — 3:20 a 7:25

## Series de tiempo: qué medimos y qué salió

Gracias. Yo desarrollé la parte de series de tiempo.

Una **serie de tiempo** es una secuencia de observaciones de una misma variable, ordenadas por el momento en que se registraron.

Lo que la distingue de una tabla común es que **el orden forma parte del dato**. En una tabla de clientes uno puede reordenar las filas sin perder información. Acá no: el valor de hoy depende del de ayer, y esa dependencia es lo que hay que modelar. (pausa)

**[FIGURA 3 — prueba de estacionariedad]**

Lo primero que revisé fue la **estacionariedad**. Una serie es estacionaria cuando sus propiedades estadísticas no dependen del momento en que uno la observe: promedio y dispersión constantes, se mire el tramo que se mire.

Para no decidirlo a ojo existe una prueba formal, la de **Dickey-Fuller aumentado**. La corrimos sobre las seis criptomonedas, en dos versiones de los datos.

Sobre el precio tal cual: **ninguna de las seis** da evidencia de estacionariedad.

Sobre los **retornos** —el cambio porcentual entre una observación y la anterior; si ayer cerró en cien y hoy en ciento cinco, es más cinco por ciento—: **las seis**, con un margen amplísimo.

Quiero ser preciso con lo que eso permite afirmar. Que la prueba no dé positivo sobre los precios **no demuestra** que no sean estacionarios: demuestra que no hay evidencia suficiente para afirmar lo contrario. (pausa)

De ahí sale la primera decisión de diseño: **las características del modelo se construyen sobre retornos y no sobre precios**. No es una convención de la disciplina, es consecuencia de esta medición.

**[FIGURA 5 y 6 — volatilidad]**

Lo segundo fue la **volatilidad**, que es la dispersión de los retornos. La calculamos con ventana móvil de treinta días, para ver cómo cambia en el tiempo en vez de tener un solo número para seis años.

Antes de medirla sobre Litecoin aplicamos el control que explicaba Fabrizio. Fijamos una volatilidad de **cero coma cero uno tres ocho** y medimos **cero coma cero uno tres nueve**; fijamos **cero coma uno dos dos** y medimos **cero coma uno dos tres**. El procedimiento devuelve lo que se le pide.

Con eso ya podíamos medir Litecoin: **el tramo más volátil se mueve ocho coma ocho veces más que el más tranquilo**.

Eso confirma que la volatilidad no es constante, sino que conmuta entre regímenes, y descarta modelos como ARIMA, que asumen varianza constante. (pausa)

**[FIGURA 7 — autocorrelación]**

Y lo tercero, que es el hallazgo principal de mi sección.

La **autocorrelación** mide cuánto se relaciona una serie consigo misma unos pasos atrás. Responde a si el pasado de la serie, por sí solo, informa sobre su futuro.

Sobre el precio da **cero coma noventa y nueve**, casi el máximo. Pero no es buena noticia: el precio de hoy se parece al de ayer porque prácticamente es el mismo número. Es la firma de una serie no estacionaria, no información aprovechable.

Sobre los retornos cae a **menos cero coma cero tres**. Y de los **cuarenta** rezagos que examiné, solo **tres** superan la banda de confianza.

Parece un resultado negativo y es lo contrario. **Significa que un modelo lineal sobre precios rezagados tendría muy poca estructura que explotar**, y por lo tanto es el argumento medido a favor de usar modelos no lineales y multivariantes. Es decir, **es la justificación del enfoque que plantea el caso**.

Le paso la palabra a Alejandro.

---
---

# 3. ALEJANDRO JOSUÉ RODRÍGUEZ ZAMORA — 7:25 a 11:30

## Criptoactivos y definición del punto de inflexión

Gracias. Yo desarrollé la parte de criptoactivos y la definición operativa del punto de inflexión.

Un **criptoactivo** es un activo digital cuyas transacciones se registran en una red distribuida, sin una entidad central que las valide. La confianza no proviene de una institución sino de que el registro está replicado y ninguna parte puede modificarlo por su cuenta.

De ahí salen dos características que condicionan nuestro problema.

**La primera: el mercado opera de forma continua**, sin apertura ni cierre y sin distinción entre día hábil y fin de semana.

Eso tiene una consecuencia que medimos. En los mercados bursátiles tradicionales está documentado un efecto de calendario: los rendimientos difieren según el día de la semana. Buscamos ese patrón en Litecoin y **la componente estacional semanal representa apenas el cero coma cuatro por ciento de la variación total**. No existe, porque no hay ningún mecanismo institucional que lo produzca, y por eso no tiene sentido darle al modelo una variable con el día de la semana. (pausa)

**La segunda: no existe un anclaje de valoración fundamental.** Una acción se valora a partir de las utilidades de la empresa. Un criptoactivo no genera flujos, así que su precio responde a oferta, demanda, noticias y decisiones regulatorias. Por eso los movimientos son tan pronunciados.

**[FIGURA 8 y 9 — correlaciones]**

Ahora, por qué el enunciado pide incorporar otras cinco criptomonedas: porque existe dependencia entre ellas, y eso lo medimos.

La **correlación** es un valor entre menos uno y uno que indica en qué medida dos series se mueven de forma conjunta. Y aquí está el hallazgo más importante de mi sección. (pausa)

Calculada **sobre precios en nivel**, la correlación entre Litecoin y Bitcoin da **cero coma uno tres**, casi nula. Y entre Litecoin y Cardano sube a **cero coma ocho**.

Ese ordenamiento es económicamente implausible: Bitcoin es el principal transmisor de choques del sector, cuando cae, cae el mercado entero.

Calculada **sobre retornos**, el orden se corrige: Litecoin con Bitcoin sube a **cero coma setenta y uno**, y el rango general se estrecha a la mitad.

La causa es la **correlación espuria**. Dos series que comparten una tendencia de largo plazo aparecen correlacionadas aunque su codependencia real sea otra, porque lo que se mide es la coincidencia de dirección y no el movimiento período a período. Como ya se midió que los precios no son estacionarios, toda correlación calculada sobre ellos hereda ese defecto.

**También aquí verificamos el procedimiento antes de aplicarlo:** pedimos una correlación de **cero coma uno** y medimos **cero coma cero nueve**; pedimos **cero coma nueve** y medimos **cero coma noventa**. (pausa)

**[FIGURA 10 — punto de inflexión]**

Cierro con la definición del punto de inflexión, que es lo que sostiene todo el proyecto.

**Un máximo no existe en términos absolutos: existe respecto de una ventana.** El precio sube y baja continuamente, a todas las escalas, así que la intuición no alcanza para construir una etiqueta.

Sobre una misma serie, mirando una observación hacia cada lado aparecen varios máximos. Mirando cinco hacia cada lado, la mayoría deja de serlo, porque en esa vecindad hay un valor más alto. **El dato no cambió: cambió la escala de observación.**

Por eso no buscamos la definición verdadera de máximo, porque no existe. Lo que hacemos es **elegir a qué escala trabaja el modelo**, y esa elección la justificamos midiendo.

Le paso la palabra a Isaac.

---
---

# 4. ISAAC FELIPE MORÚN MOREIRA — 11:30 a 15:30

## Métricas de evaluación y plan del proyecto

Gracias. A mí me corresponde la última sección: **cómo vamos a determinar si el modelo sirve**. Y aquí está el problema metodológico más serio del caso.

**[FIGURA 14 — balance de clases]**

Empiezo por una propiedad que se demuestra en dos líneas. (pausa)

**Dos máximos no pueden estar a menos de uve más uno observaciones de distancia**, donde uve es la ventana que acaba de explicar Alejandro. Si lo estuvieran, cada uno caería dentro de la ventana del otro y tendría que ser mayor que el otro. Es imposible.

De ahí se sigue que **a lo sumo una de cada uve más uno observaciones puede ser máximo**. Y lo medido queda muy por debajo: los máximos son el **seis coma seis por ciento** de la muestra, los mínimos el **seis coma cinco**, y la zona de continuidad **casi el ochenta y siete por ciento**.

El punto importante: **el desbalance no es un defecto de la muestra que se corrija recogiendo más datos.** Está garantizado por la definición de la etiqueta. (pausa)

Y la consecuencia es esta. Consideremos un modelo que no hace nada: responde siempre «zona de continuidad», sin mirar los datos. Ese modelo alcanza una **exactitud del ochenta y seis coma nueve por ciento**.

**[FIGURA 15 — matriz de confusión del modelo de referencia]**

Casi un ochenta y siete por ciento de aciertos suena a buen resultado. Y corresponde a un modelo que **no detectó un solo punto de inflexión**. Es inservible. Y no lo suponemos: lo medimos. (pausa)

Por eso descartamos la exactitud como métrica de decisión, y usamos las dos que pide el enunciado.

La primera es el **F1**, que combina dos cosas que hay que evaluar por separado. La **precisión**: de todos los giros que el modelo anunció, cuántos eran reales. Y el **recall**: de todos los giros que ocurrieron, cuántos alcanzó a anunciar.

Lo relevante es que **penaliza los dos extremos**. Un modelo que anuncia un solo giro y acierta tiene precisión perfecta y recall pésimo; uno que anuncia que todo es giro tiene el problema inverso. Solo sale alto si acierta y además no se pierde los casos.

Y lo calculamos **dando el mismo peso a las tres clases**, para que la mayoritaria no oculte a las minoritarias. Ese mismo modelo inútil, que en exactitud daba ochenta y siete, en F1 da **cero coma treinta y uno**. Los dos números salen del mismo modelo, y ahí queda expuesto el problema.

La segunda métrica es la **Precisión Direccional**, que evalúa si el modelo acierta la dirección del giro, que es lo único que le importaría a quien fuera a usar el sistema. (pausa)

Cierro con dos puntos.

**Fijamos de antemano un piso contra el cual comparar.** Medimos tres modelos de referencia triviales: el que responde siempre lo mismo, el que responde la clase mayoritaria y uno aleatorio. **Si nuestro modelo no supera a los tres, no aprendió nada**, y así lo reportaremos.

Y el plan: en la Semana dos, el marco teórico de los modelos y el procedimiento de desarrollo. En la tres, el primer modelo funcionando. En la cuatro, uno más avanzado. En la cinco, el reporte final.

Cerramos con el criterio que ordena todo el documento: **ninguna de las afirmaciones que hicimos hoy proviene únicamente de la literatura. Todas están verificadas sobre nuestros propios datos, y cada número es reproducible con un comando.**

Muchas gracias.

---
---

# Anexo — Preparación

## Ensayo recomendado

| Cuándo | Qué |
|---|---|
| Dos días antes | Cada quien lee su bloque en voz alta **tres veces**, con cronómetro |
| Un día antes | Ensayo completo, seguido, sin parar aunque alguien se trabe |
| Ese mismo día | Solo la primera frase de cada bloque, para que el arranque salga solo |

## Si se pasan de tiempo

Los recortes, en este orden, y solo estos:

1. Fabrizio: el párrafo de por qué sirven las series construidas (20 s)
2. Jose Pablo: el matiz entre *no hay evidencia en contra* y *hay evidencia a favor* (15 s)
3. Alejandro: el efecto de calendario en los mercados tradicionales (15 s)
4. Isaac: la explicación de precisión y recall por separado (20 s)

**No recorten ningún número.** Los números son lo que sostiene la exposición.

## Si preguntan al final

Contesta **quien trabajó esa parte**, no quien esté más cerca. Si nadie la trabajó, la respuesta correcta es *«eso no lo medimos, así que no lo afirmo»*.

**Nadie inventa un número.** Si no lo tiene de memoria, se abre el documento.

## Nota sobre esta entrega

Para la Semana 1 el profesor pidió expresamente **documento y no presentación**. Este guion queda preparado para la primera exposición que sí toque.
