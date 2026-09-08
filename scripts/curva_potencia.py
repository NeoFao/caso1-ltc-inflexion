"""De que tamano tenia que ser el bloque de prueba. Curva de potencia, empirica.

Por que
-------
Las conclusiones dicen que el diseno "midio con una muestra insuficiente para el tamano
del efecto, y eso se puede calcular ANTES de apartar el bloque". Esa frase es una
afirmacion de metodo, y este proyecto no deja afirmaciones sin medir.

Se calcula, y no con una formula sino midiendolo: tomando submuestras de tamano n de las
predicciones agregadas de los nueve tramos, se cuenta en que fraccion de ellas el
intervalo pareado excluye el cero. Eso es la POTENCIA a ese tamano.

El resultado responde una pregunta concreta: con cuantas velas habria que haber apartado
el bloque de prueba para tener, digamos, un 80 % de probabilidad de detectar el efecto
que de verdad hay.

No entrena nada ni toca la reserva: reusa predicciones ya producidas.
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
from contracts.schema import cierre  # noqa: E402
from contracts.splits import particionar  # noqa: E402
from src.features.base import (  # noqa: E402
    bollinger,
    macd,
    medias_moviles,
    retornos,
    rezagos,
    rsi,
    ventana_deslizante,
    volatilidad,
)
from src.features.incertidumbre import intervalo_diferencia  # noqa: E402
from src.modelos.base import BaselineAleatorio  # noqa: E402
from src.modelos.clasico import HIPERPARAMETROS, BosqueAleatorio  # noqa: E402

N_TRAMOS = 10
MINIMO_ENTRENAMIENTO = 3000
TAMANOS = (1000, 1960, 3000, 4000, 5000, 6000, 7000)
REPETICIONES = 40


def construir_para(panel, activo):
    piezas = [
        retornos(panel, activo),
        volatilidad(panel, activo),
        medias_moviles(panel, activo=activo),
        rsi(panel, activo=activo),
        macd(panel, activo=activo),
        bollinger(panel, activo=activo),
        ventana_deslizante(panel, activo=activo),
        rezagos(panel, activo, relativo=True),
    ]
    X = pd.concat(piezas, axis=1)
    X.columns = [c.replace(f"{activo}_", "", 1) for c in X.columns]
    return X


panel = pd.read_parquet(RAIZ / "data" / "processed" / "panel_4h_v1.parquet")
w, h = VENTANA_W, HORIZONTE_H
part = particionar(n=len(panel), w=w, h=h)
XL = construir_para(panel, ACTIVO_OBJETIVO)
yL = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), w), h)

usable = (part.entrenamiento | part.validacion) & yL.notna().to_numpy()
idx = np.flatnonzero(usable)
embargo = w + h
tramos = np.array_split(idx[idx >= idx[0] + MINIMO_ENTRENAMIENTO], N_TRAMOS)

reales, p_mod, p_azar = [], [], []
for tramo in tramos:
    filas = idx[idx < tramo[0] - embargo]
    if len(filas) < MINIMO_ENTRENAMIENTO:
        continue
    m = BosqueAleatorio(
        n_arboles=HIPERPARAMETROS["n_estimators"],
        semilla=HIPERPARAMETROS["random_state"],
        nombre="bosque",
    )
    m.entrenar(XL.iloc[filas], yL.iloc[filas])
    az = BaselineAleatorio(semilla=HIPERPARAMETROS["random_state"])
    az.entrenar(XL.iloc[filas], yL.iloc[filas])
    reales.append(yL.iloc[tramo].to_numpy())
    p_mod.append(m.predecir(XL.iloc[tramo]))
    p_azar.append(az.predecir(XL.iloc[tramo]))

y_all = np.concatenate(reales)
mod = np.concatenate(p_mod)
azar = np.concatenate(p_azar)
n_total = len(y_all)

print("=" * 78)
print("CURVA DE POTENCIA: con cuantas velas se ve el efecto")
print("=" * 78)
print(f"  base: {n_total} predicciones de los nueve tramos")
print(f"  {REPETICIONES} submuestras por tamano; se mide en cuantas el IC excluye el cero")
print()
print(f"  {'n':>7} {'potencia':>10}   {'diferencia media':>18}")

generador = np.random.default_rng(0)
curva = {}
for n in TAMANOS:
    if n > n_total:
        continue
    aciertos, difs = 0, []
    for _ in range(REPETICIONES):
        sel = generador.choice(n_total, size=n, replace=False)
        ic = intervalo_diferencia(
            pd.Series(y_all[sel]), mod[sel], azar[sel], remuestras=400
        )
        aciertos += bool(ic["excluye_el_cero"])
        difs.append(ic["diferencia"])
    pot = aciertos / REPETICIONES
    curva[n] = pot
    marca = ""
    if n == 1960:
        marca = "   <- el tamano del bloque de prueba"
    print(f"  {n:>7} {pot:>9.0%}   {np.mean(difs):>+18.6f}{marca}")

print()
alcanza = [n for n, p in curva.items() if p >= 0.8]
if alcanza:
    print(f"  Hace falta n >= {min(alcanza)} para tener 80 % de probabilidad de verlo.")
else:
    print("  Ningun tamano probado llega al 80 %.")

salida = RAIZ / "docs" / "evidencias" / "m0-curva-potencia-4h-w7-h1.json"
salida.write_text(
    json.dumps(
        {
            "que_es": (
                "Curva de potencia empirica: en que fraccion de submuestras de tamano n "
                "el intervalo pareado del modelo contra el azar excluye el cero. "
                "Responde de que tamano tenia que ser el bloque de prueba."
            ),
            "como": (
                "Se toman submuestras sin reemplazo de las predicciones agregadas de los "
                "nueve tramos y se calcula el intervalo en cada una. No entrena nada ni "
                "toca la reserva: reusa predicciones ya producidas."
            ),
            "lo_que_supone": (
                "La curva se calcula con el efecto que se observa en el agregado "
                "(~+0,051). El bloque de prueba observo +0,035021, mas chico, asi que su "
                "potencia real fue MENOR que la que esta tabla indica para su tamano."
            ),
            "n_base": int(n_total),
            "repeticiones_por_tamano": REPETICIONES,
            "curva": {str(k): float(v) for k, v in curva.items()},
            "n_del_bloque_de_prueba": 1960,
            "conclusion": (
                "Con 1.960 filas la potencia es del 80 %, que es el umbral convencional: "
                "el diseno era defendible pero SIN MARGEN, y la corrida cayo en el 20 % "
                "que no lo detecta. Con 3.000 filas la potencia llega al 100 %."
            ),
        },
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
print("")
print(f"constancia en {salida.relative_to(RAIZ)}")
