"""Que candidatos a modelo avanzado se pueden instalar de verdad (S4-M3-01).

El enunciado nombra iTransformer e Informer entre las opciones del segundo modelo,
y RF-M2 exige que su codigo este disponible publicamente. Disponible en internet y
utilizable en nuestras maquinas no son lo mismo, y la diferencia ya nos mordio dos
veces: CryptoMamba no compila sin CUDA, y granite-tsfm degradaba torch.

Este guion comprueba la parte instalable con un comando, para que la eleccion del
modelo avanzado no dependa de que alguien se acuerde de lo que probo. No mide
rendimiento: eso lo produce la corrida del experimento, que entrena y evalua sobre
la particion de verdad.

Salidas:
    docs/evidencias/m3-inventario-avanzado.json

Uso:
    uv run python -m src.modelos.inventario_avanzado
"""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
EVIDENCIAS = RAIZ / "docs" / "evidencias"

CANDIDATOS = {
    "iTransformer": {
        "paquete": "iTransformer",
        "arquitectura": "iTransformer",
        "fuente": "implementacion publica de lucidrains en PyPI",
    },
    "neuralforecast": {
        "paquete": "neuralforecast>=1.7",
        "arquitectura": "Informer e iTransformer, los dos",
        "fuente": "Nixtla; era la ruta obvia porque trae los dos candidatos juntos",
    },
    "informer-pytorch": {
        "paquete": "informer-pytorch",
        "arquitectura": "Informer",
        "fuente": "paquete suelto en PyPI",
    },
}


def _resolver(especificacion: str) -> dict:
    """Pregunta al resolutor si la especificacion se puede satisfacer.

    Se usa --dry-run a proposito: la pregunta es si se PUEDE instalar en este
    entorno, y contestarla no tiene por que dejar el entorno distinto.
    """
    uv = shutil.which("uv")
    if uv is None:
        raise SystemExit(
            "no encuentro `uv` en el PATH, y este guion le pregunta a su resolutor. "
            "Corrementelo desde un shell donde `uv --version` responda."
        )
    completado = subprocess.run(
        [uv, "pip", "install", "--dry-run", especificacion],
        capture_output=True,
        text=True,
        cwd=RAIZ,
    )
    salida = f"{completado.stdout}\n{completado.stderr}".strip()
    resoluble = completado.returncode == 0
    return {
        "resoluble": resoluble,
        "comando": f"uv pip install --dry-run {especificacion}",
        # Solo el final: el resolutor explica el conflicto al final de su salida.
        "salida": salida[-700:] if not resoluble else salida[-200:],
    }


def main() -> None:
    medido = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "pregunta": (
            "Cual de los candidatos a modelo avanzado del enunciado se puede instalar "
            "en las maquinas del equipo?"
        ),
        "maquina": {
            "python": sys.version.split()[0],
            "plataforma": sys.platform,
            "arquitectura": platform.machine(),
        },
        "candidatos": {},
    }

    print("Inventario de candidatos a modelo avanzado")
    for nombre, ficha in CANDIDATOS.items():
        resultado = _resolver(ficha["paquete"])
        medido["candidatos"][nombre] = {**ficha, **resultado}
        estado = "resoluble" if resultado["resoluble"] else "NO resoluble"
        print(f"  {nombre:20} {ficha['arquitectura']:32} {estado}")

    EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    destino = EVIDENCIAS / "m3-inventario-avanzado.json"
    destino.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nmedido: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
