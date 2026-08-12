"""Monta el tablero de trabajo en GitHub: etiquetas, hitos y backlog.

Es un script y no una sesion de clics para que el estado de GitHub sea
reproducible y auditable. Si alguien borra un hito por error, se vuelve a correr.

Es idempotente: crear algo que ya existe no falla, se salta.

Uso:
    uv run python scripts/scrum_github.py            # muestra que haria
    uv run python scripts/scrum_github.py --aplicar  # lo hace
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

REPO = "NeoFao/caso1-ltc-inflexion"

# Un sprint por semana de entrega. Las fechas son las estimadas contando hacia
# atras desde el 8 de septiembre; hay que confirmarlas con el profesor.
SPRINTS = [
    ("Sprint 1 — Marco teorico y datos", "2026-08-11",
     "Marco teorico de series temporales y criptoactivos. En paralelo: contratos congelados y "
     "pipeline de datos. El enunciado pide solo teoria esta semana; el codigo es nuestro colchon."),
    ("Sprint 2 — Modelos y pipeline", "2026-08-18",
     "Marco teorico de modelos y definicion del pipeline. En paralelo: caracteristicas, entorno "
     "de entrenamiento y esqueleto de la aplicacion contra datos falsos."),
    ("Sprint 3 — Modelo fundacional", "2026-08-25",
     "Modelo fundacional funcionando y evaluado, con pruebas sobre datos sinteticos, de "
     "entrenamiento y tiempo real."),
    ("Sprint 4 — Modelo avanzado", "2026-09-01",
     "Modelo avanzado con las mismas pruebas. Punto de decision el lunes: si M3 no arranca, "
     "entra el PM a apoyar."),
    ("Sprint 5 — Reporte final", "2026-09-08",
     "Reporte final y presentacion. Semana de cierre y ensayo, no de construccion."),
]

ETIQUETAS = [
    ("M0-infra", "1B2A4A", "Infraestructura, contratos, evaluacion, integracion (Fabrizio)"),
    ("M1-datos-app", "345D9D", "Datos, diagnostico y aplicacion web (Jose Pablo)"),
    ("M2-features", "1E8449", "Etiquetado, sinteticos y caracteristicas (Alejandro)"),
    ("M3-modelos", "C0392B", "Modelo fundacional y modelo avanzado (Isaac)"),
    ("tipo:spike", "F39C12", "Investigacion acotada: produce una respuesta, no producto"),
    ("tipo:feature", "5A6675", "Trabajo con entregable"),
    ("tipo:doc", "8E44AD", "Seccion del documento o del deck"),
    ("tipo:chore", "95A5A6", "Mantenimiento, infraestructura, proceso"),
    ("tipo:bug", "E74C3C", "Algo esta mal y hay evidencia de que lo esta"),
    ("bloquea", "D35400", "Alguien mas no puede avanzar hasta que esto cierre"),
    ("contrato", "8E44AD", "Toca contracts/. Requiere revision explicita de quien lo consume"),
    ("entregable", "16A085", "Entra directo en el documento semanal"),
]

HECHO = """
### Definicion de hecho
- [ ] Codigo en la rama, con sus pruebas pasando
- [ ] Un numero obtenido ejecutando, no estimando
- [ ] Seccion del documento, con figuras numeradas y referenciadas
- [ ] Slide con lo esencial
"""

# (titulo, sprint, etiquetas, cuerpo)
BACKLOG: list[tuple[str, int, list[str], str]] = [
    # ---------------------------------------------------------------- Sprint 1
    (
        "[M0] Enviar la consulta al profesor",
        1, ["M0-infra", "tipo:chore", "bloquea"],
        """### Por que
Cuatro puntos del enunciado admiten mas de una lectura y cada uno cambia el diseno.
Es lo primero de la fila porque **tiene latencia**: todo lo demas depende de nosotros,
esto depende de otro.

### Que hacer
El texto esta redactado y listo para copiar en la Parte B de
[`docs/02-consulta-profesor.md`](../blob/main/docs/02-consulta-profesor.md). No hay que
reescribir nada.

### Criterio de aceptacion
Correo enviado, y la fecha anotada en un comentario de este issue. Cuando llegue
respuesta, se pega aqui y se cierran las decisiones D4 y D5.""",
    ),
    (
        "[M0] Recolectar las especificaciones de maquina de cada integrante",
        1, ["M0-infra", "tipo:chore", "bloquea"],
        """### Por que
Riesgo R3 del PRD. Sin saber que maquinas hay, la eleccion de modelo avanzado de M3 es
a ciegas, y podriamos descubrir en la semana 4 que nadie puede entrenarlo.

### Que hacer
Preguntar en el grupo: procesador, RAM, y si tiene GPU NVIDIA.

### Criterio de aceptacion
Una tabla con las cuatro maquinas en un comentario de este issue, y RNF-4 del PRD
actualizado con cual es la mas lenta.""",
    ),
    (
        "[M0] Congelar w, h y granularidad en contracts/config.py",
        1, ["M0-infra", "contrato", "bloquea"],
        """### Por que
Es la interfaz compartida real del proyecto. Si M2 etiqueta con w=5 y M3 entrena con w=10,
los resultados no son comparables y no nos damos cuenta hasta la semana 4.

### Que hacer
Reunion con la Parte A de
[`docs/02-consulta-profesor.md`](../blob/main/docs/02-consulta-profesor.md)
proyectada. La medicion recomienda w=7, h=5, velas de 4 horas: es el w mas grande que deja
420 ejemplos de la clase minoritaria en entrenamiento, por encima del piso de 300 que se
fijo **antes** de medir.

Despues: actualizar `contracts/config.py`, quitar `PROVISIONAL = True`, regenerar el
snapshot con `uv run python scripts/exportar_estatico.py`, y avisar por escrito.

### Criterio de aceptacion
`PROVISIONAL` en `False`, las 44 pruebas pasando, y la aplicacion publicada mostrando los
valores nuevos sin la marca de parametros provisionales.

### Cuidado
Si alguien quiere cambiar el piso de 300, tiene que ser **antes** de volver a mirar las
tablas. Cambiarlo despues de ver resultados es justificar lo que ya queriamos.""",
    ),
    (
        "[M0] Publicar el backend en Hugging Face Spaces",
        1, ["M0-infra", "tipo:chore"],
        """### Por que
La pagina publicada funciona, pero siempre contra el snapshot congelado. Con el backend
arriba, el modo tiempo real deja de ser una promesa.

### Que hacer
Los tres pasos estan en [`deploy/README.md`](../blob/main/deploy/README.md). El Dockerfile
clona este repositorio en vez de duplicar codigo, asi que no hay nada que mantener en dos
sitios.

### Criterio de aceptacion
`curl https://<usuario>-caso1-ltc-backend.hf.space/api/config` devuelve JSON, la variable
de repositorio `API_BASE` esta definida, y la cabecera de la pagina dice *backend en vivo*
en vez de *datos congelados*.""",
    ),
    (
        "[M1] Tabla de estacionariedad ADF, en nivel y en retornos",
        1, ["M1-datos-app", "tipo:feature", "entregable"],
        """### Por que
El enunciado pide marco teorico de estacionariedad y no estacionariedad. Sin una prueba
corrida sobre nuestros datos, esa seccion es copiar una definicion de un libro. Con la
tabla es analisis, que es un criterio entero de la rubrica.

### Que hacer
`tabla_estacionariedad(panel, en_retornos=False)` y `en_retornos=True` en
`src/diagnostico/pruebas.py`. Ya esta escrita; lo tuyo es correrla e interpretarla.

### Criterio de aceptacion
Tabla con los seis activos en las dos formas, mas un parrafo que explique que cambia entre
ellas y por que eso justifica construir caracteristicas sobre retornos.

### Cuidado al redactar
No rechazar la hipotesis nula del ADF **no** demuestra que la serie no sea estacionaria.
Demuestra que no hay evidencia suficiente en contra. Es la diferencia entre "no hay
evidencia en contra" y "hay evidencia a favor".""",
    ),
    (
        "[M1] Autocorrelacion de LTC",
        1, ["M1-datos-app", "tipo:feature", "entregable"],
        """### Por que
El enunciado la pide explicitamente, y es lo que justifica usar precios rezagados como
variables predictoras.

### Que hacer
`autocorrelacion(serie, rezagos=40)` sobre el cierre en nivel y sobre los retornos.

### Criterio de aceptacion
Figura con la ACF y su banda de confianza al 95 %, y una frase que diga hasta que rezago
hay autocorrelacion significativa **con el numero medido**, no "hay bastante".""",
    ),
    (
        "[M1] Matriz de correlacion cruzada entre las seis criptomonedas",
        1, ["M1-datos-app", "tipo:feature", "entregable"],
        """### Por que
Es lo que justifica que el problema sea multivariante. Si LTC no se moviera con las demas,
todo el planteo del enunciado se caeria.

### Que hacer
`matriz_correlacion(panel, en_retornos=True)`.

### Por que sobre retornos y no sobre precios
Dos series con tendencia comparten tendencia, y su correlacion en nivel sale altisima
aunque no tengan ninguna relacion real. Se llama correlacion espuria. Mencionarlo en el
documento suma; caer en ella resta.

### Criterio de aceptacion
Mapa de calor de 6x6 y una frase que nombre que activo de apoyo tiene mayor correlacion con
LTC, con el valor medido.""",
    ),
    (
        "[M1] Volatilidad movil y evidencia de heterocedasticidad",
        1, ["M1-datos-app", "tipo:feature", "entregable"],
        """### Por que
El enunciado pide volatilidad y heterocedasticidad, y es lo que explica por que ARIMA y
GARCH clasicos rinden mal en este problema.

### Que hacer
Volatilidad movil de 30 velas sobre los retornos de LTC, graficada en el tiempo.

### Criterio de aceptacion
Figura donde se vea que la volatilidad no es constante, y un numero que lo respalde: por
ejemplo el cociente entre la volatilidad del tramo mas agitado y la del mas tranquilo.""",
    ),
    (
        "[M1] Seccion teorica: series temporales",
        1, ["M1-datos-app", "tipo:doc", "entregable"],
        """### Por que
Es la parte del enunciado que tu propio modulo mide.

### Que hacer
Definicion y componentes de una serie temporal, estacionariedad, no estacionariedad,
heterocedasticidad, volatilidad, autocorrelacion y correlacion cruzada. Escrita con tus
tablas al lado, no con definiciones de manual.

### Criterio de aceptacion
`docs/entregas/semana-1/m1-series-temporales.md`, con las figuras numeradas y referenciadas
en el texto, y las citas en APA.""",
    ),
    (
        "[M2] Spike: sensibilidad del etiquetador al ruido",
        1, ["M2-features", "tipo:spike", "entregable"],
        """### La pregunta
El etiquetador encuentra los giros perfectamente en una serie limpia. Con ruido, cuanto
tolera antes de empezar a inventar giros que no existen?

### Que se rompe si la respuesta llega tarde
Es la pregunta incomoda que nos pueden hacer en la exposicion: *como saben que sus
etiquetas no son ruido?* Mejor tener el numero antes que improvisar.

### Que hacer
`serie_zigzag()` en `src/sintetico/generador.py` acepta un parametro `ruido`. Con `ruido=0`
los giros son exactamente los vertices que pusimos. Subir de a poco y medir que fraccion de
los vertices verdaderos sigue detectando, y cuantos giros falsos aparecen.

### Criterio de aceptacion
Tabla de nivel de ruido contra (detectados / verdaderos) y falsos positivos, mas una figura.
El numero que buscamos es el ruido a partir del cual la deteccion se degrada.

### Cuidado
Esta serie la construis vos. **No es lo que pasa en LTC.** Presentarla como caracterizacion
del etiquetado, no como hallazgo sobre el mercado.""",
    ),
    (
        "[M2] Indicadores tecnicos sin fuga de informacion",
        1, ["M2-features", "tipo:feature"],
        """### Por que
RF-F1 los pide explicitamente y son las caracteristicas con mas historia en este dominio.

### Que hacer
Agregar a `src/features/base.py`: medias movil simple y exponencial, RSI, MACD, bandas de
Bollinger. Todas con ventanas hacia atras. Seguir el patron de `retornos()` y
`volatilidad()`, que ya estan escritas.

**No agregar `ta-lib` ni `pandas-ta` sin justificarlo.** Un RSI son seis lineas de pandas, y
una dependencia nueva es una decision, no un detalle.

### Criterio de aceptacion
Las caracteristicas nuevas estan en `construir()`, `verificar_sin_fuga()` pasa, y hay una
figura de un indicador sobre el precio que muestra que esta bien calculado.""",
    ),
    (
        "[M2] Caracteristicas de ventana deslizante",
        1, ["M2-features", "tipo:feature"],
        """### Por que
RF-F1 pide cuatro familias y esta falta.

### Que hacer
Estadisticos sobre ventanas moviles del cierre y de los retornos: minimo, maximo, rango,
posicion del precio actual dentro del rango de la ventana, asimetria, curtosis.

La **posicion dentro del rango** es la mas prometedora para este problema: un precio cerca
del maximo de sus ultimas 20 velas esta estructuralmente mas cerca de ser un maximo local.
Vale la pena medirla y comentarla aparte.

### Criterio de aceptacion
Familias nuevas en `construir()` y `verificar_sin_fuga()` pasando.

### Dato medido que condiciona esto
Con el panel de 4 horas y w=7 la clase minoritaria tiene **420 ejemplos en entrenamiento**.
Meter 200 columnas garantiza sobreajuste. El trabajo no es generar todas las caracteristicas
posibles: es generar las que aportan y demostrar cuales son.""",
    ),
    (
        "[M2] Seccion teorica: criptoactivos y punto de inflexion",
        1, ["M2-features", "tipo:doc", "entregable"],
        """### Que hacer
Criptoactivos: definicion, caracteristicas principales, tipos, mercado cripto, factores que
afectan el precio, correlacion y dependencia entre activos. Mas: definicion de punto de
inflexion y como encontrarlos.

Para la parte de punto de inflexion hay material propio:
[`docs/00-definicion-punto-inflexion.md`](../blob/main/docs/00-definicion-punto-inflexion.md)
y las mediciones del spike de ruido.

### Criterio de aceptacion
`docs/entregas/semana-1/m2-criptoactivos.md`, figuras numeradas y referenciadas, citas APA.""",
    ),
    (
        "[M3] Modelo clasico de referencia, de punta a punta",
        1, ["M3-modelos", "tipo:feature"],
        """### Por que esto antes que el fundacional
Porque necesitas recorrer el circuito completo (cargar panel, construir caracteristicas,
particionar, entrenar, evaluar) con algo que sabes que va a andar. Si el primer modelo que
intentas es un transformer de Hugging Face, cuando falle no vas a saber si el problema es el
modelo, las caracteristicas, la particion o la interfaz.

### Que hacer
`RandomForestClassifier` envuelto en la interfaz `Modelo`, en `src/modelos/clasico.py`.

### Criterio de aceptacion
Una fila en `docs/evidencias/resultados.csv` con su F1 macro sobre validacion, al lado de
los tres baselines. Si no supera al `BaselineTrivial` en F1 macro, algo esta mal y hay que
averiguar que antes de seguir.

Ese numero es el punto de referencia para todo el resto del proyecto.""",
    ),
    (
        "[M3] Spike: es viable CryptoMamba sin CUDA?",
        1, ["M3-modelos", "tipo:spike", "bloquea"],
        """### La pregunta
CryptoMamba esta en la lista del enunciado. Sospecho que depende de `mamba-ssm`, que compila
contra CUDA y es problematico en Windows. **No esta verificado.**

### Que se rompe si la respuesta llega tarde
Si es cierto y lo descubrimos en la semana 4, se cae el entregable del modelo avanzado sin
tiempo de cambiar.

### Tiempo maximo
Media hora. Buscar el repositorio, mirar sus dependencias, intentar instalarlo en un entorno
aparte.

### Que queda escrito
Un comentario en este issue: se puede o no se puede en nuestras maquinas, con la evidencia.
Si no se puede, iTransformer es el candidato mas benigno en CPU, aunque **eso tampoco esta
medido**.""",
    ),
    (
        "[M3] Spike: inventario de modelos fundacionales que corran en CPU",
        1, ["M3-modelos", "tipo:spike"],
        """### La pregunta
Cual modelo fundacional de Hugging Face es viable en nuestras maquinas, y cuanto tarda?

### Que se rompe si la respuesta llega tarde
RF-M1 exige justificar la eleccion segun las caracteristicas **medidas** de los datos, no por
popularidad. Sin mediciones no hay justificacion, hay opinion.

### Que hacer
Elegir dos o tres candidatos y medir, en tu maquina: tiempo de descarga, memoria en RAM y
tiempo de inferencia sobre una ventana de nuestro tamano.

### El punto dificil, para pensarlo desde ahora
Los modelos fundacionales de series de tiempo **pronostican, no clasifican**. Devuelven una
trayectoria futura y nosotros necesitamos tres clases. Hay dos formas de cruzar ese puente:

1. Usar el modelo congelado como **extractor de representaciones** y ponerle encima una
   cabeza de clasificacion entrenada por nosotros.
2. **Pronosticar la trayectoria** y derivar la etiqueta aplicando el `etiquetar()` del
   contrato.

Son dos proyectos distintos con metricas distintas. La 2 es mas simple y mas honesta con el
espiritu del enunciado; la 1 suele rendir mas. **No decidir solo: traerlo a la reunion.**

### Que queda escrito
Tabla de candidatos con sus tiempos medidos y una recomendacion con su razon.""",
    ),
    (
        "[M3] Seccion teorica: TSFMs, VTA, FinLSPM y CryptoMamba",
        1, ["M3-modelos", "tipo:doc", "entregable"],
        """### Que hacer
Modelos fundacionales de series de tiempo, VTA (Verbal Technical Analysis), FinLSPM y
CryptoMamba.

Escribirla **mientras** haces los dos spikes: vas a estar leyendo esos papers de todos modos,
y escribir despues significa leerlos dos veces.

### Criterio de aceptacion
`docs/entregas/semana-1/m3-modelos.md`, con citas en APA. Es un criterio entero de la rubrica
y vale lo mismo que todo el contenido tecnico.""",
    ),
    (
        "[M0] Seccion teorica: metricas de evaluacion para puntos de inflexion",
        1, ["M0-infra", "tipo:doc", "entregable"],
        """### Por que
El enunciado la lista como entregable de la **Semana 1**, junto con el resto del marco
teorico. Se me quedo fuera del backlog al crearlo; es un entregable calificado.

### Que hacer
Que metricas sirven para evaluar deteccion de puntos de inflexion y por que. En particular:
por que la exactitud no sirve con clases desbalanceadas, que mide F1 macro frente a F1
ponderado, y como se interpreta la Precision Direccional en un problema de tres clases.

Hay material propio: `contracts/metrics.py` documenta cada decision, y la aplicacion
publicada muestra el caso concreto (baseline trivial con exactitud 0.866 y F1 macro 0.309).

### Criterio de aceptacion
`docs/entregas/semana-1/m0-metricas.md`, con el ejemplo numerico medido y citas en APA.""",
    ),
    (
        "[M2] Elegir los ordenes de rezago con medicion",
        1, ["M2-features", "tipo:feature"],
        """### Contexto
El enunciado define las variables de apoyo como "los precios historicos **(rezagados)** de
las cinco criptomonedas". Es la entrada especificada de forma mas literal del documento.

El andamiaje ya genera rezagos para los seis activos, pero con ordenes `(1, 2, 3, 5)`
elegidos por defecto, sin medir nada.

### Que hacer
Medir hasta que rezago aporta informacion. La funcion de autocorrelacion que produce M1 da
la pista para LTC; para las de apoyo hace falta correlacion cruzada con desfase.

### Criterio de aceptacion
Los ordenes elegidos quedan justificados con un numero medido, no con una convencion. Si
resulta que `(1, 2, 3, 5)` esta bien, tambien vale: pero entonces hay una medicion detras.""",
    ),
    # ---------------------------------------------------------------- Sprint 2
    (
        "[M2] Feature engineering con herramientas posteriores a 2025",
        2, ["M2-features", "tipo:spike", "entregable"],
        """### Por que
El enunciado lo exige textualmente: *"Utilizar herramientas State of the Art, mayores a
2025"*. Todo lo que tenemos hoy es clasico (rezagos, retornos, volatilidad, correlacion
movil, indicadores tecnicos). Ninguna de esas familias es posterior a 2025, asi que el
requisito esta sin atender y cuenta en el criterio de Contenido.

### La pregunta
Que tecnica de representacion posterior a 2025 aporta sobre las caracteristicas clasicas,
**medido**, no supuesto?

### Que hacer
El camino mas prometedor y coherente con el resto del proyecto: usar un modelo fundacional
de series de tiempo congelado como **extractor de representaciones**, y comparar el F1 macro
con y sin esas columnas. Coordinar con M3, que ya estara evaluando candidatos.

### Cuidado
El requisito no es "usar la libreria mas nueva". Es justificar una eleccion moderna con
evidencia. Agregar una dependencia de 2026 que no mejora nada es peor que no agregarla, y
contradice la regla de no sumar dependencias sin necesidad demostrada.

### Criterio de aceptacion
Tabla comparativa con y sin la representacion nueva, y una decision escrita. **Si no aporta,
se dice y se descarta**, dejando escrito que se probo: eso tambien responde al requisito.""",
    ),
    (
        "[M3] Seccion teorica: modelos estadisticos clasicos y de machine learning",
        2, ["M3-modelos", "tipo:doc", "entregable"],
        """### Por que
La Semana 2 pide *"Marco teorico Modelos Estadisticos **y** de Machine Learning para Series
Temporales"*, que es mas amplio que los TSFMs. Falta la parte clasica, y la contextualizacion
del enunciado nombra ARIMA y GARCH explicitamente.

### Que hacer
ARIMA, GARCH y modelos de machine learning clasicos para series temporales: que asumen y por
que esos supuestos fallan con criptomonedas.

Es el argumento que sostiene todo el planteo del proyecto: si ARIMA funcionara bien, no
haria falta aprendizaje profundo. M1 va a tener las pruebas de estacionariedad y
heterocedasticidad que lo respaldan con datos nuestros.

### Criterio de aceptacion
`docs/entregas/semana-2/m3-modelos-clasicos.md` con citas APA, conectado a las mediciones de
M1 y no solo a definiciones de manual.""",
    ),
    (
        "[M0] Ensamblador del documento semanal",
        2, ["M0-infra", "tipo:chore"],
        """### Por que
Cinco documentos y cinco decks en cinco semanas. Si el ensamblaje del viernes es manual, se
come la tarde entera y compite con el trabajo tecnico.

### Que hacer
Un script en `scripts/` que tome los markdown de `docs/entregas/semana-N/` y produzca el Word
con el mismo estilo, reusando `scripts/build_prd.js`.

### Criterio de aceptacion
Un comando produce el documento de la semana con portada, indice y las figuras de
`docs/evidencias/` embebidas.""",
    ),
    (
        "[M1] Esqueleto de la aplicacion contra datos falsos",
        2, ["M1-datos-app", "tipo:feature"],
        """### Por que
No podes esperar a que exista el modelo. El backend ya devuelve predicciones del baseline con
la misma forma que va a tener el modelo real, asi que la app funciona desde el dia uno y
despues solo cambia de donde vienen los numeros.

### Que hacer
Los tres modos ya estan esbozados en `app/src/App.tsx`. Falta darles contenido real: selector
de rango de fechas en historico, comparacion de modelos lado a lado, panel de metricas
completo.

### Criterio de aceptacion
La app publicada muestra los tres modos navegables, y `npm run build` pasa con TypeScript
estricto.

### La regla que no se rompe
La aplicacion no calcula nada. Ni una metrica, ni una etiqueta, ni una prediccion.""",
    ),
    (
        "[M2] Escalado ajustado solo con datos de entrenamiento",
        2, ["M2-features", "tipo:feature"],
        """### Por que
RF-F3. Si el escalador ve el conjunto de prueba al calcular su media y su desviacion, hay
fuga de informacion, y las metricas salen mejores de lo que el sistema realmente logra.

### Criterio de aceptacion
El escalador se ajusta con la mascara de entrenamiento de `contracts/splits.py` y se aplica
al resto. Una prueba automatica lo verifica.""",
    ),
    (
        "[M3] Decidir y justificar el modelo fundacional",
        2, ["M3-modelos", "tipo:spike"],
        """### Por que
RF-M1 exige que la eleccion se justifique segun las caracteristicas medidas de los datos.

### Dato medido que condiciona la decision
El panel tiene 13 114 filas en 4 horas, con 9 165 en entrenamiento, y **420 ejemplos de la
clase minoritaria**. Eso es poco para un transformer entrenado desde cero, y empuja fuerte
hacia usar un modelo preentrenado y ajustarlo. Es un argumento medido, no una opinion, y va
al informe tal cual.

### Criterio de aceptacion
Decision escrita en `docs/07-bitacora-decisiones.md` con la alternativa descartada y el motivo.""",
    ),
    (
        "[M0] Seccion del pipeline en el documento",
        2, ["M0-infra", "tipo:doc", "entregable"],
        """### Que hacer
Extraccion, limpieza, EDA, feature engineering, seleccion de modelo, entrenamiento,
optimizacion de hiperparametros, evaluacion y despliegue. Cada paso con lo que realmente
hicimos, no con el diagrama generico del enunciado.

### Criterio de aceptacion
`docs/entregas/semana-2/m0-pipeline.md`, con la figura de arquitectura y las metricas
definidas.""",
    ),
    # ---------------------------------------------------------------- Sprint 3
    (
        "[M3] Modelo fundacional funcionando y evaluado",
        3, ["M3-modelos", "tipo:feature", "entregable"],
        """### Criterio de aceptacion
Cumple la interfaz `Modelo`, entrena con semilla fija, y tiene su fila en
`docs/evidencias/resultados.csv` producida por `evaluar_modelo()`. Comparado contra los tres
baselines y contra el modelo clasico de referencia.

### Cuidado
Si el F1 sale sospechosamente alto, desconfia antes de festejar. Casi siempre es fuga de
informacion. Pedile a M2 que corra `verificar_sin_fuga` sobre las caracteristicas que estas
usando.""",
    ),
    (
        "[M1] Modos sintetico e historico conectados al modelo real",
        3, ["M1-datos-app", "tipo:feature"],
        """### Criterio de aceptacion
La app muestra las predicciones del modelo fundacional junto a las etiquetas verdaderas, y el
selector de modelo permite alternar entre baseline y fundacional sobre el mismo periodo.""",
    ),
    (
        "[M2] Medicion de importancia de caracteristicas",
        3, ["M2-features", "tipo:feature", "entregable"],
        """### Por que
RF-F4. Con 420 ejemplos de la clase minoritaria, mas caracteristicas no es mejor. Hay que
demostrar cuales aportan.

### Criterio de aceptacion
Tabla ordenada por importancia con el metodo usado documentado, y una decision escrita sobre
cuales se conservan.""",
    ),
    (
        "[M0] Pruebas de deteccion: sintetico, entrenamiento y tiempo real",
        3, ["M0-infra", "tipo:feature", "entregable"],
        """### Por que
El enunciado las exige explicitamente en las semanas 3 y 4.

### Criterio de aceptacion
Las tres corren con un comando y dejan sus resultados en `docs/evidencias/` con fecha. El
modo tiempo real depende de la respuesta del profesor a la consulta 3.""",
    ),
    # ---------------------------------------------------------------- Sprint 4
    (
        "[M3] Modelo avanzado funcionando y evaluado",
        4, ["M3-modelos", "tipo:feature", "entregable"],
        """### Punto de decision
El **lunes** de esta semana se revisa el estado. Si el modelo avanzado no arranca, entra el
PM a apoyar. Esta previsto en el PRD como riesgo R2 y no es un fracaso: es el plan.

### Criterio de aceptacion
Misma interfaz, misma particion, misma funcion de metricas que el fundacional. Sin eso, la
comparacion no es una comparacion.

### Presupuesto (RNF-4)
Si entrenar supera las dos horas en la maquina mas lenta del equipo, se reduce el alcance del
modelo. No aceptamos que solo una persona pueda entrenarlo.""",
    ),
    (
        "[M1] Modo tiempo real en la aplicacion",
        4, ["M1-datos-app", "tipo:feature"],
        """### Bloqueado por
La consulta 3 al profesor: si el sistema confirma el giro w velas despues, o lo anuncia en el
momento. Son dos productos distintos.

### Criterio de aceptacion
RF-U3 y RF-U5: muestra siempre la fecha del dato, y si no hay conexion arranca con el ultimo
cacheado declarando su antiguedad.""",
    ),
    (
        "[M2] Ablaciones: aporta realmente el enfoque multivariante?",
        4, ["M2-features", "tipo:feature", "entregable"],
        """### Por que
Todo el planteo del enunciado descansa en que BTC, ETH, SOL, XRP y ADA aportan informacion
sobre LTC. Medirlo en vez de asumirlo es de lo mejor que podemos llevar al reporte final.

### Que hacer
Entrenar con y sin la familia de correlacion cruzada y comparar F1 macro.

### Criterio de aceptacion
Tabla con la diferencia medida. **Si no aporta, se dice.** Un resultado negativo bien medido
vale mas que uno positivo mal medido.""",
    ),
    (
        "[M0] Comparacion fundacional contra avanzado y decision final",
        4, ["M0-infra", "tipo:feature", "entregable"],
        """### Criterio, fijado antes de medir
Gana el de mayor F1 macro sobre prueba. Si la diferencia es **menor a 0.02 absoluto**, se
recomienda el fundacional por ser mas simple, y el avanzado se documenta igual.

Esta implementado en `decidir()` en `src/evaluacion/arnes.py` para que la decision no dependa
de quien mire la tabla.

### Criterio de aceptacion
Tabla comparativa, matrices de confusion de ambos, y la decision escrita en la bitacora.""",
    ),
    (
        "[M3] Optimizacion de hiperparametros de ambos modelos",
        4, ["M3-modelos", "tipo:feature", "entregable"],
        """### Por que
Es un paso explicito del pipeline del enunciado y no estaba en el backlog.

### Que hacer
Buscar la combinacion que maximice el rendimiento, de los dos modelos, con el mismo
procedimiento para que la comparacion siga siendo valida.

### La regla que no se puede romper
**La busqueda se hace contra validacion, nunca contra prueba.** Si se ajustan
hiperparametros mirando el conjunto de prueba, ese conjunto deja de ser datos no vistos y el
numero del informe queda inflado sin que se note.

`contracts/splits.py` ya separa los tres bloques con embargo entre ellos; usar la mascara de
validacion de ahi.

### Criterio de aceptacion
La rejilla explorada queda registrada, no solo el ganador. Los resultados van a
`docs/evidencias/resultados.csv` con su fecha, y el informe reporta el rendimiento final
sobre prueba, medido **una sola vez**, despues de fijar los hiperparametros.""",
    ),
    # ---------------------------------------------------------------- Sprint 5
    (
        "[Todos] Reporte final ensamblado",
        5, ["tipo:doc", "entregable"],
        """### Que hacer
Cada modulo entrega su seccion final; el PM ensambla, unifica estilo y revisa APA.

### Criterio de aceptacion
Documento completo con: diseno, rendimiento medido (Precision Direccional, F1 y
complementarias), y **analisis de limitaciones del enfoque con datos estaticos**, que el
enunciado pide explicitamente.

Todo numero del informe se regenera con un comando. Si uno no se puede reproducir, no entra.""",
    ),
    (
        "[Todos] Ensayo con exposicion cruzada",
        5, ["tipo:chore"],
        """### Por que
Calidad de la exposicion y comunicacion efectiva suman 33,3 % de la nota, lo mismo que
contenido y analisis juntos. Si llegamos con cuatro especialistas que solo saben defender su
parte, perdemos ahi.

### Que hacer
Cada persona expone el modulo de **otro**. No es trabajo compartido: cada quien sigue
construyendo lo suyo. Es un ensayo.

### Criterio de aceptacion
Ensayo completo cronometrado, y una lista de las preguntas incomodas que nos pueden hacer con
su respuesta preparada.""",
    ),
]


def correr(argumentos: list[str], entrada: str | None = None) -> tuple[int, str]:
    resultado = subprocess.run(
        argumentos, input=entrada, capture_output=True, text=True, encoding="utf-8"
    )
    return resultado.returncode, (resultado.stdout or "") + (resultado.stderr or "")


def existentes(recurso: str) -> set[str]:
    """Titulos ya creados, para que el script se pueda volver a correr sin duplicar."""
    if recurso == "labels":
        codigo, salida = correr(["gh", "label", "list", "-R", REPO, "--json", "name", "-L", "200"])
        return {e["name"] for e in json.loads(salida)} if codigo == 0 else set()
    if recurso == "milestones":
        codigo, salida = correr(["gh", "api", f"repos/{REPO}/milestones?state=all&per_page=100"])
        return {e["title"] for e in json.loads(salida)} if codigo == 0 else set()
    codigo, salida = correr(
        ["gh", "issue", "list", "-R", REPO, "--json", "title", "-L", "200", "--state", "all"]
    )
    return {e["title"] for e in json.loads(salida)} if codigo == 0 else set()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true", help="sin esto solo muestra que haria")
    argumentos = parser.parse_args()
    seco = not argumentos.aplicar

    if seco:
        print("MODO SECO. Nada se crea. Agregar --aplicar para ejecutar.\n")

    print(f"[1/3] Etiquetas ({len(ETIQUETAS)})")
    ya = existentes("labels")
    for nombre, color, descripcion in ETIQUETAS:
        if nombre in ya:
            print(f"  = {nombre}")
            continue
        print(f"  + {nombre}")
        if not seco:
            correr(
                ["gh", "label", "create", nombre, "-R", REPO,
                 "--color", color, "--description", descripcion, "--force"]
            )

    print(f"\n[2/3] Hitos ({len(SPRINTS)})")
    ya = existentes("milestones")
    for titulo, vence, descripcion in SPRINTS:
        if titulo in ya:
            print(f"  = {titulo}")
            continue
        print(f"  + {titulo}  (vence {vence})")
        if not seco:
            correr(
                ["gh", "api", f"repos/{REPO}/milestones", "-X", "POST",
                 "-f", f"title={titulo}", "-f", f"description={descripcion}",
                 "-f", f"due_on={vence}T23:59:59Z"]
            )

    print(f"\n[3/3] Issues ({len(BACKLOG)})")
    ya = existentes("issues")
    creados = 0
    for titulo, sprint, etiquetas, cuerpo in BACKLOG:
        if titulo in ya:
            print(f"  = {titulo}")
            continue
        print(f"  + [S{sprint}] {titulo}")
        if not seco:
            comando = ["gh", "issue", "create", "-R", REPO, "--title", titulo,
                       "--milestone", SPRINTS[sprint - 1][0], "--body-file", "-"]
            for etiqueta in etiquetas:
                comando += ["--label", etiqueta]
            codigo, salida = correr(comando, entrada=cuerpo.strip() + "\n" + HECHO)
            if codigo != 0:
                print(f"      FALLO: {salida.strip()[:160]}")
                continue
            creados += 1

    if seco:
        print("\nNada se creo. Volver a correr con --aplicar.")
        sys.exit(0)
    print(f"\nListo. {creados} issues creados.")
    print(f"https://github.com/{REPO}/issues")


if __name__ == "__main__":
    main()
