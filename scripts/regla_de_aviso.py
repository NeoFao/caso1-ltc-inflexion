"""Cuando hablar y que decir son dos decisiones, y hoy las toma un solo numero.

El hueco
--------
La regla de aviso vigente anuncia si `max(p_maximo, p_minimo)` supera un umbral, y
anuncia esa clase. Eso funde dos preguntas distintas:

1. **¿Hablo?** -- cuanta confianza tengo en que **viene un giro**, del tipo que sea.
2. **¿Que digo?** -- cual de los dos tipos es mas probable.

Fundirlas tiene una consecuencia concreta. Si el modelo reparte 0,30 y 0,30 entre
maximo y minimo, el maximo es 0,30 y el sistema **se calla** -- cuando en realidad
esta diciendo que hay un 60 % de probabilidad de giro. Al reves, si reparte 0,35 y
0,02, habla con menos evidencia de giro que en el caso anterior.

La regla alternativa separa las dos: **se elige a quien hablarle por `p_maximo +
p_minimo`** (confianza en que viene un giro) y **el tipo por el argmax** (cual de los
dos). El tipo no cambia nunca entre las dos reglas; lo unico que cambia es **a que
velas se les habla**.

Por que podria no servir
------------------------
Si la probabilidad de las dos clases raras esta casi siempre concentrada en una sola,
las dos reglas ordenan igual y no hay diferencia. Y si el modelo reparte entre maximo
y minimo justo cuando **no** hay giro -- porque la vela es ambigua para todo, no solo
para el tipo -- entonces la suma seleccionaria peor que el maximo.

El criterio, fijado ANTES de correr
-----------------------------------
Para no comparar reglas a coberturas distintas, las dos se evaluan **a la misma
cobertura**: se toman las `k` velas con mayor puntaje de cada regla, con la misma `k`.
Las coberturas se declaran aca y son **las tres que el proyecto ya reporta**, no una
elegida despues:

    90 %, 55 % y 18,37 % (el punto de trabajo)

Se adopta la regla de la suma **solo si se cumplen las dos**:

1. Su precision **supera** a la de la regla vigente **en las tres coberturas**.
2. En el punto de trabajo, el signo de esa diferencia es **estable en al menos 8 de
   los 9 tramos**.

Si gana en una o dos coberturas pero no en las tres, la conclusion es **que no se
establece**. Si gana en las tres pero sin estabilidad, tambien.

La expectativa, tambien antes de mirar
--------------------------------------
Se espera una mejora **pequena y positiva**: la suma usa informacion que el maximo
tira, pero en un problema con 4,6 % de clase rara la masa de probabilidad de las dos
raras casi siempre esta en una sola, asi que las dos reglas deberian ordenar parecido.
**Si la mejora fuera grande, lo sospechoso seria eso**, y habria que mirar si la
cobertura quedo mal igualada.

Que NO hace
-----------
No toca el bloque de reserva: mide sobre los nueve tramos de la validacion deslizante.
No reentrena nada distinto ni cambia el modelo: usa **las mismas probabilidades** del
mismo bosque, y solo cambia como se leen.

Punto de entrada:
    uv run python scripts/regla_de_aviso.py
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

SALIDA = RAIZ / "docs" / "evidencias" / "m0-regla-de-aviso-4h-w7-h1.json"

N_TRAMOS = 9
VELAS_DE_MARGEN = 2
#: Las tres coberturas que el proyecto ya reporta. Se declaran antes de correr.
COBERTURAS = [0.9040, 0.5500, 0.1837]
COBERTURA_DE_TRABAJO = 0.1837
TRAMOS_MINIMOS = 8

RARAS = (int(Clase.MAXIMO), int(Clase.MINIMO))


def puntajes(prob: np.ndarray, clases: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Devuelve (puntaje del maximo, puntaje de la suma, tipo anunciado).

    El tipo es el mismo para las dos reglas: lo que cambia es a quien se le habla.
    """
    columnas = [int(np.flatnonzero(clases == c)[0]) for c in RARAS]
    p_raras = prob[:, columnas]
    tipo = np.array(RARAS)[p_raras.argmax(axis=1)]
    return p_raras.max(axis=1), p_raras.sum(axis=1), tipo


def aciertos_de_los_mejores(
    puntaje: np.ndarray, tipo: np.ndarray, verdad: np.ndarray, k: int
) -> int:
    """Cuantos aciertos hay entre las k velas de mayor puntaje."""
    if k <= 0:
        return 0
    elegidas = np.argpartition(-puntaje, min(k, len(puntaje) - 1))[:k]
    return int((tipo[elegidas] == verdad[elegidas]).sum())


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
        f"{c:.4f}": {"k": 0, "maximo": 0, "suma": 0, "azar": 0, "tramos_a_favor": 0, "tramos": 0}
        for c in COBERTURAS
    }
    total = 0

    cabecera = " ".join(f"{'cob ' + f'{c:.0%}':>22}" for c in COBERTURAS)
    print(f"{'tramo':>6} {'velas':>6} " + cabecera)
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
        p_max, p_suma, tipo = puntajes(prob, clases)

        pred_azar = np.asarray(azar.predecir(X.iloc[tramo]), dtype=int)
        generador = np.random.default_rng(HIPERPARAMETROS["random_state"] + i)
        total += len(tramo)

        celdas = []
        for c in COBERTURAS:
            clave = f"{c:.4f}"
            k = int(round(c * len(tramo)))
            ac_max = aciertos_de_los_mejores(p_max, tipo, verdad, k)
            ac_suma = aciertos_de_los_mejores(p_suma, tipo, verdad, k)

            elegidas = generador.choice(len(tramo), size=k, replace=False)
            tipos_azar = np.where(
                np.isin(pred_azar[elegidas], RARAS),
                pred_azar[elegidas],
                generador.choice(RARAS, size=k),
            )
            ac_azar = int((tipos_azar == verdad[elegidas]).sum())

            d = acumulado[clave]
            d["k"] += k
            d["maximo"] += ac_max
            d["suma"] += ac_suma
            d["azar"] += ac_azar
            d["tramos"] += 1
            d["tramos_a_favor"] += int(ac_suma > ac_max)
            celdas.append(f"{ac_max / k:>10.6f} {ac_suma / k:>10.6f}")
        print(f"{i:>6} {len(tramo):>6} " + " ".join(celdas))

    resultados = {}
    for c in COBERTURAS:
        clave = f"{c:.4f}"
        d = acumulado[clave]
        p_max = d["maximo"] / d["k"]
        p_suma = d["suma"] / d["k"]
        p_azar = d["azar"] / d["k"]
        resultados[clave] = {
            "cobertura_declarada": c,
            "avisos": d["k"],
            "precision_regla_vigente": round(p_max, 6),
            "precision_regla_suma": round(p_suma, 6),
            "precision_azar": round(p_azar, 6),
            "cociente_vigente": round(p_max / p_azar, 6) if p_azar else None,
            "cociente_suma": round(p_suma / p_azar, 6) if p_azar else None,
            "diferencia": round(p_suma - p_max, 6),
            "tramos_a_favor": d["tramos_a_favor"],
            "tramos_medidos": d["tramos"],
        }

    gana_en_las_tres = all(r["diferencia"] > 0 for r in resultados.values())
    trabajo = resultados[f"{COBERTURA_DE_TRABAJO:.4f}"]
    estable = trabajo["tramos_a_favor"] >= TRAMOS_MINIMOS
    adopta = gana_en_las_tres and estable

    if adopta:
        veredicto = (
            "Se adopta la regla de la suma: gana en las tres coberturas declaradas y el "
            f"signo aguanta en {trabajo['tramos_a_favor']} de {trabajo['tramos_medidos']} "
            f"tramos en el punto de trabajo. Ahi el cociente pasa de "
            f"{trabajo['cociente_vigente']:.4f} a {trabajo['cociente_suma']:.4f}."
        )
    else:
        falta = []
        if not gana_en_las_tres:
            falta.append("no gana en las tres coberturas")
        if not estable:
            falta.append(
                f"el signo solo aguanta en {trabajo['tramos_a_favor']} de "
                f"{trabajo['tramos_medidos']} tramos"
            )
        veredicto = "No se adopta la regla de la suma: " + " y ".join(falta) + "."

    print()
    print(veredicto)

    SALIDA.write_text(
        json.dumps(
            {
                "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                "que_mide": (
                    "Si separar 'cuando hablar' de 'que decir' mejora la precision del aviso. "
                    "La regla vigente usa max(p_maximo, p_minimo) para las dos cosas; la "
                    "alternativa elige a quien hablarle por p_maximo + p_minimo y el tipo por "
                    "el argmax."
                ),
                "como_se_comparan": (
                    "A la misma cobertura: se toman las k velas de mayor puntaje de cada regla, "
                    "con la misma k. El tipo anunciado es identico en las dos reglas."
                ),
                "criterio_preregistrado": (
                    "Se adopta solo si la precision de la suma supera a la vigente en las tres "
                    "coberturas declaradas (90 %, 55 % y 18,37 %) y el signo aguanta en al menos "
                    f"{TRAMOS_MINIMOS} de {N_TRAMOS} tramos en el punto de trabajo."
                ),
                "expectativa_declarada_antes": (
                    "Una mejora pequena y positiva. Con 4,6 % de clase rara la masa de las dos "
                    "raras casi siempre esta en una sola, asi que las dos reglas deberian ordenar "
                    "parecido. Una mejora grande seria sospechosa de cobertura mal igualada."
                ),
                "no_toca_la_reserva": "Nueve tramos de validacion deslizante.",
                "objetivo": (
                    f"solo_adelante_{VELAS_DE_MARGEN}_velas: hay un giro de ese tipo en las "
                    f"proximas {VELAS_DE_MARGEN} velas. La ventana no mira al pasado."
                ),
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
