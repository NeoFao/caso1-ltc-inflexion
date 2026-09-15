"""¿Quien gana sobre el objetivo que SI funciona? Nunca se ha comparado.

El hueco
--------
La comparacion que sostiene el veredicto del proyecto -- "ningun modelo profundo
mejora al bosque clasico" -- se ha hecho **siempre sobre el objetivo exacto**: acertar
la vela en la que ocurre el giro.

Y ese objetivo resulto ser el que peor le sienta al sistema. Sobre el de **proximidad
a una vela**, la ventaja del bosque sobre el azar se multiplica por cinco.

**Los tres modelos nunca se han comparado sobre ese objetivo.** Y el veredicto podria
cambiar: los dos profundos pronostican una **trayectoria** y despues se etiqueta. Si
lo que el puente estropea es la precision de la vela exacta -- que es lo que la
medicion de M3 sugiere, con el iTransformer marcando giros pero lejos -- entonces una
etiqueta con margen deberia **perdonarles** justamente eso.

Es la comparacion con mas probabilidad de dar vuelta una conclusion del informe, y
esta sin hacer.

Que se mide
-----------
Los tres modelos -- bosque, Chronos-Bolt e iTransformer -- mas el
`baseline_aleatorio`, sobre los nueve tramos, con **los dos objetivos**: el exacto y
el de proximidad a una vela. El exacto sirve de control: si no reprodujera el orden
conocido, el defecto estaria en este guion.

El criterio, fijado ANTES de correr
-----------------------------------
Para decir que el veredicto cambia con el objetivo de proximidad:

1. Algun modelo profundo tiene que **superar al bosque** en F1 macro sobre el
   objetivo de proximidad.
2. Con el signo **estable en los nueve tramos**. Una media a favor con cuatro tramos
   en contra no da vuelta nada: es la leccion de la limitacion 2.

Y sobre el iTransformer manda la D25: **su intervalo no decide**, porque no reproduce
entre procesos. Lo que decide es la estabilidad del signo entre tramos.

Y la expectativa, tambien antes de mirar
----------------------------------------
**Se espera que el bosque siga ganando, pero que la distancia se acorte.**

El razonamiento: el puente perjudica la precision de la vela exacta, y una etiqueta
con margen deberia perdonar parte de eso. Pero el bosque tambien mejora con el
margen, y parte de sus 63 columnas -- la posicion en el rango, la distancia a la media
-- son justamente informacion de "estamos cerca de un extremo", que es lo que la
etiqueta nueva premia.

**Si algun profundo ganara en los nueve tramos, seria el resultado mas importante de
todo el trabajo**, porque daria vuelta la conclusion central. Por eso el criterio pide
los nueve y no una media.

No toca la reserva. Nueve tramos de validacion deslizante.

Punto de entrada (necesita el entorno con torch y chronos):
    ...\\.venvs\\caso1\\Scripts\\python.exe scripts/modelos_sobre_proximidad.py
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
from src.modelos.base import BaselineAleatorio  # noqa: E402
from src.modelos.clasico import HIPERPARAMETROS, BosqueAleatorio  # noqa: E402

sys.path.insert(0, str(RAIZ / "scripts"))
from objetivo_proximidad import objetivo_cercano  # noqa: E402

SALIDA = RAIZ / "docs" / "evidencias" / "m0-modelos-sobre-proximidad-4h-w7-h1.json"
N_TRAMOS = 9


def fabricas(panel: pd.DataFrame) -> dict:
    from src.modelos.avanzado import ITransformerAvanzado, cierres_del_panel
    from src.modelos.fundacional import ChronosBolt

    semilla = HIPERPARAMETROS["random_state"]
    return {
        "bosque_aleatorio": lambda: BosqueAleatorio(
            n_arboles=HIPERPARAMETROS["n_estimators"],
            semilla=semilla,
            nombre="bosque_aleatorio_rezagos_relativos",
        ),
        "chronos_bolt": lambda: ChronosBolt(
            cierre(panel, ACTIVO_OBJETIVO), w=VENTANA_W, h=HORIZONTE_H
        ),
        "itransformer": lambda: ITransformerAvanzado(
            cierres_del_panel(panel), w=VENTANA_W, h=HORIZONTE_H, semilla=semilla
        ),
        "baseline_aleatorio": lambda: BaselineAleatorio(semilla=semilla),
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    panel = pd.read_parquet(RAIZ / "data" / "processed" / f"panel_{GRANULARIDAD}_v1.parquet")
    X = construir(panel, rezagos_relativos=True)
    exacto = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), VENTANA_W), HORIZONTE_H)
    nombres = ["bosque_aleatorio", "chronos_bolt", "itransformer", "baseline_aleatorio"]

    resultados: dict[str, dict] = {}
    for k, objetivo_nombre in ((0, "exacto"), (1, "proximidad_1_vela")):
        y = objetivo_cercano(exacto, k)
        validos = np.flatnonzero(y.notna().to_numpy())
        embargo = VENTANA_W + HORIZONTE_H
        corte = len(validos) // 2
        ancho = (len(validos) - corte) // N_TRAMOS

        por_modelo = {n: [] for n in nombres}
        print(f"\n=== objetivo {objetivo_nombre} ===", flush=True)
        for i in range(N_TRAMOS):
            inicio = corte + i * ancho
            fin = inicio + ancho if i < N_TRAMOS - 1 else len(validos)
            tramo = validos[inicio:fin]
            entrenar_en = validos[: max(0, inicio - embargo)]
            if len(entrenar_en) == 0 or len(tramo) == 0:
                continue

            verdad = y.iloc[tramo].astype(int).to_numpy()
            linea = [f"  tramo {i}:"]
            for n in nombres:
                modelo = fabricas(panel)[n]()
                modelo.entrenar(X.iloc[entrenar_en], y.iloc[entrenar_en])
                m = evaluar(verdad, np.asarray(modelo.predecir(X.iloc[tramo]), dtype=int))
                por_modelo[n].append(m["f1_macro"])
                linea.append(f"{n[:8]} {m['f1_macro']:.4f}")
            print("  ".join(linea), flush=True)

        base = np.array(por_modelo["bosque_aleatorio"])
        azar = np.array(por_modelo["baseline_aleatorio"])
        fila = {}
        for n in nombres:
            v = np.array(por_modelo[n])
            contra_bosque = v - base
            fila[n] = {
                "f1_macro": round(float(v.mean()), 6),
                "ventaja_sobre_azar": round(float((v - azar).mean()), 6),
                "contra_el_bosque": round(float(contra_bosque.mean()), 6),
                "tramos_por_encima_del_bosque": int((contra_bosque > 0).sum()),
                "tramos_medidos": int(len(v)),
                "gana_al_bosque_en_los_nueve": bool(
                    n != "bosque_aleatorio" and (contra_bosque > 0).all()
                ),
            }
        resultados[objetivo_nombre] = fila

    prox = resultados["proximidad_1_vela"]
    cambia = [n for n in ("chronos_bolt", "itransformer") if prox[n]["gana_al_bosque_en_los_nueve"]]

    medido = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "que_mide": (
            "Quien gana entre los tres modelos sobre el objetivo de proximidad a una "
            "vela. La comparacion que sostiene el veredicto del proyecto se ha hecho "
            "siempre sobre el objetivo exacto, que resulto ser el que peor le sienta al "
            "sistema."
        ),
        "por_que_podria_cambiar": (
            "Los dos profundos pronostican una trayectoria y despues se etiqueta. Si lo "
            "que el puente estropea es la precision de la vela exacta -- que es lo que "
            "midio M3, con el iTransformer marcando giros pero lejos -- una etiqueta con "
            "margen deberia perdonarles justamente eso."
        ),
        "criterio_preregistrado": (
            "Para decir que el veredicto cambia: algun profundo supera al bosque en F1 "
            "macro sobre el objetivo de proximidad, con el signo estable en los NUEVE "
            "tramos. Una media a favor con cuatro tramos en contra no da vuelta nada: es "
            "la leccion de la limitacion 2. Y sobre el iTransformer manda la D25, su "
            "intervalo no decide."
        ),
        "expectativa_declarada_antes": (
            "Que el bosque siga ganando pero que la distancia se acorte. El puente "
            "perjudica la vela exacta y el margen deberia perdonar parte, pero el bosque "
            "tambien mejora con el margen y parte de sus 63 columnas -- posicion en el "
            "rango, distancia a la media -- son justamente informacion de 'estamos cerca "
            "de un extremo', que es lo que la etiqueta nueva premia. Si algun profundo "
            "ganara en los nueve, seria el resultado mas importante del trabajo."
        ),
        "el_exacto_es_el_control": (
            "Si el objetivo exacto no reprodujera el orden conocido, el defecto estaria "
            "en este guion y no en los modelos."
        ),
        "no_toca_la_reserva": "Nueve tramos de validacion deslizante.",
        "resultados": resultados,
        "modelos_que_dan_vuelta_el_veredicto": cambia,
        "veredicto": (
            f"El veredicto CAMBIA sobre el objetivo de proximidad: {', '.join(cambia)} "
            "supera al bosque en los nueve tramos."
            if cambia
            else "El veredicto NO cambia: ningun modelo profundo supera al bosque en los "
            "nueve tramos, tampoco sobre el objetivo de proximidad."
        ),
    }
    SALIDA.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")

    for objetivo_nombre, fila in resultados.items():
        print(f"\n--- objetivo {objetivo_nombre}")
        print(f"{'modelo':22} {'F1 macro':>10} {'vs azar':>9} {'vs bosque':>10} {'tramos':>7}")
        for n in nombres:
            d = fila[n]
            print(
                f"{n:22} {d['f1_macro']:>10.6f} {d['ventaja_sobre_azar']:>+9.6f} "
                f"{d['contra_el_bosque']:>+10.6f} "
                f"{d['tramos_por_encima_del_bosque']:>3}/{d['tramos_medidos']:<3}"
            )
    print(f"\n{medido['veredicto']}")
    print(f"constancia en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
