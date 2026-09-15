"""El modelo avanzado solo ve precios de cierre. Las 63 columnas van solo al bosque.

El handicap
-----------
`ITransformerAvanzado` recibe `cierres_del_panel(panel)`: **seis series de cierre y
nada mas**. Las 63 caracteristicas que M2 construyo -- retornos, volatilidad, RSI,
MACD, Bollinger, ventana deslizante, correlacion cruzada -- van **solo al bosque**.

Y despues el informe concluye que ningun modelo profundo mejora al clasico. Esa
conclusion se saco con los profundos **atados**: comparamos un modelo que ve 63
columnas contra uno que ve 6 series.

Chronos-Bolt no entra aqui, y hay que decir por que
---------------------------------------------------
Chronos es *zero-shot* y pronostica una serie a partir de su propio pasado. **No hay
donde inyectarle caracteristicas** sin reentrenarlo, y reentrenar un modelo
fundacional es otro proyecto. Su handicap es estructural y se declara, no se corrige.

El iTransformer si: atiende **entre series**, asi que darle mas series es su forma
natural de recibir mas informacion.

Que se prueba
-------------
El mismo iTransformer con dos entradas distintas:

- **6 series**: los cierres de los seis activos. Es lo que recibe hoy.
- **12 series**: esos seis mas seis indicadores de LTC, **uno por familia** de las que
  exige la RF-F1, en este orden fijo: volatilidad, RSI, MACD, posicion en el rango,
  distancia a la media movil y %B de Bollinger.

**Uno por familia y no los mejores.** Elegir las columnas por su importancia medida
seria elegir la respuesta; ademas esa importancia se midio sobre validacion, que es
justo donde esto se evalua.

La columna de LTC va **primera** en los dos casos, porque el modelo etiqueta la
variate 0: cambiar eso cambiaria lo que se predice y no lo que se ve.

El riesgo, declarado antes
--------------------------
El iTransformer se entrena a **pronosticar todas las series** con un error cuadratico
comun. Con seis series mas, buena parte de la perdida pasa a ser pronosticar RSI y
MACD, que **no es lo que nos interesa**. Puede empeorar por esa via, y si empeora hay
que decir que es eso y no que "las caracteristicas no sirven".

El criterio, fijado ANTES de correr
-----------------------------------
Para decir que darle las caracteristicas ayuda, sobre los nueve tramos:

1. La **ventaja sobre el azar** con 12 series es mayor que con 6.
2. El signo es **estable en los nueve tramos**.

Y la expectativa, tambien antes de mirar
----------------------------------------
**Se espera que no ayude**, por el riesgo de arriba y porque los doce ejes probados
hasta ahora dejaron dos que funcionan y **ninguno toca lo que el modelo ve**.

Pero es el ultimo hueco declarado del proyecto: mientras no se mida, "los profundos
no mejoran al clasico" arrastra la objecion de que nunca les dimos lo mismo.
**Se publique lo que se publique, la objecion queda cerrada.**

No toca la reserva ni el panel del informe.

Punto de entrada (necesita el entorno con torch):
    ...\\.venvs\\caso1\\Scripts\\python.exe scripts/avanzado_con_caracteristicas.py
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

from contracts.config import ACTIVO_OBJETIVO, GRANULARIDAD, HORIZONTE_H, VENTANA_W  # noqa: E402
from contracts.labeling import etiquetar, objetivo  # noqa: E402
from contracts.metrics import evaluar  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from src.features.base import construir  # noqa: E402
from src.modelos.avanzado import ITransformerAvanzado, cierres_del_panel  # noqa: E402
from src.modelos.base import BaselineAleatorio  # noqa: E402
from src.modelos.clasico import HIPERPARAMETROS  # noqa: E402

SALIDA = RAIZ / "docs" / "evidencias" / "m0-avanzado-con-caracteristicas-4h-w7-h1.json"
N_TRAMOS = 9

#: Una por familia de la RF-F1, en orden fijo. Elegidas por familia y no por
#: importancia medida: lo segundo seria elegir la respuesta.
INDICADORES = [
    f"{ACTIVO_OBJETIVO}_volatilidad_7",
    f"{ACTIVO_OBJETIVO}_rsi_14",
    f"{ACTIVO_OBJETIVO}_macd",
    f"{ACTIVO_OBJETIVO}_posicion_rango_7",
    f"{ACTIVO_OBJETIVO}_dist_sma_7",
    f"{ACTIVO_OBJETIVO}_bollinger_pctb_20",
]


def medir(series: pd.DataFrame, X: pd.DataFrame, y: pd.Series, etiqueta: str) -> dict:
    """Nueve tramos con ventana expansiva, el avanzado contra el azar."""
    validos = np.flatnonzero(y.notna().to_numpy())
    embargo = VENTANA_W + HORIZONTE_H
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

        modelo = ITransformerAvanzado(
            series, w=VENTANA_W, h=HORIZONTE_H, semilla=HIPERPARAMETROS["random_state"]
        )
        modelo.entrenar(X.iloc[entrenar_en], y.iloc[entrenar_en])
        azar = BaselineAleatorio(semilla=HIPERPARAMETROS["random_state"])
        azar.entrenar(X.iloc[entrenar_en], y.iloc[entrenar_en])

        verdad = y.iloc[tramo].astype(int).to_numpy()
        mb = evaluar(verdad, np.asarray(modelo.predecir(X.iloc[tramo]), dtype=int))
        ma = evaluar(verdad, np.asarray(azar.predecir(X.iloc[tramo]), dtype=int))
        f1.append(mb["f1_macro"])
        f1_azar.append(ma["f1_macro"])
        ventajas.append(mb["f1_macro"] - ma["f1_macro"])
        print(f"    tramo {i}: {mb['f1_macro']:.6f} vs {ma['f1_macro']:.6f}", flush=True)

    v = np.array(ventajas)
    return {
        "series_de_entrada": int(series.shape[1]),
        "nombres": list(series.columns),
        "f1_macro": round(float(np.mean(f1)), 6),
        "f1_macro_azar": round(float(np.mean(f1_azar)), 6),
        "ventaja_sobre_azar": round(float(v.mean()), 6),
        "tramos_a_favor": int((v > 0).sum()),
        "tramos_medidos": int(len(v)),
        "signo_estable": bool((v > 0).all()),
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    panel = pd.read_parquet(RAIZ / "data" / "processed" / f"panel_{GRANULARIDAD}_v1.parquet")
    X = construir(panel, rezagos_relativos=True)
    y = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), VENTANA_W), HORIZONTE_H)

    seis = cierres_del_panel(panel)
    faltan = [c for c in INDICADORES if c not in X.columns]
    if faltan:
        raise SystemExit(f"faltan columnas declaradas: {faltan}")
    # La de LTC va primera en los dos: el modelo etiqueta la variate 0.
    doce = pd.concat([seis, X[INDICADORES]], axis=1)

    print(f"6 series:  {list(seis.columns)}", flush=True)
    print(f"12 series: {list(doce.columns)}\n", flush=True)

    print("con 6 series (lo de hoy):", flush=True)
    a6 = medir(seis, X, y, "6_cierres")
    print("\ncon 12 series (mas seis indicadores):", flush=True)
    a12 = medir(doce, X, y, "12_con_indicadores")

    ayuda = bool(a12["ventaja_sobre_azar"] > a6["ventaja_sobre_azar"] and a12["signo_estable"])

    medido = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "que_mide": (
            "Si darle al iTransformer indicadores ademas de los cierres mejora su "
            "deteccion. Hoy recibe seis series de cierre y nada mas, mientras el bosque "
            "recibe 63 columnas: el informe concluye que los profundos no mejoran al "
            "clasico con los profundos atados."
        ),
        "por_que_chronos_no_entra": (
            "Es zero-shot y pronostica una serie a partir de su propio pasado: no hay "
            "donde inyectarle caracteristicas sin reentrenarlo, y reentrenar un modelo "
            "fundacional es otro proyecto. Su handicap es estructural y se declara."
        ),
        "como_se_eligieron_los_indicadores": (
            "Uno por familia de la RF-F1, en orden fijo, y no por importancia medida: "
            "elegir por importancia seria elegir la respuesta, y ademas esa importancia "
            "se midio sobre validacion, que es donde esto se evalua."
        ),
        "riesgo_declarado_antes": (
            "El iTransformer se entrena a pronosticar TODAS las series con un error "
            "cuadratico comun. Con seis series mas, buena parte de la perdida pasa a ser "
            "pronosticar RSI y MACD, que no es lo que interesa. Si empeora, es por eso y "
            "no porque las caracteristicas no sirvan."
        ),
        "criterio_preregistrado": (
            "La ventaja sobre el azar con 12 series es mayor que con 6, y el signo es "
            "estable en los nueve tramos."
        ),
        "expectativa_declarada_antes": (
            "Que no ayude, por el riesgo de arriba y porque de los doce ejes probados los "
            "dos que funcionan no tocan lo que el modelo ve. Pero es el ultimo hueco "
            "declarado: mientras no se mida, 'los profundos no mejoran al clasico' "
            "arrastra la objecion de que nunca les dimos lo mismo. Se publique lo que se "
            "publique, la objecion queda cerrada."
        ),
        "no_toca_la_reserva": "Nueve tramos de validacion deslizante.",
        "con_6_series": a6,
        "con_12_series": a12,
        "ayuda": ayuda,
        "veredicto": (
            "Darle indicadores al avanzado SI mejora su ventaja sobre el azar."
            if ayuda
            else "Darle indicadores al avanzado NO mejora su ventaja: el handicap no "
            "explicaba su resultado."
        ),
    }
    SALIDA.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{'':22} {'series':>7} {'F1':>10} {'azar':>9} {'ventaja':>9} {'tramos':>7}")
    for nombre, d in (("6 cierres (hoy)", a6), ("12 con indicadores", a12)):
        print(
            f"{nombre:22} {d['series_de_entrada']:>7} {d['f1_macro']:>10.6f} "
            f"{d['f1_macro_azar']:>9.6f} {d['ventaja_sobre_azar']:>+9.6f} "
            f"{d['tramos_a_favor']:>3}/{d['tramos_medidos']:<3}"
        )
    print(f"\n{medido['veredicto']}")
    print(f"constancia en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
