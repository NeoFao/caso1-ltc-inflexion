# Conclusión

## El resultado central de esta semana, sin adornos

**Ningún modelo profundo mejora al bosque aleatorio clásico.**

- El **bosque clásico** queda primero, con F1 macro **0,390498** y precisión direccional
  **0,103627**.
- **Chronos-Bolt** queda 0,021908 por debajo del bosque, con intervalo que incluye el cero: no se
  distingue de él.
- **iTransformer** queda por debajo del bosque en las cinco semillas.

**Y sobre este bloque, ninguno de los dos profundos supera al azar de forma distinguible.** Le ganan
en la media y el intervalo incluye el cero en los dos casos.

> **Esa última frase se acotó después, y conviene decirlo acá.** Medida sobre nueve tramos
> consecutivos —**7 311 observaciones** en vez de 1 959— la lectura **se parte en dos**:
> Chronos-Bolt **sí** supera al azar (+0,027769, intervalo que excluye el cero) y el iTransformer
> **sigue sin superarlo** ni con cuatro veces más observaciones.
>
> Lo que era «ninguno de los dos» resultó ser **uno de cada**. Y la mitad que queda más fuerte es la
> del avanzado: no superar al azar con 7 311 observaciones dice bastante más que no superarlo con
> 1 959. Está desarrollado en el informe final.

El enunciado sugiere que un modelo fundacional y un Transformer son las herramientas para este
problema. Medido con el mismo arnés, la misma partición y el mismo piso, no le ganan a un bosque
aleatorio.

---

## Por qué ese resultado se puede creer

Porque las tres cosas que lo harían dudoso se cerraron antes de medir:

**El criterio estaba escrito.** Cuando el margen y el intervalo discrepan manda el intervalo, y se
prefiere el modelo más simple. Eso se fijó antes de ver la tabla, no después.

**El piso no se eligió por conveniencia.** Los modelos se comparan contra el azar de la misma
corrida, que se mueve con los datos, y no contra un número fijo.

**Los hiperparámetros no se ajustaron buscando el mejor número.** El rango entre cinco semillas del
modelo avanzado es **0,030377**, que supera el umbral de decisión de **0,02**. Con esa dispersión,
elegir la mejor celda de una rejilla no selecciona la mejor configuración: selecciona **la celda a la
que le tocó la semilla más afortunada**. Por eso se promedian cinco semillas y se compara de forma
pareada.

---

## Una limitación del instrumento, encontrada midiendo

Uno de los intervalos de esta entrega **no se reproduce entre corridas**. Volviendo a medir
validación con el mismo código y los mismos datos, el intervalo del contraste entre el iTransformer y
el bosque cambió de lado, porque el límite vivía a menos de dos milésimas del cero.

**La causa está identificada y no es el remuestreo**, que está sembrado y es determinista dadas las
predicciones: lo que se mueve es el iTransformer, que no reproduce entre procesos.

Y el fondo no es fragilidad: el remuestreo pareado resamplea las **filas** condicionando en **un solo
sorteo del entrenamiento**. Cuando el sorteo del entrenamiento es la fuente dominante de variación,
el intervalo de una corrida no es un instrumento frágil — **es el instrumento equivocado**.

Se decidió qué hacer con eso **antes** de tocar el bloque de prueba: donde entre un modelo que no
reproduce, el intervalo se reporta pero no decide, y el peso lo lleva la estabilidad del signo entre
semillas.

**El alcance está acotado y medido:** el bosque y el `baseline_aleatorio` reproducen bit a bit entre
procesos, con la misma huella SHA-256 de las 1 959 predicciones. La comparación de la que depende el
veredicto del proyecto no está afectada.

---

## Lo que sigue

La Semana 5 mide **una sola vez** sobre el bloque de prueba, con el protocolo escrito de antemano y
las tres lecturas posibles fijadas antes de ver el número. No hay una segunda corrida.

**Y la expectativa se dice de antemano, para que no se lea como excusa después:** no hay razón para
esperar que el bloque de prueba mejore lo de validación. Esperar que datos no vistos favorezcan a un
modelo más que los datos con los que se eligió es al revés de como funciona.
