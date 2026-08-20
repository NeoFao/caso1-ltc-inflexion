"""Repite los diagnosticos del marco teorico sobre el panel de 4 horas.

El marco teorico de la Semana 1 se midio sobre velas diarias, que era la
granularidad vigente entonces. El contrato quedo congelado despues en 4 horas, de
modo que el documento caracteriza el fenomeno en una granularidad distinta de la
que usa el proyecto.

Este guion mide lo mismo sobre el panel de trabajo para poder declarar en el
documento donde las conclusiones se sostienen y donde cambian. No sustituye a las
figuras de la Semana 1: las complementa.

Salida:
    docs/evidencias/verificacion-4h.json

Uso:
    uv run python scripts/verificacion_4h.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from contracts.config import ACTIVO_OBJETIVO  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from src.diagnostico.pruebas import autocorrelacion, tabla_estacionariedad  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
VENTANA_VOLATILIDAD = 30
REZAGOS = 40


def main() -> None:
    panel = pd.read_parquet(RAIZ / "data" / "processed" / "panel_4h_v1.parquet")
    objetivo = cierre(panel, ACTIVO_OBJETIVO)
    retornos = objetivo.pct_change().dropna()

    nivel = tabla_estacionariedad(panel, en_retornos=False)
    en_retornos = tabla_estacionariedad(panel, en_retornos=True)

    volatilidad = retornos.rolling(VENTANA_VOLATILIDAD).std().dropna()

    acf_nivel = autocorrelacion(objetivo, rezagos=REZAGOS)
    acf_retornos = autocorrelacion(retornos, rezagos=REZAGOS)
    # statsmodels devuelve el intervalo CENTRADO EN LA PROPIA ESTIMACION, no una
    # banda alrededor de cero. Comparar acf contra su propio limite superior no
    # puede dar verdadero nunca; el criterio correcto es contrastar la magnitud de
    # la estimacion contra el margen de error, que es lo que hace
    # scripts/figuras_marco_teorico.py y lo que sostiene el "3 de 40" del documento.
    #
    # Se cuenta desde el rezago 1: el 0 es la serie consigo misma y vale siempre 1.
    sin_cero = acf_retornos.iloc[1:]
    margen = (sin_cero["superior"] - sin_cero["acf"]).abs()
    fuera = sin_cero[sin_cero["acf"].abs() > margen]

    medido = {
        "_meta": {
            "generado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "proposito": (
                "Verificar sobre el panel de 4 horas los diagnosticos que el marco "
                "teorico de la Semana 1 midio sobre velas diarias."
            ),
            "granularidad": "4h",
            "n_observaciones": int(len(panel)),
        },
        "estacionariedad": {
            "nivel": {
                f["serie"]: {
                    "p_valor": round(float(f["p_valor"]), 4),
                    "rechaza": bool(f["rechaza_raiz_unitaria_5pct"]),
                }
                for _, f in nivel.iterrows()
            },
            "cuantas_rechazan_en_nivel": int(nivel["rechaza_raiz_unitaria_5pct"].sum()),
            "cuantas_rechazan_en_retornos": int(en_retornos["rechaza_raiz_unitaria_5pct"].sum()),
        },
        "volatilidad": {
            "maxima": round(float(volatilidad.max()), 4),
            "minima": round(float(volatilidad.min()), 4),
            "cociente_agitado_tranquilo": round(float(volatilidad.max() / volatilidad.min()), 1),
            "ventana": VENTANA_VOLATILIDAD,
        },
        "autocorrelacion": {
            "acf_nivel_rezago_1": round(float(acf_nivel["acf"].iloc[1]), 3),
            "acf_retornos_rezago_1": round(float(acf_retornos["acf"].iloc[1]), 3),
            "rezagos_significativos_en_retornos": [int(r) for r in fuera["rezago"]][:12],
            "cuantos_significativos": int(len(fuera)),
            "rezagos_evaluados": REZAGOS,
        },
    }

    destino = RAIZ / "docs" / "evidencias" / "verificacion-4h.json"
    destino.write_text(json.dumps(medido, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"escrito: {destino.relative_to(RAIZ)}")
    print(json.dumps(medido["estacionariedad"], ensure_ascii=False, indent=2))
    print(json.dumps(medido["volatilidad"], ensure_ascii=False))
    print(json.dumps(medido["autocorrelacion"], ensure_ascii=False))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
