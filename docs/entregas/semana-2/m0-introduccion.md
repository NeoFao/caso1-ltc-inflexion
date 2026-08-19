# Introducción

**Autor:** Fabrizio Espinoza Arce · Ensamblaje

Este documento constituye la segunda entrega del Caso N.º 1 y continúa el marco teórico presentado el 18 de agosto. Su objeto es doble: revisar los modelos estadísticos y de aprendizaje automático aplicables a series temporales, y definir el procedimiento completo de desarrollo del modelo de puntos de inflexión.

La primera entrega estableció qué se quiere predecir y con qué se va a medir el éxito. Esta establece **con qué se va a predecir y en qué orden**, que son las dos preguntas que quedaban abiertas.

Entre una entrega y otra el proyecto tomó una decisión que conviene declarar desde el inicio porque afecta a todo lo que sigue. Los tres parámetros que definen el problema —la granularidad de las observaciones, la ventana `w` que determina qué es un giro y el horizonte `h` de pronóstico— **dejaron de ser provisionales el 18 de agosto** y quedaron fijados en velas de 4 horas, `w = 7` y `h = 1`. Los tres salen de medición y cada uno de un criterio distinto, fijado antes de mirar el resultado; el estudio completo está en el repositorio del proyecto.

Los números de la entrega anterior se midieron con velas diarias y `w = 5`, que era la configuración vigente entonces, y no se regeneraron. Ninguno de aquellos resultados depende de la etiqueta: la estacionariedad, la autocorrelación, la volatilidad y la correlación cruzada se calculan sobre precios y retornos. Cuando este documento compara con un valor de la entrega anterior, indica con qué configuración se midió cada uno.

Se mantienen los dos criterios metodológicos declarados en la primera entrega. **Ningún concepto se expone únicamente como definición**: cada afirmación que admite comprobación se acompaña de su verificación sobre los datos del proyecto, y lo que no se ha medido se declara como no medido. Y **los procedimientos se validan primero sobre casos donde la respuesta correcta la fijamos nosotros**, antes de aplicarlos sobre datos reales.

La exposición se organiza en dos bloques. El primero revisa los modelos: los fundacionales de series de tiempo, VTA, FinLSPM, CryptoMamba y el Transformer, y cierra justificando cuál se elige y por qué. El segundo recorre las ocho etapas del procedimiento de desarrollo —extracción, limpieza, análisis exploratorio, ingeniería de características, partición, selección del modelo, entrenamiento y evaluación—, declarando en cada una qué está construido y medido y qué queda pendiente.
