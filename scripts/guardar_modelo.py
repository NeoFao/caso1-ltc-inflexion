"""Guarda los modelos entrenados como archivo, y comprueba que lo guardado sirve.

Por que existe
--------------
El caso pide dos entregables: el informe **y** el modelo de clasificacion entrenado.
Hasta ahora lo segundo era el repositorio: `modelos_entrenados/` estaba vacia y no
habia un solo `joblib`, `pickle` ni `torch.save` en todo el codigo. Los modelos se
entrenaban en memoria en cada corrida y se descartaban.

Eso es defendible -- el bosque reproduce bit a bit, asi que el codigo mas la semilla
determinan el modelo por completo -- pero **no es un modelo entrenado**, es la receta
para volver a entrenarlo. Quien reciba el trabajo no tiene un archivo que cargar.

Lo que hace
-----------
1. Entrena cada modelo con el bloque de entrenamiento de siempre.
2. Lo guarda en `modelos_entrenados/`.
3. **Lo vuelve a cargar desde el disco y comprueba que predice exactamente lo
   mismo**, comparando la huella SHA-256 de las predicciones sobre validacion.

El paso 3 es el que importa. Un archivo que se guarda pero predice distinto al
cargarse es peor que no tenerlo: parece un entregable y no lo es. Si la huella no
coincide, el guion falla y no deja el archivo como bueno.

Un efecto de lado que vale la pena
----------------------------------
La [D25](../docs/DECISIONES.md) documenta que el iTransformer **no reproduce entre
procesos**: reentrenarlo da pesos distintos, y de ahi salio que el intervalo de una
corrida no sea el instrumento adecuado para el.

El artefacto arregla eso para quien lo reciba. Lo que no reproduce es el
**entrenamiento**; la **inferencia** con los pesos guardados es determinista. Cargar
el archivo da siempre las mismas predicciones, y esta comprobado abajo.

Chronos-Bolt no se guarda
-------------------------
Es *zero-shot*: no hay nada ajustado por nosotros que guardar. Lo que se deja
registrado es el repositorio y la revision exacta de los pesos de Amazon, que es lo
que hace reproducible su parte.

Uso:
    uv run python scripts/guardar_modelo.py            # el bosque
    ...\\.venvs\\caso1\\Scripts\\python.exe scripts/guardar_modelo.py --con-avanzado
"""

from __future__ import annotations

import argparse
import hashlib
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
from contracts.splits import particionar  # noqa: E402
from src.features.base import construir  # noqa: E402
from src.modelos.clasico import HIPERPARAMETROS, BosqueAleatorio  # noqa: E402
from src.modelos.fundacional import REPO_POR_DEFECTO  # noqa: E402

DESTINO = RAIZ / "modelos_entrenados"
EVIDENCIA = RAIZ / "docs" / "evidencias" / "m0-modelo-guardado.json"


def huella(valores: np.ndarray) -> str:
    """SHA-256 de las predicciones. Dos modelos iguales la comparten; dos distintos, no."""
    return hashlib.sha256(np.asarray(valores, dtype=np.int64).tobytes()).hexdigest()


def huella_archivo(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def guardar_bosque(X, y, entrenables, evaluables) -> dict:
    """joblib sobre el objeto entero: lleva la tuberia y la lista de columnas."""
    import joblib

    modelo = BosqueAleatorio(
        n_arboles=HIPERPARAMETROS["n_estimators"],
        semilla=HIPERPARAMETROS["random_state"],
        nombre="bosque_aleatorio_rezagos_relativos",
    )
    modelo.entrenar(X[entrenables], y[entrenables].astype(int).to_numpy())

    antes = np.asarray(modelo.predecir(X[evaluables]), dtype=int)
    ruta = DESTINO / "bosque_aleatorio.joblib"
    joblib.dump(modelo, ruta, compress=3)

    # Se carga de nuevo desde el disco, en vez de reutilizar el objeto en memoria:
    # el objetivo es probar el archivo, no el objeto.
    recargado = joblib.load(ruta)
    despues = np.asarray(recargado.predecir(X[evaluables]), dtype=int)

    metricas = evaluar(y[evaluables].astype(int).to_numpy(), despues)
    return {
        "archivo": ruta.name,
        "formato": "joblib (objeto BosqueAleatorio con su Pipeline de scikit-learn)",
        "megabytes": round(ruta.stat().st_size / 1_048_576, 2),
        "sha256_archivo": huella_archivo(ruta),
        "n_entrenamiento": int(entrenables.sum()),
        "hiperparametros": {k: str(v) for k, v in HIPERPARAMETROS.items()},
        "huella_predicciones_en_memoria": huella(antes),
        "huella_predicciones_recargado": huella(despues),
        "el_archivo_predice_igual": bool(np.array_equal(antes, despues)),
        "f1_macro_validacion": round(metricas["f1_macro"], 6),
        "precision_direccional_validacion": round(metricas["precision_direccional"], 6),
        "como_se_usa": (
            "import joblib; modelo = joblib.load('modelos_entrenados/"
            "bosque_aleatorio.joblib'); modelo.predecir(X)"
        ),
    }


def guardar_avanzado(panel, X, y, entrenables, evaluables) -> dict:
    """Los pesos de la red, no el objeto: el objeto carga el panel entero."""
    import torch

    from src.modelos.avanzado import (
        DIMENSION,
        EPOCAS,
        LOOKBACK_POR_DEFECTO,
        PROFUNDIDAD,
        ITransformerAvanzado,
        cierres_del_panel,
    )

    cierres = cierres_del_panel(panel)
    modelo = ITransformerAvanzado(cierres, w=VENTANA_W, h=HORIZONTE_H, semilla=0)
    modelo.entrenar(X[entrenables], y[entrenables].astype(int).to_numpy())

    antes = np.asarray(modelo.predecir(X[evaluables]), dtype=int)

    ruta = DESTINO / "itransformer.pt"
    torch.save(
        {
            "state_dict": modelo._red.state_dict(),
            "constructor": {
                "w": VENTANA_W,
                "h": HORIZONTE_H,
                "lookback": LOOKBACK_POR_DEFECTO,
                "dimension": DIMENSION,
                "profundidad": PROFUNDIDAD,
                "epocas": EPOCAS,
                "semilla": 0,
                "columnas": list(cierres.columns),
            },
            "n_parametros": modelo.n_parametros,
        },
        ruta,
    )

    # Se reconstruye el envoltorio desde cero y se le inyectan los pesos del archivo.
    # No se entrena: si hiciera falta entrenar, el archivo no serviria de nada.
    guardado = torch.load(ruta, weights_only=False)
    recargado = ITransformerAvanzado(cierres, w=VENTANA_W, h=HORIZONTE_H, semilla=0)
    red = recargado._construir_red(len(guardado["constructor"]["columnas"]))
    red.load_state_dict(guardado["state_dict"])
    red.eval()
    recargado._red = red
    despues = np.asarray(recargado.predecir(X[evaluables]), dtype=int)

    metricas = evaluar(y[evaluables].astype(int).to_numpy(), despues)
    return {
        "archivo": ruta.name,
        "formato": "torch.save con state_dict y los parametros del constructor",
        "megabytes": round(ruta.stat().st_size / 1_048_576, 2),
        "sha256_archivo": huella_archivo(ruta),
        "n_parametros": modelo.n_parametros,
        "segundos_entrenamiento": modelo.segundos_entrenamiento,
        "perdida_final": round(float(modelo.perdida_final), 6),
        "huella_predicciones_en_memoria": huella(antes),
        "huella_predicciones_recargado": huella(despues),
        "el_archivo_predice_igual": bool(np.array_equal(antes, despues)),
        "f1_macro_validacion": round(metricas["f1_macro"], 6),
        "lo_que_esto_arregla": (
            "La D25 documenta que este modelo no reproduce ENTRE PROCESOS: reentrenarlo "
            "da pesos distintos. El archivo lo arregla para quien lo reciba, porque lo "
            "que no reproduce es el entrenamiento y la inferencia con pesos fijos si es "
            "determinista. Cargar este archivo da siempre las mismas predicciones."
        ),
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    analizador = argparse.ArgumentParser(description=__doc__)
    analizador.add_argument(
        "--con-avanzado",
        action="store_true",
        help="guarda tambien el iTransformer; necesita el entorno con torch",
    )
    argumentos = analizador.parse_args()

    DESTINO.mkdir(exist_ok=True)

    panel = pd.read_parquet(RAIZ / "data" / "processed" / f"panel_{GRANULARIDAD}_v1.parquet")
    X = construir(panel, rezagos_relativos=True)
    y = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), VENTANA_W), HORIZONTE_H)
    particion = particionar(n=len(y), w=VENTANA_W, h=HORIZONTE_H)
    entrenables = particion.entrenamiento & y.notna().to_numpy()
    evaluables = particion.validacion & y.notna().to_numpy()

    print(f"entrenamiento: {int(entrenables.sum())} velas · validacion: {int(evaluables.sum())}\n")

    modelos = {}
    print("bosque aleatorio...", flush=True)
    modelos["bosque_aleatorio"] = guardar_bosque(X, y, entrenables, evaluables)

    if argumentos.con_avanzado:
        print("iTransformer...", flush=True)
        modelos["itransformer"] = guardar_avanzado(panel, X, y, entrenables, evaluables)

    medido = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "que_es": (
            "Los modelos entrenados, guardados como archivo y comprobados: cada uno se "
            "vuelve a cargar desde el disco y se verifica que predice exactamente lo "
            "mismo, por huella SHA-256 de las predicciones sobre validacion."
        ),
        "por_que": (
            "El caso pide el modelo de clasificacion entrenado como entregable. Antes de "
            "esto se entregaba el codigo que lo reentrena, que no es lo mismo."
        ),
        "chronos_bolt": {
            "se_guarda": False,
            "por_que": (
                "Es zero-shot: no hay nada ajustado por nosotros que guardar. Lo que lo "
                "hace reproducible es el repositorio y la revision de los pesos."
            ),
            "repo": REPO_POR_DEFECTO,
        },
        "modelos": modelos,
    }
    EVIDENCIA.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    for nombre, d in modelos.items():
        estado = "IDENTICAS" if d["el_archivo_predice_igual"] else "DISTINTAS"
        print(f"  {nombre:20} {d['megabytes']:>7} MB   recargado -> {estado}")
        print(f"  {'':20} huella {d['huella_predicciones_recargado'][:16]}…")

    if not all(d["el_archivo_predice_igual"] for d in modelos.values()):
        raise SystemExit(
            "\nERROR: algun archivo no predice lo mismo al recargarse. No se entrega "
            "asi: un artefacto que parece el modelo y no lo es es peor que ninguno."
        )

    print(f"\nconstancia en {EVIDENCIA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
