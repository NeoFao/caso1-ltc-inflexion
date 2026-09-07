"""Comprueba que un modelo prediga bit a bit lo mismo en procesos distintos.

Por que existe
--------------
La D25 acota donde la condicion 2 de la D16 puede decidir: solo en contrastes entre
modelos cuyas predicciones se reproducen. El remuestreo pareado resamplea las FILAS
condicionando en un solo sorteo del entrenamiento, asi que su supuesto --predicciones
fijas-- se viola cuando el modelo no reproduce, y el intervalo pasa a responder otra
pregunta.

Esa decision se apoyaba en una medicion que vivia solo en la prosa: que el bosque y el
`baseline_aleatorio` si reproducen. Una afirmacion de la que cuelga que la regla de la
seccion 5 del protocolo siga en pie no puede ser una frase; tiene que ser algo que
cualquiera vuelva a correr.

Como se usa
-----------
Se corre DOS o mas veces, en procesos distintos, y se comparan los hashes:

    uv run python scripts/reproducibilidad_predicciones.py
    uv run python scripts/reproducibilidad_predicciones.py

Con `--json <ruta>` deja la constancia en un archivo. Iguales entre corridas quiere
decir que el modelo reproduce; distintos, que no.

Lo que NO hace
--------------
No toca `docs/evidencias/` salvo que se le pida el `--json`, y **nunca** mide sobre el
bloque de prueba: solo validacion. No pasa por el arnes ni por el pestillo, porque no
produce cifras comparables -- produce huellas.
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

from contracts.config import ACTIVO_OBJETIVO, HORIZONTE_H, VENTANA_W  # noqa: E402
from contracts.labeling import etiquetar, objetivo  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from contracts.splits import particionar  # noqa: E402
from src.features.base import construir  # noqa: E402
from src.modelos.base import BaselineAleatorio  # noqa: E402
from src.modelos.clasico import HIPERPARAMETROS, BosqueAleatorio  # noqa: E402


def huellas() -> dict:
    """SHA-256 de las predicciones de cada modelo sobre validacion."""
    panel = pd.read_parquet(RAIZ / "data" / "processed" / "panel_4h_v1.parquet")
    X = construir(panel, rezagos_relativos=True)
    w, h = VENTANA_W, HORIZONTE_H
    y = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), w), h)
    particion = particionar(n=len(y), w=w, h=h)

    entrenables = particion.entrenamiento & y.notna().to_numpy()
    mascara = particion.validacion & y.notna().to_numpy()
    semilla = HIPERPARAMETROS["random_state"]

    modelos = {
        "bosque_aleatorio_rezagos_relativos": BosqueAleatorio(
            n_arboles=HIPERPARAMETROS["n_estimators"],
            semilla=semilla,
            nombre="bosque_aleatorio_rezagos_relativos",
        ),
        "baseline_aleatorio": BaselineAleatorio(semilla=semilla),
    }

    resultado = {}
    for nombre, modelo in modelos.items():
        modelo.entrenar(X[entrenables], y[entrenables])
        pred = np.asarray(modelo.predecir(X[mascara])).astype("int64")
        resultado[nombre] = hashlib.sha256(pred.tobytes()).hexdigest()

    return {
        "que_es": (
            "Huella SHA-256 de las predicciones sobre validacion. Dos corridas en "
            "procesos distintos con la misma huella quiere decir que el modelo "
            "reproduce bit a bit, que es lo que la condicion 2 de la D16 necesita "
            "para tener sentido (D25)."
        ),
        "conjunto": "validacion",
        "n_filas": int(mascara.sum()),
        "semilla": semilla,
        "cuando_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "huellas": resultado,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default=None, help="deja la constancia en esta ruta")
    argumentos = parser.parse_args()

    datos = huellas()
    print(f"validacion: {datos['n_filas']} filas, semilla {datos['semilla']}")
    for nombre, firma in datos["huellas"].items():
        print(f"  {nombre:38} {firma}")

    if argumentos.json:
        ruta = Path(argumentos.json)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nconstancia en {ruta}")


if __name__ == "__main__":
    main()
