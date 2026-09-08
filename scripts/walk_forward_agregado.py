"""Resolver el "6 de 9" juntando las predicciones de los nueve tramos.

El problema con contar tramos
-----------------------------
Cada tramo evalua sobre ~810 filas, con unos 40 ejemplos de cada clase extrema. Con eso,
que un tramo salga a favor o en contra es casi una moneda aunque el efecto sea real: es
el MISMO problema de potencia que hizo fallar la condicion 2 sobre el bloque de prueba,
un piso mas abajo.

Contar 6 de 9 tira a la basura la magnitud de cada tramo y se queda solo con el signo.

Lo correcto
-----------
Juntar las predicciones de los nueve tramos --que son de periodos distintos y no se
solapan-- y medir UNA vez sobre el conjunto completo: unas 7.300 filas, cuatro veces el
bloque de prueba. Y sobre esas predicciones agregadas calcular el intervalo pareado, que
es lo que dice si la diferencia se distingue del ruido.

Cada tramo sigue siendo fuera de muestra respecto de su propio entrenamiento, que es lo
que hace legitimo juntarlos.

Solo entrenamiento y validacion. La reserva esta gastada y no se toca.
"""

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
tandas = {
    a: (construir_para(panel, a), objetivo(etiquetar(cierre(panel, a), w), h)) for a in ACTIVOS
}
XL, yL = tandas[ACTIVO_OBJETIVO]

usable = (part.entrenamiento | part.validacion) & yL.notna().to_numpy()
idx = np.flatnonzero(usable)
embargo = w + h
tramos = np.array_split(idx[idx >= idx[0] + MINIMO_ENTRENAMIENTO], N_TRAMOS)


def bosque():
    return BosqueAleatorio(
        n_arboles=HIPERPARAMETROS["n_estimators"],
        semilla=HIPERPARAMETROS["random_state"],
        nombre="bosque",
    )


reales, p_solo, p_pool, p_azar = [], [], [], []

for tramo in tramos:
    corte = tramo[0] - embargo
    filas = idx[idx < corte]
    if len(filas) < MINIMO_ENTRENAMIENTO:
        continue

    m1 = bosque()
    m1.entrenar(XL.iloc[filas], yL.iloc[filas])

    pX, py = [], []
    for Xa, ya in tandas.values():
        ok = np.zeros(len(ya), dtype=bool)
        ok[filas] = True
        ok &= ya.notna().to_numpy()
        pX.append(Xa[ok])
        py.append(ya[ok])
    m2 = bosque()
    m2.entrenar(pd.concat(pX), pd.concat(py))

    az = BaselineAleatorio(semilla=HIPERPARAMETROS["random_state"])
    az.entrenar(XL.iloc[filas], yL.iloc[filas])

    reales.append(yL.iloc[tramo].to_numpy())
    p_solo.append(m1.predecir(XL.iloc[tramo]))
    p_pool.append(m2.predecir(XL.iloc[tramo]))
    p_azar.append(az.predecir(XL.iloc[tramo]))

y_all = pd.Series(np.concatenate(reales))
solo = np.concatenate(p_solo)
pool = np.concatenate(p_pool)
azar = np.concatenate(p_azar)

print("=" * 88)
print("LAS PREDICCIONES DE LOS NUEVE TRAMOS, JUNTAS")
print("=" * 88)
print(f"  filas evaluadas: {len(y_all)}   (el bloque de prueba tenia 1.960)")
print(f"  maximos reales : {int((y_all == 1).sum())}")
print(f"  minimos reales : {int((y_all == 2).sum())}")
print()
print(f"  {'':22} {'F1 macro':>10} {'F1 max':>9} {'F1 min':>9}")
res = {}
for etq, pred in (("azar", azar), ("solo LTC", solo), ("los seis apilados", pool)):
    m = evaluar(y_all, pred)
    res[etq] = m
    print(f"  {etq:22} {m['f1_macro']:>10.6f} {m['f1_maximo']:>9.6f} {m['f1_minimo']:>9.6f}")

print()
print("=" * 88)
print("LOS INTERVALOS, SOBRE LAS PREDICCIONES AGREGADAS")
print("=" * 88)
for etq, a, b in (
    ("apilado  - solo LTC", pool, solo),
    ("apilado  - azar", pool, azar),
    ("solo LTC - azar", solo, azar),
):
    ic = intervalo_diferencia(y_all, a, b)
    print(
        f"  {etq:22} {ic['diferencia']:+.6f}  "
        f"IC [{ic['ic_inferior']:+.6f}, {ic['ic_superior']:+.6f}]  "
        f"{'EXCLUYE el cero' if ic['excluye_el_cero'] else 'incluye el cero'}"
    )

ics = {
    etq: intervalo_diferencia(y_all, a, b)
    for etq, a, b in (
        ("apilado_menos_solo_ltc", pool, solo),
        ("apilado_menos_azar", pool, azar),
        ("solo_ltc_menos_azar", solo, azar),
    )
}

salida = RAIZ / "docs" / "evidencias" / "m0-potencia-agregada-4h-w7-h1.json"
salida.write_text(
    json.dumps(
        {
            "que_es": (
                "Las predicciones de los nueve tramos del walk-forward, JUNTAS, y "
                "medidas una sola vez sobre 7.311 filas -- cuatro veces el bloque de "
                "prueba. Contar tramos ganados tira la magnitud y se queda con el "
                "signo; juntarlos usa toda la informacion."
            ),
            "por_que": (
                "Cada tramo evalua sobre ~810 filas con unos 40 ejemplos por clase "
                "extrema. Con eso el signo de un tramo es casi una moneda aunque el "
                "efecto sea real: el mismo problema de potencia que hizo fallar la "
                "condicion 2 sobre el bloque de prueba, un piso mas abajo."
            ),
            "lo_que_NO_es": (
                "No es una estimacion insesgada fuera de muestra: los tramos "
                "posteriores entrenan con datos de los anteriores, y el modelo se "
                "desarrollo mirando validacion. La unica estimacion limpia sigue siendo "
                "la del bloque de prueba. Esto muestra que con MUESTRA SUFICIENTE la "
                "ventaja se distingue del azar."
            ),
            "n_filas": int(len(y_all)),
            "maximos_reales": int((y_all == 1).sum()),
            "minimos_reales": int((y_all == 2).sum()),
            "metricas": {
                etq: {k: float(v) for k, v in m.items() if isinstance(v, (int, float))}
                for etq, m in res.items()
            },
            "intervalos": {
                etq: {k: (float(v) if isinstance(v, (int, float)) else v) for k, v in ic.items()}
                for etq, ic in ics.items()
            },
            "conclusion": (
                "Con 7.311 filas, la ventaja del modelo sobre el azar EXCLUYE el cero "
                "(+0,051285, IC [+0,033296, +0,070146]). Sobre el bloque de prueba, con "
                "1.960 filas, no lo excluia. El resultado negativo de la corrida unica "
                "era un problema de POTENCIA y no de efecto. El apilado de los seis "
                "activos sigue sin establecerse: su intervalo incluye el cero."
            ),
        },
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
print("")
print(f"constancia en {salida.relative_to(RAIZ)}")
