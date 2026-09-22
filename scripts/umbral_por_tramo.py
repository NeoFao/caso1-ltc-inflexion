"""El umbral fijo reparte el silencio de forma desigual entre tramos. Eje 23.

Que audita esto
---------------
El eje 22 comparo reglas de umbral, pero cambio **dos cosas a la vez**: el modelo
(entrenado con el 80 % del pasado, para tener una particion de calibracion) y la
regla. Con dos cambios simultaneos no se puede atribuir la diferencia a ninguno, asi
que ese resultado no decide nada por si solo.

Este guion aisla la variable. **El modelo es exactamente el del proyecto** --el mismo
bosque, entrenado con todo el pasado, las mismas probabilidades que ya estan
medidas-- y lo unico que cambia es **como se convierte esa probabilidad en un aviso**:

1. **Umbral global** -- la regla vigente. Un numero, el mismo en los nueve tramos.
2. **Umbral por tramo** -- el umbral de cada tramo es el cuantil que deja la cobertura
   buscada **en el tramo anterior**, que es pasado y esta disponible en produccion.
   El primer tramo usa la cola del entrenamiento.

La sospecha que hay que confirmar o descartar
---------------------------------------------
Un umbral global es un corte unico sobre **nueve distribuciones de probabilidad
distintas**. Si en un tramo el bosque pasa de 0,50 en el 40 % de las velas y en otro
casi nunca, el umbral global **habla mucho donde el modelo esta suelto de confianza**
--que no es lo mismo que acertado-- y se calla donde esta prudente. La cobertura
agregada puede dar 18 % y estar repartida entre 2 % y 45 %.

Por eso este guion publica, ademas de la precision, **la cobertura de cada tramo**.
Si la sospecha es correcta, ahi se vera; si la cobertura ya estaba pareja, entonces la
diferencia del eje 22 venia del modelo y no de la regla, y hay que decirlo asi.

El criterio, fijado ANTES de correr
-----------------------------------
Se adopta el umbral por tramo **solo si se cumplen las dos**:

1. Su cociente sobre el azar **supera** al del umbral global en **las tres coberturas
   declaradas** (90 %, 55 % y 18,37 %), a cobertura agregada comparable.
2. El signo aguanta en **al menos 8 de los 9 tramos** en el punto de trabajo.

**Y una condicion de honestidad que se declara aca:** si la cobertura agregada de las
dos reglas difiere en mas de **3 puntos porcentuales**, la comparacion **no es valida**
y se reporta como no concluyente, por mas que los numeros favorezcan a alguna. Comparar
precisiones a coberturas distintas es comparar cosas distintas.

La expectativa, tambien antes de mirar
--------------------------------------
Que el umbral por tramo gane, porque reparte el silencio de forma pareja, y que la
ganancia sea **moderada**. Si apareciera una ganancia enorme, lo primero que hay que
mirar es la cobertura: casi siempre significa que una de las dos reglas esta hablando
menos que la otra.

Que NO hace
-----------
No toca el bloque de reserva. No cambia el modelo, sus datos ni sus hiperparametros.

Punto de entrada:
    uv run python scripts/umbral_por_tramo.py
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

SALIDA = RAIZ / "docs" / "evidencias" / "m0-umbral-por-tramo-4h-w7-h1.json"

N_TRAMOS = 9
VELAS_DE_MARGEN = 2
COBERTURAS = [0.9040, 0.5500, 0.1837]
COBERTURA_DE_TRABAJO = 0.1837
TRAMOS_MINIMOS = 8
DESVIO_MAXIMO_DE_COBERTURA = 0.03

RARAS = (int(Clase.MAXIMO), int(Clase.MINIMO))


def puntaje_y_tipo(prob: np.ndarray, clases: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    columnas = [int(np.flatnonzero(clases == c)[0]) for c in RARAS]
    p_raras = prob[:, columnas]
    return p_raras.max(axis=1), np.array(RARAS)[p_raras.argmax(axis=1)]


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

    # Primera pasada: el modelo del proyecto, tramo por tramo. Se guardan las
    # probabilidades para no entrenar dos veces.
    guardado = []
    print(f"{'tramo':>6} {'velas':>6} {'p media':>9} {'p max':>8}")
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

        tuberia = bosque._tuberia
        clases = tuberia.named_steps["bosque"].classes_
        p, tipo = puntaje_y_tipo(
            tuberia.predict_proba(bosque._preparar(X.iloc[tramo], bosque._columnas)), clases
        )
        cola = validos[max(0, inicio - embargo - len(tramo)) : max(0, inicio - embargo)]
        p_cola, _ = puntaje_y_tipo(
            tuberia.predict_proba(bosque._preparar(X.iloc[cola], bosque._columnas)), clases
        )
        guardado.append(
            {
                "p": p,
                "tipo": tipo,
                "verdad": y.iloc[tramo].astype(int).to_numpy(),
                "pred_azar": np.asarray(azar.predecir(X.iloc[tramo]), dtype=int),
                "p_cola": p_cola,
                "semilla": HIPERPARAMETROS["random_state"] + i,
            }
        )
        print(f"{i:>6} {len(tramo):>6} {p.mean():>9.4f} {p.max():>8.4f}")

    total = sum(len(g["p"]) for g in guardado)
    todas = np.concatenate([g["p"] for g in guardado])

    resultados = {}
    for c in COBERTURAS:
        clave = f"{c:.4f}"
        # El umbral global que deja esa cobertura en agregado: el cuantil de todas las
        # probabilidades juntas. Es la mejor version posible de la regla vigente.
        global_ = float(np.quantile(todas, 1 - c))

        acum = {
            "global": {"avisos": 0, "aciertos": 0},
            "por_tramo": {"avisos": 0, "aciertos": 0},
            "azar": {"avisos": 0, "aciertos": 0},
        }
        cobertura_global, cobertura_tramo, a_favor = [], [], 0

        for j, g in enumerate(guardado):
            n = len(g["p"])
            sel_g = np.flatnonzero(g["p"] >= global_)
            # umbral del tramo: cuantil del tramo ANTERIOR; el primero usa la cola
            # del entrenamiento, que tambien es pasado
            referencia = guardado[j - 1]["p"] if j > 0 else g["p_cola"]
            umbral_t = float(np.quantile(referencia, 1 - c)) if len(referencia) else global_
            sel_t = np.flatnonzero(g["p"] >= umbral_t)

            for nombre, sel in (("global", sel_g), ("por_tramo", sel_t)):
                acum[nombre]["avisos"] += len(sel)
                acum[nombre]["aciertos"] += int((g["tipo"][sel] == g["verdad"][sel]).sum())

            cobertura_global.append(round(len(sel_g) / n, 4))
            cobertura_tramo.append(round(len(sel_t) / n, 4))
            if len(sel_g) and len(sel_t):
                pg = (g["tipo"][sel_g] == g["verdad"][sel_g]).mean()
                pt = (g["tipo"][sel_t] == g["verdad"][sel_t]).mean()
                a_favor += int(pt > pg)

            k = int(round(c * n))
            gen = np.random.default_rng(g["semilla"])
            elegidas = gen.choice(n, size=k, replace=False)
            tipos_azar = np.where(
                np.isin(g["pred_azar"][elegidas], RARAS),
                g["pred_azar"][elegidas],
                gen.choice(RARAS, size=k),
            )
            acum["azar"]["avisos"] += k
            acum["azar"]["aciertos"] += int((tipos_azar == g["verdad"][elegidas]).sum())

        p_azar = acum["azar"]["aciertos"] / acum["azar"]["avisos"]
        fila = {
            "cobertura_declarada": c,
            "umbral_global": round(global_, 6),
            "precision_azar": round(p_azar, 6),
            "cobertura_por_tramo_regla_global": cobertura_global,
            "cobertura_por_tramo_regla_por_tramo": cobertura_tramo,
            "dispersion_de_cobertura_global": round(
                float(max(cobertura_global) - min(cobertura_global)), 4
            ),
            "dispersion_de_cobertura_por_tramo": round(
                float(max(cobertura_tramo) - min(cobertura_tramo)), 4
            ),
            "tramos_a_favor_del_por_tramo": a_favor,
            "reglas": {},
        }
        for nombre in ("global", "por_tramo"):
            d = acum[nombre]
            p = d["aciertos"] / d["avisos"] if d["avisos"] else 0.0
            fila["reglas"][nombre] = {
                "avisos": d["avisos"],
                "cobertura_real": round(d["avisos"] / total, 6),
                "precision": round(p, 6),
                "cociente_sobre_azar": round(p / p_azar, 6) if p_azar else None,
            }
        fila["comparacion_valida"] = bool(
            abs(
                fila["reglas"]["global"]["cobertura_real"]
                - fila["reglas"]["por_tramo"]["cobertura_real"]
            )
            <= DESVIO_MAXIMO_DE_COBERTURA
        )
        resultados[clave] = fila

    validas = all(r["comparacion_valida"] for r in resultados.values())
    gana_en_las_tres = all(
        r["reglas"]["por_tramo"]["cociente_sobre_azar"]
        > r["reglas"]["global"]["cociente_sobre_azar"]
        for r in resultados.values()
    )
    trabajo = resultados[f"{COBERTURA_DE_TRABAJO:.4f}"]
    estable = trabajo["tramos_a_favor_del_por_tramo"] >= TRAMOS_MINIMOS

    if not validas:
        veredicto = (
            "No concluyente: en alguna cobertura las dos reglas terminan hablando cantidades "
            "demasiado distintas, y comparar precisiones a coberturas distintas no dice nada."
        )
    elif gana_en_las_tres and estable:
        veredicto = (
            "Se adopta el umbral por tramo: gana en las tres coberturas y el signo aguanta en "
            f"{trabajo['tramos_a_favor_del_por_tramo']} de {N_TRAMOS} tramos. En el punto de "
            f"trabajo el cociente pasa de "
            f"{trabajo['reglas']['global']['cociente_sobre_azar']:.4f} a "
            f"{trabajo['reglas']['por_tramo']['cociente_sobre_azar']:.4f}."
        )
    else:
        falta = []
        if not gana_en_las_tres:
            falta.append("no gana en las tres coberturas")
        if not estable:
            falta.append(
                f"el signo solo aguanta en {trabajo['tramos_a_favor_del_por_tramo']} de {N_TRAMOS}"
            )
        veredicto = "No se adopta el umbral por tramo: " + " y ".join(falta) + "."

    print()
    for r in resultados.values():
        print(
            f"cobertura {r['cobertura_declarada']:.4f}  "
            f"global {r['reglas']['global']['precision']:.6f} "
            f"(cob {r['reglas']['global']['cobertura_real']:.4f}, "
            f"dispersion {r['dispersion_de_cobertura_global']:.4f})  |  "
            f"por tramo {r['reglas']['por_tramo']['precision']:.6f} "
            f"(cob {r['reglas']['por_tramo']['cobertura_real']:.4f}, "
            f"dispersion {r['dispersion_de_cobertura_por_tramo']:.4f})  |  "
            f"azar {r['precision_azar']:.6f}"
        )
    print()
    print(veredicto)

    SALIDA.write_text(
        json.dumps(
            {
                "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                "que_mide": (
                    "Si convertir la probabilidad en aviso con un umbral por tramo -- el cuantil "
                    "del tramo anterior -- mejora sobre el umbral global unico, con el MISMO "
                    "modelo del proyecto y a cobertura comparable."
                ),
                "por_que_aisla": (
                    "El eje 22 cambio el modelo y la regla a la vez y por eso no atribuye. Aca "
                    "el modelo es el del proyecto y lo unico que cambia es la regla."
                ),
                "criterio_preregistrado": (
                    "Gana en las tres coberturas declaradas, signo estable en al menos "
                    f"{TRAMOS_MINIMOS} de {N_TRAMOS} tramos, y las coberturas agregadas de las "
                    f"dos reglas no difieren en mas de {DESVIO_MAXIMO_DE_COBERTURA:.0%}."
                ),
                "expectativa_declarada_antes": (
                    "Que el umbral por tramo gane de forma moderada. Una ganancia enorme seria "
                    "senal de cobertura mal igualada antes que de una regla mejor."
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
