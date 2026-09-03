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
| Prueba de detección: tiempo real | **Bloqueada** | Depende de la consulta al profesor |
| Rendimiento sobre datos no vistos | **Pendiente** | Se mide el sábado 5, una vez (D18) |
| Informe técnico | **Este documento** | En construcción |

---

## Estructura, y por qué esta

El informe no repite los marcos teóricos ya entregados: los cita. Lo que aporta es **lo que se construyó, lo que se midió y lo que no se pudo afirmar**.

| Sección | Qué contiene | Fuente del material |
|---|---|---|
| Introducción | Qué se construyó y qué se puede afirmar hoy | nueva |
| 1. Diseño | Los tres parámetros, la partición con embargo, y por qué cada decisión | D1–D3, `docs/04` |
| 2. Ingeniería de características | Las cinco familias, por qué ninguna es precio crudo, y la importancia medida con su piso de ruido | `docs/07`, D6 |
| 3. Los dos modelos | Fundacional y avanzado: qué son, por qué se eligieron, qué costaron | D12, D14, `semana-2/m3-modelos.md` |
| 4. Pruebas de detección | Las tres del enunciado, con la tercera declarada como bloqueada | `pruebas-deteccion.json` |
| 5. Rendimiento | La comparación sobre validación y **la medición única sobre prueba** | pendiente del sábado |
| 6. Limitaciones | Lo que el enfoque no puede, incluido el análisis con datos estáticos que pide el enunciado | `docs/06`, D15, D20 |
| Conclusiones | Lo que se sostiene y lo que no | nueva |

---

## Las tres limitaciones que el informe tiene que declarar

El enunciado pide explícitamente **«un análisis de las limitaciones del enfoque con datos estáticos»**. Las tres están medidas y no son opiniones:

**1. Los activos de apoyo no aportan de forma distinguible.** Diferencia de 0,00078 en F1 macro, con el signo cambiando entre semillas, y del mismo tamaño que un control que añade columnas duplicadas. El mecanismo está medido: los seis activos son fuertemente proporcionales entre sí —de +0,5175 a +0,8300— y **no existe ninguna relación inversa**, así que traen poca información que LTC no tenga (D20).

**2. Ningún modelo profundo mejora al bosque clásico.** iTransformer queda 0,0448 por debajo con intervalo que excluye el cero; Chronos-Bolt no se distingue de él.

**3. El puente de trayectoria a etiqueta amplifica diferencias mínimas.** El etiquetador exige catorce comparaciones estrictas, y sobre un pronóstico suave un vecino a 10⁻¹¹ cambia la clase (D15).

---

## Lo que falta para cerrarlo

1. **La medición sobre el bloque de prueba**, sábado 5. Es la única cifra que el informe todavía no tiene.
2. **La respuesta del profesor** sobre tiempo real y sobre el calendario.
3. **Redactar las secciones**, domingo 6 y lunes 7.

El esqueleto existe para que el domingo sea rellenar y no escribir desde cero.
