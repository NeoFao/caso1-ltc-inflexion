"""Busqueda de hiperparametros del modelo avanzado (S4-M3-02, segunda mitad).

Va en un modulo aparte del fundacional a proposito, porque la busqueda es de otra
naturaleza y mezclarlas escondaria justo lo que las distingue.

El fundacional es determinista: una celda da siempre el mismo numero, asi que
medirla una vez alcanza. El avanzado se entrena, y su F1 se mueve **0,0304 entre
semillas**, mas que el umbral de decision del equipo. Con esa dispersion, elegir el
maximo de una rejilla medida con UNA semilla no selecciona la mejor configuracion:
selecciona la celda a la que le toco la semilla mas afortunada. Y como despues se
reporta esa celda, el numero queda inflado por la misma razon por la que la tarea
prohibe mirar prueba, solo que mas dificil de ver.

Por eso la D15 decidio medir cada celda con CINCO semillas y ordenar por la media.
Cambia lo que significa "la mejor configuracion": pasa a ser la mejor en promedio,
no la mejor observada. Es lo que se puede defender.

Y la comparacion entre celdas se hace PAREADA POR SEMILLA. La semilla 3 tiende a
salir bien en todas las celdas, asi que comparar medias sueltas mezcla el efecto de
la configuracion con el de que semillas le tocaron. Pareando, cada semilla se
compara consigo misma.

La D15 fija ademas, ANTES de correr esto, que si el ruido entre semillas alcanza a
la diferencia entre celdas no se corona ganadora y se conserva la configuracion por
defecto. Ese criterio se aplica en el codigo y no a criterio de quien lea la tabla.

La regla que no se puede romper sigue siendo la misma y por eso vuelve a estar en
el codigo: la busqueda se hace contra validacion. Este guion no sabe evaluar sobre
prueba.

Salidas:
    docs/evidencias/m3-hiperparametros-avanzado-<intervalo>-w<w>-h<h>.json

Uso:
    uv sync --group dev --group modelos
    uv run python -m src.modelos.hiperparametros_avanzado
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

from contracts.config import ACTIVO_OBJETIVO
from contracts.labeling import etiquetar, objetivo
from contracts.schema import cierre, validar_panel
from contracts.splits import particionar
from src.evaluacion.arnes import evaluar_modelo
from src.features.base import construir
from src.modelos.avanzado import ITransformerAvanzado, cierres_del_panel
from src.modelos.base import BaselineAleatorio, BaselineTrivial

RAIZ = Path(__file__).resolve().parents[2]
EVIDENCIAS = RAIZ / "docs" / "evidencias"

LOOKBACKS = (48, 96, 192)
DIMENSIONES = (32, 64)
SEMILLAS = (0, 1, 2, 3, 4)

# Constante y no bandera, igual que en la mitad determinista: no quiero que exista
# la forma facil de buscar contra prueba.
CONJUNTO_DE_BUSQUEDA = "validacion"

# La configuracion con la que se midio el modelo en S4-M3-01, para poder leer
# cuanto se gano ajustando y no solo cual celda gano.
POR_DEFECTO = (96, 64)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intervalo", default="4h")
    parser.add_argument("--w", type=int, default=7)
    parser.add_argument("--h", type=int, default=1)
    argumentos = parser.parse_args()
    w, h = argumentos.w, argumentos.h

    panel = pd.read_parquet(
        RAIZ / "data" / "processed" / f"panel_{argumentos.intervalo}_v1.parquet"
    )
    validar_panel(panel)
    X = construir(panel)
    y = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), w), h)
    particion = particionar(n=len(y), w=w, h=h)
    cierres = cierres_del_panel(panel)

    rejilla = list(product(LOOKBACKS, DIMENSIONES))
    print(
        f"Hiperparametros del avanzado -- {len(rejilla)} celdas x {len(SEMILLAS)} semillas "
        f"sobre {CONJUNTO_DE_BUSQUEDA}, {argumentos.intervalo}, w={w}, h={h}"
    )

    referencias = {}
    for modelo in (BaselineTrivial(), BaselineAleatorio(semilla=0)):
        referencias[modelo.nombre] = evaluar_modelo(
            modelo, X, y, particion, conjunto=CONJUNTO_DE_BUSQUEDA
        )["f1_macro"]
    print(
        f"  piso: trivial {referencias['baseline_trivial']:.6f}  "
        f"azar {referencias['baseline_aleatorio']:.6f}\n"
    )

    celdas = []
    for numero, (lookback, dimension) in enumerate(rejilla, start=1):
        reloj = time.perf_counter()
        f1_por_semilla = {}
        for semilla in SEMILLAS:
            modelo = ITransformerAvanzado(
                cierres,
                w=w,
                h=h,
                lookback=lookback,
                dimension=dimension,
                semilla=semilla,
            )
            f1_por_semilla[semilla] = evaluar_modelo(
                modelo, X, y, particion, conjunto=CONJUNTO_DE_BUSQUEDA
            )["f1_macro"]

        valores = np.array(list(f1_por_semilla.values()))
        celdas.append(
            {
                "lookback": lookback,
                "dimension": dimension,
                "f1_por_semilla": {str(k): v for k, v in f1_por_semilla.items()},
                "f1_medio": float(valores.mean()),
                "f1_minimo": float(valores.min()),
                "f1_maximo": float(valores.max()),
                "desviacion": float(valores.std()),
                "es_la_por_defecto": (lookback, dimension) == POR_DEFECTO,
                "segundos": round(time.perf_counter() - reloj, 1),
            }
        )
        print(
            f"  [{numero}/{len(rejilla)}] lookback {lookback:4}  dim {dimension:3}  "
            f"F1 medio {valores.mean():.6f}  (min {valores.min():.6f}, "
            f"max {valores.max():.6f})"
        )

    orden = sorted(celdas, key=lambda c: c["f1_medio"], reverse=True)
    mejor = orden[0]
    por_defecto = next(c for c in celdas if c["es_la_por_defecto"])

    # Pareada por semilla: la semilla 3 tiende a salir bien en todas las celdas, asi
    # que comparar medias sueltas mezcla la configuracion con las semillas que le
    # tocaron. Cada semilla se compara consigo misma.
    diferencias = np.array(
        [
            mejor["f1_por_semilla"][str(s)] - por_defecto["f1_por_semilla"][str(s)]
            for s in SEMILLAS
        ]
    )
    ganancia = {
        "diferencia_media": float(diferencias.mean()),
        "minima": float(diferencias.min()),
        "maxima": float(diferencias.max()),
        "semillas_a_favor": int((diferencias > 0).sum()),
        "de_semillas": len(SEMILLAS),
        "cambia_de_signo": bool(diferencias.min() < 0 < diferencias.max()),
        "pareada_por_semilla": True,
    }

    dispersion_entre_celdas = mejor["f1_medio"] - orden[-1]["f1_medio"]
    dispersion_entre_semillas = float(
        np.mean([c["f1_maximo"] - c["f1_minimo"] for c in celdas])
    )

    medido = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "tarea": "S4-M3-02, segunda mitad (modelo avanzado)",
        "conjunto": CONJUNTO_DE_BUSQUEDA,
        "metodo": (
            "Cada celda se mide con cinco semillas y se ordena por la media, no por el "
            "maximo observado. Con una sola semilla se estaria eligiendo la celda mas "
            "afortunada y no la mejor configuracion, porque el F1 se mueve entre "
            "semillas mas que el umbral de decision del equipo."
        ),
        "regla": (
            "La busqueda se hace contra validacion. El bloque de prueba no se toca aqui."
        ),
        "parametros_fijos": {"intervalo": argumentos.intervalo, "w": w, "h": h},
        "rejilla_explorada": {
            "lookbacks": list(LOOKBACKS),
            "dimensiones": list(DIMENSIONES),
            "semillas": list(SEMILLAS),
            "n_celdas": len(rejilla),
            "n_entrenamientos": len(rejilla) * len(SEMILLAS),
        },
        "referencias": referencias,
        "celdas": celdas,
        "mejor": mejor,
        "por_defecto": por_defecto,
        "ganancia_del_ajuste": ganancia,
        "dispersion_entre_celdas": dispersion_entre_celdas,
        "dispersion_media_entre_semillas": dispersion_entre_semillas,
        "el_ruido_supera_a_la_senal": bool(
            dispersion_entre_semillas >= dispersion_entre_celdas
        ),
        # El criterio lo fijo la D15 ANTES de correr esto, que es lo que le da valor:
        # si el ruido entre semillas iguala o supera a la diferencia entre celdas, la
        # rejilla no distingue configuraciones, no se corona ganadora y se conserva la
        # de por defecto. Se aplica aqui en vez de dejarlo a criterio de quien lea la
        # tabla, que es justo el momento en que la tentacion de reinterpretarlo es
        # mayor.
        "veredicto_d15": {
            "regla": (
                "D15: si la dispersion entre semillas dentro de una celda iguala o "
                "supera la dispersion entre celdas, no se corona ganadora y se "
                "conserva la configuracion por defecto."
            ),
            "se_corona_ganadora": bool(
                dispersion_entre_semillas < dispersion_entre_celdas
            ),
            "configuracion_elegida": (
                {"lookback": mejor["lookback"], "dimension": mejor["dimension"]}
                if dispersion_entre_semillas < dispersion_entre_celdas
                else {
                    "lookback": por_defecto["lookback"],
                    "dimension": por_defecto["dimension"],
                }
            ),
            "por_que": (
                "La rejilla distingue configuraciones."
                if dispersion_entre_semillas < dispersion_entre_celdas
                else "El ruido entre semillas alcanza a la diferencia entre celdas, "
                "asi que la rejilla no distingue configuraciones y ajustar no tiene "
                "de donde mejorar."
            ),
        },
        "el_mejor_le_gana_al_azar": bool(
            mejor["f1_medio"] > referencias["baseline_aleatorio"]
        ),
        "prueba_sin_tocar": (
            "El bloque de prueba NO se midio aqui. Se mide una sola vez, aparte, "
            "despues de fijar la configuracion de los dos modelos."
        ),
    }

    destino = (
        EVIDENCIAS / f"m3-hiperparametros-avanzado-{argumentos.intervalo}-w{w}-h{h}.json"
    )
    EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        f"\n  mejor: lookback {mejor['lookback']} dim {mejor['dimension']} -> "
        f"F1 medio {mejor['f1_medio']:.6f}"
    )
    print(f"  por defecto: F1 medio {por_defecto['f1_medio']:.6f}")
    print(
        f"  ganancia pareada: {ganancia['diferencia_media']:+.6f} de media, "
        f"{ganancia['semillas_a_favor']}/{ganancia['de_semillas']} semillas a favor"
    )
    print(f"  dispersion entre celdas:  {dispersion_entre_celdas:.6f}")
    print(f"  dispersion entre semillas: {dispersion_entre_semillas:.6f}")
    veredicto = medido["veredicto_d15"]
    if veredicto["se_corona_ganadora"]:
        print(f"\n  D15: se corona ganadora -> {veredicto['configuracion_elegida']}")
    else:
        print(
            "\n  D15: NO se corona ganadora. El ruido entre semillas alcanza a la\n"
            "  diferencia entre celdas, asi que la rejilla no distingue configuraciones.\n"
            f"  Se conserva la de por defecto: {veredicto['configuracion_elegida']}"
        )
    print(f"\nmedido: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
