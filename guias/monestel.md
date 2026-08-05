# Guía de Jose Pablo — M1 · Datos, diagnóstico y aplicación

## Qué es tuyo

```
src/diagnostico/     pruebas estadísticas sobre las series
src/visual/          el estilo de figuras de todo el proyecto y los gráficos
app/                 la aplicación web (arranca en la semana 2)
```

**Qué no tocás:** `contracts/`, `src/panel/`, `src/features/`, `src/modelos/`, `src/evaluacion/`. Si necesitás algo de ahí, lo pedís.

## Tu papel en una frase

Sos el que responde **"¿cómo son realmente estos datos?"** con números y figuras, y después el que hace que todo el proyecto se pueda ver.

Tu módulo es el que sostiene el marco teórico de la Semana 1: nadie escribe "las series de cripto no son estacionarias" sin la tabla que lo demuestre, y esa tabla la producís vos.

---

## Antes de empezar

El panel ya existe y ya está medido. No tenés que descargar nada:

```bash
uv run python -c "import pandas as pd; p=pd.read_parquet('data/processed/panel_4h_v1.parquet'); print(p.shape); print(p.columns.tolist()[:6]); print(p.tail(3).iloc[:,:4])"
```

13 114 filas, 30 columnas, de 2020-08-11 a 2026-08-05. Seis criptos × cinco campos OHLCV.

Para acceder a una serie usá siempre el contrato, nunca el nombre de columna a mano:

```python
from contracts.schema import cierre
from contracts.config import ACTIVOS
import pandas as pd

panel = pd.read_parquet("data/processed/panel_4h_v1.parquet")
ltc = cierre(panel, "LTC")
```

---

## Semana 1 — cuatro tareas

Cada una es independiente: podés hacerlas en cualquier orden y ninguna espera a nadie.

### T1.1 — Tabla de estacionariedad

**Por qué:** el enunciado pide marco teórico de estacionariedad y no estacionariedad. Sin una prueba corrida sobre nuestros datos, esa sección es copiar una definición de un libro. Con la tabla, es análisis, que es un criterio entero de la rúbrica.

**Qué hacer:**

```python
from src.diagnostico.pruebas import tabla_estacionariedad

en_nivel = tabla_estacionariedad(panel, en_retornos=False)
en_retornos = tabla_estacionariedad(panel, en_retornos=True)
```

`tabla_estacionariedad` ya está escrita. Lo tuyo es correrla, interpretarla y escribir qué significa.

**Criterio de aceptación:** una tabla con los seis activos en nivel y en retornos, y un párrafo que explique qué cambia entre las dos y por qué eso justifica que las características se construyan sobre retornos.

**Cuidado al redactar:** no rechazar la hipótesis nula del test ADF **no** demuestra que la serie no sea estacionaria. Demuestra que no hay evidencia suficiente en contra. Es la diferencia entre "no hay evidencia en contra" y "hay evidencia a favor", y es exactamente el tipo de precisión que separa un 3 de un 4 en el criterio de Contenido.

### T1.2 — Autocorrelación de LTC

**Por qué:** el enunciado la pide explícitamente, y es lo que justifica usar precios rezagados como variables.

**Qué hacer:** usá `autocorrelacion(serie, rezagos=40)` de `src/diagnostico/pruebas.py`. Corré sobre el cierre en nivel y sobre los retornos.

**Criterio de aceptación:** una figura con la ACF y su banda de confianza al 95 %, y una frase que diga hasta qué rezago hay autocorrelación significativa **con el número medido**, no "hay bastante".

### T1.3 — Correlación cruzada entre las seis criptos

**Por qué:** es lo que justifica que el problema sea multivariante. Si LTC no se moviera con las demás, todo el planteo del enunciado se caería.

**Qué hacer:** `matriz_correlacion(panel, en_retornos=True)`.

**Por qué sobre retornos y no sobre precios:** dos series con tendencia comparten tendencia, y su correlación en nivel sale altísima aunque no tengan ninguna relación real. Se llama correlación espuria y es la trampa clásica. Mencionarlo en el documento suma; caer en ella resta.

**Criterio de aceptación:** un mapa de calor de 6×6 y una frase que nombre cuál activo de apoyo tiene mayor correlación con LTC, con el valor medido.

### T1.4 — Volatilidad y heterocedasticidad

**Por qué:** el enunciado pide volatilidad y heterocedasticidad, y es lo que explica por qué ARIMA y GARCH clásicos rinden mal acá.

**Qué hacer:** volatilidad móvil de 30 velas sobre los retornos de LTC, graficada en el tiempo.

**Criterio de aceptación:** una figura donde se vea a ojo que la volatilidad no es constante, y un número que lo respalde — por ejemplo el cociente entre la volatilidad del tramo más agitado y la del más tranquilo.

---

## Cómo se hacen las figuras

**Siempre** con el estilo compartido. No configures matplotlib a mano:

```python
from src.visual import estilo

estilo.aplicar()
fig = estilo.grafico_serie_con_giros(ltc.tail(300), etiquetas, titulo="LTC")
estilo.guardar(fig, "ltc-giros-w7")
```

`guardar()` deja la figura en `docs/evidencias/` y escribe al lado un `.generado.txt` con la fecha. Eso está para que nunca metas en el documento una figura vieja creyendo que se regeneró.

**Reglas de figura:** número, pie, y referencia en el texto. Una figura que aparece sin que el texto la mencione resta en el criterio de estructura y redacción.

Si necesitás un tipo de gráfico que no existe todavía, lo agregás a `src/visual/estilo.py` — ese archivo es tuyo, y el resto del equipo lo va a usar.

---

## Semanas 2 a 5 — la aplicación

**Semana 2:** el esqueleto del frontend, **contra datos falsos**. No esperás a que Isaac tenga modelo. El backend ya devuelve predicciones del baseline con la misma forma que va a tener el modelo real, así que la app funciona desde el día uno y después solo cambia de dónde vienen los números.

Levantá el backend:

```bash
uv run uvicorn src.api.main:app --reload --port 8000
```

Y mirá qué devuelve:

```bash
curl http://localhost:8000/api/sintetico
```

**Semanas 3 y 4:** los tres modos — sintético, histórico y tiempo real — y la comparación de los dos modelos.

**Semana 5:** pulido y ensayo.

El alcance está cerrado en esos tres modos más el selector de activo, la comparación de modelos y el panel de métricas. Cualquier cosa fuera de esa lista se discute antes de escribirla.

**La regla que no se rompe:** la aplicación no calcula nada. Ni una métrica, ni una etiqueta, ni una predicción. Todo viene del backend. Si una métrica se calculara en los dos lados, tarde o temprano darían distinto y nadie sabría cuál va al informe.

---

## Tu sección del documento

Marco teórico de series temporales: definición, componentes, estacionariedad, no estacionariedad, heterocedasticidad, volatilidad, autocorrelación y correlación cruzada.

Es la parte del enunciado que tu propio módulo mide. Escribí con tus tablas al lado, no con definiciones de manual.

---

## Si te trabás

- **Un error de pandas que no entendés:** copialo entero al grupo. No lo resumas: el mensaje completo suele decir exactamente qué pasa.
- **Una prueba estadística que no sabés interpretar:** preguntá. Interpretar mal un p-valor en el documento es peor que no poner la prueba.
- **Más de un día trabado:** decilo.
