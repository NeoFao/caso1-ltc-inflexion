# Marco teórico: criptoactivos y sus características

**Autor:** Alejandro Zamora · **Issue:** [S1-M2-05](https://github.com/NeoFao/caso1-ltc-inflexion/issues/13)

> **Nota para el ensamblaje (Fabrizio).** La numeración de figuras es local a esta sección
> (Figura 1 a Figura 5). Al unir los tres archivos hay que renumerarlas de corrido y ajustar las
> referencias del texto. Las referencias bibliográficas están al final en APA 7; **falta
> verificar volumen, páginas y DOI de cada una contra la fuente antes de la entrega definitiva**.
>
> El noveno punto del enunciado — métricas de evaluación — va en [`m2-metricas.md`](m2-metricas.md).

---

## 1. Definición de criptoactivo

Un criptoactivo es una representación digital de valor que se registra, se transfiere y se almacena
mediante criptografía sobre un registro distribuido, y cuya validez no depende de que una entidad
central certifique cada operación. El Grupo de Acción Financiera Internacional lo define de forma
funcional —por lo que el activo hace, no por quién lo emite—, como una representación digital de
valor negociable electrónicamente y utilizable para pago o inversión (Financial Action Task Force
[FATF], 2021).

Lo que lo distingue de un activo financiero tradicional no es que sea digital, porque un depósito
bancario también lo es, sino **quién garantiza el registro**. En un activo tradicional el libro
contable de un intermediario es la fuente de verdad y la propiedad es una anotación en ese libro.
En un criptoactivo el libro está replicado por una red que acuerda su contenido mediante un
protocolo de consenso, de modo que la propiedad se prueba con una clave criptográfica y no con la
palabra de un custodio (Nakamoto, 2008; Narayanan et al., 2016).

De ahí se deriva la propiedad que más importa aquí: **no existe un emisor con obligación de pago**.
Un bono tiene un flujo contractual y una acción un derecho residual sobre las utilidades; un
criptoactivo no tiene ninguno de los dos, y carece por tanto de anclaje de valoración fundamental.
Böhme et al. (2015) señalan que su precio se determina enteramente por el equilibrio entre
compradores y vendedores, sin un valor de referencia externo que ancle las expectativas.

Esa ausencia de ancla es la razón técnica por la que el proyecto se plantea como **reconocimiento
de patrones sobre la serie de precios** y no como valoración: no hay un múltiplo al que el precio
deba revertir, hay una dinámica que caracterizar. Y es también la razón del enfoque multivariante:
si no hay fundamentales que expliquen el precio de LTC, buena parte de la información disponible
está en cómo se comportan los demás criptoactivos.

---

## 2. Características principales

**Descentralización del registro.** Ningún participante puede modificar unilateralmente el
historial. La consecuencia práctica es que no existe un precio oficial: cada exchange forma el
suyo, y elegir la fuente es una decisión metodológica que hay que declarar (sección 4).

**Operación continua.** El mercado funciona las veinticuatro horas los siete días, sin apertura ni
cierre. Se ve directamente en nuestros datos: la descomposición de la serie diaria de LTC atribuye
a la componente estacional apenas el **0,426 %** de la variación total. En un mercado con horario
aparecería un efecto de fin de semana y un patrón intrasemanal apreciable.

No es un dato descriptivo: **justifica una decisión de diseño**. Sin estacionalidad relevante, no
tiene sentido gastar características en codificar el día de la semana, y ese presupuesto queda
disponible para variables que sí informan.

**Divisibilidad.** Un criptoactivo se fracciona hasta ocho decimales o más, así que no hay tamaño
mínimo de operación comparable al lote de una acción y la serie no presenta discretización
artificial por tamaño de contrato.

**Transparencia del registro y opacidad del participante.** Las transacciones son públicas pero las
direcciones no están asociadas a identidades. Existe por tanto información en cadena (*on-chain*)
potencialmente utilizable. No la usamos: el enunciado especifica los precios rezagados de las seis
criptomonedas como entrada, y ampliar las fuentes sin una necesidad medida sería complejidad sin
justificación.

**Ausencia de cierre diario.** La vela diaria es un corte de reloj convencional —00:00 UTC—, no un
evento de mercado. Un cierre bursátil concentra órdenes y produce un precio con significado
institucional; un corte a medianoche en cripto es una convención del exchange. Eso refuerza la
conveniencia de trabajar con velas de 4 horas: si el corte es arbitrario de todos modos, la
granularidad se elige por criterio estadístico y no por respeto a una convención vacía.

**Volatilidad elevada y variable en el tiempo.** Sobre los datos del proyecto, la desviación
estándar móvil de los retornos de LTC en ventanas de 30 días recorre de **0,0138 a 0,122**: el
período más agitado fue **8,8 veces** más volátil que el más tranquilo. La literatura lo documenta
de forma sistemática: Katsiampa (2017) compara modelos GARCH sobre Bitcoin, y Caporale y Zekokh
(2019) muestran, con modelos GARCH de cambio markoviano, que la volatilidad de los criptoactivos no
solo es alta sino que **conmuta entre estados**. La implicación metodológica es directa: como la
varianza no es constante, cualquier característica construida sobre magnitudes absolutas de precio
será inestable entre períodos, y por eso el pipeline trabaja sobre retornos y sobre estadísticos
normalizados por ventana.

---

## 3. Principales tipos

La clasificación por función económica es la útil aquí, porque explica por qué las seis
criptomonedas del proyecto no son intercambiables:

**Monedas de pago.** Diseñadas como medio de intercambio, con funcionalidad programable limitada.
**LTC** pertenece a esta categoría: nació en 2011 como variante de Bitcoin con bloques más rápidos
y una prueba de trabajo distinta, orientada a transacciones de menor valor.

**Reserva de valor y activo de referencia.** **BTC** cumple hoy sobre todo esta función. Baur et
al. (2018) muestran que su uso predominante es especulativo y de tenencia antes que transaccional,
lo que lo aproxima más a un activo de inversión que a un medio de pago.

**Plataformas de contratos inteligentes (capa 1).** Redes cuyo valor deriva de la actividad que
alojan. **ETH** es la de mayor adopción; **SOL** compite ofreciendo mayor rendimiento a cambio de
supuestos de descentralización distintos; **ADA** sigue una ruta más conservadora y por etapas.

**Orientados a pagos transfronterizos.** **XRP** apunta a la liquidación entre instituciones
financieras, y su valor está más expuesto que el resto a decisiones regulatorias sobre su
naturaleza jurídica.

**Stablecoins.** Mantienen paridad con una moneda fiduciaria. Quedan fuera del estudio
precisamente por eso: su precio es aproximadamente constante por diseño, no tiene puntos de
inflexión que pronosticar.

La composición de la canasta importa. Las seis series no son seis observaciones independientes del
mismo mercado: son cuatro funciones económicas distintas, y esa heterogeneidad es lo que permite
que la correlación cruzada de la sección 6 aporte información en lugar de redundancia.

---

## 4. Mercado cripto

El mercado se organiza en torno a **exchanges centralizados**, con libros de órdenes de
emparejamiento continuo, y a mercados descentralizados basados en contratos inteligentes. La
formación de precios sucede en cada plaza por separado y el arbitraje mantiene las cotizaciones
alineadas sin hacerlas idénticas. No existe, a diferencia de los mercados regulados, un mecanismo
de consolidación que produzca un precio único de referencia.

**Decisión de fuente y su consecuencia.** Los precios provienen de la API pública de Binance. Hay
que declararlo porque condiciona lo que los resultados significan: son los precios de **un**
exchange y no un promedio ponderado del mercado, de modo que incorporan la microestructura de esa
plaza. Un punto de inflexión detectado sobre esta serie es un punto de inflexión en Binance. Dado
que concentra una parte sustancial del volumen de las seis parejas contra USDT, es una
aproximación razonable al precio de mercado, pero es una aproximación y así se reporta.

**Ventana histórica común.** El panel arranca el **11 de agosto de 2020** porque esa ventana la
determina el activo de listado más reciente, Solana. Las coberturas individuales son mucho más
amplias —LTC desde el 13 de diciembre de 2017 y BTC desde el 17 de agosto de 2017—, pero un panel
multivariante exige que las seis series existan simultáneamente en cada instante.

El costo es cuantificable. Con velas diarias el panel queda en **2 185 observaciones** frente a las
3 157 de la serie individual de LTC: se sacrifica cerca de un tercio del historial para poder
plantear el problema como multivariante. Con velas de 4 horas el mismo período produce **13 114
observaciones**, y por eso esa es la granularidad de trabajo. El requisito de simultaneidad se paga
en historia, y la granularidad más fina devuelve el volumen de ejemplos.

La cobertura del panel de 4 horas es prácticamente completa: sobre los 13 114 instantes esperados
para SOL no hay ningún hueco, y los de los demás activos en su historia completa van de 9 a 16
velas, menos del 0,1 %. La calidad del dato está medida en
[`docs/evidencias/spike-datos-4h.json`](../../evidencias/spike-datos-4h.json).

---

## 5. Factores que afectan el precio

**Oferta y demanda con oferta programada.** LTC tiene un tope de 84 millones de unidades y una
reducción de la recompensa por bloque —*halving*— aproximadamente cada cuatro años. La oferta
futura es conocida de antemano y no responde al precio, así que todo el ajuste ocurre por el lado
de la demanda. El efecto de los halvings es objeto de debate: al ser un evento anunciado, la
hipótesis de mercados eficientes predice que ya está incorporado, aunque la evidencia sobre
eficiencia en cripto es mixta (Urquhart, 2016).

**Regulación.** Los anuncios regulatorios producen movimientos abruptos y sincronizados en todo el
sector. Auer y Claessens (2018) documentan una reacción marcada de los precios, diferenciada según
el tipo de anuncio. Para nuestro problema importa por una razón concreta: esos saltos son
**exógenos a la serie**, ninguna característica construida sobre el histórico de precios puede
anticiparlos, y hay por tanto una fracción irreducible de los puntos de inflexión que el modelo no
puede predecir por construcción.

**Sentimiento y atención.** La ausencia de anclaje fundamental deja más espacio a la expectativa, y
hay evidencia cuantitativa. Liu y Tsyvinski (2021) muestran que los rendimientos de los
criptoactivos no están expuestos a los factores de riesgo de acciones, divisas ni materias primas,
ni a las variables macroeconómicas habituales, y que en cambio sí resultan predichos de forma
robusta por el momento del precio y por medidas de atención del inversor. Es la confirmación
empírica del argumento de la sección 1: si los fundamentales no explican el precio, lo que queda
por explotar es la dinámica de la propia serie.

**Flujos institucionales y liquidez.** La entrada de vehículos de inversión regulados modificó la
base de participantes y con ella el régimen de volatilidad, lo que es coherente con el cociente de
8,8 medido en nuestra serie: no describe un mercado de volatilidad alta y estable, sino uno que
**cambia de régimen**.

**Contagio entre activos.** Es el factor que justifica el diseño multivariante y por eso tiene
sección propia. Ji et al. (2019) y Yi et al. (2018) documentan una red densa de transmisión de
retornos y volatilidad entre criptoactivos, con Bitcoin en posición dominante como emisor de
choques. La selección de las cinco variables de apoyo que hace el enunciado es consistente con esa
literatura: BTC como transmisor sistémico, ETH como segundo motor, SOL como indicador de actividad
especulativa en capas 1 de alto rendimiento, XRP por su sensibilidad regulatoria y ADA como reflejo
de la rotación de capital entre plataformas.

---

## 6. Correlación y dependencia entre activos

![Figura 1](../../evidencias/mt-07-correlacion.png)

**Figura 1.** Matriz de correlación entre las seis criptomonedas, calculada sobre retornos diarios
del panel 11/08/2020 – 04/08/2026 (n = 2 185). Fuente: elaboración propia sobre datos de Binance.

**Medido sobre retornos:** todas las parejas caen entre **0,475 y 0,806**, con una media fuera de
la diagonal de **0,625**. LTC se correlaciona más con **ETH (0,740)** y con **BTC (0,715)**, y
menos con **SOL (0,524)**.

M1 desarrolla la mecánica estadística de la correlación cruzada. Lo que sigue es la interpretación
económica.

**Por qué ETH y BTC encabezan la lista.** LTC nació como variante técnica de Bitcoin y comparte con
él la función de moneda de pago; se negocia en las mismas plazas, contra los mismos pares y ante
los mismos flujos de noticias. BTC es además el activo de referencia del sector: Ji et al. (2019)
lo identifican como principal emisor de choques de retorno, de modo que un movimiento suyo se
propaga a LTC casi por definición. ETH queda ligeramente por encima porque comparte con LTC el
estatus de activo de gran capitalización y alta liquidez, destino habitual de los mismos flujos.

**Por qué SOL es la menos correlacionada.** Es el activo más joven de la canasta y el de perfil más
especulativo, y su precio responde en mayor medida a factores propios de su ecosistema que no
afectan a LTC. Es por tanto el activo cuya información resulta **menos redundante**, y por eso
mismo el candidato más interesante a aportar señal incremental. La medición de importancia de
características de la Semana 3 permitirá contrastar esta hipótesis con un número.

**Qué significa un mercado con correlaciones de 0,5 a 0,8.** Tres consecuencias:

1. **La diversificación dentro del sector es limitada.** Una cartera de las seis criptomonedas se
   comporta aproximadamente como una posición sobre un factor común. Yi et al. (2018) llegan a una
   conclusión equivalente sobre 52 criptomonedas: la red de transmisión de volatilidad es densa, de
   modo que el riesgo no se reparte al añadir más activos del mismo sector.
2. **El contagio es rápido.** Con correlaciones de esa magnitud sobre retornos diarios, un choque en
   un activo se refleja en los demás dentro de la misma vela.
3. **Hay información compartida, pero no toda lo es.** Una correlación media de 0,625 implica que
   alrededor del 39 % de la varianza es común y el 61 % restante idiosincrásico. Esa es la
   condición que hace útil el enfoque multivariante: con correlación 0,99 las series de apoyo serían
   redundantes y con 0,1 no aportarían nada. El valor medido está en el rango donde sí puede
   aportar.

**Advertencia metodológica.** Sobre precios en **nivel** el rango se dispara a **0,126 – 0,888** y
el orden económico se desmorona: LTC–BTC, que sobre retornos es la segunda pareja más fuerte, cae a
**0,126**, mientras LTC–ADA sube a **0,796**. La razón es que las seis series son no estacionarias
según midió M1, y la correlación entre series con tendencia mide la coincidencia de tendencias y no
la codependencia de sus movimientos. Es la regresión espuria de Granger y Newbold (1974), y por eso
toda la correlación cruzada del proyecto se calcula sobre retornos.

**Control sobre serie construida.** Sobre paneles sintéticos con correlación objetivo conocida, la
medición recupera **0,0945** cuando pedimos correlación baja y **0,903** cuando la pedimos alta.
Verifica que el procedimiento hace lo que decimos, antes de aplicarlo a datos donde nadie conoce la
respuesta.

---

## 7. Definición de punto de inflexión

![Figura 2](../../evidencias/mt-08a-giros-construidos.png)

**Figura 2.** Serie construida por nosotros mediante `serie_zigzag()`. Los giros marcados son
exactamente los vértices que colocamos al generarla; **no son datos de mercado**. Fuente:
elaboración propia.

Intuitivamente, un máximo es el punto donde el precio deja de subir y empieza a bajar. El problema
es que un precio sube y baja continuamente, a todas las escalas, de modo que la intuición no basta
para construir una etiqueta.

**Un máximo no existe en términos absolutos: existe respecto de una ventana.** Sobre una misma
serie, mirando una observación a cada lado aparecen varios máximos; mirando cinco, la mayoría deja
de serlo porque dentro de esa vecindad hay un valor más alto. El dato no cambió, cambió la escala
de observación, y las dos lecturas son correctas: es un giro local pequeño y no es un giro
estructural. De ahí se sigue lo esencial de esta sección: no buscamos la definición verdadera de
máximo, porque no existe. Estamos **eligiendo a qué escala trabaja el modelo**, y esa elección hay
que justificarla con datos.

**Definición operativa adoptada.** El proyecto fija la etiqueta en un único lugar
([`contracts/labeling.py`](../../../contracts/labeling.py)) y los cuatro módulos la consumen:

> Una vela `t` es **Máximo** si su precio de cierre es estrictamente mayor que el de todas las
> velas entre `t-w` y `t+w`. Es **Mínimo** si es estrictamente menor que todas ellas. En cualquier
> otro caso es **Zona de Continuidad**.

Dos precisiones que no son cosméticas. La exigencia de desigualdad **estricta** contra las 2w
vecinas es lo que garantiza la propiedad aritmética del párrafo siguiente; admitiendo empates se
pierde. Y las primeras y últimas `w` velas quedan **sin etiqueta**, no etiquetadas como
Continuidad: no tienen ventana completa, su clase es desconocida, y contarlas como Continuidad
inflaría artificialmente la clase mayoritaria.

**Propiedad aritmética: la cota superior del desbalance.** Dos máximos no pueden estar a menos de
`w+1` velas de distancia, porque cada uno caería dentro de la ventana del otro y cada uno tendría
que ser estrictamente mayor que el otro. Por lo tanto, **como mucho 1 de cada `w+1` velas puede ser
Máximo**, y lo mismo vale para Mínimo.

Esto es aritmética, no una medición, y su consecuencia condiciona todo el proyecto: el desbalance
de clases **está garantizado por la definición de la etiqueta**, no es un accidente de los datos.
Con `w = 5` los máximos no pueden superar el 16,7 % de las observaciones; con `w = 7`, el 12,5 %.
La medición sobre el panel confirma que la proporción real queda muy por debajo de esa cota, como
corresponde a un límite superior. La elección concreta de granularidad y de ventana pertenece a la
etapa de extracción de datos, que el enunciado sitúa en la entrega siguiente.

**El horizonte `h`.** Es independiente de `w`: mientras `w` define *qué* es un giro, `h` define *con
cuánta anticipación* se anuncia. El modelo observa la información disponible hasta `t` y responde
qué etiqueta corresponderá a la vela `t+h`.

**La latencia real del sistema.** Para saber si la vela `t` fue un máximo hay que observar las `w`
velas posteriores, de modo que su etiqueta **no se conoce hasta `t+w`**. Si predecimos desde `t` la
etiqueta de `t+h`, esa etiqueta no existirá hasta `t+h+w`: la anticipación efectiva es de **`h+w`
velas, no de `h`**, y reportar solo `h` sería engañoso. El proyecto expone esa cantidad como
función explícita para que el número entre al informe calculado y no estimado.

De esta propiedad se desprende el riesgo técnico más serio del proyecto. Como la etiqueta se
construye mirando el futuro, es fácil contaminar las características con información posterior al
instante de predicción sin darse cuenta, y es particularmente peligroso porque **no se manifiesta
como un error**: produce métricas excelentes y un sistema inservible. La literatura de aprendizaje
automático aplicado a finanzas insiste en el punto (López de Prado, 2018), y por eso el proyecto lo
trata con una prueba automática obligatoria y con un embargo de `w+h` velas en cada frontera de la
partición temporal (Bergmeir & Benítez, 2012).

---

## 8. Cómo encontrar puntos de inflexión

![Figura 3](../../evidencias/mt-08b-giros-ltc.png)

**Figura 3.** Últimas 250 velas diarias de LTC con los giros detectados por el criterio de ventana
(`w = 5`). Fuente: elaboración propia sobre datos de Binance.

Existen dos enfoques, y contrastarlos aclara qué estamos haciendo y qué dejamos fuera.

### 8.1 Estructura de mercado (HH, HL, LH, LL)

Es el enfoque clásico del análisis técnico y el de la figura del enunciado. Se identifican máximos
y mínimos sucesivos y se clasifican como *higher high* (HH), *higher low* (HL), *lower high* (LH) y
*lower low* (LL). Una secuencia de HH y HL describe tendencia alcista; una de LH y LL, bajista. El
giro se señala cuando la secuencia se rompe: en tendencia alcista, el primer máximo que no supera
al anterior seguido de un mínimo que perfora al anterior (Murphy, 1999).

Su virtud es incorporar el contexto de la tendencia: no pregunta solo si un punto es un extremo
local, sino si rompe una estructura. Su limitación es decisiva para un trabajo cuantitativo:
**depende del criterio del observador**. Qué oscilación cuenta como máximo relevante y cuál es
ruido no está definido por el método, y dos analistas pueden etiquetar la misma serie de forma
distinta. Sin regla explícita no hay verdad de referencia reproducible, y sin ella no hay
aprendizaje supervisado posible.

### 8.2 Criterio automático de ventana

Es el que adopta el proyecto, definido en la sección 7. Tiene lo que le falta al anterior: es
**reproducible**, porque la misma serie produce siempre las mismas etiquetas; es **auditable**,
porque cabe en una función con pruebas; y es **explícito** en su escala, porque `w` está a la
vista.

Su costo es que exige elegir `w` y que ignora el contexto de tendencia: trata por igual un máximo
en medio de una tendencia alcista y uno que marca su final. Es un intercambio consciente, y elegir
`w` con criterio medido es lo que impide que se convierta en arbitrariedad.

### 8.3 Validación del detector sobre una serie donde conocemos la respuesta

El argumento que sostiene todo lo demás: **antes de creerle al detector sobre datos donde nadie
sabe la verdad, hay que verificar que encuentra lo que debe sobre una serie donde la verdad la
pusimos nosotros.**

Sobre la serie construida de la Figura 2 —lineal a tramos, con vértices colocados por
construcción— el detector encontró **18 de 18** vértices, exactamente y sin falsos positivos. Esto
no dice nada sobre el mercado: dice que la implementación del etiquetador es correcta, condición
previa a cualquier otra afirmación del proyecto.

### 8.4 A qué nivel de ruido se rompe el etiquetado

La comprobación anterior deja abierta la pregunta incómoda: *¿cómo saben que sus etiquetas no son
ruido?* Una serie lineal a tramos sin ruido es un caso fácil; la pregunta relevante es cuánto ruido
tolera el detector antes de inventar giros. Es medible, y lo medimos.

**Diseño.** Se generan series de 800 velas con vértices colocados por construcción y se les suma
ruido gaussiano de desviación creciente. La verdad de referencia se toma de la serie **limpia** y
no de la salida del etiquetador —de lo contrario la prueba compararía la función consigo misma y
pasaría siempre—, y la detección se evalúa sobre la **ruidosa**. Cada nivel promedia **diez
semillas**, porque una sola serie no distingue el efecto del ruido del azar de esa serie concreta:
498 giros verdaderos por nivel.

El ruido se expresa **relativo al cambio típico de precio entre velas consecutivas**, no en
unidades absolutas: un σ de 0,5 es enorme en una serie que se mueve 0,2 por vela e irrelevante en
una que se mueve 20, y el cociente es lo que hace la medición comparable entre series. Y se miden
dos cosas a propósito, porque perder un giro no es lo mismo que detectarlo corrido una vela: la
detección **exacta** y la detección **con tolerancia de una vela**.

| σ | Ruido relativo | Giros recuperados (tolerancia 1 vela) | Giros recuperados (vela exacta) | Giros falsos por giro verdadero |
|---|---|---|---|---|
| 0,00 | 0,00 | **1,000** | **1,000** | 0,000 |
| 0,10 | 0,07 | 1,000 | 1,000 | 0,000 |
| 0,25 | 0,18 | 1,000 | 0,998 | 0,000 |
| 0,50 | 0,36 | 1,000 | 0,944 | 0,000 |
| 0,70 | 0,50 | 0,992 | 0,857 | **0,008** |
| 1,00 | 0,72 | 0,960 | 0,729 | 0,040 |
| 2,00 | 1,44 | 0,852 | 0,501 | 0,150 |
| 4,00 | 2,87 | 0,669 | 0,325 | 0,467 |

**Tabla 1.** Sensibilidad del etiquetador al ruido. Serie construida de 800 velas, `w = 7`,
promedio de 10 semillas por nivel (498 giros verdaderos en cada uno). La fila σ = 0,70 proviene
del barrido fino. Fuente:
[`m2-ruido-etiquetado.json`](../../evidencias/m2-ruido-etiquetado.json), regenerable con
`uv run python -m src.sintetico.sensibilidad`.

![Figura 4](../../evidencias/m2-ruido-curvas.png)

**Figura 4.** Izquierda: fracción de giros verdaderos recuperados, con y sin tolerancia de una
vela. Derecha: giros falsos por giro verdadero. **Serie construida por nosotros; no es Litecoin.**
Fuente: elaboración propia.

![Figura 5](../../evidencias/m2-ruido-series.png)

**Figura 5.** Un mismo tramo de 220 velas a tres niveles de ruido: el caso limpio, el punto de
quiebre medido y el ruido máximo probado. Punto relleno: giro verdadero, colocado por
construcción. Círculo hueco: giro detectado. Los conteos del título corresponden a este tramo y
esta semilla; los valores citables son los promedios de la Tabla 1. Fuente: elaboración propia.

**Tres resultados, en orden de importancia:**

1. **El umbral de aparición de giros falsos está en un ruido relativo de 0,50.** Hasta un σ
   equivalente al 36 % del movimiento típico por vela, el detector recupera los 498 giros sin
   inventar ninguno. El primer falso positivo aparece cuando σ alcanza aproximadamente la mitad del
   movimiento por vela.
2. **La detección exacta se degrada mucho antes que la detección del giro.** Con ruido relativo
   0,36 el detector encuentra el 100 % de los giros pero solo el 94,4 % cae en la vela exacta; con
   0,72, encuentra el 96,0 % y acierta la vela en el 72,9 %. **El fallo dominante en ruido moderado
   no es perder giros: es correrlos de lugar.** Evaluar el modelo exigiendo la vela exacta puede
   penalizar como error lo que es un desplazamiento de una vela.
3. **La degradación es gradual, no catastrófica.** Incluso con σ casi tres veces el movimiento
   típico por vela el detector recupera el 66,9 % de los giros. No hay un punto de quiebre, hay una
   pendiente. Como contraste, la confusión de tipo —marcar un máximo donde había un mínimo, el peor
   error posible— aparece **una sola vez en los 3 486 giros evaluados**, y solo en el nivel de ruido
   más alto.

**Cómo hay que leer esto.** La serie es lineal a tramos con ruido gaussiano: **no es Litecoin**. No
tiene heterocedasticidad, ni colas pesadas, ni saltos, y su relación señal-ruido la fijamos
nosotros. Estos números **caracterizan al etiquetador**, no al mercado, y no permiten afirmar que
un porcentaje determinado de las etiquetas de LTC sea correcto. Lo que sí permiten afirmar es que
el etiquetador tiene un régimen medido de funcionamiento correcto, expresado en una magnitud
comparable entre series, y que su modo de fallo dominante está identificado: desplaza antes de
perder, y prácticamente nunca invierte el tipo.

---

## Referencias

Auer, R., & Claessens, S. (2018). Regulating cryptocurrencies: Assessing market reactions. *BIS
Quarterly Review*, September, 51–65.

Baur, D. G., Hong, K., & Lee, A. D. (2018). Bitcoin: Medium of exchange or speculative assets?
*Journal of International Financial Markets, Institutions and Money, 54*, 177–189.
https://doi.org/10.1016/j.intfin.2017.12.004

Bergmeir, C., & Benítez, J. M. (2012). On the use of cross-validation for time series predictor
evaluation. *Information Sciences, 191*, 192–213. https://doi.org/10.1016/j.ins.2011.12.028

Böhme, R., Christin, N., Edelman, B., & Moore, T. (2015). Bitcoin: Economics, technology, and
governance. *Journal of Economic Perspectives, 29*(2), 213–238. https://doi.org/10.1257/jep.29.2.213

Caporale, G. M., & Zekokh, T. (2019). Modelling volatility of cryptocurrencies using
Markov-Switching GARCH models. *Research in International Business and Finance, 48*, 143–155.
https://doi.org/10.1016/j.ribaf.2018.12.009

Financial Action Task Force. (2021). *Updated guidance for a risk-based approach to virtual assets
and virtual asset service providers*. FATF.

Granger, C. W. J., & Newbold, P. (1974). Spurious regressions in econometrics. *Journal of
Econometrics, 2*(2), 111–120. https://doi.org/10.1016/0304-4076(74)90034-7

Ji, Q., Bouri, E., Lau, C. K. M., & Roubaud, D. (2019). Dynamic connectedness and integration in
cryptocurrency markets. *International Review of Financial Analysis, 63*, 257–272.
https://doi.org/10.1016/j.irfa.2018.12.002

Katsiampa, P. (2017). Volatility estimation for Bitcoin: A comparison of GARCH models. *Economics
Letters, 158*, 3–6. https://doi.org/10.1016/j.econlet.2017.06.023

Liu, Y., & Tsyvinski, A. (2021). Risks and returns of cryptocurrency. *The Review of Financial
Studies, 34*(6), 2689–2727. https://doi.org/10.1093/rfs/hhaa113

López de Prado, M. (2018). *Advances in financial machine learning*. John Wiley & Sons.

Murphy, J. J. (1999). *Technical analysis of the financial markets: A comprehensive guide to
trading methods and applications*. New York Institute of Finance.

Nakamoto, S. (2008). *Bitcoin: A peer-to-peer electronic cash system*.

Narayanan, A., Bonneau, J., Felten, E., Miller, A., & Goldfeder, S. (2016). *Bitcoin and
cryptocurrency technologies: A comprehensive introduction*. Princeton University Press.

Urquhart, A. (2016). The inefficiency of Bitcoin. *Economics Letters, 148*, 80–82.
https://doi.org/10.1016/j.econlet.2016.09.019

Yi, S., Xu, Z., & Wang, G.-J. (2018). Volatility connectedness in the cryptocurrency market: Is
Bitcoin a dominant cryptocurrency? *International Review of Financial Analysis, 60*, 98–114.
https://doi.org/10.1016/j.irfa.2018.08.012
