"""Predecir "hay un giro cerca" en vez de "esta vela exacta es el giro".

De donde sale esto
------------------
`aviso_con_tolerancia.py` midio que los fallos del modelo **no son aleatorios: caen
alrededor del giro real**. Admitiendo una vela de margen, la ventaja sobre el azar
pasa de +0,050963 a +0,228766 -- cuatro veces y media.

O sea que el modelo ya contesta bastante bien *"estamos cerca de un giro"*, y todo
el proyecto lo ha estado puntuando por *"esta vela exacta es el giro"*. Esto prueba
lo obvio que faltaba: **entrenarlo directamente en la pregunta que responde mejor**.

Que cambia
----------
La etiqueta. Una vela es **Maximo** si hay un maximo real a `k` velas o menos;
**Minimo** igual; **Continuidad** si no hay ninguno cerca. Si hubiera de los dos,
gana el mas cercano, y en empate el maximo (regla arbitraria, fijada aqui y no
despues).

Con `k = 0` es **exactamente** la etiqueta de siempre, y eso sirve de control: si a
k=0 este guion no reprodujera las cifras conocidas, el defecto estaria aqui.

Y de paso ataca el desbalance: con `k = 2` cada giro genera hasta cinco filas
positivas en vez de una. Los 420 ejemplos de la clase minoritaria dejan de ser 420.

Esto NO es una mejora del modelo. Es un problema distinto
---------------------------------------------------------
Y hay que decirlo fuerte, porque la tentacion de presentarlo como mejora es enorme:
**predecir "hay giro cerca" es mas facil que predecir "es aqui".** El F1 va a subir
solo, sin que el modelo sea mejor.

Por eso la unica comparacion que significa algo es **contra el `baseline_aleatorio`
entrenado y medido sobre la MISMA etiqueta**. Si el F1 sube pero la ventaja sobre el
azar no, entonces la tarea se hizo mas facil para todos y no ganamos nada.

El criterio, fijado ANTES de correr
-----------------------------------
Para decir que el objetivo de proximidad aporta, para algun `k >= 1`:

1. La **ventaja sobre el azar** en F1 macro es **mayor** que la que hay en `k = 0`.
2. La ventaja es positiva en las **dos clases extremas**.
3. El signo es **estable en los nueve tramos**.

Y la expectativa, tambien antes de mirar
----------------------------------------
Se espera que el F1 absoluto suba con `k` en los dos, modelo y azar. **Lo que no se
sabe es si la ventaja crece.** La medicion de tolerancia sugiere que si, pero eso
media un modelo entrenado en la etiqueta exacta y evaluado con margen; aqui el
modelo se entrena en la etiqueta nueva, que es otra cosa y puede salir peor.

**Si la ventaja no crece, la conclusion es que no aporta**, y se publica asi.

Lo que esto NO hace
-------------------
No reemplaza nada. El objetivo del informe sigue siendo el exacto, que es el que
pide el enunciado. Esto se reporta **al lado**, como un problema distinto.

Y no toca el bloque de prueba, que se gasto el 07/09. Nueve tramos de validacion
deslizante.

Punto de entrada:
    uv run python scripts/objetivo_proximidad.py
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
from contracts.labeling import Clase, etiquetar, objetivo  # noqa: E402
from contracts.metrics import evaluar  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from src.features.base import construir  # noqa: E402
from src.modelos.base import BaselineAleatorio  # noqa: E402
from src.modelos.clasico import HIPERPARAMETROS, BosqueAleatorio  # noqa: E402

SALIDA = RAIZ / "docs" / "evidencias" / "m0-objetivo-proximidad-4h-w7-h1.json"

N_TRAMOS = 9
CERCANIAS = [0, 1, 2, 3]
MAXIMO, MINIMO, CONTINUIDAD = int(Clase.MAXIMO), int(Clase.MINIMO), int(Clase.CONTINUIDAD)


def objetivo_cercano(exacto: pd.Series, k: int) -> pd.Series:
    """La etiqueta de proximidad: hay un giro de ese tipo a `k` velas o menos.

    Con k=0 devuelve la etiqueta exacta sin tocarla. Donde el exacto es nulo -- las
    filas sin ventana completa -- el resultado sigue siendo nulo: no se inventa
    informacion en los bordes.
    """
    if k == 0:
        return exacto.copy()

    v = exacto.to_numpy(dtype=float)
    n = len(v)
    salida = np.full(n, np.nan)
    for i in range(n):
        if np.isnan(v[i]):
            continue
        desde, hasta = max(0, i - k), min(n, i + k + 1)
        ventana = v[desde:hasta]
        posiciones = np.arange(desde, hasta)
        etiqueta = CONTINUIDAD
        mejor = None
        for clase in (MAXIMO, MINIMO):
            donde = posiciones[ventana == clase]
            if len(donde):
                d = int(np.min(np.abs(donde - i)))
                # Empate a la misma distancia: gana Maximo. Regla arbitraria, fijada
                # aqui y no despues de ver el resultado.
                if mejor is None or d < mejor:
                    mejor, etiqueta = d, clase
        salida[i] = etiqueta
    return pd.Series(salida, index=exacto.index, name="objetivo").astype("Int64")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    panel = pd.read_parquet(RAIZ / "data" / "processed" / f"panel_{GRANULARIDAD}_v1.parquet")
    X = construir(panel, rezagos_relativos=True)
    exacto = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), VENTANA_W), HORIZONTE_H)

    embargo = VENTANA_W + HORIZONTE_H
    resultados: dict[str, dict] = {}

    for k in CERCANIAS:
        y = objetivo_cercano(exacto, k)
        validos = np.flatnonzero(y.notna().to_numpy())
        corte = len(validos) // 2
        ancho = (len(validos) - corte) // N_TRAMOS

        ventajas, ventajas_max, ventajas_min = [], [], []
        f1_modelo, f1_azar = [], []
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

            f1_modelo.append(mb["f1_macro"])
            f1_azar.append(ma["f1_macro"])
            ventajas.append(mb["f1_macro"] - ma["f1_macro"])
            ventajas_max.append(mb["f1_maximo"] - ma["f1_maximo"])
            ventajas_min.append(mb["f1_minimo"] - ma["f1_minimo"])

        vent = np.array(ventajas)
        yv = y.dropna().astype(int)
        resultados[str(k)] = {
            "velas_de_margen": k,
            "horas_de_margen": k * 4,
            "por_ciento_giros": round(float((yv != CONTINUIDAD).mean()), 6),
            "n_clase_maximo": int((yv == MAXIMO).sum()),
            "n_clase_minimo": int((yv == MINIMO).sum()),
            "f1_macro_modelo": round(float(np.mean(f1_modelo)), 6),
            "f1_macro_azar": round(float(np.mean(f1_azar)), 6),
            "ventaja_f1_macro": round(float(vent.mean()), 6),
            "ventaja_f1_maximo": round(float(np.mean(ventajas_max)), 6),
            "ventaja_f1_minimo": round(float(np.mean(ventajas_min)), 6),
            "tramos_a_favor": int((vent > 0).sum()),
            "tramos_medidos": int(len(vent)),
            "signo_estable": bool((vent > 0).all()),
        }
        d = resultados[str(k)]
        print(
            f"k={k} ({k * 4:>2} h)  giros {d['por_ciento_giros']:.4f}  "
            f"F1 {d['f1_macro_modelo']:.6f} vs {d['f1_macro_azar']:.6f}  "
            f"ventaja {d['ventaja_f1_macro']:+.6f}  "
            f"tramos {d['tramos_a_favor']}/{d['tramos_medidos']}",
            flush=True,
        )

    base = resultados["0"]["ventaja_f1_macro"]
    cumplen = [
        k
        for k in map(str, CERCANIAS[1:])
        if resultados[k]["ventaja_f1_macro"] > base
        and resultados[k]["ventaja_f1_maximo"] > 0
        and resultados[k]["ventaja_f1_minimo"] > 0
        and resultados[k]["signo_estable"]
    ]

    medido = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "que_mide": (
            "Entrenar el modelo en 'hay un giro a k velas o menos' en vez de 'esta vela "
            "exacta es el giro'. Con k=0 es la etiqueta de siempre y sirve de control."
        ),
        "no_es_una_mejora_del_modelo": (
            "Es un problema DISTINTO y mas facil: el F1 sube solo sin que el modelo sea "
            "mejor. Por eso la unica comparacion que significa algo es contra el "
            "baseline_aleatorio entrenado y medido sobre la MISMA etiqueta. Si el F1 "
            "sube pero la ventaja no, la tarea se hizo mas facil para todos."
        ),
        "criterio_preregistrado": (
            "Para algun k>=1: (1) la ventaja sobre el azar en F1 macro es MAYOR que la "
            "de k=0, (2) la ventaja es positiva en las dos clases extremas, y (3) el "
            "signo es estable en los nueve tramos."
        ),
        "expectativa_declarada_antes": (
            "Se espera que el F1 absoluto suba con k en los dos. No se sabe si la "
            "ventaja crece: la medicion de tolerancia lo sugiere, pero aquella media un "
            "modelo entrenado en la etiqueta exacta y evaluado con margen, y aqui el "
            "modelo se entrena en la etiqueta nueva, que es otra cosa y puede salir "
            "peor. Si la ventaja no crece, no aporta."
        ),
        "regla_de_empate": "A la misma distancia gana Maximo. Fijada antes de correr.",
        "no_reemplaza_nada": (
            "El objetivo del informe sigue siendo el exacto, que es el que pide el "
            "enunciado. Esto se reporta al lado, como un problema distinto."
        ),
        "no_toca_la_reserva": "Nueve tramos de validacion deslizante.",
        "parametros": {
            "intervalo": GRANULARIDAD,
            "w": VENTANA_W,
            "h": HORIZONTE_H,
            "cercanias": CERCANIAS,
            "n_tramos": N_TRAMOS,
        },
        "resultados": resultados,
        "cercanias_que_cumplen": cumplen,
        "veredicto": (
            "El objetivo de proximidad SI aporta: la ventaja sobre el azar crece."
            if cumplen
            else "La ventaja sobre el azar no crece: la tarea se hizo mas facil para "
            "todos y el objetivo de proximidad no aporta."
        ),
    }
    SALIDA.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n{medido['veredicto']}")
    print(f"constancia en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
