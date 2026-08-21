"""Cuanto se mueve el modelo avanzado si solo cambia la semilla (S4-M3-01).

Por que existe. El fundacional es zero-shot y determinista: dos corridas dan el
mismo numero. El avanzado se entrena, y ahi aparecen dos fuentes de variabilidad
que conviene separar y que un solo F1 esconde.

La primera es la semilla, que es la de siempre. La segunda es mas incomoda y se
midio al toparse con ella: **dos procesos con la MISMA semilla no dan exactamente
el mismo resultado**. Las diferencias en la perdida son del orden de 1e-11, orden
de reduccion en punto flotante de la CPU, y aun asi mueven el F1 de forma visible.

La razon de que algo tan pequeno se note esta en el puente, no en el modelo:
`etiquetar()` decide con desigualdades ESTRICTAS, asi que sobre una trayectoria
pronosticada casi plana una diferencia minima alcanza para voltear la etiqueta de
Continuidad a Maximo. Es una propiedad del metodo y va al informe como tal.

Consecuencia practica: el numero que se reporta del avanzado tiene que venir con
su dispersion, no solo. Reportar cuatro decimales de un valor que se mueve en el
tercero seria fingir una precision que no tenemos.

Salidas:
    docs/evidencias/m3-sensibilidad-avanzado-<intervalo>-w<w>-h<h>.json

Uso:
    uv run python -m src.modelos.sensibilidad_avanzado
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
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

RAIZ = Path(__file__).resolve().parents[2]
EVIDENCIAS = RAIZ / "docs" / "evidencias"
SEMILLAS = (0, 1, 2, 3, 4)


def _f1(cierres, X, y, particion, semilla: int, solo_objetivo: bool) -> float:
    modelo = ITransformerAvanzado(
        cierres, w=7, h=1, semilla=semilla, solo_objetivo=solo_objetivo
    )
    return evaluar_modelo(modelo, X, y, particion, conjunto="validacion")["f1_macro"]


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

    print(f"Sensibilidad del modelo avanzado -- {argumentos.intervalo}, w={w}, h={h}")

    por_semilla = []
    for semilla in SEMILLAS:
        completo = _f1(cierres, X, y, particion, semilla, solo_objetivo=False)
        solo_ltc = _f1(cierres, X, y, particion, semilla, solo_objetivo=True)
        por_semilla.append(
            {
                "semilla": semilla,
                "f1_completo": completo,
                "f1_solo_LTC": solo_ltc,
                "diferencia": completo - solo_ltc,
            }
        )
        print(
            f"  semilla {semilla}: completo {completo:.6f}  solo LTC {solo_ltc:.6f}  "
            f"diferencia {completo - solo_ltc:+.6f}"
        )

    # La segunda fuente: misma semilla, otro proceso. Se repite la semilla 0 aqui
    # mismo; si difiere de la de arriba, la variabilidad no es solo de la semilla.
    repeticion = _f1(cierres, X, y, particion, 0, solo_objetivo=False)
    primera = por_semilla[0]["f1_completo"]

    completos = np.array([f["f1_completo"] for f in por_semilla])
    diferencias = np.array([f["diferencia"] for f in por_semilla])

    medido = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "pregunta": "Cuanto se mueve el F1 del modelo avanzado si solo cambia la semilla?",
        "parametros": {
            "intervalo": argumentos.intervalo,
            "w": w,
            "h": h,
            "conjunto": "validacion",
            "semillas": list(SEMILLAS),
        },
        "por_semilla": por_semilla,
        "resumen_f1_completo": {
            "media": float(completos.mean()),
            "minimo": float(completos.min()),
            "maximo": float(completos.max()),
            "desviacion": float(completos.std()),
            "rango": float(completos.max() - completos.min()),
        },
        "aporte_de_los_activos_de_apoyo": {
            "diferencia_media": float(diferencias.mean()),
            "minima": float(diferencias.min()),
            "maxima": float(diferencias.max()),
            "cambia_de_signo": bool(diferencias.min() < 0 < diferencias.max()),
            "nota": (
                "Misma pregunta que respondio el #62 sobre el bosque, ahora sobre la "
                "arquitectura cuyo argumento de venta es atender entre series."
            ),
        },
        "misma_semilla_otra_corrida": {
            "primera": primera,
            "repeticion": repeticion,
            "identicas": bool(primera == repeticion),
            "diferencia_absoluta": abs(primera - repeticion),
            "nota": (
                "Si no son identicas, la variabilidad no viene solo de la semilla sino "
                "del orden de reduccion en punto flotante de la CPU. Se amplifica porque "
                "etiquetar() usa desigualdades estrictas sobre una trayectoria casi plana."
            ),
        },
    }

    print(f"\n  media {completos.mean():.6f}  rango {completos.max() - completos.min():.6f}")
    print(
        f"  misma semilla, otra corrida: {primera:.6f} vs {repeticion:.6f}  "
        f"(identicas: {primera == repeticion})"
    )

    EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    destino = (
        EVIDENCIAS / f"m3-sensibilidad-avanzado-{argumentos.intervalo}-w{w}-h{h}.json"
    )
    destino.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nmedido: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
