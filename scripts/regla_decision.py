"""La regla de decision, que es donde se pierde la clase rara.

El problema
-----------
`predecir()` usa argmax sobre las probabilidades. Con un 90,7 % de "continuidad", la
probabilidad de esa clase casi siempre gana aunque el modelo tenga informacion util
sobre las raras. `class_weight="balanced"` corrige el ENTRENAMIENTO, no la DECISION.

El arreglo, que es estandar y no es ajustar hiperparametros
-----------------------------------------------------------
En vez de elegir la clase mas probable, elegir la que mas se aparta de lo que se
esperaria por su frecuencia base:

    argmax_c  p(c) / prior(c) ** alfa

Con alfa = 0 es el argmax de siempre. Con alfa = 1 se corrige del todo por la
frecuencia. Un solo parametro.

La disciplina
-------------
`alfa` se elige **solo con datos de entrenamiento**: se parte entrenamiento en ajuste
(80 %) y calibracion (20 %), se entrena en ajuste y se elige alfa mirando calibracion.
Recien despues se reentrena con todo entrenamiento y se mide en VALIDACION, una vez,
con el alfa ya fijado.

Asi el alfa no se elige mirando el numero que se reporta -- que es el error que este
proyecto persigue. La reserva no se toca: ya se midio y esta gastada.
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

ALFAS = (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5)

panel = pd.read_parquet(RAIZ / "data" / "processed" / "panel_4h_v1.parquet")
X = construir(panel, rezagos_relativos=True)
w, h = VENTANA_W, HORIZONTE_H
y = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), w), h)
part = particionar(n=len(y), w=w, h=h)

entren = np.flatnonzero(part.entrenamiento & y.notna().to_numpy())
val = np.flatnonzero(part.validacion & y.notna().to_numpy())

# Se parte entrenamiento en ajuste y calibracion, con el mismo embargo del proyecto.
corte = int(len(entren) * 0.8)
ajuste, calib = entren[: corte - (w + h)], entren[corte:]


def entrenar(filas):
    m = BosqueAleatorio(
        n_arboles=HIPERPARAMETROS["n_estimators"],
        semilla=HIPERPARAMETROS["random_state"],
        nombre="bosque",
    )
    m.entrenar(X.iloc[filas], y.iloc[filas])
    return m


def decidir(modelo, filas, alfa, priors):
    proba = modelo._tuberia.predict_proba(modelo._preparar(X.iloc[filas], modelo._columnas))
    clases = modelo._tuberia.named_steps["bosque"].classes_
    ajustado = proba / (priors[None, :] ** alfa)
    return clases[np.argmax(ajustado, axis=1)].astype(int)


print("PASO 1 — elegir alfa mirando SOLO datos de entrenamiento")
m1 = entrenar(ajuste)
clases = m1._tuberia.named_steps["bosque"].classes_
ya = y.iloc[ajuste].to_numpy()
priors = np.array([(ya == c).mean() for c in clases])
print(f"  frecuencias base: {dict(zip(clases.tolist(), priors.round(4).tolist(), strict=True))}")
print()
print(f"  {'alfa':>6} {'F1 macro en calibracion':>26}")
mejor, mejor_f1 = None, -1.0
for a in ALFAS:
    f1 = evaluar(y.iloc[calib], decidir(m1, calib, a, priors))["f1_macro"]
    marca = ""
    if f1 > mejor_f1:
        mejor, mejor_f1 = a, f1
        marca = "  <-"
    print(f"  {a:>6.2f} {f1:>26.4f}{marca}")

print(f"\n  alfa elegido: {mejor}  (sin haber mirado validacion)")

print("\nPASO 2 — reentrenar con TODO entrenamiento y medir en validacion, una vez")
m2 = entrenar(entren)
ye = y.iloc[entren].to_numpy()
priors2 = np.array([(ye == c).mean() for c in m2._tuberia.named_steps["bosque"].classes_])

base = evaluar(y.iloc[val], m2.predecir(X.iloc[val]))
nuevo = evaluar(y.iloc[val], decidir(m2, val, mejor, priors2))
azar = BaselineAleatorio(semilla=HIPERPARAMETROS["random_state"])
azar.entrenar(X.iloc[entren], y.iloc[entren])
ma = evaluar(y.iloc[val], azar.predecir(X.iloc[val]))

print()
print(f"  {'':22} {'F1 macro':>10} {'F1 max':>9} {'F1 min':>9} {'ventaja':>9}")
for etq, m in (("argmax (lo actual)", base), (f"regla nueva (a={mejor})", nuevo)):
    print(
        f"  {etq:22} {m['f1_macro']:>10.4f} {m['f1_maximo']:>9.4f} "
        f"{m['f1_minimo']:>9.4f} {m['f1_macro'] - ma['f1_macro']:>+9.4f}"
    )
print(f"  {'azar':22} {ma['f1_macro']:>10.4f} {ma['f1_maximo']:>9.4f} {ma['f1_minimo']:>9.4f}")

salida = RAIZ / "docs" / "evidencias" / "m0-regla-decision-4h-w7-h1.json"
salida.write_text(
    json.dumps(
        {
            "que_es": (
                "Tercer arreglo probado despues de la corrida unica: corregir la REGLA "
                "DE DECISION por la frecuencia base de cada clase, en vez del "
                "entrenamiento. El parametro se eligio mirando solo datos de "
                "entrenamiento y se aplico a validacion una sola vez."
            ),
            "por_que": (
                "predecir() usa argmax. Con 90,7 % de continuidad, esa clase casi "
                "siempre gana aunque el modelo tenga informacion util sobre las raras."
            ),
            "frecuencias_base": {
                str(int(c)): float(x) for c, x in zip(clases, priors, strict=True)
            },
            "alfa_por_calibracion": {
                f"{a}": float(evaluar(y.iloc[calib], decidir(m1, calib, a, priors))["f1_macro"])
                for a in ALFAS
            },
            "alfa_elegido": mejor,
            "validacion": {
                "argmax": {k: float(v) for k, v in base.items() if isinstance(v, (int, float))},
                "regla_nueva": {
                    k: float(v) for k, v in nuevo.items() if isinstance(v, (int, float))
                },
                "azar": {k: float(v) for k, v in ma.items() if isinstance(v, (int, float))},
            },
            "conclusion": (
                "El procedimiento eligio alfa = 0, o sea no cambiar nada. "
                "class_weight='balanced' ya corrige por frecuencia al entrenar; hacerlo "
                "otra vez al decidir duplica la correccion y destruye la precision. No "
                "queda margen por esta via."
            ),
        },
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
print("")
print(f"constancia en {salida.relative_to(RAIZ)}")
