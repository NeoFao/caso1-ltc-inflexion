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

Ya lo comprobamos con el sistema corriendo: nuestro baseline trivial da **exactitud 0,912** y **F1 macro 0,318**, con **precisión direccional 0,000**.

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

*Reescrita el 1 de septiembre. La versión anterior tenía seis preguntas y proponía `h = 5`;
desde entonces el equipo fijó `h = 1` y resolvió por su cuenta cuatro de los seis puntos.
Enviar aquella hoy sería preguntar por cosas ya decididas.*

*Copiar desde acá.*

---

**Asunto:** Caso N.º 1 (puntos de inflexión en LTC) — una consulta que nos bloquea, y cuatro decisiones que tomamos

Estimado profesor Roberto Calvo,

Somos el equipo del Caso N.º 1: Alejandro Zamora, Jose Pablo Monestel, Isaac Morun y Fabrizio Espinoza Arce.

Le escribimos por **una pregunta que nos bloquea** y para dejarle constancia de **cuatro decisiones que tomamos nosotros** ante ambigüedades del enunciado, por si alguna no coincide con lo que esperaba.

---

## La consulta: qué debe mostrar la vista en tiempo real

Queremos precisar algo antes de construirla, porque afecta a lo que se ve en pantalla y no al modelo.

**El modelo ya predice de verdad.** Estando parado en `t`, y usando únicamente información disponible hasta `t`, anuncia qué será el instante `t + h`. Lo garantizamos con una comprobación automática que perturba todo el futuro y exige que las características del pasado no cambien; hay además una prueba que confirma que esa comprobación detecta una fuga deliberada.

Lo que no se puede adelantar es **la verificación**. Para saber si el anuncio hecho en `t` fue correcto hay que esperar a que existan las `w` velas posteriores a `t + h`: en total `h + w`, ocho velas o 32 horas con nuestra configuración.

De ahí la duda, que es sobre la presentación:

- **(a)** La vista muestra el anuncio **en el momento**, sin marca de acierto, y la marca aparece 32 horas después.
- **(b)** La vista muestra solo lo ya verificable, con 32 horas de retraso, de modo que todo lo que se ve viene con su acierto o su fallo al lado.

**¿Cuál espera ver en la demostración?** La (a) enseña el sistema tal como funcionaría en producción; la (b) es más fácil de evaluar de un vistazo porque nada aparece sin su resultado.

Es lo único que tenemos detenido: la tercera prueba de detección que pide el enunciado depende de esta definición, y preferimos no elegirla por nuestra cuenta.

---

## Las cuatro decisiones que tomamos

Las tomamos porque el proyecto no podía esperar, y cada una quedó registrada con su evidencia. **Si alguna no coincide con lo que esperaba, todavía estamos a tiempo de corregirla.**

**1. Ventana, horizonte y granularidad: velas de 4 horas, `w = 7`, `h = 1`.**

Entendimos que la elección era nuestra y que debía justificarse con los datos. La ventana común a las seis criptomonedas está acotada por Solana, que en Binance arranca el 11 de agosto de 2020: son 2 185 observaciones diarias. Fijamos como criterio previo disponer de al menos 300 ejemplos de la clase minoritaria en entrenamiento, y **con velas diarias ninguna combinación lo alcanza**. Con velas de 4 horas el panel pasa a 13 114 observaciones y el criterio se cumple hasta `w = 7`, con 420 ejemplos.

La anticipación real que ofrece el sistema es `h + w`, es decir **8 velas o 32 horas**, no una sola vela.

**2. El F1-Score se reporta como macro.**

Con `w = 7` medimos 4,63 % de máximos y 4,66 % de mínimos. Un clasificador que responda siempre «Continuidad» alcanza **91,2 % de exactitud** sin detectar un solo giro, así que la exactitud no puede ser la métrica principal. El F1 macro da igual peso a las tres clases.

La Precisión Direccional la definimos, a falta de una definición para clasificación multiclase, como **la fracción de los puntos de inflexión reales cuyo tipo se predijo correctamente**.

**3. El segundo modelo es iTransformer, y no CryptoMamba.**

El apartado de entregables pide «un Transformer» y la lista de opciones incluye CryptoMamba. **CryptoMamba no es una arquitectura Transformer**, sino un modelo de espacio de estados: elegirlo cumpliría con la lista pero no con el requisito literal. Además no se instala sin CUDA en ninguna de nuestras máquinas, lo que comprobamos.

Descartamos también Informer porque no encontramos una vía instalable en nuestro entorno —lo reportamos como lo que es, lo que pudimos verificar acá, y no como una afirmación sobre el paquete.

**4. Un resultado negativo que preferimos declarar.**

Medimos si las cinco criptomonedas de apoyo aportan información sobre los giros de Litecoin. **No podemos afirmar que aporten:** la diferencia es de 0,0008 en F1 macro, cambia de signo según la semilla, y es del mismo tamaño que la de un control que añade columnas duplicadas sin información nueva.

No invalida el planteamiento —las correlaciones medidas lo justificaban— pero **cambia la conclusión**, y preferimos reportarlo así.

---

Todo lo anterior está medido y es reproducible; con gusto le mostramos el detalle.

Quedamos atentos a su respuesta sobre el punto de tiempo real.

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
