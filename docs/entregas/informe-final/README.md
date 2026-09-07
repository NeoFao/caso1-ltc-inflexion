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
| Rendimiento sobre datos no vistos | **Medido** | 07/09/2026, **una sola vez**. Dos de las tres condiciones: no se puede afirmar detección |
| Informe técnico | **Este documento** | **Completo.** La 5.4 se rellenó con la cifra de la corrida |

---

## Estructura, y por qué esta

El informe no repite los marcos teóricos ya entregados: los cita. Lo que aporta es **lo que se construyó, lo que se midió y lo que no se pudo afirmar**.

| Sección | Archivo | Autor | Quién la revisa |
|---|---|---|---|
| Introducción | [`00-introduccion.md`](00-introduccion.md) | Fabrizio (M0) | el equipo |
| 1. Diseño | [`01-diseno.md`](01-diseno.md) | Fabrizio (M0) | **Alejandro** (etiquetado y ventana) |
| 2. Ingeniería de características | [`02-ingenieria-de-caracteristicas.md`](02-ingenieria-de-caracteristicas.md) | Alejandro (M2) | Fabrizio |
| 3. Los dos modelos | [`m3-modelos.md`](m3-modelos.md) | Isaac (M3) | Fabrizio |
| 4. Pruebas de detección | [`04-pruebas-deteccion.md`](04-pruebas-deteccion.md) | Fabrizio (M0) | **Jose Pablo** (tiempo real y la app) |
| 5. Rendimiento | [`05-rendimiento.md`](05-rendimiento.md) | Fabrizio (M0), sobre material de M3 | **Isaac** (5.2 y 5.3) |
| 6. Limitaciones | [`06-limitaciones.md`](06-limitaciones.md) | Fabrizio (M0) | **Isaac** (6.2, 6.3) y **Alejandro** (6.1, 6.4) |
| Conclusiones | [`99-conclusiones.md`](99-conclusiones.md) | Fabrizio (M0) | el equipo |

**Todas escritas, y la 5.4 rellenada.** La corrida única se hizo el 07/09 y el informe reporta la
primera y única cifra que salió, con la lectura que estaba escrita de antemano.

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

> ⚠️ **La fila «Avanzado · Sí» tampoco se reproduce, y es la que la D24 fija.** El ensayo en seco del 07/09 volvió a medir validación **con** variantes, dos veces, y aplicó las tres condiciones de la [D16](../../DECISIONES.md) al aporte de los activos de apoyo:
>
> | Condición | Comprometido (21/08) | Ensayo, 2.ª corrida (07/09) |
> |---|---|---|
> | 1 · La diferencia es positiva | +0,012586 | **+0,021870** · se reproduce |
> | 2 · El intervalo excluye el cero | [**+0,000434** , +0,044067] · **sí** | [**−0,001736** , +0,045490] · **no** |
> | 3 · El signo no cambia en cinco semillas | positivo en las cinco | positivo en las cinco · se reproduce |
>
> **Dos de las tres se reproducen. La 2 no**, ni en esta corrida ni en la anterior del mismo ensayo. El límite inferior comprometido vive a **0,0004 del cero**.
>
> **La causa está identificada.** El remuestreo pareado *sí* está sembrado (`np.random.default_rng(semilla)` en `src/features/incertidumbre.py`), así que el intervalo es determinista **dadas las predicciones**. Lo que se mueve es el iTransformer, que no es determinista al entrenar. Por eso el mismo efecto aparece en dos comparaciones distintas del mismo archivo: esta y la de la limitación 2.
>
> **Lo que esto no toca:** el razonamiento de la D24 —que el umbral de la D5 respondía la pregunta equivocada— sigue siendo correcto, y la condición 3, que es la que la propia D24 argumenta como discriminante, **se reproduce**. Lo que no se sostiene es la frase «las tres se cumplen».
>
> **Y lo que urge:** sobre el bloque de prueba hay **una sola corrida**. Cualquier veredicto que salga de la condición 2 en un contraste donde entre el iTransformer será un veredicto que una segunda corrida no reproduciría — y no habrá segunda corrida. **Esto lo decide el equipo antes de correr**, no después de ver el número.
>
> Evidencia: `m0-ensayo-en-seco-validacion-con-variantes-4h-w7-h1.json`.
>
> **Resuelto por la [D25](../../DECISIONES.md).** Donde entre un modelo que no reproduce, la condición 2 **se reporta pero no decide**, y el peso lo lleva la condición 3. El veredicto de la D24 queda retirado; su corrección de criterio sigue en pie.
>
> **Y el alcance está acotado, medido:** el bosque y el `baseline_aleatorio` reproducen **bit a bit entre procesos** —misma huella SHA-256 de las 1 959 predicciones de validación en tres procesos distintos, en `m0-reproducibilidad-predicciones-4h-w7-h1.json`—. La regla de la sección 5 del protocolo, que es la que decide el veredicto del proyecto, **no está afectada**. El problema vive solo en los contrastes donde entra el iTransformer.

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
> El límite superior vive a menos de 0,002 del cero, así que el veredicto binario se da vuelta aunque la cifra casi no se mueva. **Un resultado que no se reproduce no se puede presentar como el que se afirma con seguridad.** La sección de M3 lo llamaba *«el único resultado de esta tabla que se puede afirmar con seguridad»*; **ya no**: la [D25](../../DECISIONES.md) lo corrigió y ahora lo que sostiene esa fila es el signo estable en las cinco semillas, no el intervalo de una corrida.
>
> **Queda una alternativa por descartar** antes de atribuirlo del todo a que el iTransformer no es determinista: la corrida del 21/08 incluía las variantes y el ensayo llevaba `--sin-variantes`. La causa la confirma M3; la conclusión para el informe no cambia con ninguna de las dos.
>
> Es la misma forma que la limitación 1 y la misma lección de la [D24](../../DECISIONES.md): **la condición 2 de la [D16](../../DECISIONES.md) es un umbral binario, y sobre un límite que roza el cero decide el ruido y no el modelo.**

**3. El puente de trayectoria a etiqueta amplifica diferencias mínimas.** El etiquetador exige catorce comparaciones estrictas, y sobre un pronóstico suave un vecino a 10⁻¹¹ cambia la clase (D15).

---

## Lo que falta para cerrarlo

**La medición ya está hecha.** Se corrió el 07/09/2026, una sola vez, y el pestillo lo registra con
`n_corridas: 1`.

1. **Que cada quien revise lo suyo**, según la columna «quién la revisa» de la tabla de arriba. Las
   secciones están escritas; lo que falta es que quien midió cada cosa confirme que está bien
   contada.
2. **La revisión de QA del flujo terminado** ([#115](https://github.com/NeoFao/caso1-ltc-inflexion/issues/115)),
   que es la única capa que ve alguien de fuera.
3. **El ensayo de la exposición**, cronometrado y con la rotación
   ([#32](https://github.com/NeoFao/caso1-ltc-inflexion/issues/32)).

Ya no falta ninguna respuesta del profesor: la consulta **no se envía** y las preguntas abiertas las
resolvió el equipo — qué muestra la vista en tiempo real ([D21](../../DECISIONES.md)), qué se
entrega y cuándo ([D22](../../DECISIONES.md)) y en qué formato ([D26](../../DECISIONES.md)).

Tampoco falta resolver la contradicción de la limitación 1: la [D24](../../DECISIONES.md) la declaró
por familia y la [D25](../../DECISIONES.md) retiró su veredicto.
