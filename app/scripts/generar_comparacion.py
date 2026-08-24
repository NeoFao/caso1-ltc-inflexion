"""Congela la comparacion de modelos para el panel de la aplicacion (S2-M1-01).

No mide nada nuevo (RF-U6): lee las metricas que M3 ya calculo y publico en
docs/evidencias/m3-modelos-profundos-4h-w7-h1.json -- los cinco modelos evaluados
sobre la MISMA particion de validacion, que es lo que hace valida la comparacion
lado a lado -- y las copia a app/public/datos/ con los nombres que la interfaz
necesita. Si M3 remide y el JSON de origen cambia, correr este script de nuevo
actualiza el panel sin que nadie edite un numero a mano.

Uso:
    uv run python app/scripts/generar_comparacion.py
"""

from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ORIGEN = RAIZ / "docs" / "evidencias" / "m3-modelos-profundos-4h-w7-h1.json"
DESTINO = RAIZ / "app" / "public" / "datos" / "comparacion-modelos.json"

# Que modelo del JSON de origen entra al panel, con que rotulo y que papel juega
# segun las decisiones ya tomadas por el equipo: D7 (los tres baselines son el
# piso obligatorio -- se muestra el mas exigente, el aleatorio), D14 (avanzado:
# iTransformer con las seis series), D12 (fundacional: Chronos-Bolt), y el bosque
# aleatorio de referencia de S1-M3-01 como "clasico".
MODELOS = [
    ("baseline_aleatorio", "Baseline aleatorio", "piso obligatorio (D7)"),
    ("bosque_aleatorio_rezagos_relativos", "Clasico (bosque aleatorio)", "referencia (S1-M3-01)"),
    ("chronos_bolt", "Fundacional (Chronos-Bolt)", "D12"),
    ("itransformer", "Avanzado (iTransformer)", "D14"),
]

CAMPOS = (
    "f1_macro",
    "precision_direccional",
    "exactitud",
    "f1_maximo",
    "f1_minimo",
    "f1_continuidad",
)


def main() -> None:
    if not ORIGEN.exists():
        raise SystemExit(
            f"falta {ORIGEN.relative_to(RAIZ)}. Es evidencia de M3, no se regenera aca."
        )

    fuente = json.loads(ORIGEN.read_text(encoding="utf-8"))
    metricas = fuente["metricas"]

    modelos = []
    for clave, etiqueta, papel in MODELOS:
        if clave not in metricas:
            raise SystemExit(f"{clave!r} no esta en {ORIGEN.name}; revisar MODELOS")
        m = metricas[clave]
        modelos.append(
            {
                "clave": clave,
                "etiqueta": etiqueta,
                "papel": papel,
                **{campo: m[campo] for campo in CAMPOS},
            }
        )

    salida = {
        "fuente": str(ORIGEN.relative_to(RAIZ)).replace("\\", "/"),
        "ejecutado_utc": fuente["ejecutado_utc"],
        "particion": fuente["parametros"],
        "n": metricas[MODELOS[0][0]]["n"],
        "modelos": modelos,
    }

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"escrito {DESTINO.relative_to(RAIZ)} con {len(modelos)} modelos")


if __name__ == "__main__":
    main()
