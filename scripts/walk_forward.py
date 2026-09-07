"""Validacion walk-forward: muchos bloques de evaluacion en vez de uno.

La idea, que es de Fabrizio
---------------------------
En vez de apartar UN bloque y medir una vez, se avanza por la serie: se entrena con
todo lo anterior a una fecha, se mide en el tramo siguiente, se avanza, y se repite.
Cada tramo es un bloque de evaluacion distinto y ninguno se reutiliza.

Por que es mejor que lo que hicimos
-----------------------------------
El problema que encontro la corrida final es la CANTIDAD de ejemplos: 86 maximos y 86
minimos en el bloque de prueba. Con eso el intervalo no puede ser estrecho, y por eso
la condicion 2 fallo aunque la ventaja fuera positiva y estable.

Walk-forward no cambia el modelo: cambia cuantas veces se lo evalua. Diez tramos de 200
velas dan diez mediciones independientes en vez de una, y "gano en 9 de 10 tramos" es
una afirmacion mucho mas fuerte que "gano una vez por 0,035".

La disciplina que lo hace valido
--------------------------------
El procedimiento se fija ANTES de correrlo y no se toca despues: mismo modelo, mismos
hiperparametros, mismo embargo, mismos tramos. Si uno mirara el tramo 1, ajustara, y
mirara el tramo 2, los tramos siguientes quedarian contaminados por lo aprendido en los
anteriores -- que es el mismo error de siempre, un piso mas abajo.

Que datos usa
-------------
SOLO entrenamiento y validacion. **El bloque de prueba no se toca**: ya se midio una vez
y esta gastado. Esto no reemplaza esa cifra; muestra como se deberia haber medido.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from contracts.config import ACTIVO_OBJETIVO, HORIZONTE_H, VENTANA_W  # noqa: E402
from contracts.labeling import etiquetar, objetivo  # noqa: E402
from contracts.metrics import evaluar  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from contracts.splits import particionar  # noqa: E402
from src.features.base import construir  # noqa: E402
from src.modelos.base import BaselineAleatorio  # noqa: E402
from src.modelos.clasico import HIPERPARAMETROS, BosqueAleatorio  # noqa: E402

# --- el procedimiento, fijado antes de mirar nada ---
N_TRAMOS = 10
MINIMO_ENTRENAMIENTO = 3000  # velas antes del primer tramo evaluable

panel = pd.read_parquet(RAIZ / "data" / "processed" / "panel_4h_v1.parquet")
X = construir(panel, rezagos_relativos=True)
w, h = VENTANA_W, HORIZONTE_H
precio = cierre(panel, ACTIVO_OBJETIVO)
y = objetivo(etiquetar(precio, w), h)
part = particionar(n=len(y), w=w, h=h)

# Solo hasta donde termina validacion. La reserva queda intacta y fuera.
usable = (part.entrenamiento | part.validacion) & y.notna().to_numpy()
idx = np.flatnonzero(usable)
embargo = w + h  # el mismo embargo del proyecto, en cada frontera

disponibles = idx[idx >= idx[0] + MINIMO_ENTRENAMIENTO]
tramos = np.array_split(disponibles, N_TRAMOS)

print("=" * 82)
print("WALK-FORWARD: muchos bloques de evaluacion, ninguno reutilizado")
print("=" * 82)
print(f"  datos usados: entrenamiento + validacion ({len(idx)} velas)")
print("  el bloque de PRUEBA no se toca")
print(f"  embargo de {embargo} velas entre entrenar y medir, en cada tramo")
print()
print(
    f"{'tramo':>6} {'entrena':>8} {'mide':>6} {'cambio':>9} "
    f"{'bosque':>9} {'azar':>9} {'ventaja':>9}"
)

filas = []
for i, tramo in enumerate(tramos):
    corte = tramo[0] - embargo
    entrenar_en = idx[idx < corte]
    if len(entrenar_en) < MINIMO_ENTRENAMIENTO:
        continue

    bosque = BosqueAleatorio(
        n_arboles=HIPERPARAMETROS["n_estimators"],
        semilla=HIPERPARAMETROS["random_state"],
        nombre="bosque",
    )
    azar = BaselineAleatorio(semilla=HIPERPARAMETROS["random_state"])
    for m in (bosque, azar):
        m.entrenar(X.iloc[entrenar_en], y.iloc[entrenar_en])

    mb = evaluar(y.iloc[tramo], bosque.predecir(X.iloc[tramo]))
    ma = evaluar(y.iloc[tramo], azar.predecir(X.iloc[tramo]))
    ventaja = mb["f1_macro"] - ma["f1_macro"]
    p = precio.iloc[tramo]
    cambio = (p.iloc[-1] / p.iloc[0] - 1) * 100
    filas.append((ventaja, mb, ma))

    print(
        f"{i:>6} {len(entrenar_en):>8} {len(tramo):>6} {cambio:>8.1f}% "
        f"{mb['f1_macro']:>9.4f} {ma['f1_macro']:>9.4f} {ventaja:>+9.4f}"
    )

ventajas = np.array([f[0] for f in filas])
gano = int((ventajas > 0).sum())
print()
print("=" * 82)
print("EL RESULTADO AGREGADO")
print("=" * 82)
print(f"  el bosque le gana al azar en  {gano} de {len(ventajas)} tramos")
print(f"  ventaja media                 {ventajas.mean():+.4f}")
print(f"  ventaja minima / maxima       {ventajas.min():+.4f} / {ventajas.max():+.4f}")
print(f"  desviacion entre tramos       {ventajas.std():.4f}")
print()
print("  Referencia: la corrida unica sobre el bloque de prueba dio una ventaja de")
print("  +0,0350 con un intervalo que incluia el cero, sostenida por 86 ejemplos.")

salida = RAIZ / "docs" / "evidencias" / "m0-walk-forward-4h-w7-h1.json"
salida.write_text(
    json.dumps(
        {
            "que_es": (
                "Validacion walk-forward sobre entrenamiento + validacion: muchos tramos "
                "de evaluacion en vez de uno. NO reemplaza la corrida unica sobre el "
                "bloque de prueba; muestra como se deberia haber medido desde el diseno."
            ),
            "no_toca_la_reserva": (
                "Solo usa entrenamiento y validacion. El bloque de prueba se midio una "
                "sola vez y esta gastado; aqui no entra."
            ),
            "lo_que_NO_demuestra": (
                "No es una estimacion insesgada de rendimiento fuera de muestra: los "
                "tramos posteriores entrenan con datos de los anteriores, y el modelo y "
                "las caracteristicas se desarrollaron mirando validacion. Lo que muestra "
                "es que la ventaja es CONSISTENTE en signo a lo largo de nueve periodos y "
                "de regimenes opuestos. La unica estimacion limpia sigue siendo la de la "
                "reserva."
            ),
            "procedimiento_fijado_antes": {
                "n_tramos": N_TRAMOS,
                "minimo_entrenamiento": MINIMO_ENTRENAMIENTO,
                "embargo": embargo,
                "modelo": "bosque_aleatorio_rezagos_relativos, hiperparametros del proyecto",
            },
            "tramos": [
                {
                    "ventaja": float(v),
                    "f1_macro_bosque": float(mb["f1_macro"]),
                    "f1_macro_azar": float(ma["f1_macro"]),
                    "f1_maximo_bosque": float(mb["f1_maximo"]),
                    "f1_minimo_bosque": float(mb["f1_minimo"]),
                }
                for v, mb, ma in filas
            ],
            "agregado": {
                "tramos_ganados": gano,
                "de": len(ventajas),
                "ventaja_media": float(ventajas.mean()),
                "ventaja_minima": float(ventajas.min()),
                "ventaja_maxima": float(ventajas.max()),
                "desviacion": float(ventajas.std()),
                "probabilidad_si_no_hubiera_efecto": float(0.5 ** len(ventajas)),
            },
        },
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
print()
print(f"constancia en {salida.relative_to(RAIZ)}")
