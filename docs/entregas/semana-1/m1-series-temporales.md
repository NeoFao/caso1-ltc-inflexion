# Marco teórico: series de tiempo

**Autor:** Jose Pablo Monestel · **Issue:** [S1-M1-06](https://github.com/NeoFao/caso1-ltc-inflexion/issues/9)

> **Este archivo es un esqueleto.** Cada sección trae la figura y los números ya medidos.
> Lo que falta es tu texto. Borrá los bloques `> ESCRIBÍ ACÁ` a medida que los completes.
> Todos los valores citados salen de `docs/evidencias/marco-teorico.json`, medidos el
> 12/08/2026 sobre 2 185 velas diarias de 2020-08-11 a 2026-08-04.

---

## 1. Definición de serie temporal

![Figura 1](../../evidencias/mt-01-serie-temporal.png)

**Figura 1.** Precio de cierre diario de Litecoin, 2 185 observaciones entre el 11 de agosto de 2020 y el 4 de agosto de 2026.

> **ESCRIBÍ ACÁ.** Qué es una serie temporal y qué la distingue de un conjunto de datos cualquiera: el orden importa, y las observaciones no son independientes entre sí. Conectá con la Figura 1: nuestro caso son 2 185 observaciones equiespaciadas de una sola variable, el precio de cierre.

---

## 2. Componentes de una serie temporal

![Figura 2](../../evidencias/mt-02-componentes.png)

**Figura 2.** Descomposición aditiva de la serie de LTC en tendencia, estacionalidad de período semanal y residuo.

**Medido:** el componente estacional representa el **0,426 %** de la desviación total de la serie.

> **ESCRIBÍ ACÁ.** Tendencia, estacionalidad, ciclo y componente irregular. El dato interesante para analizar: la estacionalidad semanal es prácticamente inexistente (0,426 %), a diferencia de lo que pasa en series financieras de mercados con horario y días hábiles. Explicá por qué: el mercado cripto opera 24/7, así que no hay efecto fin de semana. Casi toda la variación es tendencia y residuo.

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

**Un matiz que conviene mencionar:** ETH queda en 0,059, apenas por encima del umbral de 0,05. No cambia la conclusión, pero decirlo demuestra que leíste la tabla en vez de resumirla. Un caso al borde merece nombrarse: con otro período de muestra podría cruzar el umbral, y eso ilustra que el resultado del test depende de la ventana observada.

> **ESCRIBÍ ACÁ.** Qué significa que una serie sea estacionaria: media, varianza y autocovarianza que no dependen del tiempo. Explicá el test ADF y su hipótesis nula.
>
> **Cuidado con la redacción, esto es lo que separa un 3 de un 4:** no rechazar la hipótesis nula **no demuestra** que la serie no sea estacionaria; demuestra que no hay evidencia suficiente en contra. Es la diferencia entre "no hay evidencia en contra" y "hay evidencia a favor".

---

## 4. No estacionariedad

Mismo material que la sección anterior, leído al revés.

> **ESCRIBÍ ACÁ.** Por qué los precios no son estacionarios: tienen tendencia y su varianza crece con el nivel. Qué consecuencias tiene para el modelado, y por qué la transformación a retornos resuelve el problema. Cerrá con la consecuencia práctica: **las características del modelo se construyen sobre retornos, no sobre precios en nivel**, y eso está decidido por esta medición y no por costumbre.

---

## 5. Heterocedasticidad

![Figura 5](../../evidencias/mt-05-heterocedasticidad.png)

**Figura 5.** Serie construida con volatilidad constante (arriba) y con volatilidad por tramos (abajo). Ambas generadas por nosotros; no son datos de mercado.

**Medido en las series construidas:** cociente entre la volatilidad del tramo agitado y la del tranquilo — **1,28×** sin regímenes, **6,41×** con regímenes.

> **ESCRIBÍ ACÁ.** Definí homocedasticidad y heterocedasticidad. Usá la Figura 5 para mostrar el contraste con la respuesta conocida: en el panel de arriba pusimos volatilidad constante y el cociente sale 1,28, cerca de 1 como corresponde; en el de abajo la multiplicamos por 5 en tramos alternos y el cociente sale 6,41. Recién después pasá a LTC en la sección siguiente.
>
> Cerrá explicando por qué esto rompe a ARIMA: asume varianza constante en los errores.

---

## 6. Volatilidad

![Figura 6](../../evidencias/mt-04-volatilidad.png)

**Figura 6.** Precio de cierre de LTC y su volatilidad móvil de 30 velas.

**Medido:** la volatilidad del tramo más agitado es **8,8 veces** la del más tranquilo (máxima 0,0774; mínima 0,0088).

> **ESCRIBÍ ACÁ.** Qué es la volatilidad y cómo se estima con desviación estándar móvil de los retornos. El número que sostiene toda la sección es el 8,8×: es evidencia directa de heterocedasticidad en datos reales, no una afirmación de manual. Señalá en la Figura 6 que los picos de volatilidad coinciden con los movimientos bruscos del precio.

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

> **ESCRIBÍ ACÁ.** Definí la ACF y para qué sirve. La lectura de la Figura 7 tiene dos partes:
>
> 1. En nivel, la autocorrelación es 0,991 y decae lentísimo. Eso **es** la firma de una serie no estacionaria, y confirma la sección 3 desde otro ángulo.
> 2. En retornos cae a −0,036 y casi ningún rezago es significativo.
>
> **Este es el hallazgo más fuerte de tu sección y conviene que lo desarrolles.** Que los retornos no tengan autocorrelación lineal significativa quiere decir que un modelo lineal sobre rezagos no va a poder predecir mucho. Es un argumento medido a favor de necesitar modelos no lineales y multivariantes, que es exactamente lo que plantea el proyecto. No es un resultado negativo: es la justificación del enfoque.

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

**Control:** las construidas se pidieron con correlación 0,1 y 0,9; salieron medidas en **0,094** y **0,903**.

> **ESCRIBÍ ACÁ.** Definí correlación cruzada y su diferencia con la autocorrelación.
>
> **El punto de análisis fuerte es el contraste nivel/retornos, y hay que contarlo bien.** El problema de la correlación en nivel acá no es que infle los valores: es que es **errática**. Ordena los activos de forma económicamente implausible — atribuye a LTC una relación casi nula con Bitcoin, que es el activo que marca la tendencia de todo el mercado, y fuerte con Cardano. Sobre retornos el rango se estrecha a la mitad y el orden tiene sentido.
>
> Cerrá con la consecuencia: esto es lo que justifica que el problema sea multivariante. Si LTC se moviera solo, las cinco variables de apoyo del enunciado sobrarían; con correlaciones de 0,47 a 0,81 en retornos, no sobran.

---

## Referencias

> **ESCRIBÍ ACÁ.** Formato APA. Mínimo una fuente académica por concepto principal: series temporales, estacionariedad, test ADF, heterocedasticidad, autocorrelación.
>
> Es un criterio entero de la rúbrica y vale lo mismo que todo el contenido técnico.
