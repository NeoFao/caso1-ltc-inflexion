"""¿Los avisos que fallan, fallan por mucho o por una vela?

La pregunta
-----------
Todo lo que este proyecto mide usa la definicion **exacta**: un aviso acierta solo si
**esa vela exacta** era el giro. Errar por una vela cuenta igual que errar por diez.

Eso es lo correcto para medir el modelo y no se toca. Pero no es la pregunta que se
hace quien mira el grafico: un aviso **una vela antes** del giro real no se lee como
un fallo, se lee como un aviso a tiempo. Son cuatro horas.

**Nadie lo ha medido.** Y cambia que frase es verdad: no es lo mismo "nueve de cada
diez avisos estan mal" que "nueve de cada diez no caen en la vela exacta, pero la
mitad de esos cae al lado".

Que se mide
-----------
La precision del aviso admitiendo una tolerancia de `k` velas: un aviso de clase `c`
en la vela `i` acierta si **alguna** vela de `[i-k, i+k]` es un giro real de clase
`c`. Con `k = 0` es exactamente la medida de siempre.

Se mide para k = 0, 1, 2 y 3, en el umbral **0,40**, que es el punto de operacion
defendible que dejo `aviso_con_abstencion.py`.

El piso se mueve con la tolerancia, y ahi esta la trampa
--------------------------------------------------------
Ampliar la ventana sube la precision **de cualquiera**, incluido el azar: con `k = 3`
cada aviso tiene siete velas para acertar en vez de una. Reportar la precision con
tolerancia sin mover el piso seria inflar el numero.

Por eso el `baseline_aleatorio` se mide **con la misma tolerancia y a la misma
cobertura**. Lo que importa no es que el numero suba, sino **si sube mas que el del
azar**.

El criterio, fijado ANTES de correr
-----------------------------------
Para decir que la tolerancia cambia algo tiene que cumplirse, para algun `k >= 1`:

1. La precision con tolerancia **supera a la del azar con la misma tolerancia y
   cobertura**.
2. La **ventaja sobre el azar** es mayor que la que ya hay en `k = 0`. Si la ventaja
   no crece, la tolerancia esta ayudando por igual a los dos y no dice nada del
   modelo.
3. El signo de esa ventaja es **estable en los nueve tramos**.

Y la expectativa, tambien antes de mirar
----------------------------------------
Se espera que la precision suba con `k` en los dos, modelo y azar. **No se sabe si la
ventaja crece.** Si el modelo estuviera detectando "zonas de giro" en vez de velas
exactas, deberia crecer; si sus fallos fueran aleatorios, la tolerancia ayudaria a los
dos por igual y la ventaja se quedaria igual o bajaria.

**Si la ventaja no crece, la conclusion es que los fallos no son por poco**, y se
publica asi.

Lo que esto NO responde
-----------------------
**No dice si el sistema sirve para operar.** Operar exige entradas, salidas y costos,
y nada de eso se ha simulado en este proyecto. Medir detección con tolerancia sigue
siendo medir detección.

No toca el bloque de prueba. Nueve tramos de validacion deslizante, sin reentrenar
nada.

Punto de entrada:
    uv run python scripts/aviso_con_tolerancia.py
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
from contracts.schema import cierre  # noqa: E402
from src.features.base import construir  # noqa: E402
from src.modelos.base import BaselineAleatorio  # noqa: E402
from src.modelos.clasico import HIPERPARAMETROS, BosqueAleatorio  # noqa: E402

SALIDA = RAIZ / "docs" / "evidencias" / "m0-aviso-con-tolerancia-4h-w7-h1.json"

N_TRAMOS = 9
UMBRAL = 0.40
TOLERANCIAS = [0, 1, 2, 3]
RARAS = (int(Clase.MAXIMO), int(Clase.MINIMO))


def acierta_con_tolerancia(anuncio: np.ndarray, verdad: np.ndarray, k: int) -> tuple[int, int]:
    """Cuantos avisos hubo y cuantos caen a `k` velas o menos de un giro de su clase."""
    dio = np.flatnonzero(anuncio != 0)
    if len(dio) == 0:
        return 0, 0
    aciertos = 0
    n = len(verdad)
    for i in dio:
        clase = anuncio[i]
        desde, hasta = max(0, i - k), min(n, i + k + 1)
        if np.any(verdad[desde:hasta] == clase):
            aciertos += 1
    return len(dio), aciertos


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    panel = pd.read_parquet(RAIZ / "data" / "processed" / f"panel_{GRANULARIDAD}_v1.parquet")
    X = construir(panel, rezagos_relativos=True)
    y = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), VENTANA_W), HORIZONTE_H)

    validos = np.flatnonzero(y.notna().to_numpy())
    embargo = VENTANA_W + HORIZONTE_H
    corte = len(validos) // 2
    ancho = (len(validos) - corte) // N_TRAMOS

    por_tramo: list[dict] = []
    print(f"{'tramo':>6} {'avisos':>7} " + " ".join(f"{'k=' + str(k):>9}" for k in TOLERANCIAS))

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
        prob = tuberia.predict_proba(bosque._preparar(X.iloc[tramo], bosque._columnas))
        columnas = [int(np.flatnonzero(clases == c)[0]) for c in RARAS]
        p_raras = prob[:, columnas]
        anuncio = np.where(
            p_raras.max(axis=1) >= UMBRAL, np.array(RARAS)[p_raras.argmax(axis=1)], 0
        ).astype(int)

        verdad = y.iloc[tramo].astype(int).to_numpy()

        # El piso: misma cobertura, velas al azar, tipo del baseline.
        pred_azar = np.asarray(azar.predecir(X.iloc[tramo]), dtype=int)
        generador = np.random.default_rng(HIPERPARAMETROS["random_state"] + i)
        n_avisos = int((anuncio != 0).sum())
        anuncio_azar = np.zeros_like(anuncio)
        if n_avisos:
            elegidas = generador.choice(len(tramo), size=n_avisos, replace=False)
            tipos = np.where(
                np.isin(pred_azar[elegidas], RARAS),
                pred_azar[elegidas],
                generador.choice(RARAS, size=n_avisos),
            )
            anuncio_azar[elegidas] = tipos

        fila = {"tramo": i, "n": int(len(tramo)), "avisos": n_avisos, "tolerancias": {}}
        for k in TOLERANCIAS:
            n_a, ac = acierta_con_tolerancia(anuncio, verdad, k)
            n_z, ac_z = acierta_con_tolerancia(anuncio_azar, verdad, k)
            p = ac / n_a if n_a else None
            pz = ac_z / n_z if n_z else None
            fila["tolerancias"][str(k)] = {
                "precision": round(p, 6) if p is not None else None,
                "precision_azar": round(pz, 6) if pz is not None else None,
                "ventaja": round(p - pz, 6) if (p is not None and pz is not None) else None,
            }
        por_tramo.append(fila)
        print(
            f"{i:>6} {n_avisos:>7} "
            + " ".join(f"{fila['tolerancias'][str(k)]['precision']:>9.4f}" for k in TOLERANCIAS)
        )

    agregado = {}
    for k in TOLERANCIAS:
        ps = [f["tolerancias"][str(k)] for f in por_tramo]
        total_avisos = sum(f["avisos"] for f in por_tramo)
        # Agregado ponderado por avisos de cada tramo.
        pares = list(zip(ps, por_tramo, strict=True))
        prec = sum(d["precision"] * f["avisos"] for d, f in pares) / total_avisos
        prec_az = sum(d["precision_azar"] * f["avisos"] for d, f in pares) / total_avisos
        a_favor = sum(1 for d in ps if d["ventaja"] is not None and d["ventaja"] > 0)
        agregado[str(k)] = {
            "precision": round(prec, 6),
            "precision_azar": round(prec_az, 6),
            "ventaja": round(prec - prec_az, 6),
            "veces_el_azar": round(prec / prec_az, 4) if prec_az else None,
            "tramos_a_favor": a_favor,
            "tramos_medidos": len(ps),
            "signo_estable": bool(a_favor == len(ps)),
        }

    base = agregado["0"]["ventaja"]
    cumplen = [
        k
        for k in map(str, TOLERANCIAS[1:])
        if agregado[k]["ventaja"] > 0  # condicion 1: supera al azar
        and agregado[k]["ventaja"] > base  # condicion 2: la ventaja CRECE
        and agregado[k]["signo_estable"]
    ]

    medido = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "que_mide": (
            "Si los avisos que fallan fallan por mucho o por una vela. Precision del "
            "aviso admitiendo una tolerancia de k velas, en el umbral 0,40."
        ),
        "por_que_el_piso_se_mueve": (
            "Ampliar la ventana sube la precision de cualquiera, incluido el azar: con "
            "k=3 cada aviso tiene siete velas para acertar en vez de una. Por eso el "
            "baseline_aleatorio se mide con la MISMA tolerancia y cobertura. Lo que "
            "importa no es que el numero suba, sino si sube mas que el del azar."
        ),
        "criterio_preregistrado": (
            "Para decir que la tolerancia cambia algo, para algun k>=1: (1) la precision "
            "supera a la del azar con la misma tolerancia y cobertura, (2) la VENTAJA "
            "sobre el azar es mayor que la de k=0, y (3) el signo es estable en los "
            "nueve tramos. Si la ventaja no crece, los fallos no son por poco."
        ),
        "lo_que_no_responde": (
            "No dice si el sistema sirve para operar. Operar exige entradas, salidas y "
            "costos, y nada de eso se ha simulado. Esto sigue siendo medir deteccion."
        ),
        "parametros": {
            "umbral": UMBRAL,
            "tolerancias": TOLERANCIAS,
            "n_tramos": N_TRAMOS,
            "intervalo": GRANULARIDAD,
            "horas_por_vela": 4,
        },
        "agregado": agregado,
        "por_tramo": por_tramo,
        "tolerancias_que_cumplen": cumplen,
        "veredicto": (
            "La ventaja sobre el azar CRECE con la tolerancia: los fallos no son al azar."
            if cumplen
            else "La ventaja no crece con la tolerancia: los fallos no son por poco."
        ),
    }
    SALIDA.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        f"\n{'k':>3} {'horas':>6} {'precision':>10} {'azar':>9} {'ventaja':>9} "
        f"{'x azar':>7} {'tramos':>7}"
    )
    for k in TOLERANCIAS:
        d = agregado[str(k)]
        print(
            f"{k:>3} {k * 4:>6} {d['precision']:>10.6f} {d['precision_azar']:>9.6f} "
            f"{d['ventaja']:>+9.6f} {d['veces_el_azar']:>7.2f} "
            f"{d['tramos_a_favor']:>3}/{d['tramos_medidos']:<3}"
        )
    print(f"\n{medido['veredicto']}")
    print(f"constancia en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
