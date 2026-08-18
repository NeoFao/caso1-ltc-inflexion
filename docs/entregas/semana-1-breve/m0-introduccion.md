# Introducción

**Autor:** Fabrizio Espinoza Arce · Ensamblaje

Este documento constituye el marco teórico del Caso N.º 1, primera de las cinco entregas del proyecto. Establece los fundamentos sobre series de tiempo y sobre criptoactivos que sustentan el desarrollo posterior de un modelo de aprendizaje automático supervisado para el pronóstico de puntos de inflexión en el precio de Litecoin.

El problema es clasificar cada instante de la serie de precios de LTC en una de tres categorías —máximo local, mínimo local o zona de continuidad— usando como variables de apoyo las cinco criptomonedas de mayor capitalización con función sistémica: Bitcoin, Ethereum, Solana, XRP y Cardano. La dificultad no está en la formulación, que es una clasificación multiclase, sino en las propiedades de las series: ausencia de estacionariedad, volatilidad elevada y variable en el tiempo, y ausencia de un anclaje de valoración fundamental que permita anticipar reversiones por argumentos económicos.

El documento adopta dos criterios metodológicos que conviene declarar desde el inicio, porque condicionan la forma de todas las secciones.

**Primero: ningún concepto se expone únicamente como definición.** Cada propiedad enunciada se acompaña de su verificación sobre los datos del proyecto y el valor obtenido se reporta explícitamente. Cuando una afirmación no ha sido comprobada, se indica que no lo ha sido en lugar de omitirse.

**Segundo, sugerido por el profesor durante la sesión de trabajo:** varios conceptos se ilustran mediante **series construidas sintéticamente por los autores**, con la volatilidad y la correlación fijadas de antemano. El propósito es verificar que los procedimientos detectan aquello que declaran detectar antes de aplicarlos sobre datos reales, donde la respuesta correcta se desconoce. Las series construidas se identifican como tales en cada figura, y ninguna afirmación sobre el mercado se apoya en ellas.

La exposición se organiza en tres bloques: los fundamentos de series de tiempo, los criptoactivos y su punto de inflexión, y las métricas de evaluación, que exigen tratamiento propio por el desbalance estructural de las clases.

Los datos provienen de la interfaz pública de Binance y comprenden 2 185 observaciones diarias del precio de cierre de las seis criptomonedas, entre el 11 de agosto de 2020 y el 4 de agosto de 2026. La ventana está acotada por Solana, cuya cotización se inicia en la primera de esas fechas: un panel multivariante exige que las seis series existan simultáneamente en cada instante.
