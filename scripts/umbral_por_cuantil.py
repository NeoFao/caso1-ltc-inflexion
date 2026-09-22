"""El umbral del aviso es un numero fijo, y deberia ser un cuantil. Eje 22.

De donde sale este eje
----------------------
Midiendo la regla de aviso (eje 21) aparecio algo que no se buscaba: tomando las
velas con mayor probabilidad **dentro de cada tramo** hasta llenar la misma
cobertura, la precision sube mucho por encima de la que da el umbral fijo de 0,50
declarado en el proyecto. Misma cobertura agregada, mismo modelo, mismo objetivo.

La causa es que **un umbral fijo es un corte global sobre nueve distribuciones
distintas**. En un tramo el bosque puede pasar de 0,50 en el 30 % de las velas y en
otro casi nunca; el umbral fijo habla mucho donde el modelo esta suelto de confianza
--que no es lo mismo que acertado-- y se calla donde esta prudente.

Y hay una trampa
----------------
Tomar el top k **del tramo de evaluacion** exige conocer ese tramo entero para
calcular su percentil. **Eso es mirar hacia adelante** y por lo tanto no se puede
reportar, por mas que el numero salga bonito. Es exactamente la forma de error que
este proyecto ya cometio una vez, con la ventana simetrica de proximidad.

La version honesta mide lo mismo sin mirar el futuro: **el cuantil se calcula sobre
datos de entrenamiento** y se aplica tal cual al tramo siguiente. El entrenamiento se
parte en ajuste (80 %) y calibracion (20 %, la parte mas reciente); el bosque se
entrena solo con ajuste, el cuantil sale de las probabilidades sobre calibracion, y
el tramo de evaluacion no se toca hasta el final. Es el mismo patron que ya usa
`scripts/regla_decision.py` para elegir alfa.

Las tres reglas que se comparan, a la misma cobertura declarada
---------------------------------------------------------------
1. **Umbral fijo** -- la regla vigente: se avisa si la probabilidad pasa un numero
   fijo, el mismo en los nueve tramos. Se toma el numero que da esa cobertura en
   agregado.
2. **Cuantil de calibracion** -- la candidata: el umbral es el percentil que deja esa
   cobertura **en calibracion**, y se aplica al tramo. Causal.
3. **Top k del tramo** -- el techo inalcanzable: se conoce el tramo entero. **Se
   publica marcado como no reportable**, porque decir cuanto se pierde por ser
   honesto es informacion, y esconderlo seria lo contrario.

El criterio, fijado ANTES de correr
-----------------------------------
Se adopta el cuantil de calibracion **solo si se cumplen las dos**:

1. Su cociente contra el azar **supera** al del umbral fijo en **las tres coberturas
   declaradas** (90 %, 55 % y 18,37 %), que son las que el proyecto ya reporta.
2. En el punto de trabajo, el signo de esa diferencia es **estable en al menos 8 de
   los 9 tramos**.

La expectativa, tambien antes de mirar
--------------------------------------
Se espera que el cuantil de calibracion quede **entre** las otras dos: mejor que el
umbral fijo, porque se adapta a cada tramo, y peor que el top k, porque calibra con
datos anteriores al tramo y la distribucion se mueve. **Si quedara al nivel del top
k, habria que sospechar de la particion**; si quedara al nivel del umbral fijo, la
conclusion seria que la distribucion de probabilidad cambia tanto entre tramos que ni
el tramo anterior sirve para calibrar.

Que NO hace
-----------
No toca el bloque de reserva. No cambia el modelo ni sus hiperparametros: cambia
**como se lee su salida**. El bosque de las reglas 1 y 2 se entrena con menos datos
que el del proyecto (80 % del pasado), y eso juega **en contra** de la candidata: si
gana igual, gana con handicap.

Punto de entrada:
    uv run python scripts/umbral_por_cuantil.py
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
sys.path.insert(0, str(RAIZ / "scripts"))

from proximidad_solo_adelante import objetivo_solo_adelante  # noqa: E402

from contracts.config import ACTIVO_OBJETIVO, GRANULARIDAD, HORIZONTE_H, VENTANA_W  # noqa: E402
from contracts.labeling import Clase, etiquetar, objetivo  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from src.features.base import construir  # noqa: E402
from src.modelos.base import BaselineAleatorio  # noqa: E402
from src.modelos.clasico import HIPERPARAMETROS, BosqueAleatorio  # noqa: E402

SALIDA = RAIZ / "docs" / "evidencias" / "m0-umbral-por-cuantil-4h-w7-h1.json"

N_TRAMOS = 9
VELAS_DE_MARGEN = 2
COBERTURAS = [0.9040, 0.5500, 0.1837]
COBERTURA_DE_TRABAJO = 0.1837
TRAMOS_MINIMOS = 8
PARTE_DE_CALIBRACION = 0.20

RARAS = (int(Clase.MAXIMO), int(Clase.MINIMO))
REGLAS = ("umbral_fijo", "cuantil_de_calibracion", "top_k_del_tramo")


def puntaje_y_tipo(prob: np.ndarray, clases: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    columnas = [int(np.flatnonzero(clases == c)[0]) for c in RARAS]
    p_raras = prob[:, columnas]
    return p_raras.max(axis=1), np.array(RARAS)[p_raras.argmax(axis=1)]


def aciertos(elegidas: np.ndarray, tipo: np.ndarray, verdad: np.ndarray) -> tuple[int, int]:
    if len(elegidas) == 0:
        return 0, 0
    return len(elegidas), int((tipo[elegidas] == verdad[elegidas]).sum())


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    panel = pd.read_parquet(RAIZ / "data" / "processed" / f"panel_{GRANULARIDAD}_v1.parquet")
    X = construir(panel, rezagos_relativos=True)
    exacto = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), VENTANA_W), HORIZONTE_H)
    y = objetivo_solo_adelante(exacto, VELAS_DE_MARGEN)

    validos = np.flatnonzero(y.notna().to_numpy())
    embargo = VENTANA_W + HORIZONTE_H
    corte = len(validos) // 2
    ancho = (len(validos) - corte) // N_TRAMOS

    acumulado = {
        f"{c:.4f}": {
            r: {"avisos": 0, "aciertos": 0, "a_favor": 0} for r in (*REGLAS, "azar")
        }
        for c in COBERTURAS
    }
    umbrales_vistos = {f"{c:.4f}": [] for c in COBERTURAS}
    total = 0

    cabecera = "  ".join(f"{'cob ' + f'{c:.0%}':>26}" for c in COBERTURAS)
    print(f"{'tramo':>6} {'velas':>6}  " + cabecera)
    for i in range(N_TRAMOS):
        inicio = corte + i * ancho
        fin = inicio + ancho if i < N_TRAMOS - 1 else len(validos)
        tramo = validos[inicio:fin]
        pasado = validos[: max(0, inicio - embargo)]
        if len(pasado) < 200 or len(tramo) == 0:
            continue

        # ajuste y calibracion, con el mismo embargo entre las dos partes
        n_cal = int(len(pasado) * PARTE_DE_CALIBRACION)
        ajuste = pasado[: max(0, len(pasado) - n_cal - embargo)]
        calibracion = pasado[len(pasado) - n_cal :]
        if len(ajuste) == 0 or len(calibracion) == 0:
            continue

        bosque = BosqueAleatorio(
            n_arboles=HIPERPARAMETROS["n_estimators"],
            semilla=HIPERPARAMETROS["random_state"],
            nombre="bosque_aleatorio_rezagos_relativos",
        )
        bosque.entrenar(X.iloc[ajuste], y.iloc[ajuste])
        azar = BaselineAleatorio(semilla=HIPERPARAMETROS["random_state"])
        azar.entrenar(X.iloc[ajuste], y.iloc[ajuste])

        tuberia = bosque._tuberia
        clases = tuberia.named_steps["bosque"].classes_
        p_cal, _ = puntaje_y_tipo(
            tuberia.predict_proba(bosque._preparar(X.iloc[calibracion], bosque._columnas)), clases
        )
        p_tramo, tipo = puntaje_y_tipo(
            tuberia.predict_proba(bosque._preparar(X.iloc[tramo], bosque._columnas)), clases
        )
        verdad = y.iloc[tramo].astype(int).to_numpy()
        pred_azar = np.asarray(azar.predecir(X.iloc[tramo]), dtype=int)
        generador = np.random.default_rng(HIPERPARAMETROS["random_state"] + i)
        total += len(tramo)

        celdas = []
        for c in COBERTURAS:
            clave = f"{c:.4f}"
            k = int(round(c * len(tramo)))

            # 1 · umbral fijo: el mismo numero en los nueve tramos, sacado del cuantil
            #     global de calibracion del PRIMER tramo. Se guarda para el informe.
            if not umbrales_vistos[clave]:
                umbrales_vistos[clave].append(float(np.quantile(p_cal, 1 - c)))
            fijo = umbrales_vistos[clave][0]
            sel_fijo = np.flatnonzero(p_tramo >= fijo)

            # 2 · cuantil de calibracion: se recalcula en cada tramo, con datos pasados
            umbral_cal = float(np.quantile(p_cal, 1 - c))
            sel_cal = np.flatnonzero(p_tramo >= umbral_cal)

            # 3 · top k del tramo: mira el tramo entero. NO reportable.
            sel_top = np.argpartition(-p_tramo, min(k, len(p_tramo) - 1))[:k]

            for regla, sel in (
                ("umbral_fijo", sel_fijo),
                ("cuantil_de_calibracion", sel_cal),
                ("top_k_del_tramo", sel_top),
            ):
                n, ac = aciertos(sel, tipo, verdad)
                acumulado[clave][regla]["avisos"] += n
                acumulado[clave][regla]["aciertos"] += ac

            elegidas = generador.choice(len(tramo), size=k, replace=False)
            tipos_azar = np.where(
                np.isin(pred_azar[elegidas], RARAS),
                pred_azar[elegidas],
                generador.choice(RARAS, size=k),
            )
            acumulado[clave]["azar"]["avisos"] += k
            acumulado[clave]["azar"]["aciertos"] += int((tipos_azar == verdad[elegidas]).sum())

            n_f, ac_f = aciertos(sel_fijo, tipo, verdad)
            n_c, ac_c = aciertos(sel_cal, tipo, verdad)
            if n_f and n_c and ac_c / n_c > ac_f / n_f:
                acumulado[clave]["cuantil_de_calibracion"]["a_favor"] += 1
            celdas.append(
                f"{(ac_f / n_f if n_f else 0):>8.4f} {(ac_c / n_c if n_c else 0):>8.4f} "
                f"{aciertos(sel_top, tipo, verdad)[1] / k:>8.4f}"
            )
        print(f"{i:>6} {len(tramo):>6}  " + "  ".join(celdas))

    resultados = {}
    for c in COBERTURAS:
        clave = f"{c:.4f}"
        azar = acumulado[clave]["azar"]
        p_azar = azar["aciertos"] / azar["avisos"]
        fila = {"cobertura_declarada": c, "precision_azar": round(p_azar, 6), "reglas": {}}
        for r in REGLAS:
            d = acumulado[clave][r]
            p = d["aciertos"] / d["avisos"] if d["avisos"] else 0.0
            fila["reglas"][r] = {
                "avisos": d["avisos"],
                "cobertura_real": round(d["avisos"] / total, 6),
                "precision": round(p, 6),
                "cociente_sobre_azar": round(p / p_azar, 6) if p_azar else None,
            }
        fila["reglas"]["cuantil_de_calibracion"]["tramos_a_favor"] = acumulado[clave][
            "cuantil_de_calibracion"
        ]["a_favor"]
        fila["umbral_fijo_usado"] = round(umbrales_vistos[clave][0], 6)
        resultados[clave] = fila

    gana_en_las_tres = all(
        r["reglas"]["cuantil_de_calibracion"]["cociente_sobre_azar"]
        > r["reglas"]["umbral_fijo"]["cociente_sobre_azar"]
        for r in resultados.values()
    )
    trabajo = resultados[f"{COBERTURA_DE_TRABAJO:.4f}"]
    a_favor = trabajo["reglas"]["cuantil_de_calibracion"]["tramos_a_favor"]
    estable = a_favor >= TRAMOS_MINIMOS

    if gana_en_las_tres and estable:
        veredicto = (
            "Se adopta el cuantil de calibracion: gana en las tres coberturas y el signo "
            f"aguanta en {a_favor} de {N_TRAMOS} tramos. En el punto de trabajo el cociente "
            f"pasa de {trabajo['reglas']['umbral_fijo']['cociente_sobre_azar']:.4f} a "
            f"{trabajo['reglas']['cuantil_de_calibracion']['cociente_sobre_azar']:.4f}."
        )
    else:
        falta = []
        if not gana_en_las_tres:
            falta.append("no gana en las tres coberturas")
        if not estable:
            falta.append(f"el signo solo aguanta en {a_favor} de {N_TRAMOS} tramos")
        veredicto = "No se adopta el cuantil de calibracion: " + " y ".join(falta) + "."

    print()
    print(veredicto)

    SALIDA.write_text(
        json.dumps(
            {
                "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                "que_mide": (
                    "Si fijar el umbral del aviso como un CUANTIL calculado sobre datos de "
                    "entrenamiento mejora sobre el umbral fijo que usa hoy el proyecto, a la "
                    "misma cobertura declarada."
                ),
                "la_trampa_que_evita": (
                    "Tomar el top k del tramo de evaluacion exige conocer ese tramo entero para "
                    "calcular su percentil: es mirar hacia adelante. Se publica igual, marcado "
                    "como NO reportable, para decir cuanto se pierde por ser honesto."
                ),
                "criterio_preregistrado": (
                    "Se adopta solo si el cociente sobre el azar supera al del umbral fijo en las "
                    "tres coberturas declaradas y el signo aguanta en al menos "
                    f"{TRAMOS_MINIMOS} de {N_TRAMOS} tramos en el punto de trabajo."
                ),
                "expectativa_declarada_antes": (
                    "Que quede entre las otras dos: mejor que el umbral fijo por adaptarse a "
                    "cada tramo, y peor que el top k por calibrar con datos anteriores."
                ),
                "handicap_de_la_candidata": (
                    "Las reglas 1 y 2 entrenan con el 80 % del pasado, no con todo, porque el "
                    "20 % mas reciente se reserva para calibrar. Juega en contra de la candidata."
                ),
                "no_toca_la_reserva": "Nueve tramos de validacion deslizante.",
                "objetivo": f"solo_adelante_{VELAS_DE_MARGEN}_velas",
                "observaciones": total,
                "resultados": resultados,
                "veredicto": veredicto,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nEvidencia en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
