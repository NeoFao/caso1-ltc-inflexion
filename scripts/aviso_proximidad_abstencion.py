"""Las dos cosas que funcionan, juntas. Nunca se habian combinado.

De donde sale
-------------
De trece ejes probados, **dos** se sostienen, y ninguno toca el modelo:

- **Dejar que se calle** (`aviso_con_abstencion.py`): con umbral 0,40 avisa en el
  26,96 % de las velas y acierta 0,099660 contra 0,049830 del azar.
- **Preguntarle "hay giro cerca"** (`objetivo_proximidad.py`): con una vela de margen
  la ventaja en F1 macro pasa de +0,044619 a +0,230081.

**Se midieron por separado y nunca juntos.** La abstencion se midio sobre el objetivo
exacto; la proximidad, con el modelo respondiendo siempre. Componerlas es lo obvio y
esta sin hacer.

Que se mide
-----------
El mismo barrido de umbrales de `aviso_con_abstencion.py`, pero con el modelo
**entrenado y evaluado sobre el objetivo de proximidad a una vela**. Y el objetivo
exacto al lado, con el mismo barrido, para que la comparacion sea directa.

Lo que se compara es **la precision del aviso**: de las veces que el sistema anuncia
un giro, cuantas aciertan. Contra el `baseline_aleatorio` a la **misma cobertura**,
como en todo el resto.

Donde esta la trampa, otra vez
------------------------------
La precision sobre el objetivo de proximidad **va a ser mas alta por construccion**:
acertar "hay giro en +-1 vela" es mas facil que acertar la vela exacta, y ademas la
frecuencia base sube del 9,29 % al 27,47 %.

**Por eso el criterio no mira la precision sino cuanto le gana al azar.** Si la
precision sube igual que la frecuencia base, no hemos ganado nada: solo hemos hecho
la pregunta mas facil.

El criterio, fijado ANTES de correr
-----------------------------------
Para decir que la composicion aporta sobre cada parte por separado, tiene que existir
un umbral donde:

1. La precision del aviso supere la **frecuencia base** del objetivo de proximidad.
2. El **cociente** precision / precision-del-azar-a-la-misma-cobertura sea **mayor**
   que el mejor cociente que consigue el objetivo exacto (**2,18x**, en el umbral
   0,50 de la medicion anterior).
3. El signo de esa ventaja sea **estable en los nueve tramos**.

La condicion 2 es la que importa: compara **cuanto le gana al azar** en los dos
objetivos, y es inmune a que uno sea mas facil que el otro.

Y la expectativa, tambien antes de mirar
----------------------------------------
**Se espera que aporte.** Las dos partes funcionan por separado y actuan sobre cosas
distintas -- una sobre que se pregunta, otra sobre cuando se contesta -- asi que no
hay razon para que se estorben.

**La duda es de cuanto.** Podria ser que la abstencion ya estuviera capturando lo
mismo que la proximidad: si el modelo esta seguro justo cuando hay un giro cerca,
filtrar por confianza y ensanchar la ventana serian dos formas de lo mismo, y
combinarlas no sumaria. **Si el cociente no mejora el 2,18x, eso es lo que habra
pasado**, y se publica asi.

No toca la reserva. Nueve tramos de validacion deslizante, sin reentrenar nada nuevo.

Punto de entrada:
    uv run python scripts/aviso_proximidad_abstencion.py
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

sys.path.insert(0, str(RAIZ / "scripts"))
from aviso_con_abstencion import avisos, precision_del_aviso  # noqa: E402
from objetivo_proximidad import objetivo_cercano  # noqa: E402

SALIDA = RAIZ / "docs" / "evidencias" / "m0-aviso-proximidad-abstencion-4h-w7-h1.json"

N_TRAMOS = 9
UMBRALES = [0.0, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70]
#: El mejor cociente precision/azar que consigue el objetivo exacto, medido en
#: m0-aviso-con-abstencion: 0,129825 / 0,059649 en el umbral 0,50.
MEJOR_COCIENTE_EXACTO = 2.18
RARAS = (int(Clase.MAXIMO), int(Clase.MINIMO))


def barrido(X: pd.DataFrame, y: pd.Series) -> dict:
    """El barrido de umbrales sobre un objetivo dado, contra el azar por cobertura."""
    validos = np.flatnonzero(y.notna().to_numpy())
    embargo = VENTANA_W + HORIZONTE_H
    corte = len(validos) // 2
    ancho = (len(validos) - corte) // N_TRAMOS

    por_umbral = {
        f"{u:.2f}": {"avisos": 0, "aciertos": 0, "azar_n": 0, "azar_ac": 0, "tramos": []}
        for u in UMBRALES
    }
    total, giros = 0, 0

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
        verdad = y.iloc[tramo].astype(int).to_numpy()
        pred_azar = np.asarray(azar.predecir(X.iloc[tramo]), dtype=int)
        generador = np.random.default_rng(HIPERPARAMETROS["random_state"] + i)

        total += len(tramo)
        giros += int(np.isin(verdad, RARAS).sum())

        for u in UMBRALES:
            clave = f"{u:.2f}"
            anuncio = avisos(prob, clases, u)
            n_a, ac = precision_del_aviso(anuncio, verdad)

            anuncio_azar = np.zeros_like(anuncio)
            if n_a > 0:
                elegidas = generador.choice(len(tramo), size=n_a, replace=False)
                tipos = np.where(
                    np.isin(pred_azar[elegidas], RARAS),
                    pred_azar[elegidas],
                    generador.choice(RARAS, size=n_a),
                )
                anuncio_azar[elegidas] = tipos
            n_z, ac_z = precision_del_aviso(anuncio_azar, verdad)

            d = por_umbral[clave]
            d["avisos"] += n_a
            d["aciertos"] += ac
            d["azar_n"] += n_z
            d["azar_ac"] += ac_z
            if n_a and n_z:
                d["tramos"].append(ac / n_a > ac_z / n_z)

    frecuencia_base = giros / total
    salida = {"frecuencia_base": round(frecuencia_base, 6), "n": total, "umbrales": {}}
    for clave, d in por_umbral.items():
        if d["avisos"] == 0:
            salida["umbrales"][clave] = None
            continue
        p = d["aciertos"] / d["avisos"]
        pz = d["azar_ac"] / d["azar_n"] if d["azar_n"] else None
        salida["umbrales"][clave] = {
            "avisos": d["avisos"],
            "cobertura": round(d["avisos"] / total, 6),
            "cobertura_por_ciento": round(100 * d["avisos"] / total, 2),
            "precision": round(p, 6),
            "precision_azar": round(pz, 6) if pz else None,
            "cociente_sobre_azar": round(p / pz, 4) if pz else None,
            "supera_frecuencia_base": bool(p > frecuencia_base),
            "tramos_a_favor": int(sum(d["tramos"])),
            "tramos_medidos": int(len(d["tramos"])),
            "signo_estable": bool(d["tramos"] and all(d["tramos"])),
        }
    return salida


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    panel = pd.read_parquet(RAIZ / "data" / "processed" / f"panel_{GRANULARIDAD}_v1.parquet")
    X = construir(panel, rezagos_relativos=True)
    exacto = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), VENTANA_W), HORIZONTE_H)

    resultados = {}
    for k, nombre in ((0, "objetivo_exacto"), (1, "objetivo_proximidad_1_vela")):
        print(f"\n=== {nombre} ===", flush=True)
        resultados[nombre] = barrido(X, objetivo_cercano(exacto, k))
        r = resultados[nombre]
        print(f"frecuencia base {r['frecuencia_base']:.6f}  ({r['n']} observaciones)")
        print(
            f"{'umbral':>7} {'avisos':>7} {'cobert.':>8} {'precision':>10} {'azar':>9} "
            f"{'x azar':>7} {'tramos':>7}"
        )
        for clave, d in r["umbrales"].items():
            if d is None:
                print(f"{clave:>7}  (nunca avisa)")
                continue
            print(
                f"{clave:>7} {d['avisos']:>7} {d['cobertura_por_ciento']:>7.2f}% "
                f"{d['precision']:>10.6f} {d['precision_azar']:>9.6f} "
                f"{d['cociente_sobre_azar']:>7.2f} "
                f"{d['tramos_a_favor']:>3}/{d['tramos_medidos']:<3}"
            )

    prox = resultados["objetivo_proximidad_1_vela"]["umbrales"]
    cumplen = [
        clave
        for clave, d in prox.items()
        if d
        and d["supera_frecuencia_base"]
        and d["cociente_sobre_azar"] is not None
        and d["cociente_sobre_azar"] > MEJOR_COCIENTE_EXACTO
        and d["signo_estable"]
    ]
    mejor = max(
        (d["cociente_sobre_azar"] for d in prox.values() if d and d["cociente_sobre_azar"]),
        default=None,
    )

    medido = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "que_mide": (
            "Las dos unicas intervenciones que funcionan, combinadas: el objetivo de "
            "proximidad a una vela Y el umbral de confianza. Se habian medido por "
            "separado y nunca juntas."
        ),
        "donde_esta_la_trampa": (
            "La precision sobre el objetivo de proximidad es mas alta por construccion, "
            "porque acertar 'hay giro en +-1 vela' es mas facil y la frecuencia base sube "
            "del 9,29 % al 27,47 %. Por eso el criterio no mira la precision sino el "
            "COCIENTE sobre el azar a la misma cobertura, que es inmune a que un objetivo "
            "sea mas facil que el otro."
        ),
        "criterio_preregistrado": (
            "Tiene que existir un umbral donde la precision supere la frecuencia base del "
            "objetivo de proximidad, el cociente precision/azar supere el mejor cociente "
            f"del objetivo exacto ({MEJOR_COCIENTE_EXACTO}x) y el signo sea estable en los "
            "nueve tramos."
        ),
        "expectativa_declarada_antes": (
            "Que aporte, porque las dos partes actuan sobre cosas distintas -- una sobre "
            "que se pregunta, otra sobre cuando se contesta -- y no hay razon para que se "
            "estorben. La duda es de cuanto: si el modelo esta seguro justo cuando hay un "
            "giro cerca, filtrar por confianza y ensanchar la ventana serian dos formas de "
            "lo mismo y combinarlas no sumaria. Si el cociente no mejora el 2,18x, eso es "
            "lo que habra pasado."
        ),
        "no_toca_la_reserva": "Nueve tramos de validacion deslizante.",
        "mejor_cociente_del_objetivo_exacto": MEJOR_COCIENTE_EXACTO,
        "mejor_cociente_medido_en_proximidad": mejor,
        "resultados": resultados,
        "umbrales_que_cumplen": cumplen,
        "veredicto": (
            "Combinarlas SI aporta: el cociente sobre el azar supera al del objetivo exacto."
            if cumplen
            else "Combinarlas no supera el cociente del objetivo exacto: la abstencion y "
            "la proximidad capturan en buena parte lo mismo."
        ),
    }
    SALIDA.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n{medido['veredicto']}")
    print(f"constancia en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
