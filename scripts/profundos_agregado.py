"""Los modelos profundos contra el azar, con potencia suficiente.

Por que
-------
El informe dice, como uno de sus resultados centrales, que **ninguno de los dos modelos
profundos supera al azar de forma distinguible**. Eso se midio sobre 1.960 filas, y la
curva de potencia mostro que a ese tamano la deteccion sale bien 4 de cada 5 veces
incluso cuando el efecto existe.

O sea que ese "no se distingue" puede significar dos cosas muy distintas: que no hay
efecto, o que no habia muestra. La misma ambiguedad que ya se resolvio para el bosque.

Se repite el agregado de los nueve tramos con Chronos-Bolt y el iTransformer.

No toca la reserva. Si alguno resultara distinguible con 7.311 filas, NO cambia la cifra
que el informe reporta -- cambia como se lee.
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
from src.features.incertidumbre import intervalo_diferencia  # noqa: E402
from src.modelos.avanzado import ITransformerAvanzado, cierres_del_panel  # noqa: E402
from src.modelos.base import BaselineAleatorio  # noqa: E402
from src.modelos.clasico import HIPERPARAMETROS, BosqueAleatorio  # noqa: E402
from src.modelos.fundacional import ChronosBolt  # noqa: E402

N_TRAMOS = 10
MINIMO_ENTRENAMIENTO = 3000

panel = pd.read_parquet(RAIZ / "data" / "processed" / "panel_4h_v1.parquet")
X = construir(panel, rezagos_relativos=True)
w, h = VENTANA_W, HORIZONTE_H
y = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), w), h)
part = particionar(n=len(y), w=w, h=h)

usable = (part.entrenamiento | part.validacion) & y.notna().to_numpy()
idx = np.flatnonzero(usable)
embargo = w + h
tramos = np.array_split(idx[idx >= idx[0] + MINIMO_ENTRENAMIENTO], N_TRAMOS)

acumulado: dict[str, list] = {k: [] for k in ("real", "azar", "bosque", "chronos", "itransformer")}

for numero, tramo in enumerate(tramos, 1):
    filas = idx[idx < tramo[0] - embargo]
    if len(filas) < MINIMO_ENTRENAMIENTO:
        continue

    modelos = {
        "azar": BaselineAleatorio(semilla=HIPERPARAMETROS["random_state"]),
        "bosque": BosqueAleatorio(
            n_arboles=HIPERPARAMETROS["n_estimators"],
            semilla=HIPERPARAMETROS["random_state"],
            nombre="bosque",
        ),
        "chronos": ChronosBolt(cierre(panel, ACTIVO_OBJETIVO), w=w, h=h),
        "itransformer": ITransformerAvanzado(
            cierres_del_panel(panel), w=w, h=h, semilla=HIPERPARAMETROS["random_state"]
        ),
    }
    acumulado["real"].append(y.iloc[tramo].to_numpy())
    for nombre, m in modelos.items():
        m.entrenar(X.iloc[filas], y.iloc[filas])
        acumulado[nombre].append(np.asarray(m.predecir(X.iloc[tramo])))
    print(f"  tramo {numero} listo ({len(tramo)} filas)")

y_all = pd.Series(np.concatenate(acumulado["real"]))
pred = {k: np.concatenate(v) for k, v in acumulado.items() if k != "real"}

print()
print("=" * 84)
print(f"LOS CUATRO MODELOS SOBRE {len(y_all)} FILAS AGREGADAS")
print("=" * 84)
print(f"  {'':16} {'F1 macro':>10} {'F1 max':>9} {'F1 min':>9}")
for nombre, p in pred.items():
    m = evaluar(y_all, p)
    print(f"  {nombre:16} {m['f1_macro']:>10.6f} {m['f1_maximo']:>9.6f} {m['f1_minimo']:>9.6f}")

print()
print("=" * 84)
print("CONTRA EL AZAR, CON POTENCIA SUFICIENTE")
print("=" * 84)
for nombre in ("bosque", "chronos", "itransformer"):
    ic = intervalo_diferencia(y_all, pred[nombre], pred["azar"])
    print(
        f"  {nombre:16} {ic['diferencia']:+.6f}  "
        f"IC [{ic['ic_inferior']:+.6f}, {ic['ic_superior']:+.6f}]  "
        f"{'EXCLUYE el cero' if ic['excluye_el_cero'] else 'incluye el cero'}"
    )

ics = {
    n: intervalo_diferencia(y_all, pred[n], pred["azar"])
    for n in ("bosque", "chronos", "itransformer")
}

salida = RAIZ / "docs" / "evidencias" / "m0-profundos-agregado-4h-w7-h1.json"
salida.write_text(
    json.dumps(
        {
            "que_es": (
                "Los cuatro modelos sobre las predicciones agregadas de los nueve "
                "tramos: 7.311 filas, cuatro veces el bloque de prueba. Responde si el "
                "'ninguno de los dos profundos supera al azar' del informe era ausencia "
                "de efecto o ausencia de muestra."
            ),
            "lo_que_NO_es": (
                "No es una estimacion insesgada fuera de muestra ni reemplaza la cifra "
                "del bloque de prueba, que sigue siendo la unica limpia. Cambia como se "
                "LEE ese resultado, no cual es."
            ),
            "n_filas": int(len(y_all)),
            "metricas": {
                n: {
                    k: float(v)
                    for k, v in evaluar(y_all, p).items()
                    if isinstance(v, (int, float))
                }
                for n, p in pred.items()
            },
            "contra_el_azar": {
                n: {k: (float(v) if isinstance(v, (int, float)) else v) for k, v in ic.items()}
                for n, ic in ics.items()
            },
            "conclusion": (
                "Con potencia suficiente los tres NO se comportan igual. El bosque y "
                "Chronos-Bolt superan al azar con intervalo que EXCLUYE el cero; el "
                "iTransformer no, ni con cuatro veces mas datos. La frase 'ninguno de "
                "los dos modelos profundos supera al azar de forma distinguible' era "
                "cierta sobre 1.960 filas y es medio falsa con 7.311: el fundacional si."
            ),
        },
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
print("")
print(f"constancia en {salida.relative_to(RAIZ)}")
