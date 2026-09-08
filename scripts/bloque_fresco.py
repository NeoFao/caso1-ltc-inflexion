"""Un bloque de prueba NUEVO: velas que no existian cuando se construyo el modelo.

Que es esto
-----------
El panel del proyecto termina el 05/08/2026. Desde entonces el mercado siguio y hay
velas nuevas. Este guion las descarga y las usa como un bloque de evaluacion **que nadie
ha visto nunca** -- ni el modelo, ni nosotros al elegir caracteristicas, ni al fijar
`w`, `h` o la granularidad.

Es la evidencia mas limpia que puede existir para este proyecto, y la unica que no
depende de la disciplina de nadie: **no existia cuando se tomaron las decisiones.**

Lo que NO es
------------
**No reemplaza al bloque de prueba**, que se midio una sola vez el 07/09 y cuya cifra el
informe reporta sin cambios. Este bloque es adicional, se declara como tal, y su
resultado se publica **salga como salga**.

Y viene con una limitacion grande que hay que decir antes de mirar el numero: son unas
200 velas, con unos nueve ejemplos de cada clase extrema. La curva de potencia del propio
proyecto dice que a ese tamano **no se puede esperar que un intervalo excluya el cero**
aunque el efecto exista: con 1.000 velas la deteccion sale el 42 % de las veces, y aqui
hay cinco veces menos.

Asi que esto no puede confirmar deteccion. Lo que si puede es **desmentirla**: si el
modelo saliera claramente por debajo del azar sobre datos frescos, eso si seria
informativo.

El modelo NO se reentrena
-------------------------
Se entrena con el mismo bloque de entrenamiento de siempre y se le pide que prediga las
velas nuevas. Reentrenar con datos posteriores convertiria esto en otra cosa.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from contracts.config import ACTIVO_OBJETIVO, ACTIVOS, HORIZONTE_H, VENTANA_W  # noqa: E402
from contracts.labeling import etiquetar, objetivo  # noqa: E402
from contracts.metrics import evaluar  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from contracts.splits import particionar  # noqa: E402
from src.features.base import construir  # noqa: E402
from src.features.incertidumbre import intervalo_diferencia  # noqa: E402
from src.modelos.base import BaselineAleatorio  # noqa: E402
from src.modelos.clasico import HIPERPARAMETROS, BosqueAleatorio  # noqa: E402
from src.panel.consolidacion import consolidar  # noqa: E402
from src.panel.descarga import descargar_activo  # noqa: E402

EVIDENCIAS = RAIZ / "docs" / "evidencias"
PANEL_VIEJO = RAIZ / "data" / "processed" / "panel_4h_v1.parquet"

panel_viejo = pd.read_parquet(PANEL_VIEJO)
fin_viejo = panel_viejo.index.max()
print(f"El panel del proyecto termina el {fin_viejo}")

print("\nDescargando velas nuevas de los seis activos...")
series = {a: descargar_activo(a, "4h", desde="2020-08-01") for a in ACTIVOS}
panel = consolidar(series)
panel = panel.loc[panel.index >= panel_viejo.index.min()]

nuevas = panel.index > fin_viejo
print(f"  panel extendido: {len(panel)} velas   nuevas: {int(nuevas.sum())}")
if nuevas.sum() == 0:
    raise SystemExit("no hay velas nuevas: no hay nada que medir")

# Las caracteristicas se calculan sobre el panel ENTERO porque necesitan historia hacia
# atras; la evaluacion mira solo las filas nuevas.
X = construir(panel, rezagos_relativos=True)
w, h = VENTANA_W, HORIZONTE_H
y = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), w), h)

# El entrenamiento es el MISMO de siempre: la particion original sobre el panel viejo.
part_vieja = particionar(n=len(panel_viejo), w=w, h=h)
indices_entrenamiento = panel_viejo.index[part_vieja.entrenamiento]
entren = panel.index.isin(indices_entrenamiento) & y.notna().to_numpy()
frescas = nuevas & y.notna().to_numpy()

print(f"  entrenamiento: {int(entren.sum())} velas (las de siempre)")
print(f"  bloque fresco evaluable: {int(frescas.sum())} velas")
yf = y[frescas]
print(f"    maximos reales: {int((yf == 1).sum())}   minimos reales: {int((yf == 2).sum())}")

bosque = BosqueAleatorio(
    n_arboles=HIPERPARAMETROS["n_estimators"],
    semilla=HIPERPARAMETROS["random_state"],
    nombre="bosque_aleatorio_rezagos_relativos",
)
bosque.entrenar(X[entren], y[entren])
azar = BaselineAleatorio(semilla=HIPERPARAMETROS["random_state"])
azar.entrenar(X[entren], y[entren])

p_bosque = np.asarray(bosque.predecir(X[frescas]))
p_azar = np.asarray(azar.predecir(X[frescas]))

m_b = evaluar(yf, p_bosque)
m_a = evaluar(yf, p_azar)
ic = intervalo_diferencia(yf, p_bosque, p_azar)

print()
print("=" * 78)
print("EL BLOQUE FRESCO — datos que no existian cuando se construyo el modelo")
print("=" * 78)
print(f"  {'':10} {'F1 macro':>10} {'F1 max':>9} {'F1 min':>9} {'Prec. dir.':>11}")
for etq, m in (("bosque", m_b), ("azar", m_a)):
    print(
        f"  {etq:10} {m['f1_macro']:>10.6f} {m['f1_maximo']:>9.6f} "
        f"{m['f1_minimo']:>9.6f} {m['precision_direccional']:>11.6f}"
    )
print()
print(
    f"  diferencia {ic['diferencia']:+.6f}   IC [{ic['ic_inferior']:+.6f}, "
    f"{ic['ic_superior']:+.6f}]   "
    f"{'EXCLUYE el cero' if ic['excluye_el_cero'] else 'incluye el cero'}"
)

salida = EVIDENCIAS / "m0-bloque-fresco-4h-w7-h1.json"
salida.write_text(
    json.dumps(
        {
            "que_es": (
                "Bloque de evaluacion con velas descargadas DESPUES de construir el "
                "modelo: no existian cuando se eligieron caracteristicas, w, h ni "
                "granularidad. Es la unica evidencia que no depende de la disciplina de "
                "nadie."
            ),
            "no_reemplaza_la_reserva": (
                "El bloque de prueba se midio una sola vez el 07/09 y su cifra es la que "
                "el informe reporta. Este bloque es ADICIONAL y se publica salga como "
                "salga."
            ),
            "limitacion": (
                "Son pocas velas y unos nueve ejemplos por clase extrema. La curva de "
                "potencia del proyecto dice que a ese tamano no cabe esperar que el "
                "intervalo excluya el cero aunque el efecto exista. Esto NO puede "
                "confirmar deteccion; si podria desmentirla."
            ),
            "el_modelo_no_se_reentrena": (
                "Se entrena con el mismo bloque de entrenamiento de siempre y se le pide "
                "predecir las velas nuevas."
            ),
            "panel_viejo_termina": str(fin_viejo),
            "n_velas_nuevas": int(nuevas.sum()),
            "n_evaluables": int(frescas.sum()),
            "maximos_reales": int((yf == 1).sum()),
            "minimos_reales": int((yf == 2).sum()),
            "metricas": {
                "bosque": {k: float(v) for k, v in m_b.items() if isinstance(v, (int, float))},
                "azar": {k: float(v) for k, v in m_a.items() if isinstance(v, (int, float))},
            },
            "contra_el_azar": {
                k: (float(v) if isinstance(v, (int, float)) else v) for k, v in ic.items()
            },
        },
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
print(f"\nconstancia en {salida.relative_to(RAIZ)}")
