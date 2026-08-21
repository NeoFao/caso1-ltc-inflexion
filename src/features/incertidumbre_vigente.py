"""Los intervalos, remedidos con la representacion que quedo vigente tras el #58.

Por que este archivo existe en vez de regenerar el otro
-------------------------------------------------------
`src/features/incertidumbre.py` produjo `docs/evidencias/m2-incertidumbre.json`, y
esas cifras estan citadas en las conclusiones de la Semana 2, que ya se entrego. La
**D13** dice que remedir una entrega pasada produce evidencia nueva y nunca reescribe
la entregada. Asi que aquel archivo se queda como esta —declarando que midio rezagos
en nivel, que era el default cuando se midio— y las cifras vigentes van aqui.

Que cambio y por que hay que remedirlo
--------------------------------------
Cuando se corrio el bootstrap original, `construir()` producia rezagos en nivel de
precio. El PR #58 cambio ese default a rezagos relativos. Un intervalo calculado sobre
la representacion anterior es el intervalo de una configuracion que ya no existe: sigue
siendo cierto sobre lo que midio, y deja de describir el modelo del proyecto.

El propio comentario del archivo original lo anticipaba: *"cuando entre el cambio de
default hay que repetir esto"*.

La comparacion que ahora importa
--------------------------------
El bootstrap original comparaba `bosque_aleatorio` contra una variante que quitaba las
columnas de precio en nivel. Esa comparacion respondia una pregunta que ya se
respondio: se tomo la decision, entro en el #58. La pregunta viva es otra —**cuanto
compro ese cambio**, y si el modelo con la representacion nueva supera al azar de forma
distinguible— y para eso los dos modelos se entrenan sobre matrices distintas y se
evaluan sobre las mismas filas.

El remuestreo pareado sigue siendo valido ahi: lo que se remuestrea son las filas de
validacion, que son las mismas para los dos, no las columnas con que se entrenaron.

Punto de entrada:  uv run python -m src.features.incertidumbre_vigente
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from contracts.config import (
    ACTIVO_OBJETIVO,
    DELTA_F1_DECISIVO,
    GRANULARIDAD,
    HORIZONTE_H,
    VENTANA_W,
)
from contracts.labeling import etiquetar, objetivo
from contracts.metrics import f1_macro, precision_direccional
from contracts.schema import cierre
from contracts.splits import particionar
from src.features.base import construir
from src.features.incertidumbre import (
    REMUESTRAS,
    intervalo_diferencia,
    intervalo_metrica,
    resumen_clases,
)
from src.modelos.base import BaselineAleatorio, BaselineTrivial
from src.modelos.clasico import BosqueAleatorio

EVIDENCIAS = Path("docs/evidencias")

#: Los dos numeros que este modulo tiene que reproducir antes de publicar nada.
#: Salen de dos mediciones independientes que ya estan en el repositorio, y el
#: segundo lo obtuvieron por separado M3 (#63) y M2 (#62) con codigo distinto.
CONTROLES = {
    "bosque_rezagos_en_nivel": 0.3443065490077563,
    "bosque_aleatorio": 0.390497720487045,
}


def _matrices():
    """Las dos representaciones sobre las mismas filas.

    Que las filas coincidan es lo que hace legitimo el remuestreo pareado entre
    modelos entrenados con matrices distintas, asi que se construyen juntas y con las
    mismas mascaras a proposito.
    """
    panel = pd.read_parquet(f"data/processed/panel_{GRANULARIDAD}_v1.parquet")
    y = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), VENTANA_W), HORIZONTE_H)
    particion = particionar(len(panel), VENTANA_W, HORIZONTE_H)

    entrenables = particion.entrenamiento & y.notna().to_numpy()
    validables = particion.validacion & y.notna().to_numpy()

    matrices = {}
    for clave, relativo in (("relativo", True), ("nivel", False)):
        X = construir(panel, rezagos_relativos=relativo)
        matrices[clave] = (X[entrenables], X[validables])

    return (
        matrices,
        y[entrenables],
        y[validables].astype(int).to_numpy(),
        y[particion.prueba & y.notna().to_numpy()].astype(int).to_numpy(),
    )


def _predicciones(matrices, y_entrena, semilla: int = 0) -> dict[str, np.ndarray]:
    salida: dict[str, np.ndarray] = {}
    for nombre, modelo, clave in (
        ("baseline_trivial", BaselineTrivial(), "relativo"),
        ("baseline_aleatorio", BaselineAleatorio(semilla=semilla), "relativo"),
        ("bosque_aleatorio", BosqueAleatorio(semilla=semilla), "relativo"),
        (
            "bosque_rezagos_en_nivel",
            BosqueAleatorio(semilla=semilla, nombre="bosque_rezagos_en_nivel"),
            "nivel",
        ),
    ):
        X_entrena, X_valida = matrices[clave]
        modelo.entrenar(X_entrena, y_entrena)
        salida[nombre] = np.asarray(modelo.predecir(X_valida), dtype=int)
    return salida


def verificar_controles(predicciones, y_valida, tolerancia: float = 1e-9) -> dict:
    """Los dos modelos tienen que reproducir cifras que ya estan publicadas.

    Si alguno no lo hace, algo cambio en el camino —el filtrado de filas, el orden de
    las columnas, los hiperparametros— y ningun intervalo de este archivo describe lo
    que dice describir.
    """
    obtenidos = {
        nombre: float(f1_macro(y_valida, predicciones[nombre])) for nombre in CONTROLES
    }
    fallos = [
        f"{nombre}: obtenido {obtenidos[nombre]!r}, publicado {esperado!r}"
        for nombre, esperado in CONTROLES.items()
        if abs(obtenidos[nombre] - esperado) > tolerancia
    ]
    if fallos:
        raise AssertionError(
            "Los controles no reproducen las cifras ya publicadas. No se publica nada "
            "hasta entenderlo:\n  - " + "\n  - ".join(fallos)
        )
    return obtenidos


def sensibilidad_a_la_semilla(semillas=(0, 1, 2, 3, 4)) -> dict:
    """Las dos diferencias que sostienen conclusiones, por semilla del bosque.

    El bootstrap acota la variabilidad del conjunto de evaluacion. Esto acota la del
    ajuste. Una diferencia que cambia de signo al reentrenar no es un efecto, por
    estrecho que salga su intervalo.
    """
    matrices, y_entrena, y_valida, _ = _matrices()

    filas = []
    for semilla in semillas:
        pred = _predicciones(matrices, y_entrena, semilla=semilla)
        f1 = {nombre: float(f1_macro(y_valida, p)) for nombre, p in pred.items()}
        filas.append(
            {
                "semilla": int(semilla),
                **{f"f1_{k}": v for k, v in f1.items()},
                "vs_baseline_aleatorio": f1["bosque_aleatorio"] - f1["baseline_aleatorio"],
                "vs_rezagos_en_nivel": (
                    f1["bosque_aleatorio"] - f1["bosque_rezagos_en_nivel"]
                ),
            }
        )

    resumen = {"por_semilla": filas}
    for clave in ("vs_baseline_aleatorio", "vs_rezagos_en_nivel"):
        valores = np.array([f[clave] for f in filas])
        resumen[clave] = {
            "media": float(valores.mean()),
            "minima": float(valores.min()),
            "maxima": float(valores.max()),
            "desviacion": float(valores.std(ddof=1)),
            "cambia_de_signo": bool(valores.min() < 0 < valores.max()),
            "todas_superan_el_umbral": bool((np.abs(valores) >= DELTA_F1_DECISIVO).all()),
        }
    return resumen


def generar_evidencia(directorio: Path | None = None) -> dict:
    matrices, y_entrena, y_valida, y_prueba = _matrices()
    predicciones = _predicciones(matrices, y_entrena)
    obtenidos = verificar_controles(predicciones, y_valida)

    intervalos = {
        nombre: {
            "f1_macro": intervalo_metrica(y_valida, pred, f1_macro),
            "precision_direccional": intervalo_metrica(y_valida, pred, precision_direccional),
        }
        for nombre, pred in predicciones.items()
    }

    comparaciones = {
        f"{a}__vs__{b}": intervalo_diferencia(y_valida, predicciones[a], predicciones[b], f1_macro)
        for a, b in (
            ("bosque_aleatorio", "baseline_aleatorio"),
            ("bosque_aleatorio", "baseline_trivial"),
            ("bosque_aleatorio", "bosque_rezagos_en_nivel"),
            ("bosque_rezagos_en_nivel", "baseline_aleatorio"),
        )
    }

    destino = directorio or EVIDENCIAS
    destino.mkdir(parents=True, exist_ok=True)

    evidencia = {
        "que_es": (
            "Los intervalos del proyecto remedidos con rezagos relativos, que es el "
            "default desde el PR #58. NO reemplaza a m2-incertidumbre.json, que midio "
            "rezagos en nivel y esta citado en las conclusiones de la Semana 2: por la "
            "D13, aquello es lo que se entrego y esto es lo que vale hoy."
        ),
        "parametros": {
            "panel": GRANULARIDAD,
            "w": VENTANA_W,
            "h": HORIZONTE_H,
            "conjunto": "validacion",
            "representacion": "rezagos relativos (default desde el #58)",
            "remuestras": REMUESTRAS,
            "remuestreo": "estratificado por clase real, pareado entre modelos",
            "delta_f1_decisivo": DELTA_F1_DECISIVO,
        },
        "controles": {
            "descripcion": (
                "Cada modelo reproduce una cifra ya publicada antes de que se calcule "
                "ningun intervalo. El 0,390497720487045 lo obtuvieron por separado M3 "
                "en el #63 y M2 en el #62, con codigo distinto."
            ),
            "esperado": CONTROLES,
            "obtenido": obtenidos,
            "reproduce": True,
        },
        "tamano_validacion": resumen_clases(y_valida).to_dict(orient="records"),
        "tamano_prueba_sin_tocar": resumen_clases(y_prueba).to_dict(orient="records"),
        "intervalos": intervalos,
        "comparaciones_pareadas": comparaciones,
        "sensibilidad_a_la_semilla": sensibilidad_a_la_semilla(),
        "_meta": {
            "generado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "reemplaza_para_citas_vigentes": "docs/evidencias/m2-incertidumbre.json",
            "advertencia": (
                "Medido sobre VALIDACION y no sobre prueba, por las mismas dos razones "
                "de siempre: las cifras que se quieren acotar estan medidas ahi, y el "
                "bloque de prueba se reserva para el resultado final."
            ),
        },
    }

    ruta = destino / f"m2-incertidumbre-vigente-{GRANULARIDAD}-w{VENTANA_W}-h{HORIZONTE_H}.json"
    ruta.write_text(json.dumps(evidencia, indent=1, ensure_ascii=False), encoding="utf-8")
    return evidencia


if __name__ == "__main__":
    salida = generar_evidencia()
    print("Controles: los dos modelos reproducen sus cifras publicadas.")
    for nombre, valor in salida["controles"]["obtenido"].items():
        print(f"  {nombre:<26} {valor!r}")

    print("\n=== F1 macro con intervalo al 95 % (validacion, rezagos relativos) ===")
    print(
        pd.DataFrame(
            [
                {
                    "modelo": nombre,
                    "f1_macro": round(b["f1_macro"]["valor"], 4),
                    "ic_95": f"[{b['f1_macro']['ic_inferior']:.4f}, "
                    f"{b['f1_macro']['ic_superior']:.4f}]",
                    "prec_dir": round(b["precision_direccional"]["valor"], 4),
                }
                for nombre, b in salida["intervalos"].items()
            ]
        ).to_string(index=False)
    )

    print("\n=== diferencias con remuestreo PAREADO ===")
    print(
        pd.DataFrame(
            [
                {
                    "comparacion": nombre.replace("__vs__", "  vs  "),
                    "diferencia": round(b["diferencia"], 4),
                    "ic_95": f"[{b['ic_inferior']:.4f}, {b['ic_superior']:.4f}]",
                    "excluye_cero": b["excluye_el_cero"],
                }
                for nombre, b in salida["comparaciones_pareadas"].items()
            ]
        ).to_string(index=False)
    )

    print("\n=== las mismas diferencias, cambiando solo la semilla ===")
    sensibilidad = salida["sensibilidad_a_la_semilla"]
    print(
        pd.DataFrame(sensibilidad["por_semilla"])[
            ["semilla", "f1_bosque_aleatorio", "vs_baseline_aleatorio", "vs_rezagos_en_nivel"]
        ]
        .round(4)
        .to_string(index=False)
    )
    for clave in ("vs_baseline_aleatorio", "vs_rezagos_en_nivel"):
        r = sensibilidad[clave]
        print(
            f"  {clave:<24} media {r['media']:+.4f}  "
            f"rango [{r['minima']:+.4f}, {r['maxima']:+.4f}]  "
            f"cambia de signo: {r['cambia_de_signo']}"
        )
