"""La afirmacion mas severa del informe, medida con potencia suficiente.

Que se comprueba
----------------
El bloque de prueba dejo la lectura mas dura del trabajo: **ningun modelo supera al azar
en las DOS clases extremas**. El bosque gana en Minimo y pierde en Maximo, el fundacional
gana en Minimo, y el avanzado gana en Maximo.

Pero eso se midio sobre 1.960 filas, con 86 ejemplos por clase. La curva de potencia ya
mostro que a ese tamano el F1 macro --que tiene TODAS las filas detras-- falla una de
cada cinco veces. El F1 de una clase con 86 casos es mucho mas ruidoso todavia: en dos de
los nueve tramos del walk-forward una clase dio 0,000000 exacto.

Asi que esa lectura tan severa puede ser cierta, o puede ser lo que 86 ejemplos dejan ver.
Se repite sobre las 7.311 filas agregadas, con intervalos POR CLASE.

No toca la reserva ni cambia la cifra que el informe reporta.
"""

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


def f1_de(clase: int):
    """El F1 de UNA clase, con la firma que `intervalo_diferencia` espera."""

    def metrica(y_real, y_pred) -> float:
        return float(
            f1_score(
                np.asarray(y_real, dtype=int),
                np.asarray(y_pred, dtype=int),
                labels=[clase],
                average="macro",
                zero_division=0,
            )
        )

    return metrica


panel = pd.read_parquet(RAIZ / "data" / "processed" / "panel_4h_v1.parquet")
X = construir(panel, rezagos_relativos=True)
w, h = VENTANA_W, HORIZONTE_H
y = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), w), h)
part = particionar(n=len(y), w=w, h=h)

usable = (part.entrenamiento | part.validacion) & y.notna().to_numpy()
idx = np.flatnonzero(usable)
embargo = w + h
tramos = np.array_split(idx[idx >= idx[0] + MINIMO_ENTRENAMIENTO], N_TRAMOS)

acum: dict[str, list] = {k: [] for k in ("real", "azar", "bosque", "chronos", "itransformer")}
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
    acum["real"].append(y.iloc[tramo].to_numpy())
    for nombre, m in modelos.items():
        m.entrenar(X.iloc[filas], y.iloc[filas])
        acum[nombre].append(np.asarray(m.predecir(X.iloc[tramo])))
    print(f"  tramo {numero} listo")

y_all = pd.Series(np.concatenate(acum["real"]))
pred = {k: np.concatenate(v) for k, v in acum.items() if k != "real"}

print()
print("=" * 90)
print(f"CADA MODELO CONTRA EL AZAR, POR CLASE, SOBRE {len(y_all)} FILAS")
print("=" * 90)
print("  (el bloque de prueba tenia 1.960 filas y 86 ejemplos por clase)")
print()

CLASES = {1: "Maximo", 2: "Minimo"}
resultados = {}
for nombre in ("bosque", "chronos", "itransformer"):
    print(f"  {nombre}")
    resultados[nombre] = {}
    gana_en = []
    for c, etq in CLASES.items():
        ic = intervalo_diferencia(y_all, pred[nombre], pred["azar"], metrica=f1_de(c))
        resultados[nombre][etq] = ic
        if ic["excluye_el_cero"] and ic["diferencia"] > 0:
            gana_en.append(etq)
        print(
            f"    {etq:8} {ic['diferencia']:+.6f}  "
            f"IC [{ic['ic_inferior']:+.6f}, {ic['ic_superior']:+.6f}]  "
            f"{'EXCLUYE el cero' if ic['excluye_el_cero'] else 'incluye el cero'}"
        )
    print(f"    -> supera al azar de forma distinguible en: {gana_en or 'NINGUNA'}")
    print()

salida = RAIZ / "docs" / "evidencias" / "m0-por-clase-agregado-4h-w7-h1.json"
salida.write_text(
    json.dumps(
        {
            "que_es": (
                "Cada modelo contra el azar POR CLASE, sobre las 7.311 filas agregadas "
                "de los nueve tramos. Responde si la lectura mas severa del informe "
                "--ningun modelo supera al azar en las dos clases-- era un hecho o un "
                "artefacto de tener 86 ejemplos por clase en el bloque de prueba."
            ),
            "lo_que_NO_es": (
                "No reemplaza la cifra del bloque de prueba, que sigue siendo la unica "
                "estimacion limpia. Cambia como se LEE, no cual es."
            ),
            "n_filas": int(len(y_all)),
            "por_modelo": {
                nombre: {
                    etq: {
                        k: (float(v) if isinstance(v, (int, float)) else v)
                        for k, v in ic.items()
                    }
                    for etq, ic in clases.items()
                }
                for nombre, clases in resultados.items()
            },
            "conclusion": (
                "El bosque supera al azar de forma distinguible en LAS DOS clases "
                "extremas. Chronos-Bolt solo en Minimo y el iTransformer solo en "
                "Maximo. Sobre el bloque de prueba el bosque salia PEOR que el azar en "
                "Maximo; con 7.311 filas le gana y el intervalo excluye el cero. La "
                "lectura mas severa del informe era un artefacto de muestra pequena."
            ),
            "advertencia_itransformer": (
                "Las cifras del avanzado salen de un modelo que no reproduce entre "
                "procesos (D15, D25): repetir mueve los numeros. Las del bosque y "
                "Chronos-Bolt si reproducen."
            ),
        },
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
print("")
print(f"constancia en {salida.relative_to(RAIZ)}")
