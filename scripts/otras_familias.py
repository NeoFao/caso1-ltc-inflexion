"""Dos vias que no se han probado, medidas con el aparato bueno.

Sexta: otra familia de modelo
-----------------------------
Todo lo probado hasta aqui cambia la etiqueta, la decision o los datos, pero siempre con
un bosque aleatorio. El *gradient boosting* por histogramas suele ir mejor que el bosque
en datos tabulares y no se ha probado ni una vez. No es ajustar hiperparametros: es
cambiar de familia, que es una decision de diseno distinta.

Septima: PESAR los ejemplos por margen, en vez de filtrarlos
------------------------------------------------------------
El primer arreglo --exigir un margen minimo-- fallo, y la razon quedo clara: filtrar
quita ejemplos de una clase que ya era diminuta, de 99 maximos a 27.

Pero la intuicion de fondo sigue en pie: un extremo que gana por 0,05 % es menos fiable
que uno que gana por 3 %. La forma correcta de usar eso no es tirar el ejemplo, es
**decirle al modelo cuanto confiar en el**. Se pesa cada extremo por su margen y no se
pierde ni una fila.

Es el mismo arreglo del intento 1 sin su defecto, y por eso vale probarlo.

Todo sobre los nueve tramos agregados, con intervalos pareados contra el bosque actual.
La reserva no se toca.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from sklearn.ensemble import (  # noqa: E402
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.impute import SimpleImputer  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.utils.class_weight import compute_sample_weight  # noqa: E402

from contracts.config import ACTIVO_OBJETIVO, HORIZONTE_H, VENTANA_W  # noqa: E402
from contracts.labeling import etiquetar, objetivo  # noqa: E402
from contracts.metrics import evaluar  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from contracts.splits import particionar  # noqa: E402
from src.features.base import construir  # noqa: E402
from src.features.incertidumbre import intervalo_diferencia  # noqa: E402
from src.modelos.base import BaselineAleatorio  # noqa: E402
from src.modelos.clasico import HIPERPARAMETROS, BosqueAleatorio  # noqa: E402

N_TRAMOS = 10
MINIMO_ENTRENAMIENTO = 3000

panel = pd.read_parquet(RAIZ / "data" / "processed" / "panel_4h_v1.parquet")
X = construir(panel, rezagos_relativos=True)
w, h = VENTANA_W, HORIZONTE_H
precio = cierre(panel, ACTIVO_OBJETIVO)
p_arr = precio.to_numpy()
y = objetivo(etiquetar(precio, w), h)
part = particionar(n=len(y), w=w, h=h)


def margen(indice: int, signo: int) -> float:
    centro = indice + h
    a, b = centro - w, centro + w + 1
    if a < 0 or b > len(p_arr):
        return 0.0
    vec = np.concatenate([p_arr[a:centro], p_arr[centro + 1 : b]])
    if signo > 0:
        return float((p_arr[centro] - vec.max()) / p_arr[centro] * 100)
    return float((vec.min() - p_arr[centro]) / p_arr[centro] * 100)


# El peso de cada fila: los extremos se ponderan por su margen, normalizado para que la
# media de cada clase siga siendo 1 y no se altere el balance que `balanced` establece.
margenes = np.ones(len(y))
v = y.to_numpy()
for etiqueta, signo in ((1, +1), (2, -1)):
    filas = np.flatnonzero(v == etiqueta)
    m = np.array([margen(int(i), signo) for i in filas])
    m = np.clip(m, 0, None)
    margenes[filas] = m / m.mean() if m.mean() > 0 else 1.0


def boosting(X_ent, y_ent, pesos=None):
    tub = Pipeline(
        [
            ("imputador", SimpleImputer(strategy="median", keep_empty_features=True)),
            (
                "boosting",
                HistGradientBoostingClassifier(
                    random_state=HIPERPARAMETROS["random_state"],
                    class_weight="balanced",
                    max_iter=200,
                ),
            ),
        ]
    )
    extra = {"boosting__sample_weight": pesos} if pesos is not None else {}
    tub.fit(X_ent, y_ent.astype(int), **extra)
    return tub


usable = (part.entrenamiento | part.validacion) & y.notna().to_numpy()
idx = np.flatnonzero(usable)
embargo = w + h
tramos = np.array_split(idx[idx >= idx[0] + MINIMO_ENTRENAMIENTO], N_TRAMOS)

acum: dict[str, list] = {k: [] for k in ("real", "azar", "bosque", "boosting", "pesado")}
for numero, tramo in enumerate(tramos, 1):
    filas = idx[idx < tramo[0] - embargo]
    if len(filas) < MINIMO_ENTRENAMIENTO:
        continue

    az = BaselineAleatorio(semilla=HIPERPARAMETROS["random_state"])
    az.entrenar(X.iloc[filas], y.iloc[filas])
    bo = BosqueAleatorio(
        n_arboles=HIPERPARAMETROS["n_estimators"],
        semilla=HIPERPARAMETROS["random_state"],
        nombre="bosque",
    )
    bo.entrenar(X.iloc[filas], y.iloc[filas])

    gb = boosting(X.iloc[filas], y.iloc[filas])

    # el bosque con pesos por margen, combinados con el balanceo de clases
    pesos = compute_sample_weight("balanced", y.iloc[filas].astype(int)) * margenes[filas]
    bp = Pipeline(
        [
            ("imputador", SimpleImputer(strategy="median", keep_empty_features=True)),
            (
                "bosque",
                RandomForestClassifier(
                    n_estimators=HIPERPARAMETROS["n_estimators"],
                    min_samples_leaf=HIPERPARAMETROS.get("min_samples_leaf", 1),
                    random_state=HIPERPARAMETROS["random_state"],
                ),
            ),
        ]
    )
    bp.fit(X.iloc[filas], y.iloc[filas].astype(int), bosque__sample_weight=pesos)

    acum["real"].append(y.iloc[tramo].to_numpy())
    acum["azar"].append(np.asarray(az.predecir(X.iloc[tramo])))
    acum["bosque"].append(np.asarray(bo.predecir(X.iloc[tramo])))
    acum["boosting"].append(gb.predict(X.iloc[tramo]).astype(int))
    acum["pesado"].append(bp.predict(X.iloc[tramo]).astype(int))
    print(f"  tramo {numero} listo")

y_all = pd.Series(np.concatenate(acum["real"]))
pred = {k: np.concatenate(v) for k, v in acum.items() if k != "real"}

print()
print("=" * 84)
print(f"SOBRE LAS {len(y_all)} FILAS AGREGADAS")
print("=" * 84)
print(f"  {'':34} {'F1 macro':>10} {'F1 max':>9} {'F1 min':>9}")
for etq, nombre in (
    ("azar", "azar"),
    ("bosque", "bosque (lo actual)"),
    ("boosting", "6. gradient boosting"),
    ("pesado", "7. bosque pesado por margen"),
):
    m = evaluar(y_all, pred[etq])
    print(f"  {nombre:34} {m['f1_macro']:>10.6f} {m['f1_maximo']:>9.6f} {m['f1_minimo']:>9.6f}")

print()
print("=" * 84)
print("CONTRA EL BOSQUE ACTUAL")
print("=" * 84)
for etq, nombre in (("boosting", "6. gradient boosting"), ("pesado", "7. pesado por margen")):
    ic = intervalo_diferencia(y_all, pred[etq], pred["bosque"])
    print(
        f"  {nombre:30} {ic['diferencia']:+.6f}  "
        f"IC [{ic['ic_inferior']:+.6f}, {ic['ic_superior']:+.6f}]  "
        f"{'EXCLUYE el cero' if ic['excluye_el_cero'] else 'incluye el cero'}"
    )

salida = RAIZ / "docs" / "evidencias" / "m0-otras-familias-4h-w7-h1.json"
salida.write_text(
    json.dumps(
        {
            "que_es": (
                "Arreglos 6 y 7 probados despues de la corrida. El 6 cambia de FAMILIA "
                "de modelo (gradient boosting por histogramas, nunca probado). El 7 pesa "
                "cada extremo por su margen en vez de filtrarlo, que es el arreglo 1 sin "
                "su defecto: filtrar quitaba ejemplos, pesar no pierde ninguno."
            ),
            "resultado": (
                "Ninguno se establece. El boosting queda por debajo del bosque y el "
                "pesado por margen empata. Los dos intervalos incluyen el cero."
            ),
            "n_filas": int(len(y_all)),
            "metricas": {
                etq: {
                    k: float(v)
                    for k, v in evaluar(y_all, pr).items()
                    if isinstance(v, (int, float))
                }
                for etq, pr in pred.items()
            },
            "contra_el_bosque": {
                etq: {
                    k: (float(v) if isinstance(v, (int, float)) else v)
                    for k, v in intervalo_diferencia(y_all, pred[etq], pred["bosque"]).items()
                }
                for etq in ("boosting", "pesado")
            },
        },
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
print("")
print(f"constancia en {salida.relative_to(RAIZ)}")
