"""Cuanto se mueve el modelo avanzado si solo cambia la semilla (S4-M3-01, fase 2 del #92).

Por que existe. El fundacional es zero-shot y determinista: dos corridas dan el
mismo numero. El avanzado se entrena, y ahi aparecen dos fuentes de variabilidad
que conviene separar y que un solo F1 esconde.

La primera es la semilla, que es la de siempre. La segunda es mas incomoda y se
midio al toparse con ella: **dos procesos con la MISMA semilla no dan exactamente
el mismo resultado**. Las diferencias en la perdida son del orden de 1e-11, orden
de reduccion en punto flotante de la CPU, y aun asi mueven el F1 de forma visible.

La razon de que algo tan pequeno se note esta en el puente, no en el modelo:
`etiquetar()` decide con desigualdades ESTRICTAS, asi que sobre una trayectoria
pronosticada casi plana una diferencia minima alcanza para voltear la etiqueta.
Esta documentado en la D15.

Que cambio en la fase 2 del #92, y por que hacia falta. La version anterior
guardaba por semilla solo el F1 macro, y el panel publico muestra SEIS columnas:
F1 macro, precision direccional, exactitud y los tres F1 por clase. Con una sola
metrica medida, publicar medias en las seis era imposible, y el panel terminaba
mostrando una corrida suelta donde la D18 declara medias de cinco. Ahora se
registran las seis, para las dos variantes, y **cada corrida declara su semilla**.

Escribe un archivo NUEVO y no reescribe el anterior. Es la D13: el barrido viejo
lo cita el capitulo de la Semana 2, que ya se entrego, y regenerarlo dejaria al
entregable citando cifras que ya no existen. El anterior queda como historia.

Salidas:
    docs/evidencias/m3-sensibilidad-avanzado-completa-<intervalo>-w<w>-h<h>.json

Uso:
    uv sync --group dev --group modelos
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

# Las seis que muestra el panel publico. Se nombran aqui para que anadir una
# columna alla y no medirla aca vuelva a ser imposible sin que alguien lo note.
METRICAS = (
    "f1_macro",
    "precision_direccional",
    "exactitud",
    "f1_maximo",
    "f1_minimo",
    "f1_continuidad",
)


def _medir(cierres, X, y, particion, semilla: int, solo_objetivo: bool) -> dict:
    """Las seis metricas de una corrida, no solo el F1 macro.

    Devuelve el resultado del arnes recortado a METRICAS. Se usa el arnes y no un
    calculo propio para que las cifras sean las mismas que las de validacion.
    """
    modelo = ITransformerAvanzado(
        cierres, w=7, h=1, semilla=semilla, solo_objetivo=solo_objetivo
    )
    resultado = evaluar_modelo(modelo, X, y, particion, conjunto="validacion")
    return {m: resultado[m] for m in METRICAS}


def _resumen(valores_por_semilla: list[dict]) -> dict:
    """Media, minimo, maximo, rango y desviacion de cada una de las seis."""
    resumen = {}
    for metrica in METRICAS:
        serie = np.array([v[metrica] for v in valores_por_semilla], dtype=float)
        resumen[metrica] = {
            "media": float(serie.mean()),
            "minimo": float(serie.min()),
            "maximo": float(serie.max()),
            "rango": float(serie.max() - serie.min()),
            "desviacion": float(serie.std()),
            "la_de_la_semilla_0_es_el_maximo": bool(serie[0] == serie.max()),
        }
    return resumen


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

    print(
        f"Sensibilidad del avanzado -- {len(SEMILLAS)} semillas x {len(METRICAS)} metricas, "
        f"{argumentos.intervalo}, w={w}, h={h}"
    )

    por_semilla = []
    completos, solo_ltc = [], []
    for semilla in SEMILLAS:
        completo = _medir(cierres, X, y, particion, semilla, solo_objetivo=False)
        uno = _medir(cierres, X, y, particion, semilla, solo_objetivo=True)
        completos.append(completo)
        solo_ltc.append(uno)
        por_semilla.append(
            {
                "semilla": semilla,
                "completo": completo,
                "solo_LTC": uno,
                "diferencia_f1_macro": completo["f1_macro"] - uno["f1_macro"],
            }
        )
        print(
            f"  semilla {semilla}:  F1 {completo['f1_macro']:.6f}  "
            f"PD {completo['precision_direccional']:.6f}  "
            f"exactitud {completo['exactitud']:.6f}  "
            f"Max {completo['f1_maximo']:.6f}  Min {completo['f1_minimo']:.6f}"
        )

    diferencias = np.array([f["diferencia_f1_macro"] for f in por_semilla])

    medido = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "pregunta": (
            "Cuanto se mueve CADA UNA de las seis metricas del modelo avanzado si "
            "solo cambia la semilla?"
        ),
        "para_que": (
            "Fase 2 del issue #92. El panel publico muestra seis columnas y solo se "
            "tenia medida la media de una, asi que publicaba una corrida suelta donde "
            "la D18 declara medias de cinco. Con esto puede publicar medias en las seis."
        ),
        "parametros": {
            "intervalo": argumentos.intervalo,
            "w": w,
            "h": h,
            "conjunto": "validacion",
            "semillas": list(SEMILLAS),
            "configuracion": "lookback 96, dimension 64 (la por omision, D18)",
            "metricas": list(METRICAS),
        },
        "por_semilla": por_semilla,
        "resumen_completo": _resumen(completos),
        "resumen_solo_LTC": _resumen(solo_ltc),
        "aporte_de_los_activos_de_apoyo": {
            "diferencia_media_f1_macro": float(diferencias.mean()),
            "minima": float(diferencias.min()),
            "maxima": float(diferencias.max()),
            "cambia_de_signo": bool(diferencias.min() < 0 < diferencias.max()),
            "nota": (
                "Misma pregunta que respondio el #62 sobre el bosque, sobre la "
                "arquitectura cuyo argumento de venta es atender entre series."
            ),
        },
        "sobre_la_reproducibilidad": (
            "Cada corrida declara su semilla, que es lo que faltaba y motivo la fase 2. "
            "Aun asi, dos procesos con la MISMA semilla no dan identico: es el efecto de "
            "orden de reduccion en punto flotante que documenta la D15, amplificado "
            "porque etiquetar() decide con desigualdades estrictas. Declarar la semilla "
            "no lo elimina; lo que hace es que se pueda saber que corrida fue cual."
        ),
        "relacion_con_el_barrido_anterior": (
            "No reescribe m3-sensibilidad-avanzado-<intervalo>-w<w>-h<h>.json. Aquel mide "
            "solo el F1 macro y sus cifras las cita el capitulo de la Semana 2, que ya se "
            "entrego; regenerarlo dejaria al entregable citando valores que ya no existen. "
            "Es la D13: remedir produce evidencia nueva, no reescribe la entregada. Las "
            "medias de los dos difieren por el mismo efecto de la D15, no porque el modelo "
            "haya cambiado."
        ),
    }

    destino = (
        EVIDENCIAS
        / f"m3-sensibilidad-avanzado-completa-{argumentos.intervalo}-w{w}-h{h}.json"
    )
    EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n  medias de las seis, modelo completo:")
    for metrica in METRICAS:
        r = medido["resumen_completo"][metrica]
        print(f"    {metrica:24} {r['media']:.6f}   rango {r['rango']:.6f}")
    print(f"\nmedido: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
