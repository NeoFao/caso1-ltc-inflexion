# Guion de exposición — Marco Teórico, 15 minutos

> **Caso N.º 1 — Señales y Sistemas — Prof. Roberto Calvo Arias**
> Universidad Invenio · Tecnologías de la Información y Comunicación Empresarial

**Cada persona habla una sola vez, de corrido.** Nadie vuelve a tomar la palabra
después. El orden está pensado para que cada bloque prepare el siguiente.

**Todo está escrito para que lo entienda alguien que no sabe nada del tema.** Si
una palabra técnica aparece, se explica en la misma frase.

| Quién | Reloj | Duración | De qué habla |
|---|---|---|---|
| **Fabrizio Espinoza Arce** | 0:00 – 3:15 | 3 min 15 s | Qué problema resolvemos y cómo trabajamos |
| **Jose Pablo Monestel** | 3:15 – 7:20 | 4 min 05 s | Cómo se comporta el precio en el tiempo |
| **Alejandro Josué Rodríguez Zamora** | 7:20 – 11:10 | 3 min 50 s | Qué son las criptomonedas y qué es un giro |
| **Isaac Felipe Morún Moreira** | 11:10 – 15:00 | 3 min 50 s | Cómo sabremos si el modelo sirve, y qué sigue |

**Instrucciones para todos:**

- Hablá **despacio**. Los tiempos están medidos a 140 palabras por minuto, que es ritmo de exposición tranquila. El total da **14 minutos 59 segundos** contando las pausas.
- Donde dice **[FIGURA n]**, cambiá la lámina y **quedate callado dos segundos** antes de seguir.
- Donde dice **(pausa)**, contá hasta dos en silencio.
- Los números en **negrita** son los que hay que decir con claridad. Son medidos por nosotros.
- Si te trabás, no vuelvas atrás: seguí. Nadie nota lo que faltó, todos notan la corrección.

---
---

# 1. FABRIZIO ESPINOZA ARCE — 0:00 a 3:15

## Qué problema resolvemos y cómo trabajamos

Buenas tardes. Somos el equipo del Caso número uno y les presentamos el marco
teórico, que es la primera de cinco entregas.

**[FIGURA 1 — el precio de Litecoin]**

Imagínense que miran una montaña rusa desde lejos, y alguien les pide una sola
cosa: *avisame cuándo el carrito está en una cima, y cuándo está en un valle*.

Eso es exactamente nuestro proyecto. El carrito es **el precio de Litecoin**, que
es una criptomoneda. Las cimas son lo que llamamos **máximos**, los valles son los
**mínimos**, y todo el camino entre unos y otros lo llamamos **zona de
continuidad**.

Nuestro trabajo del trimestre es construir un programa que aprenda a avisar cuál
de esas tres cosas está pasando. (pausa)

¿Por qué es difícil? Por tres razones que hoy demostramos con datos.

La primera: **el precio no tiene un valor normal al que volver**. Litecoin llegó a
valer **cuarenta dólares** y también **trescientos ochenta y siete**. Eso rompe
casi todas las herramientas clásicas, que dan por sentado que las cosas se mueven
alrededor de un valor estable.

La segunda: **hay épocas tranquilas y épocas de locura**, y no avisan cuándo
cambian.

Y la tercera, la más incómoda: **para saber que estás en una cima, tenés que ver
lo que viene después**. Si el carrito sigue subiendo, no era cima. La respuesta
correcta llega tarde, siempre. (pausa)

Litecoin además no se mueve solo, y por eso el caso pide acompañarlo con las cinco
criptomonedas más grandes: **Bitcoin, Ethereum, Solana, XRP y Cardano**.

Sobre cómo trabajamos, declaro dos criterios que le dan forma a todo el
documento.

**El primero: ningún concepto se expone solamente como definición.** Cada vez que
afirmamos algo, lo comprobamos sobre nuestros propios datos y reportamos el
número. Y cuando algo no lo medimos, lo decimos, en vez de omitirlo. Son **dos mil
ciento ochenta y cinco días** de precios de las seis criptomonedas, desde agosto
de dos mil veinte hasta agosto de este año.

**El segundo criterio nos lo sugirió usted, profesor, en la sesión de trabajo:
construir nosotros mismos series artificiales**, con la agitación y la relación
entre monedas puestas a mano por nosotros.

Y no es un adorno. (pausa) Si aplico una fórmula a los datos reales y me da un
número, no tengo forma de saber si describe el mercado o si es un invento de mi
fórmula. En cambio, si primero fabrico una serie donde **yo puse la respuesta
correcta** y mi fórmula la encuentra, recién ahí puedo confiar en lo que me diga
sobre los datos de verdad.

Lo hicimos en las cuatro condiciones que usted mencionó, y mis compañeros les
muestran los resultados.

Le dejo la palabra a Jose Pablo.

---
---

# 2. JOSE PABLO MONESTEL — 3:15 a 7:20

## Cómo se comporta el precio en el tiempo

Gracias. Yo trabajé la parte de **series de tiempo**.

Empiezo por lo básico: **una serie de tiempo es una lista de números en orden**.
La temperatura de cada día del año lo es. El precio de Litecoin cada día, también.

Lo que la hace especial: **si uno cambia el orden, destruye la información**. En
una tabla de clientes uno puede barajar las filas y no pierde nada. Acá no, porque
el número de hoy depende del de ayer, y ese vínculo es lo que hay que
modelar. (pausa)

Lo primero que revisé fue si el precio es **estacionario**. Esa palabra suena
complicada pero significa una cosa sencilla: **que las reglas del juego no cambien
con el tiempo**. Que el promedio sea siempre parecido y la agitación sea siempre
parecida, mire uno el tramo que mire.

**[FIGURA 3 — la prueba de estacionariedad]**

Para no decidirlo a ojo existe una prueba estadística. La corrimos sobre las seis
monedas, en dos versiones de los datos.

Primero sobre **el precio tal cual**: **ninguna de las seis** pasa. Ninguna.

Después sobre lo que llamamos **retornos**, que es **el cambio en porcentaje de un
día al siguiente**. Si ayer cerró en cien y hoy en ciento cinco, el retorno es más
cinco por ciento. Resultado: **las seis pasan**, con muchísimo margen.

Quiero ser preciso con lo que eso permite afirmar, porque es un matiz que importa.
Que la prueba no dé positivo sobre los precios **no demuestra** que no sean
estacionarios: demuestra que no hay evidencia suficiente para afirmarlo. Es la
diferencia entre *no hay pruebas en contra* y *hay pruebas a favor*. (pausa)

De ahí sale la primera decisión del proyecto: **trabajamos sobre los cambios
porcentuales, no sobre el precio**. Y no por costumbre, sino porque lo medimos.

**[FIGURA 5 y 6 — volatilidad]**

Lo segundo que revisé es la **volatilidad**, que es solo una palabra elegante para
decir **cuánto se mueve el precio**.

Antes de medirla en Litecoin hicimos lo que explicaba Fabrizio: fabricamos dos
series, una con agitación baja y otra con agitación alta, y medimos a ver si las
recuperábamos. Pedimos **cero coma cero uno tres** y medimos **cero coma cero uno
cuatro**. Pedimos **cero coma uno dos dos** y medimos casi lo mismo. Funciona.

Recién entonces medimos Litecoin. Y el resultado es que **su época más agitada se
mueve ocho coma ocho veces más que su época más tranquila**.

Eso confirma que Litecoin no tiene una agitación estable: **tiene temporadas**. Y
eso descarta de entrada las herramientas clásicas, porque todas dan por sentado
que la agitación es constante. (pausa)

**[FIGURA 7 — autocorrelación]**

Y lo tercero, que para mí es el hallazgo más importante de mi parte.

Me pregunté: **¿el cambio de precio de ayer me dice algo sobre el de hoy?** Eso se
llama **autocorrelación**: cuánto se parece la serie a sí misma unos pasos atrás.

Revisé cuarenta pasos hacia atrás, y **solamente tres** dan algo distinguible de la
casualidad. Prácticamente ninguno.

Ahora, esto suena a mala noticia y es exactamente lo contrario. **Lo que significa
es que una fórmula simple, de las de toda la vida, no va a poder predecir esto.**
Y por eso mismo hace falta un modelo más elaborado y hace falta mirar las otras
cinco monedas. O sea: **es la justificación de que este proyecto tenga sentido**.

Con eso le paso la palabra a Alejandro.

---
---

# 3. ALEJANDRO JOSUÉ RODRÍGUEZ ZAMORA — 7:20 a 11:10

## Qué son las criptomonedas y qué es exactamente un giro

Gracias. Yo trabajé la parte de **criptoactivos** y la definición del punto de
inflexión.

Primero lo básico: **una criptomoneda es dinero digital que no depende de ningún
banco ni de ningún gobierno**. Las transacciones quedan anotadas en un registro
compartido entre miles de computadoras, y ninguna puede modificarlo sola. La
confianza no sale de una institución, sale de que todos tienen la misma copia.

Eso tiene dos consecuencias que importan para el proyecto.

**La primera: el mercado no cierra nunca.** Ni fines de semana, ni feriados.

Lo comprobamos: buscamos si Litecoin tiene algún patrón semanal, como sí ocurre en
la bolsa tradicional, donde está documentado que los lunes se comportan distinto a
los viernes. **En Litecoin ese patrón es prácticamente inexistente: menos de medio
por ciento de la variación.** Como el mercado nunca cierra, no hay nada que lo
produzca. (pausa)

**La segunda: no hay nada que le ponga precio.** Una acción se puede valorar
mirando cuánto gana la empresa. Una criptomoneda no produce nada: su precio depende
de la oferta, la demanda, las noticias y los reguladores. Por eso los movimientos
son tan bruscos.

**[FIGURA 8 y 9 — las correlaciones]**

¿Por qué el caso pide acompañar a Litecoin con otras cinco monedas? Porque se
mueven juntas, y eso lo medimos.

La **correlación** es un número entre menos uno y uno que dice **cuánto se mueven
dos cosas al mismo tiempo**. Uno, idénticas; cero, sin relación.

Y acá está lo que para mí es el hallazgo más interesante. (pausa)

Midiendo **sobre el precio tal cual**, el resultado dice que **Litecoin casi no
tiene relación con Bitcoin**: da **cero coma uno dos**. Y que sí tiene muchísima
con Cardano, que es una moneda bastante menor.

Eso es un disparate: Bitcoin marca la tendencia de todo el mercado, cuando cae,
cae todo.

Midiendo **sobre los cambios porcentuales**, el orden se acomoda: Litecoin con
Bitcoin sube a **cero coma setenta y uno**.

¿Por qué pasaba? Por algo llamado **correlación espuria**. En verano suben las
ventas de helado y suben los ahogamientos; medidos juntos parecen
relacionadísimos, pero el helado no ahoga a nadie: subió el calor y arrastró a los
dos. Con los precios pasa igual.

**Acá también comprobamos el método antes de creerle.** Pedimos una relación de
**cero coma uno** y medimos **cero coma cero nueve**; pedimos **cero coma nueve** y
medimos **cero coma noventa**. (pausa)

**[FIGURA 10 — el punto de inflexión]**

Y termino con lo más importante de mi parte: **qué es exactamente un giro**.

Acá hay una idea que parece un juego de palabras y no lo es: **una cima no existe
por sí sola; existe respecto de una ventana**.

Piensen en once días de precios. Si miro **un día hacia cada lado**, hay varias
cimas pequeñas. Si miro **cinco días hacia cada lado**, la mayoría deja de serlo,
porque cerca hay algo más alto.

**El precio no cambió. Cambió la lupa.** Y las dos lecturas son correctas: es un
giro pequeño, y no es un giro importante.

Por eso **no buscamos la definición verdadera de máximo, porque no existe**. Lo que
hacemos es **elegir a qué escala trabaja el modelo**, y esa elección la
justificamos midiendo.

Le paso la palabra a Isaac.

---
---

# 4. ISAAC FELIPE MORÚN MOREIRA — 11:10 a 15:00

## Cómo sabremos si el modelo sirve, y qué sigue

Gracias. A mí me toca la última parte: **cómo vamos a saber si el modelo sirve de
algo**. Y acá está la trampa más grande del proyecto.

**[FIGURA 14 — el balance de clases]**

Empiezo por un hecho que se demuestra en dos líneas. (pausa)

**Dos cimas no pueden estar pegadas.** Si cada cima tiene que ser más alta que
todos sus vecinos, y dos están cerca, cada una tendría que ser más alta que la
otra. Imposible.

De ahí se sigue algo que condiciona todo: **las cimas y los valles van a ser
siempre poquísimos**. Lo medimos: las cimas son el **seis coma seis por ciento**,
los valles el **seis coma cinco**, y **todo el resto, casi el ochenta y siete por
ciento, es zona de continuidad**.

Y esto importa: **no es un defecto de nuestros datos**, no se arregla bajando más
historia. Sale de la definición misma. (pausa)

Ahora sí, la trampa.

Supongamos un programa **que no hace absolutamente nada**: responde siempre «zona
de continuidad», sin mirar los datos.

Ese programa acierta el **ochenta y seis coma nueve por ciento** de las veces.

**[FIGURA 15 — la matriz del modelo inútil]**

Casi un ochenta y siete por ciento suena excelente. Y **no detectó ni una sola cima
ni un solo valle**. Es completamente inservible. Y lo medimos, no lo
suponemos. (pausa)

Por eso **descartamos la exactitud** y usamos las dos medidas que pide el
enunciado.

La primera se llama **F1**, y combina dos preguntas. Una: de todas las veces que
anuncié una cima, ¿cuántas eran de verdad? Es decir, cuántas falsas alarmas di. Y
otra: de todas las cimas que hubo, ¿cuántas alcancé a anunciar?

Lo importante es que **castiga los dos extremos**. Si soy muy prudente y anuncio
una sola, me va mal. Si soy alarmista y anuncio todo, también. Solo sale bien si
acierto **y además** no se me escapan.

Y lo calculamos **dándole el mismo peso a las tres respuestas**, para que la
categoría gigante no tape a las chiquitas. Ese mismo programa inútil, que en
exactitud sacaba ochenta y siete, acá saca **cero coma treinta y uno**. Ahí se ve
el engaño, con los dos números lado a lado.

La segunda es la **Precisión Direccional**, que mira si acertamos la dirección del
giro, que es lo único que le importa a alguien que quiera usar esto. (pausa)

Y cierro con dos cosas.

**Fijamos de antemano un piso contra el cual compararnos.** Medimos qué sacan tres
programas tontos: el que siempre responde lo mismo, el que responde la categoría
más común, y uno que responde al azar. **Si nuestro modelo no le gana a los tres,
no aprendió nada**, y lo vamos a decir.

Y qué sigue: en la Semana dos, el marco teórico de los modelos y el procedimiento.
En la tres, el primer modelo funcionando. En la cuatro, uno más avanzado. En la
cinco, el reporte final.

Cerramos con la idea que ordena todo el documento: **nada de lo que afirmamos hoy
es una cita de un libro. Todo está medido sobre nuestros datos, y cada número se
puede volver a generar con un comando.**

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

1. Fabrizio: el ejemplo de por qué sirven las series artificiales (10 s)
2. Jose Pablo: el matiz de *no hay pruebas en contra* contra *hay pruebas a favor* (15 s)
3. Alejandro: el ejemplo del helado y los ahogamientos (15 s)
4. Isaac: la explicación de la Precisión Direccional (15 s)

**No recorten ningún número.** Los números son lo que sostiene la exposición.

## Si preguntan al final

Quien contesta es **quien trabajó esa parte**, no quien esté más cerca. Si nadie
lo trabajó, la respuesta correcta es *«eso no lo medimos, así que no lo afirmo»*.

**Nadie inventa un número.** Si no está de memoria, se abre el documento.

## Nota sobre esta entrega

Para la Semana 1 el profesor pidió expresamente **documento y no presentación**.
Este guion queda preparado para la primera exposición que sí toque.
