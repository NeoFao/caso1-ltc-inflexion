"""Dos decisiones nuestras que limitan justamente lo que nos limita.

De donde sale
-------------
`granularidad_1h.py` midio que **el limite es el numero de eventos**, no el de
observaciones: unos 1 220 giros en seis anios, y muestrear mas fino no crea mas. Y
dejo dos salidas: **mas periodo** o **mas activos**. Lo segundo se midio y no ayuda
(los cripto se mueven juntos).

Revisando el propio expediente aparecen **dos decisiones nuestras** que reducen el
numero de eventos. Ninguna las tomo el enunciado. Las tomamos nosotros.

Decision 1: elegimos el w que produce MENOS giros
-------------------------------------------------
`estudio-w-h.json` dice, literalmente, que la regla fue *"el **mayor** w que deja al
menos 300 ejemplos de la clase minoritaria"*. Y el estudio mide cuantos deja cada w
a 4 horas:

    w = 3  ->  884 ejemplos       w = 7  ->  420   <- el elegido
    w = 5  ->  557                w = 10 ->  299

**Elegir el mayor w admisible es elegir el que da menos eventos.** Con w = 3 hay
**mas del doble**. Y en todo el estudio **no hay una sola medicion de rendimiento por
w**: la decision se valido contra un piso de muestra, nunca contra la deteccion.

**La contrapartida es real y hay que medirla, no suponerla.** Un w menor define giros
mas superficiales: con w = 3 basta que el cierre supere a 3 vecinos por lado en vez
de 7. Mas eventos, pero cada uno menos marcado. Por eso este guion mide **tambien el
margen del extremo sobre su vecino**, que es lo que la Tabla C.1 usa para decir cuan
pronunciado es un giro. Si el rendimiento sube pero el margen se hunde, lo que se
detecta mejor es ruido.

Decision 2: incluir Solana nos cuesta 27 meses
----------------------------------------------
El panel empieza el 11/08/2020 y lo fija **SOL**, que es el activo con menos
historia. Los otros cinco empiezan entre agosto de 2017 y mayo de 2018.

    BTC, ETH  2017-08      ADA  2018-04
    LTC       2017-12      XRP  2018-05      SOL  2020-08  <- fija el panel

**Sin SOL el panel empezaria en mayo de 2018**: dos anios y tres meses mas, de 13 114
velas a unas 18 000. Cerca de **un 37 % mas de periodo y de giros** -- y "mas periodo"
es una de las dos unicas salidas que la medicion de granularidad identifico.

Mantener seis activos y ganar la historia es compatible: basta sustituir SOL por uno
con historia larga. Se usa **BCH**, que ya esta descargado y empieza antes.

Que se mide
-----------
1. El rendimiento sobre los nueve tramos con **w = 3, 5 y 7**, y el margen medio del
   extremo sobre su vecino en cada caso.
2. El rendimiento con el panel de siempre contra el **panel sin SOL** (BCH en su
   lugar), con w = 7 en los dos para que lo unico que cambie sea el periodo.

El criterio, fijado ANTES de correr
-----------------------------------
**Para w:** un w distinto de 7 mejora si su **ventaja sobre el azar** es mayor y el
signo aguanta en los nueve tramos. Y se reporta **junto al margen**: una mejora con el
margen hundido no se presenta como mejora, se presenta como que la etiqueta se
ablando.

**Para el periodo:** el panel largo mejora si su ventaja sobre el azar es mayor que la
del corto con el signo estable en los nueve. Ojo: los tramos del panel largo cubren
fechas distintas, asi que la comparacion no es pareada vela a vela; lo que se compara
es el sistema completo, no dos predicciones sobre las mismas filas.

Y la expectativa, tambien antes de mirar
----------------------------------------
**Para w se espera que 3 y 5 mejoren la ventaja**, porque el desbalance es el problema
declarado del proyecto y doblar los ejemplos lo alivia. **Y se espera que el margen
baje**, porque un giro con 3 vecinos por lado es mas superficial por construccion. La
pregunta abierta es si el margen baja tanto que la mejora no significa nada.

**Para el periodo se espera que ayude**, y es la unica de las dos salidas que la
medicion de granularidad dejo sin probar. Si no ayudara, seria informativo: querria
decir que el mercado de 2018 es tan distinto que sus giros no ensenan nada sobre los
de 2024.

**Nada de esto cambia lo que el informe reporta.** El enunciado define el punto de
inflexion y el proyecto congelo w = 7 el 18 de agosto: esto mide **el costo de esa
decision**, no la reemplaza.

No toca la reserva.

Punto de entrada:
    uv run python scripts/decisiones_que_limitan.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from contracts.config import ACTIVO_OBJETIVO, HORIZONTE_H, VENTANA_W  # noqa: E402
from contracts.labeling import Clase, etiquetar, objetivo  # noqa: E402
from contracts.metrics import evaluar  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from src.features.base import construir  # noqa: E402
from src.modelos.base import BaselineAleatorio  # noqa: E402
from src.modelos.clasico import HIPERPARAMETROS, BosqueAleatorio  # noqa: E402

SALIDA = RAIZ / "docs" / "evidencias" / "m0-decisiones-que-limitan.json"
PANEL_4H = RAIZ / "data" / "processed" / "panel_4h_v1.parquet"
CRUDOS = RAIZ / "data" / "processed" / "extra"
N_TRAMOS = 9
WS = [3, 5, 7]
MAXIMO, MINIMO, CONTINUIDAD = int(Clase.MAXIMO), int(Clase.MINIMO), int(Clase.CONTINUIDAD)


def margen_medio(serie: pd.Series, etiquetas: pd.Series, w: int) -> float:
    """Por cuanto le gana cada extremo a su vecino mas cercano, en por ciento.

    Es la misma medida de la Tabla C.1: dice cuan pronunciado es un giro, y por eso
    es la contrapartida natural de bajar w.
    """
    v = serie.to_numpy(dtype=float)
    e = etiquetas.to_numpy(dtype=float)
    margenes = []
    for i in range(w, len(v) - w):
        if e[i] == MAXIMO:
            vecino = max(v[i - 1], v[i + 1])
            margenes.append(100 * (v[i] - vecino) / vecino)
        elif e[i] == MINIMO:
            vecino = min(v[i - 1], v[i + 1])
            margenes.append(100 * (vecino - v[i]) / vecino)
    return float(np.mean(margenes)) if margenes else float("nan")


def medir(X: pd.DataFrame, y: pd.Series, w: int) -> dict:
    validos = np.flatnonzero(y.notna().to_numpy())
    embargo = w + HORIZONTE_H
    corte = len(validos) // 2
    ancho = (len(validos) - corte) // N_TRAMOS

    f1, f1_azar, ventajas = [], [], []
    for i in range(N_TRAMOS):
        inicio = corte + i * ancho
        fin = inicio + ancho if i < N_TRAMOS - 1 else len(validos)
        tramo = validos[inicio:fin]
        entrenar_en = validos[: max(0, inicio - embargo)]
        if len(entrenar_en) == 0 or len(tramo) == 0:
            continue

        bosque = BosqueAleatorio(
            n_arboles=HIPERPARAMETROS["n_estimators"],
            semilla=HIPERPARAMETROS["random_state"],
            nombre="bosque_aleatorio_rezagos_relativos",
        )
        bosque.entrenar(X.iloc[entrenar_en], y.iloc[entrenar_en])
        azar = BaselineAleatorio(semilla=HIPERPARAMETROS["random_state"])
        azar.entrenar(X.iloc[entrenar_en], y.iloc[entrenar_en])

        verdad = y.iloc[tramo].astype(int).to_numpy()
        mb = evaluar(verdad, np.asarray(bosque.predecir(X.iloc[tramo]), dtype=int))
        ma = evaluar(verdad, np.asarray(azar.predecir(X.iloc[tramo]), dtype=int))
        f1.append(mb["f1_macro"])
        f1_azar.append(ma["f1_macro"])
        ventajas.append(mb["f1_macro"] - ma["f1_macro"])

    v = np.array(ventajas)
    yv = y.dropna().astype(int)
    return {
        "n_evaluables": int(len(yv)),
        "n_clase_minoritaria": int(min((yv == MAXIMO).sum(), (yv == MINIMO).sum())),
        "por_ciento_velas_con_giro": round(float(100 * (yv != CONTINUIDAD).mean()), 2),
        "f1_macro": round(float(np.mean(f1)), 6),
        "f1_macro_azar": round(float(np.mean(f1_azar)), 6),
        "ventaja_sobre_azar": round(float(v.mean()), 6),
        "tramos_a_favor": int((v > 0).sum()),
        "tramos_medidos": int(len(v)),
        "signo_estable": bool((v > 0).all()),
    }


def panel_sin_sol() -> pd.DataFrame:
    """El panel con BCH en lugar de SOL, para recuperar el periodo que SOL recorta."""
    from src.panel.consolidacion import consolidar
    from src.panel.descarga import descargar_activo

    archivo = CRUDOS / "BCH_4h_largo.parquet"
    if archivo.exists():
        bch = pd.read_parquet(archivo)
    else:
        from contracts.config import SIMBOLOS

        SIMBOLOS.setdefault("BCH", "BCHUSDT")
        bch = descargar_activo("BCH", "4h", desde="2017-01-01")
        CRUDOS.mkdir(parents=True, exist_ok=True)
        bch.to_parquet(archivo)

    series = {}
    for a in ("LTC", "BTC", "ETH", "XRP", "ADA"):
        crudo = pd.read_parquet(RAIZ / "data" / "raw" / f"{a}_4h.parquet")
        series[a] = crudo
    # BCH ocupa el hueco de SOL: consolidar exige los seis nombres del contrato, asi
    # que entra con la etiqueta de SOL. No cambia ningun calculo -- las
    # caracteristicas de apoyo solo usan sus propias columnas -- y evita parchear un
    # contrato congelado.
    series["SOL"] = bch
    return consolidar(series)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    panel = pd.read_parquet(PANEL_4H)
    X = construir(panel, rezagos_relativos=True)
    precio = cierre(panel, ACTIVO_OBJETIVO)

    print("=== decision 1: el w que elegimos produce menos giros ===", flush=True)
    por_w = {}
    for w in WS:
        etiquetas = etiquetar(precio, w)
        y = objetivo(etiquetas, HORIZONTE_H)
        d = medir(X, y, w)
        d["margen_medio_por_ciento"] = round(margen_medio(precio, etiquetas, w), 4)
        d["horas_de_ventana"] = w * 4
        por_w[str(w)] = d
        print(
            f"  w={w} ({w * 4:>2} h)  minoria {d['n_clase_minoritaria']:>4}  "
            f"margen {d['margen_medio_por_ciento']:>6.4f} %  "
            f"F1 {d['f1_macro']:.6f} vs {d['f1_macro_azar']:.6f}  "
            f"ventaja {d['ventaja_sobre_azar']:+.6f}  "
            f"tramos {d['tramos_a_favor']}/{d['tramos_medidos']}",
            flush=True,
        )

    print("\n=== decision 2: incluir SOL recorta 27 meses ===", flush=True)
    largo = panel_sin_sol()
    Xl = construir(largo, rezagos_relativos=True)
    yl = objetivo(etiquetar(cierre(largo, ACTIVO_OBJETIVO), VENTANA_W), HORIZONTE_H)
    d_largo = medir(Xl, yl, VENTANA_W)
    d_largo["velas"] = int(len(largo))
    d_largo["desde"] = str(largo.index.min())
    d_corto = dict(por_w[str(VENTANA_W)])
    d_corto["velas"] = int(len(panel))
    d_corto["desde"] = str(panel.index.min())
    for etq, d in (("con SOL (el del informe)", d_corto), ("con BCH en su lugar", d_largo)):
        print(
            f"  {etq:26} {d['velas']:>6} velas desde {d['desde'][:10]}  "
            f"minoria {d['n_clase_minoritaria']:>4}  ventaja {d['ventaja_sobre_azar']:+.6f}  "
            f"tramos {d['tramos_a_favor']}/{d['tramos_medidos']}",
            flush=True,
        )

    base = por_w[str(VENTANA_W)]["ventaja_sobre_azar"]
    mejores_w = [
        w
        for w in map(str, WS)
        if w != str(VENTANA_W)
        and por_w[w]["ventaja_sobre_azar"] > base
        and por_w[w]["signo_estable"]
    ]
    periodo_ayuda = bool(d_largo["ventaja_sobre_azar"] > base and d_largo["signo_estable"])

    medido = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "que_mide": (
            "El costo de dos decisiones nuestras que reducen el numero de eventos, que "
            "es el limite que granularidad_1h identifico. Ninguna la tomo el enunciado."
        ),
        "decision_1": (
            "estudio-w-h fijo w=7 como 'el MAYOR w que deja al menos 300 ejemplos de la "
            "clase minoritaria'. Elegir el mayor w admisible es elegir el que da menos "
            "eventos: con w=3 hay 884 ejemplos contra 420. Y en todo el estudio no hay "
            "una sola medicion de rendimiento por w."
        ),
        "decision_2": (
            "El panel empieza el 11/08/2020 y lo fija SOL, el activo con menos historia. "
            "Los otros cinco empiezan entre 2017-08 y 2018-05. Sin SOL el panel "
            "empezaria en mayo de 2018: unos 27 meses mas."
        ),
        "criterio_preregistrado": (
            "Para w: un w distinto de 7 mejora si su ventaja sobre el azar es mayor y el "
            "signo aguanta en los nueve tramos, Y se reporta junto al margen: una mejora "
            "con el margen hundido no es una mejora, es una etiqueta ablandada. Para el "
            "periodo: el panel largo mejora si su ventaja es mayor con signo estable. La "
            "comparacion del periodo NO es pareada vela a vela, porque los tramos cubren "
            "fechas distintas: se comparan dos sistemas, no dos predicciones."
        ),
        "expectativa_declarada_antes": (
            "Para w, que 3 y 5 mejoren la ventaja porque el desbalance es el problema "
            "declarado y doblar los ejemplos lo alivia; y que el margen baje, porque un "
            "giro con 3 vecinos por lado es mas superficial por construccion. La "
            "pregunta abierta es si baja tanto que la mejora no significa nada. Para el "
            "periodo, que ayude: es la unica de las dos salidas que quedaba sin probar. "
            "Si no ayudara seria informativo: que el mercado de 2018 es tan distinto que "
            "sus giros no ensenan nada sobre los de 2024."
        ),
        "no_cambia_lo_que_el_informe_reporta": (
            "El enunciado define el punto de inflexion y el proyecto congelo w=7 el "
            "18/08. Esto mide el COSTO de esa decision, no la reemplaza."
        ),
        "por_w": por_w,
        "periodo": {"corto_con_SOL": d_corto, "largo_con_BCH": d_largo},
        "w_que_mejoran": mejores_w,
        "el_periodo_ayuda": periodo_ayuda,
    }
    SALIDA.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nw que mejoran la ventaja con signo estable: {mejores_w or 'ninguno'}")
    print(f"el periodo largo ayuda: {periodo_ayuda}")
    print(f"constancia en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
