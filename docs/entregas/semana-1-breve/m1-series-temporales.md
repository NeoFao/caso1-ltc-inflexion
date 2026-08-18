# Marco teórico: series de tiempo

**Autor:** Jose Pablo Monestel · **Issue:** [S1-M1-06](https://github.com/NeoFao/caso1-ltc-inflexion/issues/9)

> **Nota de verificación.** Todos los valores citados salen de `docs/evidencias/marco-teorico.json`,
> medidos el 12/08/2026 sobre 2 185 velas diarias de 2020-08-11 a 2026-08-04, y se comprobaron con
> `scripts/verificar_numeros.py`. Las referencias se comprobaron contra Crossref el 17 de agosto de
> 2026 —incluida la retractación de Corbet et al. (2019), que por eso no aparece citada aquí.

---

## 1. Definición de serie temporal

![Figura 1](../../evidencias/mt-01-serie-temporal.png)

**Figura 1.** Precio de cierre diario de Litecoin, 2 185 observaciones entre el 11 de agosto de 2020 y el 4 de agosto de 2026.

Una serie temporal es una secuencia de observaciones de una misma variable, indexadas por el
momento en que fueron registradas (Box et al., 2015). Lo que la separa de un conjunto de datos
transversal es que el orden constituye el dato: en una muestra de clientes las filas pueden
alterarse sin pérdida, porque cada observación es independiente por diseño; aquí la observación en
`t` está relacionada con la de `t-1`, y esa dependencia es lo que hay que modelar. Reordenarla no la
desordena, la destruye.

La Figura 1 muestra el objeto de este trabajo: **2 185 observaciones** equiespaciadas del precio de
cierre diario de Litecoin. Es una serie univariante y regular, y esa regularidad no es del mercado
sino una decisión de muestreo sobre un activo que cotiza de forma continua las veinticuatro horas.

---

## 2. Componentes de una serie temporal

![Figura 2](../../evidencias/mt-02-componentes.png)

**Figura 2.** Descomposición aditiva de la serie de LTC en tendencia, estacionalidad de período semanal y residuo.

**Medido:** el componente estacional representa el **0,426 %** de la desviación total de la serie.

Una serie temporal se descompone en cuatro componentes (Box et al., 2015). La **tendencia** es el
movimiento de largo plazo que no se revierte dentro del horizonte de la muestra. La
**estacionalidad** es un patrón de periodicidad fija que suele responder a convenciones de
calendario: en la bolsa tradicional está documentado un efecto de fin de semana, con rendimientos
distintos según el día en que cierra la operación (French, 1980). El **ciclo** es un movimiento de
duración variable, asociado a factores macroeconómicos. El **residuo** es lo que queda al retirar
los tres anteriores.

Que sobre LTC la estacionalidad semanal resulte marginal tiene explicación directa: el mercado de
criptoactivos opera de forma continua, sin apertura ni cierre y sin distinción entre día hábil y
fin de semana, de modo que no existe el mecanismo institucional que produce el efecto que documenta
French (1980). La consecuencia para el modelo es que codificar el día de la semana no aportaría
señal.

---

## 3. Estacionariedad

![Figura 3](../../evidencias/mt-03-estacionariedad.png)

**Figura 3.** p-valores del test de Dickey-Fuller aumentado sobre las seis criptomonedas, en precios en nivel y en retornos.

**Medido:**

| | Rechazan la raíz unitaria al 5 % |
|---|---|
| Precios en nivel | **0 de 6** |
| Retornos | **6 de 6** |

p-valores en nivel: LTC 0,179 · BTC 0,483 · **ETH 0,059** · SOL 0,274 · XRP 0,285 · ADA 0,159.
En retornos, los seis dan p < 0,000001.

**Control:** el test también se corrió sobre una serie construida por nosotros cuyos retornos son estacionarios por construcción, y los rechazó todos. El método detecta lo que dice detectar.

Una serie es estacionaria en sentido débil cuando sus primeros momentos no dependen del instante de
observación: media y varianza constantes, y autocovarianza que depende solo de la distancia
temporal entre dos observaciones (Box et al., 2015). Es una propiedad estadística y no una
descripción visual: una serie puede parecer estable en un gráfico sin serlo.

El **test de Dickey-Fuller aumentado (ADF)** es el instrumento estándar para probarlo (Dickey &
Fuller, 1979; Said & Dickey, 1984). Su hipótesis nula es que la serie tiene una raíz unitaria, es
decir, que **no** es estacionaria; un p-valor menor a 0,05 permite rechazarla. Se aplicó el mismo
procedimiento a las seis series, en nivel y en retornos, con selección automática de rezagos por
criterio de información de Akaike.

Conviene precisar qué permite afirmar el resultado. Que el test no rechace la nula sobre los precios
**no demuestra** que sean no estacionarios: demuestra que no hay evidencia suficiente en contra. Un
test de hipótesis nunca prueba la nula, solo puede fallar en rechazarla. El rechazo sobre retornos
sí constituye evidencia fuerte a favor de la estacionariedad.

**ETH** merece mención aparte: su p-valor en nivel queda apenas por encima del umbral. No cambia la
conclusión, pero recuerda que el resultado depende de la ventana muestral y que con otro período ese
caso podría cruzar el umbral en cualquiera de los dos sentidos.

---

## 4. No estacionariedad

El mismo resultado, leído en sentido inverso, indica que los precios son compatibles con un proceso
de tendencia estocástica —un paseo aleatorio con deriva en el caso más simple— y no con uno que
oscile alrededor de una media fija (Nelson & Plosser, 1982). Dos síntomas lo delatan sin el test: la
media no es estable en ninguna ventana razonable, porque LTC recorre de **40,92** a **387,80** dentro
de la propia muestra; y la varianza tampoco, porque un movimiento porcentual constante produce un
movimiento absoluto proporcional al nivel.

La consecuencia para el modelado no es cosmética. Una regresión, un ARIMA sin diferenciar o un
cálculo de correlación asumen que la relación entre variables es estable en el tiempo. Sobre una
serie no estacionaria esa estabilidad no existe por construcción: cualquier estadístico calculado
sobre precios en nivel queda contaminado por la tendencia común y termina describiendo la dirección
compartida de dos series más que su codependencia. La sección 8 mide esa distorsión.

La transformación a retornos —la variación porcentual entre una observación y la anterior,
`r_t = (p_t − p_{t-1}) / p_{t-1}`— resuelve el problema porque cambia la pregunta: de "cuánto vale el
precio", que acumula nivel desde el origen, a "cuánto cambió en esta vela", que no. Por eso, y no por
costumbre de la disciplina, **las características del modelo se construyen sobre retornos y no sobre
precios en nivel**.

---

## 5. Heterocedasticidad

![Figura 4](../../evidencias/mt-05-heterocedasticidad.png)

**Figura 4.** Serie construida con volatilidad constante (arriba) y con volatilidad por tramos (abajo). Ambas generadas por nosotros; no son datos de mercado.

**Medido en las series construidas:** cociente entre la volatilidad del tramo agitado y la del tranquilo — **1,28×** sin regímenes, **6,41×** con regímenes.

Un proceso es **homocedástico** cuando la dispersión de sus incrementos es constante en el tiempo, y
**heterocedástico** cuando cambia, concentrándose en episodios o regímenes (Engle, 1982). Engle
formalizó la idea con el modelo ARCH, mostrando que la varianza condicional puede depender del
historial reciente aunque la media no muestre patrón predecible: puede haber estructura en la
varianza sin haberla en el nivel.

La Figura 4 contrasta dos series construidas por nosotros con la respuesta conocida de antemano:
arriba volatilidad constante, abajo la misma serie con la volatilidad multiplicada por cinco en
tramos alternos. El cociente cercano a 1 en la primera corresponde a una volatilidad efectivamente
constante, con la desviación propia de estimar sobre muestra finita, y el de la segunda captura el
factor introducido. El procedimiento detecta la heterocedasticidad cuando existe y no la inventa
cuando no existe, que es la comprobación necesaria antes de aplicarlo a LTC.

Esto rompe un supuesto central de los modelos clásicos. Un ARIMA asume varianza constante en los
errores; cuando no se cumple, sus intervalos de confianza dejan de ser válidos y sus pronósticos
subestiman el riesgo en los períodos agitados. La literatura documenta este patrón de conmutación
entre regímenes, con modelos GARCH de cambio markoviano ajustando mejor que uno de régimen único
(Caporale & Zekokh, 2019).

---

## 6. Volatilidad

![Figura 5](../../evidencias/mt-04b-volatilidad-construida.png)

**Figura 5.** Dos series construidas por nosotros con la volatilidad fijada de antemano, en los mismos ejes. Arriba, la volatilidad más baja medida en LTC; abajo, la más alta. **Ninguna de las dos es Litecoin.** Fuente: elaboración propia.

**Medido sobre las series construidas:** pedimos una volatilidad de **0,01384** y medimos **0,01395**; pedimos **0,122** y medimos **0,12349**. El cociente pedido entre ambas era de **8,8** y el medido resultó **8,9**.

La volatilidad se estima con la desviación estándar de los retornos sobre una ventana móvil
(Katsiampa, 2017). A diferencia de un único número global, la ventana móvil deja ver cómo cambia la
dispersión a lo largo del tiempo, que es lo que hace falta para diagnosticar heterocedasticidad.

Antes de aplicarla a LTC se comprobó que el procedimiento recupera lo que se le pide. Se generaron
dos series de idéntica construcción y semilla variando un solo parámetro, la desviación estándar de
los retornos. Los dos niveles no son arbitrarios: son los extremos de la volatilidad móvil que se
mide enseguida sobre Litecoin, de manera que el rango construido cubre el que se observa en el
mercado. La discrepancia entre lo pedido y lo medido es atribuible al muestreo finito.

![Figura 6](../../evidencias/mt-04-volatilidad.png)

**Figura 6.** Precio de cierre de LTC y su volatilidad móvil de 30 velas.

**Medido:** la volatilidad del tramo más agitado es **8,8 veces** la del más tranquilo (máxima **0,1220**; mínima **0,0138**), con ventana móvil de 30 velas sobre retornos diarios.

Aplicado a la serie real, el cociente entre extremos es muy superior al de la serie construida sin
regímenes y del mismo orden que el de la construida con ellos: LTC no se comporta como una serie de
volatilidad estable sino como una que conmuta entre regímenes de intensidad muy distinta,
consistente con lo que reporta la literatura GARCH sobre criptoactivos (Katsiampa, 2017).

En la Figura 6 los picos de volatilidad coinciden con los tramos de movimiento más pronunciado en
cualquiera de las dos direcciones: la volatilidad mide la magnitud del cambio, no su signo. Es,
junto con el resultado de la sección 3, la segunda evidencia medida sobre datos reales de que los
métodos que asumen varianza constante no sirven para este problema.

---

## 7. Autocorrelación

![Figura 7](../../evidencias/mt-06-autocorrelacion.png)

**Figura 7.** Función de autocorrelación de LTC hasta el rezago 40, en nivel y en retornos, con banda de confianza al 95 %.

**Medido:**

| | Autocorrelación en el rezago 1 |
|---|---|
| Precio en nivel | **0,991** |
| Retornos | **−0,036** |

En los retornos solo **3 rezagos** salen de la banda de confianza: los rezagos **8, 14 y 31**.

La función de autocorrelación (ACF) mide la correlación lineal entre una serie y su propio pasado
para cada rezago `k` (Box & Pierce, 1970). Responde a si el pasado de la serie contiene por sí solo
información lineal sobre su futuro, que aquí equivale a preguntar si tiene sentido usar precios
rezagados como variable de entrada.

**En nivel** la autocorrelación decae muy lentamente al aumentar el rezago: es la firma de una serie
no estacionaria, donde cada observación es casi idéntica a la anterior porque comparten la mayor
parte de su nivel acumulado. Confirma con otra herramienta lo que ya mostró el test ADF.

**En retornos**, de los 40 rezagos evaluados solo tres salen de la banda de confianza al 95 %.

Ese es el hallazgo de mayor consecuencia para el diseño. Que los retornos de LTC carezcan de
autocorrelación lineal significativa implica que un modelo lineal alimentado solo con retornos
rezagados dispondría de muy poca estructura que explotar. No es un resultado negativo: **es la
justificación del enfoque**. Es consistente con la hipótesis de mercados eficientes en forma débil
(Fama, 1970) y es, medido sobre datos propios, el argumento a favor de recurrir a modelos no
lineales y multivariantes. Si tres rezagos de cuarenta bastaran para predecir, un modelo lineal
univariante alcanzaría y no harían falta ni aprendizaje profundo ni las cinco variables de apoyo.

---

## 8. Correlación cruzada

![Figura 8](../../evidencias/mt-07-correlacion.png)

**Figura 8.** Matrices de correlación. Izquierda y centro: series construidas con correlación baja y alta fijadas por nosotros. Derecha: retornos reales de las seis criptomonedas.

**Medido:**

| | Rango entre pares |
|---|---|
| Precios en nivel | **0,126 – 0,888** |
| Retornos | **0,475 – 0,806** |

Casos concretos:

| Par | En nivel | En retornos |
|---|---|---|
| LTC – BTC | 0,126 | 0,715 |
| LTC – ADA | 0,796 | 0,641 |

Mayor correlación con LTC: **ETH, 0,740**. Menor: **SOL, 0,524**.

**Control:** las construidas se pidieron con correlación 0,1 y 0,9; salieron medidas en **0,0945** y **0,9033**.

La correlación cruzada mide la asociación lineal entre dos series distintas, a diferencia de la
autocorrelación de la sección 7. Permite responder si el planteamiento multivariante tiene sustento:
si LTC no se moviera de forma relacionada con las otras cinco, incorporarlas no aportaría
información. La Figura 8 pone tres matrices 6×6 lado a lado —dos construidas por nosotros con
correlación fijada de antemano y una con los retornos reales—, de modo que el resultado real se lee
contra dos referencias donde la respuesta la pusimos nosotros.

La distorsión que introducen los precios en nivel no consiste en que la correlación resulte alta,
sino en que resulta **errática**. Sobre nivel, la pareja LTC–BTC —el activo que marca la tendencia de
todo el sector— cae al valor más bajo de la matriz mientras LTC–ADA sube: un ordenamiento
económicamente implausible. Sobre retornos el orden se corrige y el rango se estrecha a la mitad.

La explicación es que la correlación en nivel mide algo distinto de lo que se busca. Dos series con
tendencia comparten tendencia, y la correlación entre ellas captura esa coincidencia de dirección de
largo plazo más que la codependencia real de sus movimientos período a período. Es el fenómeno de la
**correlación espuria** descrito por Granger y Newbold (1974): como la sección 3 midió que los
precios no son estacionarios, cualquier correlación calculada sobre ellos hereda ese defecto.

Sobre retornos, el activo de apoyo más correlacionado con LTC es ETH y el menos, SOL. Ambos quedan
lejos de los extremos —ni cerca de 0, que dejaría a las variables de apoyo sin aportar, ni cerca de
1, que las volvería redundantes—, y esa es la condición que sostiene el planteamiento multivariante.

---

## Referencias

Box, G. E. P., & Pierce, D. A. (1970). Distribution of residual autocorrelations in
autoregressive-integrated moving average time series models. *Journal of the American Statistical
Association, 65*(332), 1509–1526. https://doi.org/10.1080/01621459.1970.10481180

Box, G. E. P., Jenkins, G. M., Reinsel, G. C., & Ljung, G. M. (2015). *Time series analysis:
Forecasting and control* (5th ed.). John Wiley & Sons.

Caporale, G. M., & Zekokh, T. (2019). Modelling volatility of cryptocurrencies using
Markov-Switching GARCH models. *Research in International Business and Finance, 48*, 143–155.
https://doi.org/10.1016/j.ribaf.2018.12.009

Dickey, D. A., & Fuller, W. A. (1979). Distribution of the estimators for autoregressive time
series with a unit root. *Journal of the American Statistical Association, 74*(366a), 427–431.
https://doi.org/10.1080/01621459.1979.10482531

Engle, R. F. (1982). Autoregressive conditional heteroscedasticity with estimates of the variance
of United Kingdom inflation. *Econometrica, 50*(4), 987–1007. https://doi.org/10.2307/1912773

Fama, E. F. (1970). Efficient capital markets: A review of theory and empirical work. *The Journal
of Finance, 25*(2), 383–417. https://doi.org/10.2307/2325486

French, K. R. (1980). Stock returns and the weekend effect. *Journal of Financial Economics,
8*(1), 55–69. https://doi.org/10.1016/0304-405X(80)90021-5

Granger, C. W. J., & Newbold, P. (1974). Spurious regressions in econometrics. *Journal of
Econometrics, 2*(2), 111–120. https://doi.org/10.1016/0304-4076(74)90034-7

Katsiampa, P. (2017). Volatility estimation for Bitcoin: A comparison of GARCH models. *Economics
Letters, 158*, 3–6. https://doi.org/10.1016/j.econlet.2017.06.023

Nelson, C. R., & Plosser, C. I. (1982). Trends and random walks in macroeconomic time series: Some
evidence and implications. *Journal of Monetary Economics, 10*(2), 139–162.
https://doi.org/10.1016/0304-3932(82)90012-5

Said, S. E., & Dickey, D. A. (1984). Testing for unit roots in autoregressive-moving average
models of unknown order. *Biometrika, 71*(3), 599–607. https://doi.org/10.1093/biomet/71.3.599
