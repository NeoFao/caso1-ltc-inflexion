"""Busqueda de hiperparametros del modelo fundacional (S4-M3-02).

Cubre la mitad determinista de la tarea. La otra --el modelo avanzado-- vive en
`src/modelos/hiperparametros_avanzado.py`, en un modulo aparte porque la busqueda
es de otra naturaleza: su F1 se mueve 0,0304 entre semillas, mas que el umbral de
decision del equipo, asi que alla cada celda se mide con cinco semillas y se ordena
por la media. Mezclar las dos busquedas en un solo guion esconderia justo lo que
las distingue.

El fundacional no tiene ese problema: es zero-shot y no muestrea, asi que la misma
celda da siempre el mismo numero y la rejilla mide lo que dice medir.

La regla que no se puede romper, y por eso esta en el codigo y no solo en el
issue: **la busqueda se hace contra validacion**. Este guion no sabe siquiera
evaluar sobre prueba; medir la configuracion ganadora contra prueba se hace UNA vez
y aparte, despues de fijarla. Si se ajustan hiperparametros mirando prueba, el
numero del informe queda inflado sin que se note.

Que se explora, y por que esos tres:

    tamano del modelo  cuanto sabe el modelo, y lo que cuesta cargarlo
    contexto           cuanta historia mira para pronosticar
    cuantil            cual de los nueve cuantiles hace de trayectoria puntual

El cuantil es el menos obvio y el mas propio de este puente: la etiqueta sale de
aplicar etiquetar() a la trayectoria, asi que inclinarla hacia arriba o hacia abajo
cambia que tan facil es que un instante quede como Maximo o como Minimo.

Se registra la rejilla ENTERA y no solo la ganadora, que es lo que pide el criterio
de aceptacion: sin las celdas perdedoras no se puede saber si la ganadora gano por
diferencia o por ruido.

Salidas:
    docs/evidencias/m3-hiperparametros-fundacional-<intervalo>-w<w>-h<h>.json

Uso:
    uv sync --group dev --group modelos
    uv run python -m src.modelos.hiperparametros
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from itertools import product
from pathlib import Path

import pandas as pd

from contracts.config import ACTIVO_OBJETIVO
from contracts.labeling import etiquetar, objetivo
from contracts.schema import cierre, validar_panel
from contracts.splits import particionar
from src.evaluacion.arnes import evaluar_modelo
from src.features.base import construir
from src.modelos.base import BaselineAleatorio, BaselineTrivial
from src.modelos.fundacional import ChronosBolt

RAIZ = Path(__file__).resolve().parents[2]
EVIDENCIAS = RAIZ / "docs" / "evidencias"

REPOS = ("amazon/chronos-bolt-tiny", "amazon/chronos-bolt-small")
CONTEXTOS = (128, 256, 512)
CUANTILES = (0.4, 0.5, 0.6)

# El conjunto sobre el que se busca. Es una constante y no una bandera a proposito:
# no quiero que exista la forma facil de buscar contra prueba.
CONJUNTO_DE_BUSQUEDA = "validacion"


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
    serie = cierre(panel, ACTIVO_OBJETIVO)
    y = objetivo(etiquetar(serie, w), h)
    particion = particionar(n=len(y), w=w, h=h)

    rejilla = list(product(REPOS, CONTEXTOS, CUANTILES))
    print(
        f"Hiperparametros del fundacional -- {len(rejilla)} celdas sobre "
        f"{CONJUNTO_DE_BUSQUEDA}, {argumentos.intervalo}, w={w}, h={h}"
    )

    # Los dos piso de comparacion, para que cada celda se lea contra algo y no
    # contra la mejor celda de su propia rejilla.
    referencias = {}
    for modelo in (BaselineTrivial(), BaselineAleatorio(semilla=0)):
        resultado = evaluar_modelo(modelo, X, y, particion, conjunto=CONJUNTO_DE_BUSQUEDA)
        referencias[modelo.nombre] = resultado["f1_macro"]
    print(
        f"  piso: trivial {referencias['baseline_trivial']:.6f}  "
        f"azar {referencias['baseline_aleatorio']:.6f}\n"
    )

    celdas = []
    for numero, (repo, contexto, cuantil) in enumerate(rejilla, start=1):
        reloj = time.perf_counter()
        modelo = ChronosBolt(
            serie, w=w, h=h, contexto=contexto, repo=repo, cuantil=cuantil
        )
        resultado = evaluar_modelo(modelo, X, y, particion, conjunto=CONJUNTO_DE_BUSQUEDA)
        celdas.append(
            {
                "repo": repo,
                "contexto": contexto,
                "cuantil": cuantil,
                "f1_macro": resultado["f1_macro"],
                "precision_direccional": resultado["precision_direccional"],
                "f1_maximo": resultado["f1_maximo"],
                "f1_minimo": resultado["f1_minimo"],
                "exactitud": resultado["exactitud"],
                "segundos": round(time.perf_counter() - reloj, 1),
            }
        )
        print(
            f"  [{numero:2}/{len(rejilla)}] {repo.split('/')[-1]:20} "
            f"contexto {contexto:4}  cuantil {cuantil}  "
            f"F1 {resultado['f1_macro']:.6f}"
        )

    orden = sorted(celdas, key=lambda c: c["f1_macro"], reverse=True)
    mejor, peor = orden[0], orden[-1]
    dispersion = mejor["f1_macro"] - peor["f1_macro"]

    # Elegir el maximo de 18 celdas contra validacion infla el resultado por si
    # solo, aunque cada celda sea determinista: se esta escogiendo la que mejor le
    # cayo a ESTE bloque. Para saber si la ganancia sobre la configuracion por
    # defecto es real o es ese efecto, se mide su intervalo pareado. Es la misma
    # funcion de M2 que se usa en el resto del modulo.
    from src.features.incertidumbre import intervalo_diferencia

    mascara = particion.validacion & y.notna().to_numpy()
    y_real = y[mascara].astype(int).to_numpy()

    def _predecir(repo, contexto, cuantil):
        modelo = ChronosBolt(serie, w=w, h=h, contexto=contexto, repo=repo, cuantil=cuantil)
        modelo.entrenar(X, y)
        return modelo.predecir(X[mascara])

    por_defecto = next(
        c
        for c in celdas
        if c["repo"] == "amazon/chronos-bolt-small"
        and c["contexto"] == 512
        and c["cuantil"] == 0.5
    )
    pred_mejor = _predecir(mejor["repo"], mejor["contexto"], mejor["cuantil"])
    pred_defecto = _predecir(
        por_defecto["repo"], por_defecto["contexto"], por_defecto["cuantil"]
    )
    ganancia = intervalo_diferencia(y_real, pred_mejor, pred_defecto)

    medido = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "tarea": "S4-M3-02, mitad determinista (modelo fundacional)",
        "conjunto": CONJUNTO_DE_BUSQUEDA,
        "regla": (
            "La busqueda se hace contra validacion. El bloque de prueba no se toca "
            "aqui: se mide UNA vez, aparte, despues de fijar la configuracion."
        ),
        "parametros_fijos": {"intervalo": argumentos.intervalo, "w": w, "h": h},
        "rejilla_explorada": {
            "repos": list(REPOS),
            "contextos": list(CONTEXTOS),
            "cuantiles": list(CUANTILES),
            "n_celdas": len(rejilla),
        },
        "referencias": referencias,
        "celdas": celdas,
        "mejor": mejor,
        "peor": peor,
        "dispersion_de_la_rejilla": dispersion,
        "el_mejor_le_gana_al_azar": bool(
            mejor["f1_macro"] > referencias["baseline_aleatorio"]
        ),
        "por_defecto": por_defecto,
        "ganancia_del_ajuste": {
            **ganancia,
            "nota": (
                "Intervalo pareado de la mejor celda contra la configuracion por "
                "defecto, sobre validacion. Si incluye el cero, la ganancia de ajustar "
                "no se distingue del efecto de haber elegido el maximo de la rejilla "
                "mirando este mismo bloque."
            ),
        },
        "prueba_sin_tocar": (
            "El bloque de prueba NO se midio. El criterio de aceptacion pide medirlo "
            "una sola vez despues de fijar los hiperparametros, y todavia falta la "
            "mitad avanzada de esta tarea, asi que fijarlos no esta terminado. Gastar "
            "esa medicion ahora dejaria al informe sin datos no vistos."
        ),
        "el_modelo_avanzado": (
            "Se busca aparte, en src/modelos/hiperparametros_avanzado.py, promediando "
            "cinco semillas por celda: su F1 se mueve 0,0304 entre semillas, mas que "
            "el umbral de decision, asi que una sola semilla elegiria la celda mas "
            "afortunada y no la mejor configuracion."
        ),
    }

    destino = (
        EVIDENCIAS
        / f"m3-hiperparametros-fundacional-{argumentos.intervalo}-w{w}-h{h}.json"
    )
    EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        f"\n  mejor: {mejor['repo'].split('/')[-1]} contexto {mejor['contexto']} "
        f"cuantil {mejor['cuantil']} -> F1 {mejor['f1_macro']:.6f}"
    )
    print(f"  por defecto: F1 {por_defecto['f1_macro']:.6f}")
    print(f"  dispersion de la rejilla: {dispersion:.6f}")
    marca = "excluye el cero" if ganancia["excluye_el_cero"] else "INCLUYE el cero"
    print(
        f"  ganancia del ajuste: {ganancia['diferencia']:+.6f}  "
        f"IC [{ganancia['ic_inferior']:+.4f}, {ganancia['ic_superior']:+.4f}]  {marca}"
    )
    print(f"\nmedido: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
