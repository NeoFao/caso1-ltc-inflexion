"""Se puede hacer reproducible el entrenamiento del iTransformer? (D25)

Por que existe. La D25 acota donde la condicion 2 de la D16 decide, y ese alcance
descansa en una afirmacion medida: **que el iTransformer no se puede volver
reproducible entre procesos con las palancas habituales**. Esa afirmacion vivia
solo en la prosa de la decision. Aqui se mide, se deja constancia, y queda un
comando para que cualquiera la vuelva a comprobar.

Es la contraparte del guion de reproducibilidad de M0: aquel muestra que el bosque
y el azar SI reproducen bit a bit; este muestra que el avanzado no, y que no es por
falta de haberlo intentado.

Que se prueba, y por que esas tres palancas

    hilos_y_algoritmos  torch.set_num_threads(1) mas use_deterministic_algorithms.
                        Si la causa fuera el orden de reduccion entre hilos, esto lo
                        cerraria.
    hash_fijo           PYTHONHASHSEED fijo. Si la causa fuera el orden de iteracion
                        de algun conjunto o diccionario --que cambia por proceso--
                        esto lo cerraria. Se pasa por el entorno, asi que este guion
                        se relanza a si mismo.
    semilla_sola        Lo que ya se hacia. Es el control: si esta reprodujera, no
                        habria nada que investigar.

Cada palanca se corre en **procesos separados**, que es el punto: dentro de un mismo
proceso el resultado es estable y no diria nada. Se comparan las perdidas finales.

Lo que se mide es la PERDIDA y no el F1, a proposito. El F1 pasa por `etiquetar()`,
que decide con desigualdades estrictas y puede tapar una diferencia --o inventarla--
segun donde caiga la trayectoria. La perdida es la salida directa del entrenamiento.

Salidas:
    docs/evidencias/m3-determinismo-avanzado.json

Uso:
    uv sync --group dev --group modelos
    uv run python -m src.modelos.determinismo_avanzado
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from contracts.config import ACTIVOS
from contracts.schema import columna

RAIZ = Path(__file__).resolve().parents[2]
EVIDENCIAS = RAIZ / "docs" / "evidencias"
DESTINO = EVIDENCIAS / "m3-determinismo-avanzado.json"

#: Corridas por palanca. Con dos ya se ve si difieren; la tercera evita concluir
#: "reproduce" por la casualidad de que dos coincidan.
CORRIDAS = 3

PALANCAS = ("semilla_sola", "hilos_y_algoritmos", "hash_fijo")


def _serie(n: int = 700, semilla: int = 7) -> pd.DataFrame:
    """Serie sintetica y fija. No se usa el panel real a proposito: la pregunta es
    sobre el entrenamiento, no sobre los datos, y asi el guion corre sin el parquet."""
    generador = np.random.default_rng(semilla)
    indice = pd.date_range("2020-08-11", periods=n, freq="4h", tz="UTC", name="fecha")
    return pd.DataFrame(
        {
            columna(activo, "cierre"): 100
            + (j + 1) * np.cumsum(generador.normal(0, 1, size=n))
            for j, activo in enumerate(ACTIVOS)
        },
        index=indice,
    )


def _una_corrida(palanca: str) -> float:
    """Entrena una vez con la palanca puesta y devuelve la perdida final."""
    import torch

    if palanca == "hilos_y_algoritmos":
        torch.set_num_threads(1)
        torch.use_deterministic_algorithms(True)

    from src.modelos.avanzado import ITransformerAvanzado

    cierres = _serie()
    modelo = ITransformerAvanzado(cierres, w=7, h=1, semilla=0, lookback=48, epocas=3)
    modelo.entrenar(
        pd.DataFrame(index=cierres.index[60:400]), pd.Series(dtype="Int64")
    )
    return float(modelo.perdida_final)


def _lanzar(palanca: str) -> float:
    """Corre `_una_corrida` en un proceso NUEVO y devuelve su perdida.

    El proceso aparte es la mitad del experimento: la variabilidad que se investiga
    es justamente la que aparece entre procesos.
    """
    entorno = dict(os.environ)
    if palanca == "hash_fijo":
        entorno["PYTHONHASHSEED"] = "0"

    salida = subprocess.run(
        [sys.executable, "-m", "src.modelos.determinismo_avanzado", "--una", palanca],
        capture_output=True,
        text=True,
        cwd=RAIZ,
        env=entorno,
        check=True,
    )
    return float(salida.stdout.strip().splitlines()[-1])


def main() -> None:
    if "--una" in sys.argv:
        print(_una_corrida(sys.argv[sys.argv.index("--una") + 1]))
        return

    print(f"Determinismo del avanzado -- {CORRIDAS} procesos por palanca\n")
    resultados = {}
    for palanca in PALANCAS:
        perdidas = [_lanzar(palanca) for _ in range(CORRIDAS)]
        distintas = len(set(perdidas))
        resultados[palanca] = {
            "perdidas": perdidas,
            "corridas": CORRIDAS,
            "valores_distintos": distintas,
            "reproduce_entre_procesos": bool(distintas == 1),
            "dispersion_absoluta": float(max(perdidas) - min(perdidas)),
        }
        estado = "REPRODUCE" if distintas == 1 else "no reproduce"
        print(f"  {palanca:20} {estado}   dispersion {max(perdidas) - min(perdidas):.3e}")

    medido = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "pregunta": (
            "Se puede hacer que el entrenamiento del iTransformer reproduzca entre "
            "procesos con las palancas habituales?"
        ),
        "para_que": (
            "La D25 acota donde la condicion 2 de la D16 decide, y ese alcance descansa "
            "en que esta via este cerrada. Sin esta constancia, la unica afirmacion "
            "medida de la D25 que nadie podia volver a comprobar era justo esta."
        ),
        "metodo": (
            "Cada palanca se corre en CORRIDAS procesos separados y se comparan las "
            "perdidas finales. Dentro de un mismo proceso el resultado es estable, asi "
            "que medirlo ahi no diria nada. Se compara la perdida y no el F1 porque el "
            "F1 pasa por etiquetar(), cuyas desigualdades estrictas pueden tapar o "
            "inventar una diferencia."
        ),
        "parametros": {
            "corridas_por_palanca": CORRIDAS,
            "semilla": 0,
            "lookback": 48,
            "epocas": 3,
            "serie": "sintetica y fija, seis activos, 700 velas",
        },
        "por_palanca": resultados,
        "veredicto": {
            "alguna_reproduce": any(
                r["reproduce_entre_procesos"] for r in resultados.values()
            ),
            "lectura": (
                "Si ninguna reproduce, la via de volver reproducible al avanzado esta "
                "cerrada con lo que hay, la D15 se sostiene, y el alcance de la D25 "
                "--que la condicion 2 no decida donde entre este modelo-- queda medido "
                "en vez de supuesto."
            ),
        },
    }

    EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(
        json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nmedido: {DESTINO.relative_to(RAIZ)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
