"""Inventario de modelos fundacionales de series de tiempo viables en CPU.

Tarea S1-M3-03. RF-M1 exige que la eleccion del modelo fundacional se justifique
segun las caracteristicas medidas de los datos y de nuestras maquinas, no por
popularidad. Sin mediciones no hay justificacion, hay opinion.

Que se mide, por candidato: tiempo de carga, tamano en disco, memoria residente y
tiempo de inferencia sobre una ventana del tamano que usariamos de verdad.

Por que el horizonte es w+h y no h: para saber la etiqueta de t+h hacen falta las
w velas posteriores a t+h. Si el puente pronostico -> clasificacion es aplicar
etiquetar() sobre la trayectoria pronosticada, el modelo tiene que producir
latencia_real(w, h) velas, no h. Ver docs/00-definicion-punto-inflexion.md.

Cada candidato se mide en un subproceso propio: cargar varios modelos en el mismo
proceso acumula memoria y la segunda medicion de RAM seria mentira.

Los paquetes de los candidatos NO estan en pyproject.toml a proposito: esto es un
spike, no codigo de produccion. Si el equipo elige uno, agregarlo al grupo
`modelos` pasa a ser un cambio que se propone por escrito. granite-tsfm quedo
fuera de la comparacion porque degrada torch de 2.13 a 2.10, y eso rompe el
entorno identico que exige RNF-3.

Salidas:
    docs/evidencias/m3-inventario-tsfm.json

Uso:
    uv pip install chronos-forecasting timesfm
    uv run python -m src.modelos.inventario_tsfm
    uv run python -m src.modelos.inventario_tsfm --solo chronos-bolt-small

`uv sync` deja el entorno como lo tiene el resto del equipo y borra esos dos
paquetes; para volver a correr este inventario hay que reinstalarlos.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from contracts.labeling import latencia_real

RAIZ = Path(__file__).resolve().parents[2]
EVIDENCIAS = RAIZ / "docs" / "evidencias"

# Contexto que se le da al modelo. 512 velas de 4 horas son ~85 dias: suficiente
# para que el modelo vea varios ciclos y dentro del contexto nativo de los tres
# candidatos, para que la comparacion sea entre modelos y no entre recortes.
CONTEXTO = 512
VENTANA_W = 7
HORIZONTE_H = 5
HORIZONTE = latencia_real(VENTANA_W, HORIZONTE_H)

REPETICIONES = 5
TAMANO_LOTE = 32
# Filas del bloque de validacion con w=7, h=5 sobre el panel de 4h. Se usa solo
# para extrapolar cuanto tardaria etiquetar el bloque entero, y va marcado como
# extrapolacion en la evidencia.
FILAS_VALIDACION = 1955

CANDIDATOS = {
    "chronos-bolt-small": {
        "repo": "amazon/chronos-bolt-small",
        "familia": "Chronos-Bolt (Amazon)",
        "paquete": "chronos-forecasting",
    },
    "chronos-t5-small": {
        "repo": "amazon/chronos-t5-small",
        "familia": "Chronos-T5 (Amazon)",
        "paquete": "chronos-forecasting",
    },
    "timesfm-2.5-200m": {
        "repo": "google/timesfm-2.5-200m-pytorch",
        "familia": "TimesFM (Google)",
        "paquete": "timesfm",
    },
}


def _serie_de_contexto() -> np.ndarray:
    """Las ultimas CONTEXTO velas de cierre de LTC del panel congelado.

    Se mide sobre datos nuestros a proposito: el tiempo de inferencia depende del
    largo del contexto, y usar una serie inventada daria un numero que no es el que
    vamos a pagar.
    """
    panel = pd.read_parquet(RAIZ / "data" / "processed" / "panel_4h_v1.parquet")
    return panel["LTC_cierre"].to_numpy(dtype="float32")[-CONTEXTO:]


def _tamano_en_cache_mb(repo: str) -> float | None:
    from huggingface_hub.constants import HF_HUB_CACHE

    carpeta = Path(HF_HUB_CACHE) / f"models--{repo.replace('/', '--')}"
    if not carpeta.exists():
        return None
    total = sum(f.stat().st_size for f in carpeta.rglob("*") if f.is_file())
    return round(total / 1024**2, 2)


def _cargar(nombre: str, repo: str):
    """Devuelve (modelo, funcion_de_pronostico). Un adaptador por familia."""
    import torch

    if nombre.startswith("chronos"):
        from chronos import BaseChronosPipeline

        tuberia = BaseChronosPipeline.from_pretrained(repo, device_map="cpu", dtype=torch.float32)

        def pronosticar(lote: list[np.ndarray]) -> np.ndarray:
            entradas = [torch.tensor(s, dtype=torch.float32) for s in lote]
            salida = tuberia.predict(entradas, prediction_length=HORIZONTE)
            return np.asarray([s.numpy() for s in salida])

        return tuberia, pronosticar

    if nombre.startswith("timesfm"):
        import timesfm

        modelo = timesfm.TimesFM_2p5_200M_torch.from_pretrained(repo)
        modelo.compile(
            timesfm.ForecastConfig(
                max_context=CONTEXTO, max_horizon=HORIZONTE, normalize_inputs=True
            )
        )

        def pronosticar(lote: list[np.ndarray]) -> np.ndarray:
            punto, _ = modelo.forecast(horizon=HORIZONTE, inputs=[s for s in lote])
            return np.asarray(punto)

        return modelo, pronosticar

    raise ValueError(f"sin adaptador para {nombre!r}")


def medir_uno(nombre: str) -> dict:
    """Mide un candidato. Un fallo tambien es una medicion y se registra como tal."""
    import psutil

    ficha = CANDIDATOS[nombre]
    repo = ficha["repo"]
    proceso = psutil.Process()

    medida = {
        "nombre": nombre,
        "repo": repo,
        "familia": ficha["familia"],
        "paquete": ficha["paquete"],
        "cache_frio": _tamano_en_cache_mb(repo) is None,
        "contexto": CONTEXTO,
        "horizonte": HORIZONTE,
    }

    rss_antes = proceso.memory_info().rss
    reloj = time.perf_counter()
    try:
        _, pronosticar = _cargar(nombre, repo)
    except Exception as error:  # noqa: BLE001 - el fallo es el resultado del spike
        medida["viable"] = False
        medida["error"] = f"{type(error).__name__}: {error}"
        return medida
    medida["tiempo_carga_s"] = round(time.perf_counter() - reloj, 2)
    medida["memoria_modelo_mb"] = round((proceso.memory_info().rss - rss_antes) / 1024**2, 1)
    medida["tamano_disco_mb"] = _tamano_en_cache_mb(repo)

    serie = _serie_de_contexto()
    try:
        pronosticar([serie])  # calentamiento: la primera pasada paga inicializaciones
        tiempos = []
        for _ in range(REPETICIONES):
            reloj = time.perf_counter()
            salida = pronosticar([serie])
            tiempos.append(time.perf_counter() - reloj)
        medida["tiempo_inferencia_s"] = round(float(np.mean(tiempos)), 4)
        medida["desvio_inferencia_s"] = round(float(np.std(tiempos)), 4)
        medida["forma_salida"] = list(np.shape(salida))

        reloj = time.perf_counter()
        pronosticar([serie] * TAMANO_LOTE)
        por_ventana = (time.perf_counter() - reloj) / TAMANO_LOTE
        medida["tiempo_por_ventana_en_lote_s"] = round(por_ventana, 4)
        medida["extrapolacion_validacion_min"] = round(por_ventana * FILAS_VALIDACION / 60, 1)
        medida["viable"] = True
    except Exception as error:  # noqa: BLE001
        medida["viable"] = False
        medida["error"] = f"{type(error).__name__}: {error}"
    medida["memoria_pico_mb"] = round(proceso.memory_info().rss / 1024**2, 1)
    return medida


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solo", choices=sorted(CANDIDATOS), help="mide un candidato y sale")
    argumentos = parser.parse_args()

    if argumentos.solo:
        print(json.dumps(medir_uno(argumentos.solo), ensure_ascii=False))
        return

    print(f"Inventario de TSFMs en CPU -- contexto {CONTEXTO}, horizonte {HORIZONTE} velas")
    print(f"  horizonte = latencia_real(w={VENTANA_W}, h={HORIZONTE_H}) = {HORIZONTE}\n")

    medidas = []
    for numero, nombre in enumerate(sorted(CANDIDATOS), start=1):
        print(f"[{numero}/{len(CANDIDATOS)}] {nombre} ...", flush=True)
        # Subproceso por candidato: la RAM de uno no puede contaminar la del otro.
        completado = subprocess.run(
            [sys.executable, "-m", "src.modelos.inventario_tsfm", "--solo", nombre],
            capture_output=True,
            text=True,
            cwd=RAIZ,
        )
        linea = completado.stdout.strip().splitlines()
        if completado.returncode != 0 or not linea:
            medidas.append(
                {
                    "nombre": nombre,
                    "repo": CANDIDATOS[nombre]["repo"],
                    "familia": CANDIDATOS[nombre]["familia"],
                    "viable": False,
                    "error": (completado.stderr.strip()[-400:] or "sin salida"),
                }
            )
        else:
            medidas.append(json.loads(linea[-1]))

        ultima = medidas[-1]
        if ultima.get("viable"):
            print(
                f"      carga {ultima['tiempo_carga_s']} s, "
                f"{ultima['tamano_disco_mb']} MB en disco, "
                f"{ultima['memoria_modelo_mb']} MB RAM, "
                f"{ultima['tiempo_inferencia_s']} s por ventana"
            )
        else:
            print(f"      NO VIABLE: {ultima['error'][:160]}")

    tabla = pd.DataFrame(medidas)
    columnas = [
        c
        for c in [
            "nombre",
            "viable",
            "tamano_disco_mb",
            "memoria_modelo_mb",
            "tiempo_carga_s",
            "tiempo_inferencia_s",
            "extrapolacion_validacion_min",
        ]
        if c in tabla.columns
    ]
    print("\n" + tabla[columnas].to_string(index=False))

    salida = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "maquina": {
            "python": sys.version.split()[0],
            "plataforma": sys.platform,
        },
        "parametros": {
            "contexto": CONTEXTO,
            "horizonte": HORIZONTE,
            "w": VENTANA_W,
            "h": HORIZONTE_H,
            "repeticiones": REPETICIONES,
            "tamano_lote": TAMANO_LOTE,
        },
        "nota_horizonte": (
            "El horizonte es latencia_real(w, h) = w + h y no h, porque para conocer la "
            "etiqueta de t+h hacen falta las w velas posteriores a t+h."
        ),
        "nota_tiempo_carga": (
            "tiempo_carga_s mide de cero hasta modelo listo. Si cache_frio es true, "
            "incluye la descarga del repositorio; si es false, es solo leer de disco e "
            "inicializar. La descarga se paga una vez por maquina."
        ),
        "nota_granite": (
            "granite-tsfm (IBM TinyTimeMixer) quedo fuera: su resolucion degrada torch de "
            "2.13.0 a 2.10.0, y un entorno distinto al del resto del equipo rompe RNF-3. "
            "Medido con uv pip install --dry-run, no instalado."
        ),
        "nota_extrapolacion": (
            f"extrapolacion_validacion_min multiplica el tiempo por ventana en lote por "
            f"{FILAS_VALIDACION} filas de validacion. Es una extrapolacion, no un cronometraje."
        ),
        "candidatos": medidas,
    }
    EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    destino = EVIDENCIAS / "m3-inventario-tsfm.json"
    destino.write_text(json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nmedido: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
