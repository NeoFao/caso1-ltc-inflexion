# Consulta al profesor — Caso N.º 1

**Documento para la reunión del equipo y texto listo para enviar**

Fecha: 5 de agosto de 2026 · revisado el 11 de agosto
Preparado por: Fabrizio Espinoza Arce
Para: Alejandro Zamora, Jose Pablo Monestel, Isaac Morun
Destinatario final: Roberto Calvo Arias

---

## Cómo usar este documento

- **Parte A** es para la reunión: qué estamos decidiendo y con qué números.
- **Parte B** es el texto de la consulta, listo para copiar y enviar. No hace falta reescribirlo.

Léanse la Parte A antes de la reunión. Son cinco minutos y la reunión sale en veinte.

---

# Parte A — Para la reunión

## A.1 Por qué existe esta consulta

El enunciado deja abiertos seis puntos que admiten más de una lectura. Ninguno es un detalle: cada uno cambia qué datos usamos, qué aprende el modelo y qué números van al informe.

Podríamos decidirlos nosotros y justificarlos. De hecho vamos a hacerlo. Pero preguntar primero cuesta un correo y evita construir cinco semanas sobre un supuesto equivocado.

## A.2 Los dos números que hay que congelar

**`w` — la ventana.** Cuántas velas miramos a cada lado para decidir si una vela fue un giro.

> Una vela es **Máximo** si su cierre es estrictamente mayor que el de las `w` velas anteriores y las `w` posteriores. **Mínimo**, al revés. En cualquier otro caso, **Continuidad**.

Con `w` chico detectamos muchos giros, y muchos son ruido. Con `w` grande detectamos solo los giros importantes, pero quedan poquísimos ejemplos para entrenar.

**`h` — el horizonte.** Cuánto hacia adelante pronosticamos. Estando parados en `t`, el modelo dice qué etiqueta tendrá `t+h`.

El desarrollo completo de por qué esto importa está en [`00-definicion-punto-inflexion.md`](00-definicion-punto-inflexion.md). Acá va lo que hace falta para decidir.

## A.3 Lo que ya medimos

Esto **no** son estimaciones. Salió de ejecutar `scripts/spike_datos.py` contra la API pública de Binance el 5 de agosto de 2026. Los datos están en `docs/evidencias/`.

### Cobertura de las seis criptomonedas

| Activo | Velas diarias | Desde |
|---|---|---|
| BTC | 3 275 | 2017-08-17 |
| ETH | 3 275 | 2017-08-17 |
| ADA | 3 032 | 2018-04-17 |
| XRP | 3 015 | 2018-05-04 |
| LTC | 3 157 | 2017-12-13 |
| **SOL** | **2 185** | **2020-08-11** |

**SOL es el que manda.** Como el modelo es multivariante, solo sirven las fechas donde existen las seis series a la vez. Esa ventana común arranca el 11 de agosto de 2020, y todo lo anterior se descarta.

Cero huecos en las seis series en granularidad diaria.

### El problema: no alcanzan los datos en velas diarias

Antes de medir fijamos un criterio, para no terminar justificando lo que ya queríamos:

> Se elige el `w` más grande que deje **al menos 300 ejemplos de la clase minoritaria en el conjunto de entrenamiento.**

Resultado sobre el panel diario (2 185 observaciones, 70 % para entrenamiento):

| `w` | % Máximos | % Mínimos | Ejemplos de clase minoritaria en entrenamiento | ¿Cumple? |
|---|---|---|---|---|
| 3 | 10,37 | 10,46 | 149 | No |
| 5 | 6,58 | 6,48 | 97 | No |
| 7 | 4,47 | 4,61 | 67 | No |
| 10 | 3,37 | 3,51 | 53 | No |
| 15 | 2,09 | 2,27 | 32 | No |

**Ninguna combinación llega.** El mejor caso da 149 ejemplos, la mitad del piso.

### La salida: velas de 4 horas

Bajando la granularidad, el panel pasa de 2 185 a **13 114 observaciones** sobre exactamente la misma ventana de fechas:

| `w` | % Máximos | % Mínimos | Ejemplos de clase minoritaria en entrenamiento | ¿Cumple? |
|---|---|---|---|---|
| 3 | 9,77 | 10,05 | 884 | Sí |
| 5 | 6,15 | 6,40 | 557 | Sí |
| **7** | **4,63** | **4,66** | **420** | **Sí** |
| 10 | 3,31 | 3,31 | 299 | No, por uno |
| 15 | 2,13 | 2,22 | 189 | No |

Aplicando el criterio que fijamos antes: **`w = 7`, `h = 5`, velas de 4 horas.**

Que `w=10` quede en 299 — un ejemplo por debajo del piso de 300 — es casualidad, pero muestra que el criterio hizo un trabajo real y no fue decorativo.

## A.4 Lo que esto implica y conviene discutir

**Las clases van a estar desbalanceadas sí o sí.** Con `w=7`, alrededor del 90 % de las velas son Continuidad. Un modelo que responda siempre "Continuidad" y no detecte un solo giro va a tener más del 90 % de exactitud y va a ser completamente inútil.

Ya lo comprobamos con el sistema corriendo: nuestro baseline trivial da **exactitud 0,914** y **F1 macro 0,318**, con **precisión direccional 0,000**.

Por eso el informe no reporta exactitud como métrica principal. Reporta F1 macro y Precisión Direccional, que es lo que el enunciado pide.

**Hay un límite aritmético que no depende de los datos.** Dos máximos no pueden estar a menos de `w+1` velas: si lo estuvieran, cada uno caería dentro de la ventana del otro y cada uno tendría que ser mayor que el otro. De ahí que como mucho 1 de cada `w+1` velas pueda ser Máximo. Con `w=7` eso es 12,5 % como techo, y medimos 4,63 %.

**La etiqueta llega tarde.** Para saber si la vela `t` fue un máximo hay que ver las `w` velas siguientes. Combinado con el horizonte, la anticipación efectiva del sistema es `h+w` velas, no `h`. Con `w=7` y `h=5` son 12 velas de 4 horas, es decir dos días. Eso hay que decirlo en el informe; reportar solo `h` sería engañoso.

## A.5 Qué decidimos en la reunión

| | Decisión | Propuesta |
|---|---|---|
| D1 | Granularidad | 4 horas. Es la única que cumple el criterio acordado |
| D2 | Ventana `w` | 7 |
| D3 | Horizonte `h` | 5 |
| D6 | Qué máquina tiene cada uno | Que cada quien diga procesador, RAM y si tiene GPU NVIDIA |
| D9 | Arquitectura del segundo modelo | iTransformer o Informer, salvo que el profesor acepte CryptoMamba |

### Sobre D9: hay una contradicción en el enunciado

El apartado de entregables pide que el segundo modelo sea **«un Transformer»**. La lista del procedimiento ofrece iTransformer, CryptoMamba, Informer, VTA y FinLSPM.

**CryptoMamba no es un Transformer**: es un modelo de espacio de estados basado en Mamba. Elegirlo cumpliría con la lista y no con el entregable. iTransformer e Informer cumplen con las dos cosas.

Esto reduce el riesgo de la Semana 4 antes de gastar tiempo: si el profesor no responde, la opción segura es un Transformer de verdad.

Si alguien tiene un argumento para cambiar el piso de 300, es el momento — **antes** de volver a mirar las tablas. Cambiarlo después de ver los resultados es justificar lo que ya queríamos.

Cuando se decida, se cambia `contracts/config.py`, se quita la marca `PROVISIONAL`, y se avisa por escrito.

---

# Parte B — Texto para enviar

*Copiar desde acá.*

---

**Asunto:** Caso N.º 1 (pronóstico de puntos de inflexión en LTC) — consulta sobre seis puntos del enunciado

Estimado profesor Roberto Calvo,

Somos el equipo del Caso N.º 1: Alejandro Zamora, Jose Pablo Monestel, Isaac Morun y Fabrizio Espinoza Arce.

Antes de fijar el diseño del modelo queremos consultarle seis puntos del enunciado que admiten más de una lectura, para no avanzar cinco semanas sobre un supuesto equivocado. Ya descargamos y caracterizamos los datos, así que las preguntas vienen con las mediciones que las motivan.

**1. Sobre la ventana `w` y el horizonte `h`.**

El enunciado define el máximo local en función de una ventana temporal `w`, pero no fija su valor, ni el del horizonte de predicción `h`. Entendemos que la elección es nuestra y que debe quedar justificada en el informe a partir de las características de los datos. ¿Es correcta esa interpretación, o hay valores o un criterio que usted espere que utilicemos?

**2. Sobre la granularidad de las velas.**

El enunciado no especifica la frecuencia de los datos, y encontramos que esa decisión condiciona todo lo demás.

La ventana común a las seis criptomonedas está acotada por Solana, cuya serie en Binance arranca el 11 de agosto de 2020. Eso deja 2 185 observaciones en velas diarias. Fijamos como criterio previo disponer de al menos 300 ejemplos de la clase minoritaria en el conjunto de entrenamiento, y con velas diarias **ninguna** combinación de `(w, h)` lo alcanza: el mejor caso, con `w=3`, da 149.

Con velas de 4 horas el panel pasa a 13 114 observaciones sobre el mismo período, y el criterio se cumple hasta `w=7`, que deja 420 ejemplos.

Por eso proponemos trabajar con velas de 4 horas, `w=7` y `h=5`. ¿Le parece adecuado, o prefiere que mantengamos granularidad diaria asumiendo la escasez de ejemplos?

**3. Sobre qué se considera "tiempo real".**

Para determinar si una vela fue un máximo local hay que observar las `w` velas siguientes, de modo que la etiqueta de un instante `t` solo se conoce en `t+w`. Las pruebas "en tiempo real" que pide el enunciado para las semanas 3 y 4 admiten entonces dos interpretaciones:

- **(a)** El sistema confirma el giro con `w` velas de retraso: detección tardía pero verificable.
- **(b)** El sistema anuncia el giro en el momento, sin esperar confirmación: predicción genuina, considerablemente más difícil.

¿Cuál de las dos espera que implementemos? ¿O deberíamos reportar ambas?

**4. Sobre la métrica de decisión.**

El enunciado solicita Precisión Direccional y F1-Score. Las clases están fuertemente desbalanceadas por construcción: con `w=7` medimos 4,63 % de máximos y 4,66 % de mínimos, de modo que un clasificador que responda siempre "Zona de Continuidad" alcanza más del 90 % de exactitud sin detectar un solo punto de inflexión.

Quisiéramos confirmar dos cosas: si el F1-Score debe reportarse como macro, que da igual peso a las tres clases, o ponderado; y cómo debe entenderse la Precisión Direccional en un problema de clasificación multiclase y no de regresión. Provisionalmente la definimos como la fracción de los puntos de inflexión reales cuyo tipo fue predicho correctamente.

**5. Sobre el segundo modelo.**

El apartado de entregables indica que el segundo modelo debe ser «un Transformer». La lista de opciones del procedimiento incluye iTransformer, CryptoMamba, Informer, VTA y FinLSPM.

Entendemos que CryptoMamba no es una arquitectura Transformer, sino un modelo de espacio de estados basado en Mamba, de modo que elegirlo cumpliría con la lista pero no con el requisito literal del entregable. ¿Debemos restringirnos a una arquitectura Transformer —iTransformer o Informer—, o cualquiera de las cinco opciones es aceptable?

**6. Sobre el calendario de entregas.**

Entendemos que la primera entrega, correspondiente al marco teórico, es el martes 18 de agosto, en formato de documento.

Nos queda una duda sobre las restantes: si las cinco entregas mantienen cadencia semanal a partir de esa fecha, la última caería el 15 de septiembre. ¿Es correcto, o las semanas 4 y 5 se agrupan para cerrar antes?

Lo consultamos porque de ello depende cuánto margen tenemos para las pruebas del modelo avanzado.

Quedamos atentos a su respuesta. Muchas gracias por su tiempo.

Atentamente,

Fabrizio Espinoza Arce
Por el equipo del Caso N.º 1

---

*Fin del texto a enviar.*

---

## Anexo — Si preguntan de dónde salen los números

Todo lo de la Parte A se reproduce con:

```bash
uv run python scripts/spike_datos.py --intervalo 4h
```

Las salidas quedan en `docs/evidencias/spike-datos-4h.json` y `docs/evidencias/spike-datos-1d.json`, cada una con su fecha de ejecución.
