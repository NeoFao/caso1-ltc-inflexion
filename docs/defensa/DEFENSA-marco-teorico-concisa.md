# Guía de Defensa — Marco Teórico, Semana 1 (versión concisa) (versión concisa)

> **Caso N.º 1 — Señales y Sistemas — Prof. Roberto Calvo Arias**
> Tecnologías de la Información y Comunicación Empresarial · Universidad Invenio
> Equipo: Fabrizio Espinoza Arce · Alejandro Josué Rodríguez Zamora · Jose Pablo Monestel · Isaac Felipe Morún Moreira

**Esta guía está escrita para gente que no sabe de señales.** No asume nada. Cada
palabra rara se explica cuando aparece por primera vez, con una comparación de la
vida diaria antes de la definición formal.

**No es el entregable.** El entregable es el Word de 54 páginas que está en
`docs/entregas/semana-1-concisa/`. Esto es para leer *antes* de pararse delante del
profesor.

> **Cuál de las dos versiones acompaña esta guía.** Existen dos Word con el mismo
> contenido y distinta redacción: la extensa, de 62 páginas, y la concisa, de 54.
> **Esta guía es la de la versión concisa.** La diferencia entre ambas es de prosa,
> no de sustancia: mismas 15 figuras, mismas 30 referencias, mismos 17 puntos del
> enunciado. Lo único que la concisa no incluye es la tabla que cruza granularidad
> y ventana, que corresponde a la extracción de datos de la Semana 2 —y eso cambia
> una de las respuestas de la Parte III, marcada más abajo.

---

## Cómo usar esta guía según el tiempo que tengas

| Tiempo | Qué leer |
|---|---|
| **Si nunca entendiste el proyecto** | **La Parte 0 completa.** Sin ella el resto son palabras sueltas |
| 20 minutos | Parte 0 + las 10 cifras + las 6 respuestas que no podés fallar |
| **2 horas** | **El plan cronometrado de abajo** |
| Una tarde | Todo, en orden |

---

## Plan de 2 horas, cronometrado

*Poné un temporizador y respetalo. La trampa al estudiar es quedarse cuarenta
minutos en lo primero y llegar sin haber visto el resto.*

| Reloj | Min | Qué hacés | Por qué ahí |
|---|---|---|---|
| **0:00 – 0:25** | 25 | **Parte 0 entera**, sin saltarte nada | Si no tenés claro qué es una vela y qué es un retorno, todo lo demás no se sostiene |
| **0:25 – 0:40** | 15 | **El dibujo del máximo y la lupa.** Tapalo y **redibujalo en papel** | Es *el* concepto del caso. Si sabés dibujarlo, tenés el proyecto |
| **0:40 – 0:55** | 15 | **Las 6 respuestas que no podés fallar**, en voz alta, no leyendo | Son las preguntas más probables. Decirlas en voz alta es lo que las fija |
| **0:55 – 1:10** | 15 | **Las 10 cifras.** Solo esas | El resto está en el documento y lo podés abrir delante del profesor |
| **1:10 – 1:30** | 20 | **Los cuatro hallazgos**: los retornos no se autocorrelacionan · la correlación en nivel es errática · el 86,9 % que engaña · la volatilidad cambia 8,8 veces | Es lo que separa "cumplió" de "entendió" |
| **1:30 – 1:45** | 15 | **Las series construidas**: por qué las hicimos y qué prueban | Lo pidió el profesor en persona. Va a preguntar |
| **1:45 – 1:55** | 10 | **Las preguntas difíciles** de la Parte III | Son las que nadie prepara |
| **1:55 – 2:00** | 5 | **La respuesta de 60 segundos**, en voz alta, tres veces | Es lo primero que vas a decir. Que salga sola |

> **Si te trabás con algo, saltalo y seguí el reloj.** Es mejor tocar los ocho
> puntos que dominar tres.

---

## Las 10 cifras que sí o sí

*Todo lo demás podés buscarlo delante del profesor, abriendo el documento. Estas
diez tienen que salir sin buscar.*

| # | Cifra | Qué es |
|---|---|---|
| 1 | **2 185** | Velas diarias del panel, del 11/08/2020 al 04/08/2026 |
| 2 | **6** | Criptomonedas: LTC más BTC, ETH, SOL, XRP y ADA |
| 3 | **0 de 6 · 6 de 6** | Series que pasan la prueba de estacionariedad: ninguna en precios, todas en retornos |
| 4 | **0,991 → −0,036** | Autocorrelación en el rezago 1, de precios a retornos |
| 5 | **3 de 40** | Rezagos con autocorrelación significativa en los retornos |
| 6 | **8,8 veces** | Cuánto más agitado es el tramo más volátil que el más tranquilo |
| 7 | **0,126 vs 0,715** | Correlación LTC–BTC en precios y en retornos. El número que delata el problema |
| 8 | **86,9 %** | Exactitud del modelo que nunca detecta nada. Por eso no usamos exactitud |
| 9 | **0,0945 y 0,9033** | Correlaciones que recuperamos habiendo pedido 0,1 y 0,9 |
| 10 | **1 de cada w+1** | Cota aritmética: como mucho esa fracción de velas puede ser máximo |

**En esta versión hay tres más**, y estas pesan porque **ya no están impresas en el
documento**: el piso de **300** ejemplos de clase minoritaria que fijamos antes de
medir, los **149** que deja el mejor caso con velas diarias, y los **420** que deja
`w=7` sobre velas de 4 horas. Sostienen la respuesta de la Parte III sobre por qué
el documento usa valores provisionales.

**Si te preguntan una cifra que no recordás, la respuesta correcta NO es inventarla:**

> «No la tengo de memoria, está en `docs/evidencias/`. Se la abro.»

Eso suma. Inventar un número que después no cuadra con el documento resta.

---
---

# PARTE 0 — DESDE CERO

*Si nunca entendiste de qué va este proyecto, empezá acá. Son veinticinco
minutos y después el resto se lee solo.*

## La analogía que sirve para todo el proyecto: la montaña rusa

Imaginate que estás mirando una montaña rusa desde lejos y alguien te pide:
**«avisame cuándo el carrito está en una cima, y cuándo está en un valle»**.

```
        CIMA                            CIMA
         /\                              /\
        /  \          CIMA              /  \
       /    \          /\              /    \
      /      \        /  \            /      \
  ___/        \______/    \__________/        \___
                VALLE          VALLE
```

Eso es todo el proyecto. El carrito es **el precio de Litecoin**. Las cimas son
los **máximos** y los valles los **mínimos**. Todo lo demás —cimas, valles y el
camino entre ellos— se llama **zona de continuidad**.

Y hay una trampa que es el corazón del caso: **para saber que estás en una cima,
tenés que ver lo que viene después.** Si el carrito sigue subiendo, no era cima.
Eso significa que la respuesta llega tarde, y con eso vamos a lidiar todo el
proyecto.

## Concepto 1: qué es una serie temporal

Una **serie temporal** es simplemente **una lista de números en orden de tiempo**.

La temperatura de cada día del año es una serie temporal. Las ventas de cada mes
son una serie temporal. **El precio de Litecoin cada día es una serie temporal.**

```
   TABLA NORMAL                    SERIE TEMPORAL
   (podés barajar las filas)       (el orden ES el dato)

   Cliente  Edad                   Día 1: 100
   Ana      34                     Día 2: 102     ← este depende del anterior
   Luis     28                     Día 3: 105     ← y este del anterior
   Marta    41                     Día 4: 103
```

**La diferencia clave:** en una tabla de clientes podés cambiar el orden de las
filas y no perdés nada. En una serie temporal, **si cambiás el orden destruís la
información**, porque cada número está relacionado con el anterior.

> **Si te preguntan qué distingue una serie temporal:** el orden no es un
> atributo, es parte del dato. Reordenarla no la desordena: la destruye.

## Concepto 2: qué es una vela

El precio de una cripto cambia a cada segundo. Nadie guarda cada segundo. Se
agrupa en bloques de tiempo, y cada bloque se llama **vela** (*candle*, en inglés).

Una vela de un día guarda cuatro números de ese día: con cuánto **abrió**, el más
**alto**, el más **bajo**, y con cuánto **cerró**.

```
   UNA VELA DIARIA
                 │  ← el precio más alto del día
              ┌──┴──┐
              │     │ ← cierre (con cuánto terminó)
              │     │
              │     │ ← apertura (con cuánto empezó)
              └──┬──┘
                 │  ← el precio más bajo del día
```

**Nosotros usamos solo el cierre.** No es decisión nuestra: el enunciado lo dice
expresamente.

**"Velas de 4 horas"** significa lo mismo pero partiendo el día en seis pedazos.
Seis datos por día en vez de uno.

## Concepto 3: qué es un retorno

Un **retorno** es **cuánto cambió el precio en porcentaje**, de una vela a la
siguiente.

Si ayer cerró en 100 y hoy en 105, el retorno es **+5 %**.

```
   PRECIO (nivel)          RETORNO (cambio %)
   100                       —
   105                     +5,0 %
   103                     −1,9 %
   110                     +6,8 %
```

**Por qué importa tanto esta distinción:** el precio de LTC pasó de **40,92** a
**387,80** dentro de nuestra muestra. Un movimiento de 10 dólares es enorme cuando
el precio vale 40 e insignificante cuando vale 380. El retorno arregla eso, porque
mide el cambio **relativo** y no el absoluto.

> Esta es la decisión técnica más repetida del documento: **trabajamos sobre
> retornos, no sobre precios.** Y no por costumbre: lo medimos. Ya vas a ver cómo.

## Concepto 4: qué es la estacionariedad

Una serie es **estacionaria** cuando **sus reglas del juego no cambian con el
tiempo**. Más formalmente: su promedio es siempre parecido y su nivel de agitación
es siempre parecido, mires el tramo que mires.

```
   ESTACIONARIA                    NO ESTACIONARIA
   (oscila alrededor de una        (se va para arriba, nunca
    línea fija)                     vuelve a donde estaba)

   ─╮╭─╮╭╮─╮╭─╮╭─╮╭──                        ╱╲╱
    ╰╯ ╰╯╰╯ ╰╯ ╰╯                       ╱╲╱╲╱
   ═══════════ media fija          ╱╲╱╲╱
                                 ╱
```

**El precio de una cripto no es estacionario:** vale 40 en 2020 y 380 en 2021. No
hay ningún "valor normal" al que vuelva.

**Por qué es un problema:** casi todas las herramientas estadísticas clásicas
—regresión, ARIMA, correlación— **asumen** que las reglas no cambian. Si las aplicás
a algo no estacionario, dan resultados que parecen buenos y son falsos.

## Concepto 5: la prueba ADF, el p-valor y la hipótesis nula

Para no decidir "a ojo" si una serie es estacionaria, existe una prueba
estadística. La nuestra se llama **ADF**, que son las iniciales de
**Dickey-Fuller Aumentado** (*Augmented Dickey-Fuller*), por los dos estadísticos
que la inventaron.

Funciona así, y es más simple de lo que parece:

- **La hipótesis nula** es la suposición de partida. Acá es: *"esta serie NO es
  estacionaria"*.
- La prueba devuelve un número entre 0 y 1 llamado **p-valor**.
- **p-valor bajo** (menor a 0,05) → hay evidencia suficiente para **descartar** la
  suposición de partida. O sea: sí es estacionaria.
- **p-valor alto** → no hay evidencia para descartarla. Nos quedamos con la duda.

> **Analogía del juicio.** La hipótesis nula es "el acusado es inocente". El
> p-valor es qué tan fuerte es la prueba en su contra. Un p-valor bajo condena.
> Un p-valor alto **no demuestra que sea inocente**: solo dice que no alcanzó la
> evidencia.

**Esta última frase es exactamente el matiz que puede subir la nota.** Lo decimos
textual en el documento: no rechazar la hipótesis nula **no demuestra** que la
serie sea no estacionaria; demuestra que no hay evidencia suficiente en contra.

### Lo que medimos

| | Rechazan la hipótesis nula al 5 % |
|---|---|
| Precios en nivel | **0 de 6** |
| Retornos | **6 de 6** |

p-valores en precios: LTC **0,179** · BTC **0,483** · ETH **0,059** · SOL **0,274**
· XRP **0,285** · ADA **0,159**. En retornos, las seis dan **p < 0,000001**.

**El caso al borde:** ETH da 0,059, apenas por encima de 0,05. No cambia la
conclusión, pero **decilo vos antes de que lo pregunten**. Muestra que leíste la
tabla en vez de resumirla.

## Concepto 6: volatilidad

**Volatilidad = cuánto se mueve el precio.** Nada más.

Se mide con la **desviación estándar** de los retornos, que es una fórmula que
responde *"¿qué tan dispersos están estos números respecto de su promedio?"*.

Nosotros la calculamos con una **ventana móvil de 30 velas**: para cada día,
miramos los 30 días anteriores y calculamos qué tan agitados estuvieron. Así vemos
cómo cambia la agitación a lo largo del tiempo, en vez de tener un solo número
para los seis años.

**Lo que medimos en LTC:** el tramo más agitado da **0,1220** y el más tranquilo
**0,0138**. El cociente es **8,8 veces**.

## Concepto 7: heterocedasticidad

Palabra fea, idea sencilla. Viene del griego: *hetero* (distinto) + *cedasticidad*
(dispersión). **Significa que la agitación cambia con el tiempo.**

```
   HOMOCEDÁSTICA                   HETEROCEDÁSTICA
   (siempre igual de agitada)      (tramos calmos y tramos locos)

   ╱╲╱╲╱╲╱╲╱╲╱╲╱╲╱╲               ╱╲╱╲──╱╲╱╲  ╱╲    ╱╲╱╲──
                                          ╲╱  ╲╱╲╱
```

- **Homocedástica** = la agitación es siempre la misma.
- **Heterocedástica** = hay épocas tranquilas y épocas de pánico.

**Las criptos son heterocedásticas**, y nuestro 8,8 lo demuestra sobre datos
reales. Eso rompe el supuesto de ARIMA, que es el modelo clásico de series
temporales y asume agitación constante.

> **Si te preguntan por qué no usan ARIMA:** porque ARIMA asume varianza constante,
> y medimos que la volatilidad de LTC varía 8,8 veces entre extremos. No es una
> objeción teórica, es un número nuestro.

## Concepto 8: autocorrelación

**Autocorrelación = cuánto se parece la serie a sí misma unos pasos atrás.**

El prefijo *auto* significa "a sí misma". La pregunta que responde es: *¿el valor
de hoy me dice algo sobre el valor de mañana?*

Un **rezago** (*lag*) es cuántos pasos atrás miramos. Rezago 1 = la vela anterior.
Rezago 5 = cinco velas atrás.

**Lo que medimos:**

| | Autocorrelación en el rezago 1 |
|---|---|
| Precio | **0,991** (casi 1: altísima) |
| Retorno | **−0,036** (casi 0: nula) |

**Cómo se leen esos dos números, que es lo importante:**

- **0,991 en el precio no es una buena noticia.** Es obvio: el precio de hoy se
  parece al de ayer porque *es casi el mismo número*. Esa es justamente la firma
  de una serie no estacionaria. No sirve para predecir nada.
- **−0,036 en el retorno sí es información real:** el porcentaje que subió ayer
  **no dice nada** sobre el que va a subir hoy.

Y de los **40 rezagos** que examinamos, solo **3** salen de la banda de confianza:
los rezagos 8, 14 y 31.

> **Cuidado: la "banda de confianza" es la franja dentro de la cual un valor se
> considera indistinguible de cero.** Salir de la banda significa "esto podría no
> ser casualidad".

## Concepto 9: correlación cruzada, y la trampa de la correlación espuria

**Correlación = cuánto se mueven dos cosas juntas.** Va de −1 a 1.

- **1** = se mueven idénticamente.
- **0** = no tienen nada que ver.
- **−1** = cuando una sube, la otra baja.

*Cruzada* solo quiere decir que son **dos series distintas** (LTC contra BTC), a
diferencia de la autocorrelación, que compara una serie consigo misma.

### La trampa, que es nuestro mejor hallazgo

Medimos la correlación de dos maneras y dieron cosas muy distintas:

| Par | Sobre precios | Sobre retornos |
|---|---|---|
| LTC – BTC | **0,126** | **0,715** |
| LTC – ADA | **0,796** | **0,641** |

**Leelo despacio, porque es el punto más fuerte que tenemos.** Sobre precios, el
resultado dice que **Litecoin casi no tiene relación con Bitcoin** (0,126) y sí
mucha con Cardano (0,796). Eso es económicamente absurdo: Bitcoin es el activo que
marca la tendencia de todo el mercado cripto.

Sobre retornos, el orden se corrige: LTC–BTC sube a 0,715 y LTC–ADA baja a 0,641.

**Por qué pasa:** se llama **correlación espuria**. Dos series que ambas suben con
el tiempo van a parecer correlacionadas *aunque no tengan nada que ver*, porque lo
que se está midiendo es que las dos suben, no que se muevan juntas.

```
   Ejemplo clásico: el consumo de helados y los ahogamientos suben los dos
   en verano. Correlación altísima. El helado no ahoga a nadie: lo que sube
   es el calor, y arrastra a los dos.
```

> **La frase para la defensa:** el problema de la correlación en nivel no es que
> infle los valores, es que es **errática**. Ordena los activos de forma
> económicamente implausible.

## Concepto 10: qué es un punto de inflexión, y la lupa

Volvé a la montaña rusa. **Un máximo no existe en términos absolutos: existe
respecto de una ventana.**

Mirá esta serie, que **nos la inventamos para explicar el punto**:

```
   Día:     1    2    3    4    5    6    7    8    9   10   11
   Cierre: 100  102  105  103  106  110  108  104  101  103  107
                      ▲              ▲
                      │              │
                  ¿es cima?      ¿es cima?
```

- **Si mirás 1 día a cada lado:** el día 3 ES una cima. 105 es mayor que 102 y que
  103.
- **Si mirás 5 días a cada lado:** el día 3 **ya no** es cima, porque dentro de esa
  vecindad está el día 6 con 110, que es más alto.

**El día 3 no cambió. Cambió la lupa.** Y las dos lecturas son correctas: el día 3
*es* un giro pequeño y *no es* un giro importante.

> **Esta es la idea central del caso entero.** No estamos buscando "la definición
> verdadera" de máximo, porque no existe. Estamos **eligiendo a qué escala trabaja
> el modelo**, y esa elección hay que justificarla.

## Concepto 11: qué son `w` y `h`

Son las dos letras que aparecen por todas partes. Son sencillas.

**`w` es la lupa: cuántas velas miramos a cada lado.**

> Una vela es **Máximo** si su cierre es mayor que el de TODAS las velas entre
> `t−w` y `t+w`. Es **Mínimo** si es menor que todas ellas. Si no, es **Zona de
> Continuidad**.

**`h` es cuánto hacia adelante predecimos.** El modelo mira lo que pasó hasta hoy
y responde: la vela de dentro de `h` velas, ¿va a ser máximo, mínimo o nada?

**No se confunden:** `w` define **qué es** un giro. `h` define **con cuánta
anticipación** lo anunciamos.

## Concepto 12: la cota aritmética y las clases desbalanceadas

Acá hay una propiedad que se demuestra en dos líneas y condiciona todo el proyecto.

> **Dos máximos no pueden estar a menos de `w+1` velas de distancia.**
> Si lo estuvieran, cada uno caería dentro de la ventana del otro, y cada uno
> tendría que ser mayor que el otro. Imposible.

**Consecuencia:** como mucho **1 de cada `w+1`** velas puede ser máximo. Con `w=5`
eso es el 16,7 %; con `w=7`, el 12,5 %. Y lo medido queda muy por debajo: con
`w=5` sobre velas diarias, apenas el **6,58 %** son máximos.

Esto se llama **clases desbalanceadas**: una de las respuestas posibles aparece
muchísimo más que las otras.

| Clase | Cuántas | Porcentaje |
|---|---|---|
| Máximo | 143 | **6,58 %** |
| Mínimo | 141 | **6,48 %** |
| Continuidad | 1 891 | **86,94 %** |

**Y esto no es un defecto de nuestros datos que se arregle bajando más historia.
Es una propiedad permanente del problema, garantizada por la definición.**

## Concepto 13: por qué la exactitud engaña

**Exactitud** (*accuracy*) = qué porcentaje de las veces acertaste.

Suena bien. Es una trampa.

```
   EL MODELO INÚTIL
   Un modelo que responde SIEMPRE "Continuidad", sin mirar nada:

   Acierta las 1 891 continuidades  ✓
   Falla los 143 máximos            ✗
   Falla los 141 mínimos            ✗
                                    ─────
   Exactitud: 86,9 %  ← ¡y no detectó un solo giro!
```

**Un 86,9 % de exactitud suena excelente en una presentación y es un modelo
completamente inservible.** Lo medimos: ese es exactamente el número de nuestro
*baseline* trivial.

> **Un baseline (línea base) es un modelo tonto a propósito**, que sirve de piso.
> Si tu modelo elaborado no le gana al tonto, no aprendió nada.

Por eso el enunciado no pide exactitud: pide **F1-Score** y **Precisión
Direccional**.

## Concepto 14: F1-Score, en cristiano

El F1 combina dos preguntas distintas:

- **Precisión:** de todos los giros que anuncié, ¿cuántos eran de verdad?
  *(¿cuántas falsas alarmas di?)*
- **Recall** (o exhaustividad): de todos los giros que hubo, ¿cuántos anuncié?
  *(¿cuántos se me pasaron?)*

```
   Un modelo que anuncia UN SOLO giro y acierta:
      Precisión: 100 %   (no se equivocó nunca)
      Recall:      1 %   (se le pasaron casi todos)

   Un modelo que anuncia que TODO es giro:
      Precisión:   7 %   (casi todo falsa alarma)
      Recall:    100 %   (no se le pasó ninguno)
```

**El F1 castiga los dos extremos.** Solo sale alto si el modelo acierta y además
no se pierde los casos.

**F1 macro** significa que calculamos el F1 de cada clase por separado y sacamos el
promedio simple, **dándole el mismo peso a las tres**. Es lo que impide que la
clase gigante tape a las dos chiquitas.

**Lo que medimos:** el baseline trivial saca **F1 macro de 0,308** frente a una
exactitud de 0,856. **Ahí se ve el engaño en dos números lado a lado.**

## Concepto 15: serie sintética o construida

Una **serie construida** (o sintética) es una serie que **fabricamos nosotros**,
donde **nosotros pusimos la respuesta correcta**.

**Para qué sirve, que es la pregunta importante:** para comprobar que nuestro
método detecta lo que dice detectar, **antes** de aplicarlo a datos reales donde
nadie sabe la verdad.

```
   SIN CONTROL                          CON CONTROL
   Aplico el método a LTC.              1. Fabrico una serie con
   Sale 0,74.                              correlación 0,9 puesta por mí
   ¿Es real o es mi método?             2. Mido → sale 0,9033  ✓ funciona
   No hay forma de saberlo.             3. AHORA sí mido LTC
```

Esto lo pidió el profesor expresamente en la sesión. **Y lo cumplimos en las
cuatro condiciones que nombró:**

| Lo que fijamos | Lo que medimos |
|---|---|
| Correlación **0,1** | **0,0945** |
| Correlación **0,9** | **0,9033** |
| Volatilidad **0,01384** | **0,01395** |
| Volatilidad **0,122** | **0,12349** |

**Detalle que vale la pena decir:** los dos niveles de volatilidad no los elegimos
al azar. Son los extremos que medimos en el LTC real, así que la serie construida
cubre exactamente el rango que se observa en el mercado.

## Las ocho palabras que tenés que poder decir sin dudar

| Palabra | Tu definición de bolsillo |
|---|---|
| **Serie temporal** | Lista de números en orden de tiempo, donde el orden es parte del dato |
| **Vela** | Un bloque de tiempo con su precio de apertura, máximo, mínimo y cierre |
| **Retorno** | Cuánto cambió el precio en porcentaje respecto de la vela anterior |
| **Estacionaria** | Que sus reglas no cambian con el tiempo: promedio y agitación estables |
| **Heterocedasticidad** | Que la agitación cambia: hay épocas calmas y épocas de pánico |
| **Autocorrelación** | Cuánto se parece la serie a sí misma unos pasos atrás |
| **Correlación espuria** | Dos series parecen relacionadas solo porque las dos suben con el tiempo |
| **Clases desbalanceadas** | Una respuesta aparece muchísimo más que las otras, y rompe la exactitud |

---
---

# PARTE I — RESUMEN COMPACTO

## La respuesta de 60 segundos

*Esto es lo primero que decís. Practicalo en voz alta hasta que salga solo.*

> «El caso pide predecir puntos de inflexión en el precio de Litecoin: máximos
> locales, mínimos locales y zonas de continuidad, usando además Bitcoin, Ethereum,
> Solana, XRP y Cardano como variables de apoyo.
>
> Esta primera entrega es el marco teórico. Cubrimos los ocho puntos de series de
> tiempo, los ocho de criptoactivos y el noveno de métricas.
>
> Lo hicimos con un criterio que declaramos desde la introducción: **ningún
> concepto se expone solo como definición.** Cada propiedad que enunciamos la
> verificamos sobre nuestros propios datos y reportamos el número. Son 2 185
> observaciones diarias de las seis criptomonedas, de agosto de 2020 a agosto de
> 2026.
>
> Y siguiendo lo que usted sugirió en la sesión, varios conceptos se ilustran
> primero sobre series que construimos nosotros, con la volatilidad y la
> correlación fijadas de antemano, para comprobar que el método detecta lo que
> dice detectar antes de aplicarlo al mercado real.»

## Lo que entregamos, en números

| | |
|---|---|
| Páginas | 54 |
| Palabras | 10 832 |
| Figuras | 15, de las cuales **6 son construidas por nosotros** |
| Tablas | 4 |
| Referencias | 30, en APA 7, con DOI verificado contra Crossref |
| Puntos del enunciado cubiertos | **17 de 17** |

## Las 6 respuestas que no podés fallar

### 1. «¿Por qué trabajan sobre retornos y no sobre precios?»

> «Porque lo medimos. La prueba ADF no rechaza la raíz unitaria en ninguna de las
> seis series de precios, y la rechaza en las seis de retornos, con p menor a
> 0,000001. La autocorrelación lo confirma desde otro ángulo: pasa de 0,991 sobre
> precios a −0,036 sobre retornos. No es una convención de la disciplina, es una
> consecuencia de nuestra medición.»

### 2. «¿Por qué no usan exactitud?»

> «Porque medimos que engaña. Un modelo que responde siempre "Continuidad" y no
> detecta un solo giro alcanza **86,9 % de exactitud**, y su F1 macro es **0,308**.
> Los dos números salen del mismo modelo. El desbalance además no es un defecto de
> la muestra: está garantizado por la definición de la etiqueta, porque dos máximos
> no pueden estar a menos de `w+1` velas.»

### 3. «¿Qué es un punto de inflexión y quién decide la ventana?»

> «Un máximo no existe en términos absolutos, existe respecto de una ventana. La
> misma vela es un giro con una lupa y no lo es con otra. El enunciado nombra la
> ventana `w` pero no fija su valor, así que la elección es nuestra y hay que
> justificarla con datos. Nuestro criterio se fijó antes de medir: el `w` más
> grande que deje al menos 300 ejemplos de la clase minoritaria.»

### 4. «¿Para qué sirven las series que construyeron?»

> «Para verificar el método antes de creerle. En cada concepto medimos primero
> sobre una serie donde la respuesta la pusimos nosotros, y solo después sobre
> Litecoin. Pedimos correlación 0,1 y medimos 0,0945; pedimos 0,9 y medimos 0,9033;
> fijamos volatilidad en 0,01384 y medimos 0,01395; en 0,122 y medimos 0,12349. Si
> el método no recuperara lo que le pedimos, no tendríamos derecho a interpretar lo
> que mide sobre datos reales.»

### 5. «¿Por qué el problema tiene que ser multivariante?»

> «Porque lo medimos, y podría haber salido que no. Sobre retornos, las
> correlaciones entre las seis van de **0,475 a 0,806**, con media 0,625. Si LTC se
> moviera de forma independiente, las cinco variables de apoyo sobrarían; si la
> correlación fuera casi 1, serían redundantes. El valor medido está en el rango
> donde sí pueden aportar información.»

### 6. «¿Cuál es el hallazgo más importante del documento?»

> «Que los retornos de LTC no tienen autocorrelación lineal significativa: de 40
> rezagos, solo 3 salen de la banda de confianza. Eso significa que un modelo
> lineal sobre precios rezagados tendría muy poco que explotar. No es un resultado
> negativo: **es la justificación del enfoque del caso**, porque es el argumento
> medido a favor de usar modelos no lineales y multivariantes.»

---
---

# PARTE II — LOS CUATRO HALLAZGOS

*Esto es lo que separa "cumplieron el temario" de "entendieron el problema".
Decilos vos antes de que los pregunten.*

## Hallazgo 1: los retornos no se autocorrelacionan, y eso es bueno

**El dato:** 3 rezagos significativos de 40. Autocorrelación en el rezago 1 de
**−0,036**.

**Por qué es nuestra mejor carta:** parece un resultado negativo y es exactamente
lo contrario. Si tres rezagos de cuarenta bastaran para predecir, alcanzaría un
modelo lineal simple y no haría falta ni aprendizaje profundo ni las cinco
criptomonedas de apoyo que pide el enunciado.

**Lo que conecta con teoría:** es consistente con la **hipótesis de mercados
eficientes en forma débil** (Fama, 1970), que dice que los precios pasados no
permiten anticipar rendimientos futuros con reglas simples.

## Hallazgo 2: la correlación en nivel no es alta, es errática

**El dato:** LTC–BTC da **0,126** en precios y **0,715** en retornos. LTC–ADA hace
el camino inverso: **0,796** en precios y **0,641** en retornos.

**Por qué importa:** mucha gente diría "la correlación en nivel infla los valores".
Nosotros medimos que el problema es peor: **desordena los activos**. Atribuye a
Litecoin una relación casi nula con Bitcoin, que es el activo que marca la
tendencia de todo el sector.

**El respaldo teórico:** Granger y Newbold (1974) describieron el fenómeno de la
regresión espuria. Como medimos que los precios no son estacionarios, cualquier
correlación calculada sobre ellos hereda ese defecto.

## Hallazgo 3: el desbalance está garantizado por la definición

**El dato:** con `w=5` sobre velas diarias, 6,58 % máximos, 6,48 % mínimos,
86,94 % continuidad. La cota teórica es 16,7 %.

**Por qué importa:** no es un problema de muestreo que se arregle bajando más
datos. Sale de una propiedad aritmética de dos líneas. Eso significa que **cualquier
equipo que haga este caso va a tener el mismo desbalance**, y quien reporte
exactitud está reportando un número vacío.

## Hallazgo 4: la volatilidad de LTC varía 8,8 veces

**El dato:** volatilidad móvil máxima **0,1220**, mínima **0,0138**, cociente
**8,8**.

**Por qué importa:** es evidencia directa de heterocedasticidad sobre datos reales.
Y tiene con qué compararse, porque lo medimos antes sobre series construidas: una
sin regímenes da **1,28** (o sea, prácticamente constante) y una con regímenes
metidos a propósito da **6,41**. El 8,8 de LTC está del lado de las series con
regímenes, no de las estables.

> **La cadena completa, que es lo que hay que saber contar:** construimos una serie
> sin regímenes y el cociente salió 1,28 → construimos una con regímenes y salió
> 6,41 → el método distingue → recién entonces medimos LTC y salió 8,8 → LTC se
> comporta como una serie con cambios de régimen.

---
---

# PARTE III — LAS PREGUNTAS DIFÍCILES

*Las que nadie prepara. Si una de estas cae y la contestás bien, se nota.*

## «El documento usa `w=5` y velas diarias. ¿Por qué esos valores?»

**Esta es la respuesta que cambia respecto de la versión extensa.** En la concisa,
la tabla que cruza granularidad y ventana **no está en el documento**: se movió a la
Semana 2, que es donde el enunciado ubica la extracción de datos. Los números
siguen medidos y siguen en `docs/evidencias/`, pero el profesor no los tiene
delante, así que hay que saberlos decir.

**Contestá con honestidad, porque la honestidad acá es la respuesta fuerte:**

> «Son valores provisionales, y está declarado así en el documento. El estudio para
> fijarlos ya está hecho y apunta a `w=7` sobre velas de 4 horas: fijamos antes de
> medir un piso de **300 ejemplos** de la clase minoritaria, y con velas diarias
> **ninguna** combinación lo alcanza —la mejor deja **149**—, mientras que con 4
> horas `w=7` deja **420**.
>
> Ese estudio no está en este documento a propósito. Ningún argumento del marco
> teórico depende de esos valores: la estacionariedad, la autocorrelación, la
> correlación y la volatilidad se calculan sobre precios y retornos, no sobre
> etiquetas. Y el enunciado ubica la extracción de datos en la Semana 2, que es
> donde corresponde documentarlo. Si quiere verlo ahora, está medido y se lo
> puedo abrir.»

**Tres números que en esta versión hay que llevar de memoria**, porque ya no están
impresos en el documento: el piso de **300**, el mejor caso diario de **149** y los
**420** que deja `w=7` sobre 4 horas.

## «¿Con cuánta anticipación va a avisar el modelo?»

**Esta es la pregunta trampa del caso, y tenemos la respuesta:**

> «La anticipación real no es `h`, es **`h + w`**. Para saber si la vela `t+h` fue
> un máximo hay que observar las `w` velas posteriores, así que su etiqueta no
> existe hasta `t+h+w`. Con `w=7` y `h=1` sobre velas de 4 horas son 8 velas, es
> decir **32 horas**. Reportar solo `h` sería engañoso.»

## «¿Cómo evitan la fuga de información?»

**Fuga de información** (*data leakage*) es cuando el modelo recibe sin querer
información del futuro. Produce resultados excelentes y falsos.

> «Es el riesgo más serio del proyecto, precisamente porque **no se manifiesta como
> un error**: el modelo da métricas excelentes y es inservible. Lo tratamos de dos
> formas: con una prueba automática que perturba el futuro y verifica que las
> características del pasado no cambian, y con un **embargo** de `w+h` velas en cada
> frontera de la partición temporal, para que ningún bloque comparta información con
> el siguiente.»

## «¿Por qué solo seis criptomonedas y desde 2020?»

> «Las seis las fija el enunciado. La fecha la fija Solana, que es la de listado
> más reciente: cotiza desde el 11 de agosto de 2020. Un panel multivariante exige
> que las seis series existan simultáneamente en cada instante, así que los
> períodos anteriores se descartan por incompletos. Sacrificamos alrededor de un
> tercio del historial disponible de Litecoin a cambio de poder plantear el problema
> como multivariante, y lo declaramos como limitación en el documento.»

## «Su información mutua es bajísima. ¿No significa que esto no se puede predecir?»

**Ojo con esta. Es la pregunta más incómoda y conviene adelantarse.**

> «Tiene razón en que el nivel absoluto es bajo, y lo decimos en el estudio. Lo que
> interpretamos no es la magnitud sino **la forma de la curva**: de `h=1` a `h=3` la
> información cae unas cuatro veces y a partir de ahí se aplana, y ese patrón se
> repite en las cuatro configuraciones que medimos. Eso es lo que nos hizo elegir
> `h=1`. Pero el nivel bajo es en sí mismo un aviso: el problema es difícil con las
> características actuales, y es parte de lo que hay que mejorar en las semanas
> siguientes.»

## «¿Por qué no hay una figura de estacionalidad si dicen que la midieron?»

> «Sí la hay, es la descomposición de la Figura 2. Lo que medimos es que la
> estacionalidad semanal representa apenas el **0,426 %** de la variación total. La
> explicación es que el mercado cripto opera de forma continua, sin sesión de
> apertura ni de cierre y sin distinción entre día hábil y fin de semana, a
> diferencia del mercado tradicional donde sí está documentado un efecto de fin de
> semana. La consecuencia práctica es que no tiene sentido darle al modelo una
> variable con el día de la semana.»

## «¿Verificaron sus referencias?»

**Acá tenemos algo que casi nadie hace:**

> «Sí, contra el registro de Crossref, con un script. Encontramos una trampa: el
> artículo de Corbet et al. de 2019 sobre criptoactivos como activo financiero está
> **retractado**, así que no lo citamos. Y hay un detalle adicional: su preprint en
> SSRN no está marcado como retractado, de modo que citarlo desde ahí seguiría
> siendo un error.»

## «¿Qué NO pueden afirmar con este trabajo?»

*Si preguntan esto, quieren ver honestidad intelectual. Dala.*

> «Tres cosas. Primero, los precios vienen de un solo mercado y no de un promedio
> de la industria, así que los giros que identificamos lo son respecto de la
> formación de precios de esa plaza. Segundo, la ventana temporal está acotada por
> Solana. Y tercero, la definición operativa del punto de inflexión depende de una
> ventana que fijamos nosotros: la escala del fenómeno es una elección
> metodológica, no una propiedad del mercado.»

---

## Si no sabés algo

**Nunca inventes un número.** La secuencia correcta es:

1. **Decí lo que sí sabés** del tema.
2. **Admitilo sin rodeos:** «ese dato no lo tengo de memoria».
3. **Ofrecé dónde está:** «está en el documento / en `docs/evidencias/`, se lo abro».
4. **Si es una pregunta conceptual que no sabés:** «no lo trabajé yo, lo trabajó
   [nombre], ¿le parece que le pregunte?» — y pasala. Es un trabajo de equipo.

**Lo que resta puntos no es no saber. Es inventar y que después no cuadre con el
documento.**

---

## Frases que suenan bien y son verdad

*Úsalas. Están todas respaldadas por una medición nuestra.*

- «No lo asumimos, lo medimos.»
- «El criterio se fijó **antes** de mirar el resultado.»
- «Primero lo verificamos sobre una serie donde la respuesta la pusimos nosotros.»
- «Ese resultado parece negativo y es justamente la justificación del enfoque.»
- «Eso no lo hemos medido, así que no lo afirmo.»
- «Es reproducible: se regenera con un comando y el número queda en el archivo de
  evidencias.»
