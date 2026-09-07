# Informe final — Caso N.º 1

**Cubre las semanas 3, 4 y 5 del enunciado.** El trabajo está hecho y medido; lo que faltaba era el documento que lo reúne.

---

## Qué pide el enunciado, textual

> **Un modelo de clasificación entrenado** (primero un modelo fundacional y segundo un Transformer) capaz de generar predicciones de puntos de inflexión para LTC.
>
> **Un informe técnico** que documente el proceso de diseño, el rendimiento del modelo —incluyendo la Precisión Direccional y otras métricas complementarias como F1-Score— y un análisis de las limitaciones del enfoque con datos estáticos.

Y por semana:

| Semana | Qué pide |
|---|---|
| **3** | Desarrollo del modelo fundacional · presentación · pruebas de detección con datos sintéticos, de entrenamiento y en tiempo real |
| **4** | Desarrollo del modelo avanzado · presentación · las mismas tres pruebas |
| **5** | Presentación del reporte |

---

## Estado de cada pieza

| Pieza | Estado | Dónde está |
|---|---|---|
| Modelo fundacional entrenado | **Hecho** | Chronos-Bolt, `src/modelos/fundacional.py`, issue #23 |
| Modelo avanzado entrenado | **Hecho** | iTransformer, `src/modelos/avanzado.py`, issue #27 |
| Prueba de detección: sintético | **Hecha** | 187/187 giros recuperados |
| Prueba de detección: entrenamiento | **Hecha** | F1 macro 0,953353 contra 0,331638 del azar |
| Prueba de detección: tiempo real | **Hecha** | 500 velas de a una, predicciones idénticas al bloque (D21) |
| Rendimiento sobre datos no vistos | **Pendiente** | Se mide el **lunes 7**, una vez (D18, fecha nueva por [D23](../../DECISIONES.md)) |
| Informe técnico | **Este documento** | Secciones 2 y 3 escritas; el resto, al rellenar la cifra |

---

## Estructura, y por qué esta

El informe no repite los marcos teóricos ya entregados: los cita. Lo que aporta es **lo que se construyó, lo que se midió y lo que no se pudo afirmar**.

| Sección | Qué contiene | Fuente del material |
|---|---|---|
| Introducción | Qué se construyó y qué se puede afirmar hoy | nueva |
| 1. Diseño | Los tres parámetros, la partición con embargo, y por qué cada decisión | D1–D3, `docs/04` |
| 2. Ingeniería de características | Las cinco familias, por qué ninguna es precio crudo, y la importancia medida con su piso de ruido | **escrita**: [`02-ingenieria-de-caracteristicas.md`](02-ingenieria-de-caracteristicas.md) |
| 3. Los dos modelos | Fundacional y avanzado: qué son, por qué se eligieron, qué costaron | **escrita**: [`m3-modelos.md`](m3-modelos.md) |
| 4. Pruebas de detección | Las cuatro, incluida la de tiempo real que la D21 desbloqueó | `pruebas-deteccion.json`, D21 |
| 5. Rendimiento | La comparación sobre validación y **la medición única sobre prueba** | la mitad de modelos, en [`m3-modelos.md`](m3-modelos.md); falta la celda de la corrida |
| 6. Limitaciones | Lo que el enfoque no puede, incluido el análisis con datos estáticos que pide el enunciado | `docs/06`, D15, D20, **D24** |
| Conclusiones | Lo que se sostiene y lo que no | nueva |

---

## Las tres limitaciones que el informe tiene que declarar

El enunciado pide explícitamente **«un análisis de las limitaciones del enfoque con datos estáticos»**. Las tres están medidas y no son opiniones:

**1. Los activos de apoyo aportan poco, y no lo mismo en las dos familias.** La [D24](../../DECISIONES.md) resolvió esto y la limitación **se declara por familia, no en general**:

| Familia | ¿Se distingue del azar? | Evidencia |
|---|---|---|
| **Bosque** | **No.** Diferencia de 0,00078 en F1 macro, con el signo cambiando entre semillas y del mismo tamaño que un control que añade columnas duplicadas | #62, D20 |
| **Avanzado** | **Sí.** Media +0,012586, intervalo pareado [0,000434 , 0,044067] que excluye el cero, y signo positivo en las cinco semillas | `m3-modelos-profundos-4h-w7-h1.json` |

Las dos mitades van juntas o ninguna: **aportar no es rescatar.** El avanzado con los cinco apoyos sigue quedando por debajo del bosque sin ellos, y la magnitud queda por debajo del umbral de 0,02 con el que preferiríamos una configuración sobre otra (D5).

El mecanismo está medido y explica el tamaño: los seis activos son fuertemente proporcionales entre sí —de +0,5175 a +0,8300— y **no existe ninguna relación inversa**, así que traen poca información que LTC no tenga (D20).

> **De dónde salía la contradicción.** El esqueleto declaraba esta limitación en general citando el 0,00078, que es del bosque. La D14 concluía lo mismo sobre el avanzado, pero aplicando el umbral de la D5 —una convención para *elegir* entre modelos— a una pregunta de *distinguibilidad*, que responden las tres condiciones de la D16. La D24 corrige esa lectura sin reescribir la D14, y con la evidencia que la D14 ya tenía delante: no hizo falta medir nada nuevo.

**2. Ningún modelo profundo mejora al bosque clásico.** iTransformer queda entre 0,042894 y 0,044792 por debajo; Chronos-Bolt no se distingue de él. **Esta mitad es sólida**: en las tres corridas que tenemos, la diferencia es negativa y del mismo tamaño, y ningún modelo profundo le gana al bosque en ninguna.

> ⚠️ **Lo que no se sostiene es la mitad fuerte: «con intervalo que excluye el cero».** El ensayo en seco del 07/09 volvió a medir validación con el mismo código, los mismos datos y las mismas cinco semillas — **dos veces**, y el intervalo incluyó el cero **las dos**:
>
> | Corrida | Diferencia | Intervalo 95 % | ¿Excluye el cero? |
> |---|---|---|---|
> | Evidencia comprometida (21/08) | −0,044792 | [−0,085204 , **−0,001457**] | **Sí** |
> | Ensayo en seco (07/09) | −0,042894 | [−0,081945 , **+0,001996**] | No |
>
> La primera corrida del ensayo, veinte minutos antes, dio lo mismo y con la misma conclusión. Se adjunta la evidencia de la segunda en `m0-ensayo-en-seco-validacion-4h-w7-h1.json`, con nombre propio para que **no se confunda con una medición citable**: es un ensayo, no una corrida del protocolo.
>
> El límite superior vive a menos de 0,002 del cero, así que el veredicto binario se da vuelta aunque la cifra casi no se mueva. **Un resultado que no se reproduce no se puede presentar como el que se afirma con seguridad**, y la sección de M3 hoy lo llama *«el único resultado de esta tabla que se puede afirmar con seguridad»*.
>
> **Queda una alternativa por descartar** antes de atribuirlo del todo a que el iTransformer no es determinista: la corrida del 21/08 incluía las variantes y el ensayo llevaba `--sin-variantes`. La causa la confirma M3; la conclusión para el informe no cambia con ninguna de las dos.
>
> Es la misma forma que la limitación 1 y la misma lección de la [D24](../../DECISIONES.md): **la condición 2 de la [D16](../../DECISIONES.md) es un umbral binario, y sobre un límite que roza el cero decide el ruido y no el modelo.**

**3. El puente de trayectoria a etiqueta amplifica diferencias mínimas.** El etiquetador exige catorce comparaciones estrictas, y sobre un pronóstico suave un vecino a 10⁻¹¹ cambia la clase (D15).

---

## Lo que falta para cerrarlo

1. **La medición sobre el bloque de prueba.** Es la única cifra que el informe todavía no tiene. Estaba prevista para el sábado 5 y no se corrió por tres defectos en el camino; la [D23](../../DECISIONES.md) la movió al **lunes 7** y los tres están arreglados y medidos (#101, #105).
2. **Las secciones que faltan**: introducción, 1 (diseño), 4 (pruebas de detección), la celda de prueba en la 5, la 6 y las conclusiones.

Ya no falta ninguna respuesta del profesor: la consulta **no se envía** y las dos preguntas abiertas las resolvió el equipo — qué muestra la vista en tiempo real ([D21](../../DECISIONES.md)) y qué se entrega y cuándo ([D22](../../DECISIONES.md)).

Tampoco falta ya resolver la contradicción de la limitación 1: la [D24](../../DECISIONES.md) la declaró por familia.

El esqueleto existe para que rellenar no sea escribir desde cero.
