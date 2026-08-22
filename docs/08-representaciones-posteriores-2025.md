# ¿Aporta una representación posterior a 2025 sobre las características clásicas?

**Autor:** Alejandro Zamora (M2) · **Issue:** [S2-M2-02](https://github.com/NeoFao/caso1-ltc-inflexion/issues/35)

> **Estado.** El arnés está construido y validado con dos controles. **La extracción real
> está pendiente** y depende de M3. Enchufar un extractor es escribir una clase que herede de
> `Extractor` y agregar una línea al registro; nada del arnés cambia.

---

## 1. Qué pide el enunciado y qué teníamos

El enunciado exige *"utilizar herramientas State of the Art, mayores a 2025"*. Todo lo que
produce `construir()` es clásico: rezagos, retornos, volatilidad, correlación móvil e
indicadores técnicos. Ninguna de esas familias es posterior a 2025.

La vía coherente con el resto del proyecto es usar un **modelo fundacional congelado como
extractor de representaciones** y medir si sus columnas aportan algo sobre las clásicas.

**Esto no es lo que ya hace M3, y conviene decirlo antes de que alguien lo confunda.** En la
D12, Chronos-Bolt se usa como **pronosticador**: predice la trayectoria y se le aplica
`etiquetar()` del contrato. La propia D12 declara que la vía de "extractor de representaciones
más cabeza de clasificación" se descartó por costo/beneficio. Aquí se mide justamente esa otra
vía. Son complementarias.

## 2. Por qué el arnés existe antes que el extractor

Porque si esperara, el issue se quedaría sin sección.

Un arnés a medias esperando una pieza ajena no es entregable. **Un arnés completo con la
extracción declarada como pendiente sí lo es**: dice qué se probó, cómo se probó, y qué falta
enchufar. Si nadie llega a tiempo, el informe puede reportar eso con honestidad — que también
responde al requisito, como dice el propio issue.

## 3. La interfaz

```python
class Extractor(ABC):
    nombre: str
    def ajustar(self, panel, mascara_entrenamiento) -> Extractor: ...
    def transformar(self, panel) -> pd.DataFrame: ...
```

Tres exigencias, cada una por un riesgo concreto:

1. **`ajustar` recibe la máscara de entrenamiento y es obligatoria.** Misma forma que
   `Escalador.ajustar()`. Un extractor ajustado sobre el panel completo mete fuga aunque su
   transformación parezca inocente, y la fuga no se manifiesta como error sino como métricas
   excelentes.
2. **`transformar` devuelve solo columnas nuevas.** El arnés concatena. Así puede medir el
   aporte marginal sin depender de que el extractor recuerde incluir las clásicas.
3. **Los nombres llevan el prefijo del extractor.** Dos extractores con columnas homónimas son
   el defecto que ya nos costó los PR #63, #68 y #74.

El arnés además rechaza en el acto una tabla con índice distinto al del panel o con columnas que
choquen con las clásicas, y verifica el extractor contra fuga con `verificar_sin_fuga()`. Eso
último importa especialmente aquí: un modelo de pronóstico congelado recibe una serie entera, y
darle más contexto del debido es fácil y silencioso.

## 4. Los dos controles

**El relleno no es ruido aleatorio, y es deliberado.** Con ruido, un arnés correcto y uno roto
darían resultados igual de plausibles. Hay una prueba que verifica que el extractor de relleno no
use el generador aleatorio.

### Control 1 — el arnés reproduce lo conocido

`ExtractorNulo` no agrega ninguna columna. Entonces la rama "con representación" tiene que dar
exactamente lo mismo que la rama "sin", y ambas el F1 macro ya publicado:

```
publicado (M3 en el #63, M2 en el #62)   0.390497720487045
obtenido por el arnés                    0.390497720487045
```

Idéntico. **Si no lo fuera, `generar_evidencia()` se detiene sin escribir**, porque ninguna
medición posterior sobre una representación real sería confiable.

### Control 2 — cuánta resolución tiene el arnés

`ExtractorEco` reemite ocho columnas que ya existen, con otro nombre. Información nueva: cero.
Lo que mide es cuánto se mueve el resultado por el **solo hecho de agregar columnas**.

**Tabla 1.** Efecto de agregar 8 columnas redundantes, por semilla del bosque.

| Semilla | Sin | Con | Diferencia |
|---|---|---|---|
| 0 | 0,39050 | 0,37213 | **−0,01837** |
| 1 | 0,37387 | 0,36602 | −0,00785 |
| 2 | 0,38142 | 0,37946 | −0,00196 |
| 3 | 0,38541 | 0,39143 | +0,00601 |
| 4 | 0,37367 | 0,39940 | **+0,02573** |
| | | **media** | **+0,00071** |

**Este resultado es una advertencia, y es lo más útil que produjo este arnés hasta ahora.**

La media es prácticamente cero, que es lo correcto: ocho columnas redundantes no aportan nada. Pero
el **rango va de −0,018 a +0,026**, más de cuatro centésimas de amplitud, con el umbral de decisión
del equipo en 0,02.

Dicho de otro modo: **con una sola semilla, agregar columnas que no contienen ninguna información
nueva puede producir una "mejora" de +0,026 que cruza el umbral.** Cualquiera que enchufe un
extractor, mida una vez y reporte el número, va a reportar ruido de reentrenamiento.

Por eso `evaluar_extractor()` corre cinco semillas por defecto y expone `cambia_de_signo`. No es
prolijidad: es el mínimo para que el arnés pueda distinguir un efecto de un accidente.

Es la misma lección que en S4-M2-01, pero medida aquí **antes** de tener nada que medir, en lugar
de descubrirla sobre un resultado que ya queríamos creer.

## 5. Lo que falta y quién lo hace

1. **Un extractor real** que herede de `Extractor` y produzca representaciones de un modelo
   fundacional congelado. Chronos-Bolt es el candidato natural, por la D12.
2. **Correr `evaluar_extractor()` con él.** No requiere tocar el arnés.

## 6. Qué se podrá afirmar, y qué no

Cuando el extractor llegue, el arnés produce: la diferencia con su intervalo por remuestreo
pareado, las cinco semillas, y la bandera `se_puede_afirmar_que_aporta`, que exige **las tres
cosas a la vez** — intervalo que excluya el cero, diferencia positiva, y signo estable entre
semillas.

Si no aporta, se dice y se descarta dejando escrito que se probó. El issue lo autoriza
explícitamente, y con el Control 2 en la mano esa conclusión es defendible: sabemos qué tamaño de
efecto este arnés puede y no puede distinguir.

**Lo que este documento no dice** es si una representación posterior a 2025 aporta. Dice que si no
aporta lo vamos a poder afirmar, y que si aporta, no va a ser un artefacto del montaje.

---

> **Nota sobre reproducibilidad.** Todo sale de `uv run python -m src.features.representacion`,
> que deja `docs/evidencias/m2-representacion-4h-w7-h1.json`. El script no escribe nada si el
> Control 1 no reproduce.
