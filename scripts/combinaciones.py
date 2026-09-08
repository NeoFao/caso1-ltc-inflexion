"""Combinar los modelos, que es lo unico que la evidencia de hoy sugiere de nuevo.

De donde sale la idea
---------------------
Medido sobre las 7.311 filas agregadas, cada modelo detecta una mitad distinta:

  bosque         gana al azar en Maximo Y en Minimo
  chronos        gana solo en Minimo
  itransformer   gana solo en Maximo

Que el fundacional y el avanzado sean complementarios --uno los techos, el otro los
suelos-- no lo dijo nadie de antemano: salio de medir. Si es real, combinarlos deberia
detectar las dos cosas mejor que cualquiera por separado.

No es "probar hasta que salga": es la unica hipotesis nueva que los datos proponen, y se
prueba una vez con el resultado que de.

Las tres formas que se prueban
------------------------------
1. **Voto por mayoria** entre los tres. Si dos coinciden, esa gana; si los tres difieren,
   se prefiere continuidad (la clase mayoritaria), que es la decision conservadora.
2. **Union de extremos**: si cualquiera de los tres dice Maximo, es Maximo; igual para
   Minimo. Prioriza encontrar extremos a costa de falsos positivos.
3. **Especialistas**: el Maximo lo decide el iTransformer y el Minimo Chronos-Bolt, que
   es cada uno en la clase donde gano. Es la lectura literal del hallazgo.

Se mide sobre las mismas 7.311 filas agregadas, con intervalos pareados contra el mejor
modelo individual. No toca la reserva.
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
CONTINUIDAD = 3

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
p = {k: np.concatenate(v).astype(int) for k, v in acum.items() if k != "real"}
n = len(y_all)

# --- 1. voto por mayoria
votos = np.stack([p["bosque"], p["chronos"], p["itransformer"]])
mayoria = np.full(n, CONTINUIDAD, dtype=int)
for clase in (1, 2, 3):
    mayoria[(votos == clase).sum(axis=0) >= 2] = clase

# --- 2. union de extremos: Maximo gana sobre Minimo si hubiera choque
union = np.full(n, CONTINUIDAD, dtype=int)
union[(votos == 2).any(axis=0)] = 2
union[(votos == 1).any(axis=0)] = 1

# --- 3. especialistas: Maximo lo decide el avanzado, Minimo el fundacional
espec = np.full(n, CONTINUIDAD, dtype=int)
espec[p["chronos"] == 2] = 2
espec[p["itransformer"] == 1] = 1

print()
print("=" * 88)
print(f"COMBINACIONES, SOBRE LAS {n} FILAS AGREGADAS")
print("=" * 88)
print(f"  {'':26} {'F1 macro':>10} {'F1 max':>9} {'F1 min':>9}")
todos = {
    "azar": p["azar"],
    "bosque (el mejor)": p["bosque"],
    "chronos": p["chronos"],
    "itransformer": p["itransformer"],
    "1. voto por mayoria": mayoria,
    "2. union de extremos": union,
    "3. especialistas": espec,
}
metricas = {}
for etq, pred in todos.items():
    m = evaluar(y_all, pred)
    metricas[etq] = m
    print(f"  {etq:26} {m['f1_macro']:>10.6f} {m['f1_maximo']:>9.6f} {m['f1_minimo']:>9.6f}")

print()
print("=" * 88)
print("CADA COMBINACION CONTRA EL MEJOR MODELO INDIVIDUAL (el bosque)")
print("=" * 88)
for etq in ("1. voto por mayoria", "2. union de extremos", "3. especialistas"):
    ic = intervalo_diferencia(y_all, todos[etq], p["bosque"])
    print(
        f"  {etq:26} {ic['diferencia']:+.6f}  "
        f"IC [{ic['ic_inferior']:+.6f}, {ic['ic_superior']:+.6f}]  "
        f"{'EXCLUYE el cero' if ic['excluye_el_cero'] else 'incluye el cero'}"
    )


# --- lo interesante: por clase, y sobre el promedio de LAS DOS EXTREMAS
from sklearn.metrics import f1_score  # noqa: E402


def f1_de(clases):
    def metrica(y_real, y_pred) -> float:
        return float(
            f1_score(
                np.asarray(y_real, dtype=int),
                np.asarray(y_pred, dtype=int),
                labels=list(clases),
                average="macro",
                zero_division=0,
            )
        )

    return metrica


print()
print("=" * 88)
print("SOLO LAS DOS CLASES QUE IMPORTAN, sin promediar Continuidad")
print("=" * 88)
print("  El F1 macro promedia las TRES clases. Continuidad es el 90,7 % de las velas y")
print("  no es lo que el enunciado pide detectar. Aqui se mira solo Maximo y Minimo.")
print()
print(f"  {'':26} {'F1 de los extremos':>20}")
for etq, pred in todos.items():
    print(f"  {etq:26} {f1_de((1, 2))(y_all, pred):>20.6f}")

print()
print("  Contra el bosque, con intervalo pareado sobre las dos clases extremas:")
for etq in ("1. voto por mayoria", "2. union de extremos", "3. especialistas"):
    ic = intervalo_diferencia(y_all, todos[etq], p["bosque"], metrica=f1_de((1, 2)))
    print(
        f'    {etq:26} {ic["diferencia"]:+.6f}  '
        f'IC [{ic["ic_inferior"]:+.6f}, {ic["ic_superior"]:+.6f}]  '
        f'{"EXCLUYE el cero" if ic["excluye_el_cero"] else "incluye el cero"}'
    )

salida = RAIZ / "docs" / "evidencias" / "m0-combinaciones-4h-w7-h1.json"
salida.write_text(
    json.dumps(
        {
            "que_es": (
                "Quinto arreglo probado: combinar los tres modelos. La idea salio de "
                "medir que cada uno detecta una mitad distinta -- Chronos los minimos y "
                "el iTransformer los maximos-- asi que combinarlos deberia detectar las "
                "dos. Se probaron tres formas."
            ),
            "resultado": (
                "Ninguna se establece. Las tres empeoran el F1 macro. La union de "
                "extremos es la mejor medida sobre las DOS clases extremas (0,109630 "
                "contra 0,091871 del bosque), pero su intervalo incluye el cero."
            ),
            "n_filas": int(n),
            "metricas": {
                etq: {k: float(v) for k, v in m.items() if isinstance(v, (int, float))}
                for etq, m in metricas.items()
            },
            "f1_de_los_extremos": {
                etq: float(f1_de((1, 2))(y_all, pred)) for etq, pred in todos.items()
            },
            "contra_el_bosque": {
                etq: {
                    "f1_macro": {
                        k: (float(v) if isinstance(v, (int, float)) else v)
                        for k, v in intervalo_diferencia(y_all, todos[etq], p["bosque"]).items()
                    },
                    "solo_extremos": {
                        k: (float(v) if isinstance(v, (int, float)) else v)
                        for k, v in intervalo_diferencia(
                            y_all, todos[etq], p["bosque"], metrica=f1_de((1, 2))
                        ).items()
                    },
                }
                for etq in ("1. voto por mayoria", "2. union de extremos", "3. especialistas")
            },
            "lo_que_si_aporta": (
                "El F1 macro promedia las TRES clases, y Continuidad es el 90,7 % de las "
                "velas y no es lo que el enunciado pide detectar. La union de extremos se "
                "ve mal en macro y bien en las extremas: la eleccion de metrica cambia "
                "que modelo parece mejor. Ninguna de las dos lecturas establece la mejora."
            ),
        },
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
print("")
print(f"constancia en {salida.relative_to(RAIZ)}")
