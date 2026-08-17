"""Metricas de evaluacion. Fuente unica de todos los numeros del informe.

Nadie calcula una metrica a mano ni la reimplementa en su modulo: si dos personas
reportan F1 con implementaciones distintas, la comparacion entre modelos deja de
ser una comparacion.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score

from contracts.labeling import NOMBRES_CLASE, Clase

CLASES_EXTREMAS = (Clase.MAXIMO, Clase.MINIMO)


def _limpiar(y_real, y_pred) -> tuple[np.ndarray, np.ndarray]:
    """Descarta las posiciones donde la etiqueta real es nula (bordes de la serie).

    Predecir sobre un instante cuya verdad no existe no es un acierto ni un error,
    y contarlo como cualquiera de los dos sesga todas las metricas.
    """
    real = pd.Series(y_real)
    pred = pd.Series(y_pred)
    if len(real) != len(pred):
        raise ValueError(f"longitudes distintas: real={len(real)}, pred={len(pred)}")

    # La comparacion es posicional: la fila i de las etiquetas contra la fila i de
    # las predicciones. El indice es metadato y no debe participar.
    #
    # Sin descartarlo, pandas alinea por indice al combinar las mascaras. El arnes
    # entrega las etiquetas como Series con DatetimeIndex y las predicciones como
    # ndarray, que recibe RangeIndex: dos indices disjuntos, interseccion vacia, y
    # todas las metricas se calculaban sobre cero filas. Reportado por M2 en el
    # issue #46.
    real = real.reset_index(drop=True)
    pred = pred.reset_index(drop=True)

    validas = real.notna() & pred.notna()
    return (
        real[validas].to_numpy(dtype=int),
        pred[validas].to_numpy(dtype=int),
    )


def precision_direccional(y_real, y_pred) -> float:
    """Fraccion de los puntos de inflexion reales cuyo tipo se predijo bien.

    De todas las velas que de verdad fueron Maximo o Minimo, cuantas anunciamos
    con el tipo correcto. Se ignoran las velas de Continuidad porque acertar
    "aqui no pasa nada" no es acertar una direccion.

    DEFINICION PROVISIONAL. El enunciado pide Precision Direccional sin precisar
    que significa en un problema de tres clases; es la consulta D5 al profesor.
    Si responde otra cosa, se cambia aqui y solo aqui.

    Devuelve NaN si no hubo ningun extremo real en el periodo, en vez de 0.0:
    no hubo nada que acertar, y un cero se leeria como fracaso del modelo.
    """
    real, pred = _limpiar(y_real, y_pred)
    es_extremo = np.isin(real, [int(c) for c in CLASES_EXTREMAS])
    if not es_extremo.any():
        return float("nan")
    return float((real[es_extremo] == pred[es_extremo]).mean())


def f1_por_clase(y_real, y_pred) -> dict[str, float]:
    real, pred = _limpiar(y_real, y_pred)
    etiquetas = [int(c) for c in Clase]
    valores = f1_score(real, pred, labels=etiquetas, average=None, zero_division=0)
    return {NOMBRES_CLASE[Clase(e)]: float(v) for e, v in zip(etiquetas, valores, strict=True)}


def f1_macro(y_real, y_pred) -> float:
    """Promedio simple del F1 de las tres clases.

    Se usa macro y no ponderado a proposito: con clases desbalanceadas, el
    ponderado premia acertar Continuidad, que es justo lo que un modelo inutil
    hace bien.
    """
    real, pred = _limpiar(y_real, y_pred)
    return float(
        f1_score(real, pred, labels=[int(c) for c in Clase], average="macro", zero_division=0)
    )


def matriz_confusion(y_real, y_pred) -> pd.DataFrame:
    real, pred = _limpiar(y_real, y_pred)
    etiquetas = [int(c) for c in Clase]
    m = confusion_matrix(real, pred, labels=etiquetas)
    nombres = [NOMBRES_CLASE[Clase(e)] for e in etiquetas]
    return pd.DataFrame(
        m,
        index=pd.Index(nombres, name="real"),
        columns=pd.Index(nombres, name="predicho"),
    )


def exactitud(y_real, y_pred) -> float:
    """Se reporta solo para mostrar por que no sirve: con las clases desbalanceadas
    que produce el etiquetado, un modelo que siempre dice Continuidad la tiene alta."""
    real, pred = _limpiar(y_real, y_pred)
    return float((real == pred).mean()) if len(real) else float("nan")


def evaluar(y_real, y_pred) -> dict:
    """Unica funcion que produce numeros para el informe (RF-V1).

    Devuelve un diccionario plano para que se pueda volcar directo a una fila de
    resultados sin que cada persona elija que reportar.
    """
    resultado = {
        "n": int(len(_limpiar(y_real, y_pred)[0])),
        "f1_macro": f1_macro(y_real, y_pred),
        "precision_direccional": precision_direccional(y_real, y_pred),
        "exactitud": exactitud(y_real, y_pred),
    }
    for nombre, valor in f1_por_clase(y_real, y_pred).items():
        resultado[f"f1_{nombre.lower()}"] = valor
    return resultado
