"""Por que el bloque de prueba no alcanzo, y que se probo para arreglarlo.

Todo esto es POSTERIOR a la corrida unica y se mide sobre entrenamiento y validacion.
La reserva esta gastada y no se toca; la cifra que el informe reporta no cambia.

Produce tres cosas, en un solo archivo de evidencia:

1. **El margen de cada extremo**: por cuanto le gana a su vecino mas cercano. Es el
   diagnostico: los minimos ganan por mas que los maximos en los tres bloques, y en
   prueba todos ganan por menos.
2. **Umbral de margen minimo**: exigir que un extremo gane por al menos X % para
   contarlo. Es el arreglo que el diagnostico sugiere.
3. **Dos clases en vez de tres**: juntar maximos y minimos en "punto de inflexion",
   que duplica los ejemplos de la clase rara.

Los dos arreglos empeoran el resultado. Se guardan igual: un intento medido que falla
es evidencia, y sin el la seccion del informe seria una afirmacion sin respaldo.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from sklearn.metrics import f1_score  # noqa: E402

from contracts.config import ACTIVO_OBJETIVO, HORIZONTE_H, VENTANA_W  # noqa: E402
from contracts.labeling import etiquetar, objetivo  # noqa: E402
from contracts.metrics import evaluar  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from contracts.splits import particionar  # noqa: E402
from src.features.base import construir  # noqa: E402
from src.modelos.base import BaselineAleatorio  # noqa: E402
from src.modelos.clasico import HIPERPARAMETROS, BosqueAleatorio  # noqa: E402

UMBRALES = (0.0, 0.1, 0.2, 0.3, 0.5, 0.8)

panel = pd.read_parquet(RAIZ / "data" / "processed" / "panel_4h_v1.parquet")
X = construir(panel, rezagos_relativos=True)
w, h = VENTANA_W, HORIZONTE_H
precio = cierre(panel, ACTIVO_OBJETIVO)
p = precio.to_numpy()
y0 = objetivo(etiquetar(precio, w), h)
part = particionar(n=len(y0), w=w, h=h)


def margen(indice: int, signo: int) -> float:
    """Por cuanto gana el extremo a su vecino mas cercano, en % del precio.

    El desfase importa: `objetivo()` corre la etiqueta h velas, asi que la etiqueta en
    `i` describe el extremo en `i + h`. Medirlo en `i` da margenes NEGATIVOS, que es
    imposible por definicion -- fue asi como se detecto el error.
    """
    centro = indice + h
    a, b = centro - w, centro + w + 1
    if a < 0 or b > len(p):
        return np.inf
    vec = np.concatenate([p[a:centro], p[centro + 1 : b]])
    if signo > 0:
        return float((p[centro] - vec.max()) / p[centro] * 100)
    return float((vec.min() - p[centro]) / p[centro] * 100)


# ---------------------------------------------------------------- 1. el margen
margenes: dict[str, dict[str, float]] = {}
print("1. MARGEN DE CADA EXTREMO SOBRE SU VECINO MAS CERCANO")
for nombre, m in (
    ("entrenamiento", part.entrenamiento),
    ("validacion", part.validacion),
    ("prueba", part.prueba),
):
    mm = m & y0.notna().to_numpy()
    bloque = {}
    for etiqueta, signo, cl in ((1, +1, "maximos"), (2, -1, "minimos")):
        vals = [
            margen(int(i), signo)
            for i in np.flatnonzero(mm & (y0.to_numpy() == etiqueta))
        ]
        vals = [v for v in vals if np.isfinite(v)]
        bloque[cl] = {"n": len(vals), "media": float(np.mean(vals))}
        print(f"   {nombre:15} {cl:8} n={len(vals):4}  media {np.mean(vals):.4f}%")
    margenes[nombre] = bloque


def ventaja(y: pd.Series, binaria: bool = False) -> dict:
    entren = part.entrenamiento & y.notna().to_numpy()
    val = part.validacion & y.notna().to_numpy()
    salida = {}
    for etq, modelo in (
        (
            "bosque",
            BosqueAleatorio(
                n_arboles=HIPERPARAMETROS["n_estimators"],
                semilla=HIPERPARAMETROS["random_state"],
                nombre="bosque",
            ),
        ),
        ("azar", BaselineAleatorio(semilla=HIPERPARAMETROS["random_state"])),
    ):
        modelo.entrenar(X[entren], y[entren])
        pred = np.asarray(modelo.predecir(X[val]))
        if binaria:
            salida[etq] = {
                "f1_macro": float(
                    f1_score(y[val].to_numpy(), pred, average="macro", zero_division=0)
                )
            }
        else:
            salida[etq] = {k: float(v) for k, v in evaluar(y[val], pred).items()}
    salida["ventaja"] = salida["bosque"]["f1_macro"] - salida["azar"]["f1_macro"]
    return salida


# ------------------------------------------------- 2. umbral de margen minimo
print("\n2. EXIGIR UN MARGEN MINIMO PARA CONTAR UN EXTREMO")
por_umbral = {}
for u in UMBRALES:
    v = y0.to_numpy().copy()
    for etiqueta, signo in ((1, +1), (2, -1)):
        for i in np.flatnonzero(v == etiqueta):
            if margen(int(i), signo) < u:
                v[i] = 3
    r = ventaja(pd.Series(v, index=y0.index))
    por_umbral[f"{u}"] = r
    print(f"   umbral {u:.1f}%   ventaja {r['ventaja']:+.4f}")

# ------------------------------------------------------------ 3. dos clases
print("\n3. JUNTAR MAXIMOS Y MINIMOS EN UNA SOLA CLASE")
v = y0.to_numpy().copy()
v[(v == 1) | (v == 2)] = 1
dos = ventaja(pd.Series(v, index=y0.index), binaria=True)
print(f"   ventaja {dos['ventaja']:+.4f}")

salida = RAIZ / "docs" / "evidencias" / "m0-diagnostico-posterior-4h-w7-h1.json"
salida.write_text(
    json.dumps(
        {
            "que_es": (
                "Investigacion POSTERIOR a la corrida unica: por que el bloque de prueba "
                "no alcanzo, y dos arreglos probados. Medido sobre entrenamiento y "
                "validacion; la reserva no se toca y la cifra reportada no cambia."
            ),
            "margen_de_los_extremos": margenes,
            "arreglo_1_umbral_de_margen": por_umbral,
            "arreglo_2_dos_clases": dos,
            "conclusion": (
                "Los dos arreglos empeoran. El cuello de botella no es el criterio ni el "
                "modelo: es la cantidad de ejemplos de la clase rara. Lo que si resolvio "
                "la pregunta fue medir muchas veces en vez de una (ver "
                "m0-walk-forward-4h-w7-h1.json)."
            ),
        },
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
print(f"\nconstancia en {salida.relative_to(RAIZ)}")
