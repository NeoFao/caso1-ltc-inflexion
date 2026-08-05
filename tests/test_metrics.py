"""Pruebas del contrato de metricas."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from contracts.labeling import Clase
from contracts.metrics import (
    evaluar,
    exactitud,
    f1_macro,
    matriz_confusion,
    precision_direccional,
)


def _serie_desbalanceada(n=1000, extremos=40, semilla=0):
    generador = np.random.default_rng(semilla)
    y = np.full(n, int(Clase.CONTINUIDAD))
    posiciones = generador.choice(n, size=extremos, replace=False)
    y[posiciones[: extremos // 2]] = int(Clase.MAXIMO)
    y[posiciones[extremos // 2 :]] = int(Clase.MINIMO)
    return pd.Series(y)


def test_prediccion_perfecta_da_f1_maximo():
    y = _serie_desbalanceada()
    assert f1_macro(y, y) == 1.0
    assert precision_direccional(y, y) == 1.0


def test_el_baseline_trivial_tiene_exactitud_alta_y_f1_macro_bajo():
    """Es la razon entera por la que el proyecto no reporta exactitud.

    Se verifica la relacion entre ambas metricas, no valores concretos: cambiar el
    desbalance del ejemplo no debe romper la prueba mientras la propiedad se cumpla.
    """
    y = _serie_desbalanceada(n=1000, extremos=40)
    trivial = pd.Series(np.full(len(y), int(Clase.CONTINUIDAD)))

    assert exactitud(y, trivial) > 0.9
    assert f1_macro(y, trivial) < 0.4
    assert precision_direccional(y, trivial) == 0.0


def test_precision_direccional_ignora_las_velas_de_continuidad():
    """Acertar 'aqui no pasa nada' no es acertar una direccion."""
    y = pd.Series([int(Clase.CONTINUIDAD)] * 8 + [int(Clase.MAXIMO), int(Clase.MINIMO)])
    pred = pd.Series([int(Clase.MAXIMO)] * 8 + [int(Clase.MAXIMO), int(Clase.MINIMO)])

    assert precision_direccional(y, pred) == 1.0


def test_precision_direccional_sin_extremos_reales_es_nan():
    """Devolver 0.0 se leeria como fracaso del modelo cuando en realidad no hubo
    nada que acertar."""
    y = pd.Series([int(Clase.CONTINUIDAD)] * 20)
    pred = pd.Series([int(Clase.CONTINUIDAD)] * 20)

    assert math.isnan(precision_direccional(y, pred))


def test_las_posiciones_sin_etiqueta_real_no_cuentan():
    """Un instante cuya verdad no existe no es acierto ni error. Contarlo como
    cualquiera de los dos sesga todas las metricas."""
    y = pd.Series(pd.array([pd.NA, pd.NA, 1, 2, 3, 3], dtype="Int64"))
    pred = pd.Series([3, 3, 1, 2, 3, 3])

    assert evaluar(y, pred)["n"] == 4
    assert f1_macro(y, pred) == 1.0


def test_matriz_confusion_conserva_el_total():
    y = _serie_desbalanceada(n=300, extremos=20, semilla=4)
    generador = np.random.default_rng(1)
    pred = pd.Series(generador.choice([1, 2, 3], size=len(y)))

    assert matriz_confusion(y, pred).to_numpy().sum() == len(y)


def test_evaluar_expone_las_metricas_del_enunciado():
    """El enunciado pide Precision Direccional y F1. Si alguien renombra una clave,
    los scripts que escriben el CSV de resultados se rompen aqui y no en el informe."""
    y = _serie_desbalanceada(n=200, extremos=20, semilla=2)
    resultado = evaluar(y, y)

    for clave in ("n", "f1_macro", "precision_direccional", "exactitud"):
        assert clave in resultado
    for clase in ("maximo", "minimo", "continuidad"):
        assert f"f1_{clase}" in resultado
