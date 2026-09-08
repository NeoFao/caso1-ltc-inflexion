"""Las figuras del informe final.

Por que existe
--------------
El informe tenia 17 tablas y **cero figuras**. En un trabajo de senales eso es un hueco
por si solo, y ademas el criterio de aceptacion de las entregas pide que las figuras
tengan numero, pie y esten referenciadas en el texto.

Las cuatro que se generan son las que llevan los mensajes que el documento no puede
transmitir con una tabla:

1. **Que hace el sistema.** El precio del bloque de prueba con los giros reales y los
   que el modelo predijo. Es la unica figura que muestra el producto funcionando.
2. **Como se parten los datos.** La particion cronologica con el embargo, que es la
   decision de diseno que evita el error mas caro del proyecto.
3. **Los modelos con su incertidumbre.** Las barras solas invitan a leer un orden que
   los intervalos desmienten; con los intervalos encima, no.
4. **La curva de potencia.** El hallazgo de metodo del trabajo: con 1.960 velas el
   efecto se ve el 80 % de las veces, con 3.000 siempre.

Todas usan `src/visual/estilo.py`, que fija la paleta del PRD y de la aplicacion. Las
cifras salen de `docs/evidencias/`; ninguna se recalcula aqui.

No toca la reserva: la figura 1 dibuja las predicciones de la corrida ya hecha,
recalculadas con modelos que reproducen bit a bit (ver la D28).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from contracts.config import ACTIVO_OBJETIVO, HORIZONTE_H, VENTANA_W  # noqa: E402
from contracts.labeling import etiquetar, objetivo  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from contracts.splits import particionar  # noqa: E402
from src.features.base import construir  # noqa: E402
from src.modelos.clasico import HIPERPARAMETROS, BosqueAleatorio  # noqa: E402
from src.visual import estilo  # noqa: E402

EVIDENCIAS = RAIZ / "docs" / "evidencias"
estilo.aplicar()

panel = pd.read_parquet(RAIZ / "data" / "processed" / "panel_4h_v1.parquet")
w, h = VENTANA_W, HORIZONTE_H
precio = cierre(panel, ACTIVO_OBJETIVO)
y = objetivo(etiquetar(precio, w), h)
part = particionar(n=len(y), w=w, h=h)
X = construir(panel, rezagos_relativos=True)

# ------------------------------------------------------------------ figura 1
entren = part.entrenamiento & y.notna().to_numpy()
prueba = part.prueba & y.notna().to_numpy()

bosque = BosqueAleatorio(
    n_arboles=HIPERPARAMETROS["n_estimators"],
    semilla=HIPERPARAMETROS["random_state"],
    nombre="bosque_aleatorio_rezagos_relativos",
)
bosque.entrenar(X[entren], y[entren])
pred = pd.Series(bosque.predecir(X[prueba]), index=precio[prueba].index)

# Se dibuja una VENTANA y no el bloque entero. Con 1.960 velas y cientos de marcadores
# la figura es un borron: se ve que hay muchos giros y no se ve ni uno. Doscientas velas
# --unos 33 dias-- es lo que deja distinguir un marcador de otro, que es el unico motivo
# por el que esta figura existe. La cifra que resume el bloque entero esta en la tabla.
VENTANA = 200
indices = np.flatnonzero(prueba)[:VENTANA]
recorte = precio.index[indices]

fig = estilo.grafico_serie_con_giros(
    precio.loc[recorte],
    etiquetas=y.loc[recorte],
    predichas=pred.loc[recorte],
    titulo="",
)
eje = fig.axes[0]
eje.set_title(
    "Bloque de prueba: giros reales y detectados\n"
    f"(primeras {VENTANA} velas, de 1 960)",
    pad=34,
)
eje.legend(ncol=3, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.20), fontsize=8)
fig.tight_layout()
ruta1 = estilo.guardar(fig, "informe-f1-prueba-giros", EVIDENCIAS)
plt.close(fig)
print(f"  {ruta1.name}")

# ------------------------------------------------------------------ figura 2
fig, eje = plt.subplots(figsize=(9, 2.8))
bloques = [
    ("Entrenamiento", part.entrenamiento, estilo.NAVY),
    ("Validación", part.validacion, estilo.ACENTO),
    ("Prueba", part.prueba, estilo.MAXIMO),
    ("Embargo", part.embargo, estilo.CONTINUIDAD),
]
for nombre, mascara, color in bloques:
    filas = np.flatnonzero(mascara)
    if len(filas) == 0:
        continue
    eje.barh(0, len(filas), left=filas[0], height=0.5, color=color, label=nombre)
# El embargo son 8 velas por frontera sobre 13.114: a esta escala es invisible, y que
# lo sea ES el mensaje --cuesta un 0,1 % de los datos y evita el error mas caro del
# proyecto--. Se anota en vez de exagerarlo, que seria dibujar algo que no es.
fronteras = [np.flatnonzero(part.validacion)[0], np.flatnonzero(part.prueba)[0]]
for x in fronteras:
    eje.annotate(
        "",
        xy=(x, 0.28),
        xytext=(x, 0.62),
        arrowprops={"arrowstyle": "->", "color": estilo.GRIS, "linewidth": 1.2},
    )
eje.text(
    fronteras[0],
    0.75,
    "embargo: 8 velas en cada frontera\n(invisible a esta escala, y ese es el punto)",
    ha="center",
    va="bottom",
    fontsize=8,
    color=estilo.GRIS,
)
eje.set_ylim(-0.45, 1.15)
eje.set_yticks([])
eje.set_xlabel("Vela (orden cronológico)")
eje.set_title("Partición cronológica, con embargo en cada frontera", pad=26)
eje.legend(ncol=4, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.30))
fig.tight_layout()
ruta2 = estilo.guardar(fig, "informe-f2-particion", EVIDENCIAS)
plt.close(fig)
print(f"  {ruta2.name}")

# ------------------------------------------------------------------ figura 3
prof = json.loads((EVIDENCIAS / "m3-modelos-profundos-4h-w7-h1-prueba.json").read_text("utf-8"))
orden = [
    ("baseline_trivial", "Trivial"),
    ("baseline_aleatorio", "Azar"),
    ("itransformer", "iTransformer"),
    ("chronos_bolt", "Chronos-Bolt"),
    ("bosque_aleatorio_rezagos_relativos", "Bosque"),
]
valores = [prof["metricas"][k]["f1_macro"] for k, _ in orden]
etiquetas = [e for _, e in orden]
ps = prof["por_semilla"]["por_modelo"]
errores = [
    [
        valores[i] - ps[k]["resumen"]["f1_macro"]["minimo"],
        ps[k]["resumen"]["f1_macro"]["maximo"] - valores[i],
    ]
    for i, (k, _) in enumerate(orden)
]

fig, eje = plt.subplots(figsize=(7.5, 3.4))
colores = [estilo.CONTINUIDAD, estilo.GRIS, estilo.ACENTO, estilo.ACENTO, estilo.NAVY]
eje.barh(etiquetas, valores, color=colores, height=0.6)
eje.errorbar(
    valores,
    etiquetas,
    xerr=np.array(errores).T,
    fmt="none",
    ecolor=estilo.MAXIMO,
    capsize=4,
    linewidth=1.4,
)
eje.axvline(
    prof["metricas"]["baseline_aleatorio"]["f1_macro"],
    color=estilo.MAXIMO,
    linestyle="--",
    linewidth=1,
)
eje.set_xlabel("F1 macro sobre el bloque de prueba")
eje.set_title("Los cinco modelos, con su rango entre cinco semillas")
eje.set_xlim(0.30, 0.42)
fig.tight_layout()
ruta3 = estilo.guardar(fig, "informe-f3-modelos-prueba", EVIDENCIAS)
plt.close(fig)
print(f"  {ruta3.name}")

# ------------------------------------------------------------------ figura 4
curva = json.loads((EVIDENCIAS / "m0-curva-potencia-4h-w7-h1.json").read_text("utf-8"))["curva"]
ns = sorted(int(k) for k in curva)
pot = [curva[str(k)] * 100 for k in ns]

fig, eje = plt.subplots(figsize=(7, 3.2))
eje.plot(ns, pot, marker="o", color=estilo.NAVY, linewidth=1.8)
eje.axhline(80, color=estilo.GRIS, linestyle=":", linewidth=1)
eje.axvline(1960, color=estilo.MAXIMO, linestyle="--", linewidth=1.2)
eje.annotate(
    "el bloque que usamos\n(1 960 velas, 80 %)",
    xy=(1960, 80),
    xytext=(2600, 55),
    color=estilo.MAXIMO,
    arrowprops={"arrowstyle": "->", "color": estilo.MAXIMO, "linewidth": 1},
)
eje.set_xlabel("Velas en el bloque de prueba")
eje.set_ylabel("Probabilidad de detectar el efecto (%)")
eje.set_title("Cuánta muestra hacía falta para ver el efecto que hay")
eje.set_ylim(0, 105)
fig.tight_layout()
ruta4 = estilo.guardar(fig, "informe-f4-curva-potencia", EVIDENCIAS)
plt.close(fig)
print(f"  {ruta4.name}")
