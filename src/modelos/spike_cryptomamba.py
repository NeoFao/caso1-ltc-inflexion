"""Spike S1-M3-02: se puede usar CryptoMamba en nuestras maquinas, sin CUDA?

Riesgo R3 del PRD. La sospecha escrita en el issue era que CryptoMamba depende de
`mamba-ssm`, que compila contra CUDA y es problematico en Windows. Este guion
comprueba la parte que se puede comprobar con un comando; el intento de
instalacion real se hace aparte, en un entorno desechable, y su resultado se pasa
por --resultado-instalacion porque instalar no es algo que convenga repetir en CI.

Lo que decide el spike no es solo si se puede instalar. El apartado de entregables
del enunciado pide que el segundo modelo sea "un Transformer", y CryptoMamba es un
modelo de espacio de estados basado en Mamba, no un Transformer. Eso es la consulta
5 al profesor (docs/02-consulta-profesor.md). iTransformer e Informer cumplen las
dos lineas del enunciado a la vez.

Salidas:
    docs/evidencias/m3-spike-cryptomamba.json

Uso:
    uv run python -m src.modelos.spike_cryptomamba
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
EVIDENCIAS = RAIZ / "docs" / "evidencias"

PYPI = "https://pypi.org/pypi/mamba-ssm/json"
REPO = "https://github.com/MShahabSepehri/CryptoMamba"
REQUISITOS = (
    "https://raw.githubusercontent.com/MShahabSepehri/CryptoMamba/main/requirements.txt"
)


def _leer(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as respuesta:
        return respuesta.read().decode("utf-8")


def distribuciones_de_mamba() -> dict:
    """Que publica mamba-ssm en PyPI para su ultima version.

    Es el nucleo del asunto: si no hay ruedas, cada instalacion compila desde
    fuente, y compilar la extension CUDA en Windows es lo que la hace inviable.
    """
    datos = json.loads(_leer(PYPI))
    version = datos["info"]["version"]
    archivos = [a["filename"] for a in datos["releases"].get(version, [])]
    return {
        "version": version,
        "archivos": archivos,
        "n_ruedas": sum(1 for a in archivos if a.endswith(".whl")),
        "n_ruedas_windows": sum(1 for a in archivos if "win_amd64" in a or "win32" in a),
        "solo_codigo_fuente": all(a.endswith(".tar.gz") for a in archivos),
    }


def main() -> None:
    import torch

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--resultado-instalacion",
        choices=["no-intentado", "exito", "fallo"],
        default="no-intentado",
        help="que paso al intentar instalar mamba-ssm en un entorno desechable",
    )
    parser.add_argument("--comando-instalacion", default="", help="el comando exacto que se corrio")
    parser.add_argument("--error-instalacion", default="", help="el error literal, sin resumir")
    argumentos = parser.parse_args()

    mamba = distribuciones_de_mamba()
    requisitos = [
        linea.strip()
        for linea in _leer(REQUISITOS).splitlines()
        if linea.strip() and not linea.startswith("#")
    ]

    medido = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "pregunta": "Es viable CryptoMamba sin CUDA, en las maquinas del equipo?",
        "maquina": {
            "python": sys.version.split()[0],
            "plataforma": sys.platform,
            "torch": torch.__version__,
            "cuda_disponible": bool(torch.cuda.is_available()),
        },
        "cryptomamba": {
            "repo": REPO,
            "requirements": requisitos,
            "declara_mamba_ssm": any("mamba" in r for r in requisitos),
        },
        "mamba_ssm_en_pypi": mamba,
        "intento_de_instalacion": {
            "resultado": argumentos.resultado_instalacion,
            "comando": argumentos.comando_instalacion,
            "error": argumentos.error_instalacion,
            "nota": (
                "Se intenta en un entorno desechable, nunca en el del proyecto. No se "
                "reproduce por comando a proposito: compilar mamba-ssm baja torch entero "
                "y no tiene lugar en CI."
            ),
        },
        "nota_arquitectura": (
            "CryptoMamba es un modelo de espacio de estados basado en Mamba, no un "
            "Transformer. El apartado de entregables del enunciado pide un Transformer, "
            "asi que aunque se pudiera instalar quedaria abierto si califica. Consulta 5 "
            "al profesor. iTransformer e Informer cumplen las dos lineas a la vez."
        ),
    }

    print("Spike S1-M3-02 -- CryptoMamba sin CUDA")
    maquina = medido["maquina"]
    print(f"  torch {maquina['torch']}, cuda disponible: {maquina['cuda_disponible']}")
    print(
        f"  mamba-ssm {mamba['version']}: {len(mamba['archivos'])} distribucion(es), "
        f"{mamba['n_ruedas']} ruedas, {mamba['n_ruedas_windows']} para Windows"
    )
    print(f"  CryptoMamba declara mamba-ssm: {medido['cryptomamba']['declara_mamba_ssm']}")

    ruta = EVIDENCIAS / "m3-spike-cryptomamba.json"
    EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nmedido: {ruta.relative_to(RAIZ)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
