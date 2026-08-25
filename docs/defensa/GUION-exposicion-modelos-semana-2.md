# Guion de exposición — Marco Teórico de Modelos, 15 minutos

> **Caso N.º 1 — Señales y Sistemas — Prof. Roberto Calvo Arias**
> Universidad Invenio · Tecnologías de la Información y Comunicación Empresarial

**Cuatro expositores, cada uno una sola vez.** Nadie vuelve a hablar después de su turno.

| Orden | Quién | Tiempo | De qué habla |
|---|---|---|---|
| 1 | **Fabrizio Espinoza Arce** | 0:00 – 3:30 | Dónde está el proyecto y cómo decidimos |
| 2 | **Isaac Felipe Morún Moreira** | 3:30 – 7:30 | Los cinco modelos y cuáles elegimos |
| 3 | **Alejandro Josué Rodríguez Zamora** | 7:30 – 11:30 | Qué pasó cuando los medimos |
| 4 | **Jose Pablo Monestel** | 11:30 – 15:00 | El procedimiento completo y qué sigue |

**Cómo usar este guion:** está escrito para leerse en voz alta tal cual, pero conviene que cada uno lo pase a sus palabras. Lo que **no** hay que cambiar son las cifras y las frases marcadas en negrita, que son las que sostienen el argumento.

---

# 1. FABRIZIO ESPINOZA ARCE — 0:00 a 3:30

## Dónde estamos y cómo decidimos

Buenas. Vamos a presentar el segundo avance del caso, que trata sobre los modelos.

Para ubicarnos: el proyecto busca **anticipar puntos de inflexión en el precio de Litecoin**. Un punto de inflexión es un momento en que el precio deja de subir y empieza a bajar, o al revés. Nuestro modelo tiene que responder una de tres cosas en cada momento: **máximo, mínimo o continuidad**.

En el primer avance definimos qué queremos predecir y con qué medir el éxito. **En este definimos con qué vamos a predecirlo.**

### Las tres decisiones que ya están cerradas

Antes de hablar de modelos hay tres cosas que fijamos y que conviene tener presentes, porque todo lo demás depende de ellas.

Trabajamos con **velas de 4 horas**, o sea que cada observación resume cuatro horas de mercado. Son **13 114 observaciones** en total.

Para decir que un momento es un máximo, exigimos que sea el punto más alto mirando **siete velas hacia cada lado**. Y pedimos que el modelo lo anuncie **una vela antes**.

Sumando las dos cosas, la anticipación real que ofrecemos son **ocho velas, es decir 32 horas**.

Los tres valores salieron de medir, y **cada uno de un criterio distinto que fijamos antes de mirar el resultado**. Eso último importa: si uno elige el criterio después de ver los números, ya no está midiendo, está justificando lo que quería hacer.

### Cómo tomamos las decisiones en este proyecto

Quiero dejar dicho cómo trabajamos, porque explica el resto de la exposición.

Tenemos tres reglas.

**La primera:** ningún número que no hayamos obtenido ejecutando algo. Si no lo corrimos, escribimos «no lo hemos medido».

**La segunda:** antes de publicar un número nuevo, el procedimiento tiene que **reproducir un número que ya conocíamos**. Si no lo reproduce, no publicamos nada hasta entender por qué.

**La tercera:** toda decisión que citemos como acordada tiene que poder señalar dónde se acordó. Llevamos dieciséis decisiones registradas, cada una con su razón y su evidencia.

Las tres salieron de errores propios. La segunda, por ejemplo, salió de que un guion mío daba cero donde tenía que dar tres, y **solo lo detecté porque puse un control que reproducía un valor que ya sabíamos**.

### Lo que van a escuchar

Isaac va a explicar los cinco modelos que pide el enunciado y cuáles elegimos. Alejandro, qué pasó cuando los medimos. Y Jose Pablo, el procedimiento completo y qué sigue.

**Les adelanto una cosa para que no los tome por sorpresa: el resultado de esta semana no es el que esperábamos.** Preferimos contarlo así.

---

# 2. ISAAC FELIPE MORÚN MOREIRA — 3:30 a 7:30

## Los cinco modelos, y cuáles elegimos

Gracias, Fabrizio. El enunciado nombra cinco modelos. Los recorro rápido y después explico la elección.

### Primero: qué es un modelo fundacional

Un **modelo fundacional de series de tiempo** es un modelo grande que alguien entrenó una vez con millones de series distintas —consumo eléctrico, ventas, tráfico, clima— y que después se puede usar sobre una serie que nunca vio, **sin volver a entrenarlo**.

Es la misma idea que hay detrás de ChatGPT, pero con series de números en vez de texto.

A eso se le llama **zero-shot**: cero entrenamiento sobre nuestros datos. Le mostramos el historial de Litecoin y pronostica.

**Por qué nos interesa:** tenemos pocos ejemplos de las clases que importan. Un modelo que ya aprendió cómo se comportan las series en general puede aprovechar eso, en lugar de tener que aprenderlo desde cero con nuestros pocos datos.

### Los que descartamos, y por qué

**VTA**, que significa *Verbal Technical Analysis*, convierte los indicadores del mercado a texto para que un modelo de lenguaje los lea. En nuestro caso habría que convertir **78 684 valores**. No medimos exactamente cuánto costaría, y lo decimos así: es un costo alto, no una cifra que inventamos.

**FinLSPM** lo descartamos por algo más simple. El enunciado exige que el código esté disponible públicamente, y **no lo encontramos**.

Y quiero ser preciso con esto, porque no es lo mismo: **no decimos que no exista. Decimos que no lo encontramos.** Solo una de esas dos cosas la podemos sostener.

**CryptoMamba** lo descartamos por dos razones que no dependen una de la otra.

La primera es técnica: **no se puede instalar sin una tarjeta gráfica NVIDIA**, y ninguna de nuestras máquinas tiene una. Lo comprobamos.

La segunda es de fondo. El enunciado pide **un Transformer** como segundo modelo, y menciona a CryptoMamba entre las opciones. Pero **CryptoMamba no es un Transformer**: es lo que se llama un modelo de espacio de estados, que funciona de otra manera. Procesa la secuencia en orden arrastrando una memoria, mientras que un Transformer compara todo contra todo a la vez.

Elegirlo cumpliría con la lista de opciones y no con lo que pide el entregable. **Esa ambigüedad la llevamos a consulta con usted en lugar de resolverla por nuestra cuenta.**

### El Transformer, y una crítica que hay que mencionar

El **Transformer** apareció en 2017 para traducción automática. Su idea central es la **atención**: para entender cada punto de una secuencia, el modelo mira todos los demás a la vez y decide cuánto le importa cada uno.

La ventaja frente a lo anterior es que **un punto de hace 200 pasos está a la misma distancia que uno reciente**. No hay que arrastrarlo por el camino y perderlo.

Ahora, hay literatura que cuestiona esa ventaja en series de tiempo. **Zeng y sus colegas mostraron en 2023 que un modelo lineal simple supera a varios Transformers** en las pruebas estándar. Su argumento es que la atención, por sí sola, **no distingue el orden temporal**: hay que decírselo aparte. Y en una serie de tiempo el orden es justamente el dato.

Esa crítica es la que motivó variantes diseñadas para series desde el principio, y no adaptadas del lenguaje. De ahí salen los dos candidatos reales: **Informer** e **iTransformer**.

### Lo que elegimos

Para el **modelo fundacional**, elegimos **Chronos-Bolt**, de Amazon. Medimos tres candidatos en nuestras máquinas, y el tiempo los separa de forma tajante: sobre el mismo bloque de datos, **Chronos-Bolt tarda 0,2 minutos y Chronos-T5 tarda 96,3**. Es **484 veces más rápido por ventana**. Nos habíamos puesto un techo de dos horas, y T5 no cabe.

Para el **modelo avanzado**, elegimos **iTransformer**. Es un Transformer que en vez de comparar instantes de tiempo entre sí, **compara series completas**: mira a Litecoin entero contra Bitcoin entero. Eso calza con nuestro problema, que tiene seis criptomonedas.

**A Informer no lo pudimos instalar.** Probamos tres caminos y ninguno resolvió en nuestro entorno. Y otra vez la precisión importa: eso **no prueba que Informer no sirva**. Es lo que pudimos verificar acá, y así lo reportamos.

Alejandro les cuenta qué pasó cuando los medimos.

---

# 3. ALEJANDRO JOSUÉ RODRÍGUEZ ZAMORA — 7:30 a 11:30

## Qué pasó cuando los medimos

Gracias, Isaac. Yo traigo los números, y hay dos que no son los que esperábamos.

### El piso contra el que se compara todo

Antes de los resultados, cómo se leen.

Tenemos tres modelos deliberadamente tontos que sirven de piso. El más simple **responde siempre «continuidad»**, o sea que nunca anuncia un giro. Otro responde al azar respetando las proporciones.

Sirven para lo siguiente: **si un modelo elaborado no le gana al que responde al azar, no aprendió nada**. Y con nuestros datos eso es más fácil de lo que parece, porque el 90 % de las velas son «continuidad». Un modelo que nunca anuncia nada acierta el 90 % de las veces y es completamente inútil.

Por eso no usamos exactitud. Usamos **F1 macro**, que pesa las tres clases por igual.

### Los resultados

| Modelo | F1 macro |
|---|---|
| Baseline trivial (responde siempre continuidad) | 0,3161 |
| Baseline aleatorio | 0,3368 |
| **Bosque aleatorio clásico** | **0,3905** |
| Chronos-Bolt, el fundacional | 0,3686 |
| iTransformer, el avanzado | 0,3457 |

**El mejor modelo del proyecto es el bosque aleatorio, que es el más simple de los tres y el que ya teníamos.**

Chronos-Bolt queda por debajo. iTransformer, más abajo todavía.

### Por qué eso no es un fracaso

Quiero explicar cómo leemos esto, porque importa más que los números.

Cada medición viene con un **intervalo de confianza**, que dice cuánto podría moverse el resultado si repitiéramos el experimento. Y la regla que usamos es: **si ese intervalo incluye el cero, no podemos afirmar que haya diferencia**, aunque el número del medio se vea bien.

Con esa regla:

- **Chronos-Bolt le gana al baseline trivial**, y eso se sostiene.
- **No le gana al baseline aleatorio.** La diferencia es +0,0318, pero el intervalo incluye el cero.
- **Contra el bosque no se distingue.**
- **iTransformer sí queda por debajo del bosque de forma distinguible**: −0,0448, y ahí el intervalo **no** incluye el cero.

Así que el resumen honesto es: **el modelo avanzado es el único cuya desventaja podemos afirmar.**

El enunciado pide comparar un fundacional contra uno avanzado. **Lo hicimos, y el resultado es que ninguno mejora al modelo clásico.** Eso es un resultado. Lo que no podíamos hacer era suponer que un Transformer sería mejor porque es lo moderno.

### El segundo resultado, y es más incómodo

Todo el planteamiento del caso descansa en un supuesto: que **Bitcoin, Ethereum, Solana, XRP y Cardano dicen algo sobre los giros de Litecoin**. Lo medimos.

La diferencia entre usar las seis criptomonedas y usar solo Litecoin es de **+0,00078**. Y cambia de signo según la semilla: en dos de cinco casos, **usar las seis da peor**.

Para saber si ese número era grande o chico, hicimos un control. Le añadimos al modelo **ocho columnas que repiten información que ya estaba**, con otro nombre. Por construcción no aportan nada nuevo, y sirven de vara.

**Esas ocho columnas inventadas dan +0,00071.**

O sea que **lo que se mide al incorporar las cinco criptomonedas es del mismo tamaño que lo que se mide al no incorporar nada.**

Y lo confirmamos desde otro lado: iTransformer es precisamente la arquitectura que compara series entre sí. Si aportaran, ahí tendría que notarse. Da **+0,0126**, por debajo del umbral que consideramos decisivo.

### Qué significa y qué no significa

**No significa que el planteamiento estuviera mal.** Las correlaciones que medimos en el primer avance justificaban plantearlo como multivariante, y esa justificación se sostiene.

**Lo que cambia es la conclusión, no el método.** Encontramos que a esta resolución y con estos modelos, la información adicional no se distingue del ruido.

Y prefiero decirlo así que presentarlo bonito, porque **una afirmación optimista se cae con una pregunta y esto no.**

---

# 4. JOSE PABLO MONESTEL — 11:30 a 15:00

## El procedimiento completo, y qué sigue

Gracias, Alejandro. Yo cierro con el procedimiento y con lo que viene.

### Los ocho pasos

El entregable incluye el procedimiento completo para desarrollar el modelo, declarando en cada paso **qué está construido y medido y qué falta**.

Son ocho: extracción de datos, limpieza, análisis exploratorio, ingeniería de características, partición, selección del modelo, entrenamiento y evaluación.

Me detengo en tres que tienen algo que contar.

### La partición, y por qué no se hace al azar

Cuando uno entrena un modelo, separa los datos en tres bloques: uno para entrenar, uno para ajustar y uno para la prueba final.

En la mayoría de los problemas eso se hace al azar. **En series de tiempo, no se puede.** Si mezclás, el modelo termina entrenando con datos del futuro y evaluándose con datos del pasado, y los resultados salen buenísimos por una razón que no sirve para nada.

Nosotros partimos **respetando el orden del tiempo**. Y hacemos algo más: dejamos un **embargo** entre bloques, o sea que descartamos unas velas en cada frontera.

El motivo es que nuestra etiqueta mira siete velas hacia adelante. Sin ese embargo, las últimas velas del bloque de entrenamiento tendrían una etiqueta que depende de datos del bloque siguiente. Son 16 observaciones descartadas de 13 114: un costo despreciable a cambio de que el resultado sea creíble.

### La ingeniería de características, y qué encontramos

Construimos 63 columnas: retornos, rezagos, indicadores técnicos, medidas de volatilidad y de correlación entre activos.

Y las medimos una por una con una técnica que se llama **importancia por permutación**: se desordena una columna a propósito y se ve cuánto empeora el modelo. **Si podés barajarla sin que pase nada, el modelo no la estaba usando.**

Acá hicimos lo mismo que Alejandro con su control: **cualquier lista ordenada por importancia se puede leer**, aunque las 63 columnas fueran ruido, porque alguna queda primera igual. Así que añadimos cinco columnas de ruido puro y usamos la mejor de ellas como piso.

**Resultado: 17 de las 63 columnas son indistinguibles de una columna inventada.**

Las que encabezan son medidas de **posición relativa** —dónde está el precio respecto de su vecindad reciente— y no el precio en sí. Eso es coherente con lo que ya habíamos encontrado en el primer avance.

### La evaluación, y una limitación que declaramos nosotros

Un modelo fundacional pronostica **el precio**, no la clase. Hay que decidir cómo se cruza ese puente.

Elegimos pronosticar la trayectoria y aplicarle **la misma función de etiquetado que usamos con los datos reales**. Lo decidió una medición: hacerlo cuesta **12 segundos** sobre el bloque entero, así que la opción más simple resultó ser también la más barata.

Y trae una limitación que preferimos declarar nosotros. Nuestro etiquetador exige que **los catorce vecinos** sean estrictamente menores que el centro para marcar un máximo. Sobre precios reales eso está bien. Sobre una trayectoria **pronosticada**, que sale muy suave, diferencias diminutas deciden la etiqueta: comprobamos que **un vecino una diezmilmillonésima por debajo cambia el resultado**.

Por eso el modelo avanzado no da exactamente el mismo número en dos corridas idénticas. **No es un defecto del etiquetador: es el precio del camino que elegimos**, y afecta a cualquier modelo que pronostique una trayectoria suave.

### Lo que sigue

Tres cosas.

La **aplicación web** ya muestra los precios reales con los giros marcados y compara los cuatro modelos lado a lado. Le falta conectarse al modelo real, que es la próxima semana.

Las **pruebas de detección**: verificar que el sistema detecta giros sobre series construidas por nosotros, donde sabemos dónde están las respuestas.

Y la **medición final sobre el bloque de prueba**, que no hemos tocado. Se gasta una sola vez, cuando la configuración esté fija. Todo lo que presentamos hoy es sobre el bloque de ajuste.

### Cierre

Para cerrar, lo que nos llevamos de esta semana.

Revisamos los cinco modelos, elegimos dos midiendo en nuestras máquinas, y **los dos resultaron peores que el modelo simple que ya teníamos**. Medimos si las otras cinco criptomonedas aportaban información, **y no pudimos afirmar que aporten**.

Ninguna de las dos cosas es lo que queríamos encontrar. **Las dos están medidas, tienen su control al lado, y son reproducibles.**

Muchas gracias.

---

# Anexo — Preparación

## Ensayo recomendado

**Una vez cada uno por separado, con cronómetro.** El objetivo es que nadie se pase de su ventana, porque el que se pasa se lo come al siguiente.

**Una vez los cuatro seguidos**, sin parar aunque alguien se trabe. Sirve para ver los empalmes, que es donde se pierde tiempo.

**Los empalmes ya están escritos** al final de cada turno: «Alejandro les cuenta qué pasó cuando los medimos». Decirlos tal cual evita el silencio incómodo.

## Si se pasan de tiempo

Lo que se puede recortar sin romper el argumento:

| Quién | Qué recortar |
|---|---|
| Fabrizio | La explicación de las tres reglas — decir solo la segunda |
| Isaac | La crítica de Zeng et al. — mencionarla en una frase |
| Alejandro | Los ocho valores de la tabla — decir tres: bosque, fundacional y avanzado |
| Jose Pablo | El embargo de la partición |

**Lo que NO se recorta:** las cifras de la tabla de resultados, el control de las columnas duplicadas, y la frase «cambia la conclusión, no el método».

## Si preguntan al final

Contesta **quien tiene el tema**, no quien esté más cerca:

- Modelos, arquitecturas, por qué se descartó cada uno → **Isaac**
- Números, intervalos, el resultado multivariante → **Alejandro**
- Procedimiento, partición, características, aplicación → **Jose Pablo**
- Decisiones del equipo, criterios, organización → **Fabrizio**

Si nadie sabe la respuesta: **«No lo hemos medido»**. Es una respuesta legítima en este proyecto y es mejor que inventar. Es literalmente la primera de nuestras reglas.

La guía de defensa completa, con las preguntas probables y sus respuestas, está en `DEFENSA-modelos-semana-2.md`.

## Nota sobre esta entrega

El Avance N.º 2 **se entrega como documento, no como presentación**. Este guion existe para tenerlo listo si el profesor pide exposición, y como base de la presentación final del 8 de septiembre.
