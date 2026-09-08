"""La mejora del apilado, comprobada en los nueve tramos del walk-forward.

Una sola particion puede dar una mejora por suerte. Antes de afirmar nada, se repite la
comparacion --entrenar solo con LTC contra entrenar con los seis apilados-- en los nueve
tramos consecutivos, con el mismo embargo y el mismo procedimiento.

Si la mejora aguanta en los nueve, es real. Si aparece en cinco, era la particion.

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
    a: (construir_para(panel, a), objetivo(etiquetar(cierre(panel, a), w), h))
    for a in ACTIVOS
}
XL, yL = tandas[ACTIVO_OBJETIVO]

usable = (part.entrenamiento | part.validacion) & yL.notna().to_numpy()
idx = np.flatnonzero(usable)
embargo = w + h
disponibles = idx[idx >= idx[0] + MINIMO_ENTRENAMIENTO]
tramos = np.array_split(disponibles, N_TRAMOS)


def bosque():
    return BosqueAleatorio(
        n_arboles=HIPERPARAMETROS["n_estimators"],
        semilla=HIPERPARAMETROS["random_state"],
        nombre="bosque",
    )


print("=" * 94)
print("SOLO LTC contra LOS SEIS APILADOS, en los nueve tramos")
print("=" * 94)
print(f"{'tramo':>6} {'solo LTC':>10} {'los seis':>10} {'diferencia':>12}   {'azar':>8}")

difs, ventajas_pool, ventajas_solo = [], [], []
for i, tramo in enumerate(tramos):
    corte = tramo[0] - embargo
    filas_ltc = idx[idx < corte]
    if len(filas_ltc) < MINIMO_ENTRENAMIENTO:
        continue

    m1 = bosque()
    m1.entrenar(XL.iloc[filas_ltc], yL.iloc[filas_ltc])
    r_solo = evaluar(yL.iloc[tramo], m1.predecir(XL.iloc[tramo]))

    # El apilado usa, de cada activo, exactamente las mismas FILAS temporales.
    pX, py = [], []
    for Xa, ya in tandas.values():
        ok = np.zeros(len(ya), dtype=bool)
        ok[filas_ltc] = True
        ok &= ya.notna().to_numpy()
        pX.append(Xa[ok])
        py.append(ya[ok])
    m2 = bosque()
    m2.entrenar(pd.concat(pX), pd.concat(py))
    r_pool = evaluar(yL.iloc[tramo], m2.predecir(XL.iloc[tramo]))

    az = BaselineAleatorio(semilla=HIPERPARAMETROS["random_state"])
    az.entrenar(XL.iloc[filas_ltc], yL.iloc[filas_ltc])
    r_az = evaluar(yL.iloc[tramo], az.predecir(XL.iloc[tramo]))

    d = r_pool["f1_macro"] - r_solo["f1_macro"]
    difs.append(d)
    ventajas_pool.append(r_pool["f1_macro"] - r_az["f1_macro"])
    ventajas_solo.append(r_solo["f1_macro"] - r_az["f1_macro"])
    print(
        f"{i:>6} {r_solo['f1_macro']:>10.4f} {r_pool['f1_macro']:>10.4f} "
        f"{d:>+12.4f}   {r_az['f1_macro']:>8.4f}"
    )

difs = np.array(difs)
print()
print("=" * 94)
print(f"  el apilado mejora en  {int((difs > 0).sum())} de {len(difs)} tramos")
print(f"  mejora media          {difs.mean():+.6f}")
print(f"  minima / maxima       {difs.min():+.6f} / {difs.max():+.6f}")
print()
print(f"  ventaja sobre el azar   solo LTC  {np.mean(ventajas_solo):+.6f}")
print(f"                          apilado   {np.mean(ventajas_pool):+.6f}")

# La particion unica del proyecto, para tener las dos lecturas en el mismo archivo: la
# que favorece al apilado y la que lo relativiza.
entren_p = np.flatnonzero(part.entrenamiento & yL.notna().to_numpy())
val_p = np.flatnonzero(part.validacion & yL.notna().to_numpy())

m_solo = bosque()
m_solo.entrenar(XL.iloc[entren_p], yL.iloc[entren_p])
r_solo_p = evaluar(yL.iloc[val_p], m_solo.predecir(XL.iloc[val_p]))

pX, py = [], []
for Xa, ya in tandas.values():
    ok = np.zeros(len(ya), dtype=bool)
    ok[entren_p] = True
    ok &= ya.notna().to_numpy()
    pX.append(Xa[ok])
    py.append(ya[ok])
m_pool = bosque()
m_pool.entrenar(pd.concat(pX), pd.concat(py))
r_pool_p = evaluar(yL.iloc[val_p], m_pool.predecir(XL.iloc[val_p]))

az_p = BaselineAleatorio(semilla=HIPERPARAMETROS["random_state"])
az_p.entrenar(XL.iloc[entren_p], yL.iloc[entren_p])
r_az_p = evaluar(yL.iloc[val_p], az_p.predecir(XL.iloc[val_p]))

print()
print("=" * 94)
print("LA PARTICION UNICA DEL PROYECTO (la lectura que favorece al apilado)")
print("=" * 94)
for etq, r in (("solo LTC", r_solo_p), ("los seis apilados", r_pool_p), ("azar", r_az_p)):
    print(
        f"  {etq:20} F1 macro {r['f1_macro']:.4f}  max {r['f1_maximo']:.4f}  "
        f"min {r['f1_minimo']:.4f}  ventaja {r['f1_macro'] - r_az_p['f1_macro']:+.4f}"
    )

salida = RAIZ / "docs" / "evidencias" / "m0-apilado-multiactivo-4h-w7-h1.json"
salida.write_text(
    json.dumps(
        {
            "que_es": (
                "Cuarto arreglo probado despues de la corrida: entrenar con los SEIS "
                "activos apilados en vez de solo LTC, para multiplicar por seis los "
                "ejemplos de la clase rara. Es el unico de los cuatro que mejora."
            ),
            "como": (
                "Se construyen las mismas familias de caracteristicas centradas en cada "
                "activo y se apilan las seis tandas. La correlacion cruzada queda FUERA "
                "del juego comun: sus columnas nombran a los otros activos, asi que "
                "'corr con BTC' significa algo distinto segun de quien sea la tanda. Por "
                "eso la comparacion usa el mismo juego de 28 columnas en los dos casos."
            ),
            "no_se_puede_afirmar": (
                "Mejora en 6 de 9 tramos, no en los nueve. El criterio del propio "
                "proyecto (condicion 3 de la D16) pide que el signo no cambie, y aqui "
                "cambia en tres. Se reporta como la via mas prometedora de las cuatro "
                "probadas, con su efecto medido, y NO como una mejora demostrada."
            ),
            "particion_unica": {
                etq: {
                    **{k: float(v) for k, v in r.items() if isinstance(v, (int, float))},
                    # La ventaja es una RESTA. Se guarda en vez de dejar que el informe
                    # la calcule: una cifra derivada que el documento cita y la
                    # evidencia no tiene es lo que `verificar_numeros` marca, con razon.
                    "ventaja_sobre_el_azar": float(r["f1_macro"] - r_az_p["f1_macro"]),
                }
                for etq, r in (
                    ("solo_ltc", r_solo_p),
                    ("apilado", r_pool_p),
                    ("azar", r_az_p),
                )
            },
            "por_tramo": [float(x) for x in difs],
            "tramos_que_mejoran": int((difs > 0).sum()),
            "de": len(difs),
            "mejora_media": float(difs.mean()),
            "mejora_minima": float(difs.min()),
            "mejora_maxima": float(difs.max()),
            "ventaja_media_sobre_el_azar": {
                "solo_ltc": float(np.mean(ventajas_solo)),
                "apilado": float(np.mean(ventajas_pool)),
            },
        },
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
print("")
print(f"constancia en {salida.relative_to(RAIZ)}")
