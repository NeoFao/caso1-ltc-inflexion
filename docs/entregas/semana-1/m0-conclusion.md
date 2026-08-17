# Conclusiones

**Autor:** Fabrizio Espinoza Arce · Ensamblaje

El marco teórico desarrollado permite extraer cuatro conclusiones que condicionan de manera directa el diseño del modelo, y que se enuncian aquí porque no son consecuencia de la literatura consultada sino de las mediciones realizadas sobre los datos del proyecto.

**Primera. La transformación a retornos no es una convención, sino una consecuencia medida.** Ninguna de las seis series rechaza la hipótesis de raíz unitaria al trabajar sobre precios en nivel, mientras que las seis la rechazan al hacerlo sobre retornos. La autocorrelación en el primer rezago pasa de 0,991 sobre niveles a −0,036 sobre retornos, lo que confirma el mismo hecho desde un ángulo distinto. En consecuencia, las características del modelo se construyen sobre retornos y sobre estadísticos normalizados por ventana, y no sobre magnitudes absolutas de precio.

**Segunda. La ausencia de autocorrelación lineal en los retornos justifica el enfoque del proyecto.** De los cuarenta rezagos examinados, únicamente tres exceden la banda de confianza del 95 %. Un modelo lineal construido sobre precios rezagados dispondría, por tanto, de muy poca estructura que explotar. Lejos de constituir un resultado negativo, esta observación es el argumento medido que sustenta el recurso a modelos no lineales y multivariantes, que es precisamente el planteamiento del caso.

**Tercera. La dependencia entre criptoactivos existe, pero debe medirse sobre retornos.** Calculada sobre precios en nivel, la correlación entre pares recorre un rango de 0,126 a 0,888 y produce un ordenamiento económicamente implausible, al atribuir a Litecoin una relación casi nula con Bitcoin. Calculada sobre retornos, el rango se estrecha a 0,475–0,806 y el ordenamiento resulta coherente con la estructura del mercado. La magnitud de esas correlaciones es lo que justifica que el problema se plantee como multivariante: si Litecoin se moviera de forma independiente, las cinco variables de apoyo serían redundantes.

**Cuarta. El desbalance de clases es estructural y determina la elección de las métricas.** Puesto que dos máximos no pueden situarse a menos de `w+1` observaciones de distancia, a lo sumo una de cada `w+1` velas puede clasificarse como máximo. El desbalance no es, por tanto, un defecto de la muestra que pueda corregirse recogiendo mejor los datos, sino una propiedad permanente del problema. Su consecuencia es directa: un modelo que no detecte ningún punto de inflexión alcanza una exactitud del 86,9 %, de modo que la exactitud queda descartada como métrica de decisión en favor del F1 macro y la Precisión Direccional.

## Limitaciones

Tres advertencias que conviene explicitar, y que se retomarán en las entregas siguientes.

Los precios proceden de un único mercado y no de un promedio ponderado de la industria, de manera que los puntos de inflexión identificados lo son respecto de la formación de precios de esa plaza. La ventana temporal, acotada por el listado de Solana, sacrifica aproximadamente un tercio del historial disponible de Litecoin a cambio de poder plantear el problema como multivariante. Y la definición operativa del punto de inflexión depende de una ventana cuyo valor se fija por criterio del equipo, de modo que la escala del fenómeno estudiado es una elección metodológica y no una propiedad del mercado.

## Trabajo siguiente

La segunda entrega aborda el marco teórico de los modelos estadísticos y de aprendizaje automático aplicables a series temporales, así como la definición del procedimiento completo de desarrollo: extracción y limpieza de datos, análisis exploratorio, ingeniería de características, selección del modelo, entrenamiento, optimización de hiperparámetros y evaluación. Las decisiones sobre granularidad de las observaciones y sobre los parámetros que definen el punto de inflexión se documentan en esa entrega, por corresponder a la etapa de extracción de datos del procedimiento.
