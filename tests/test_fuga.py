"""Pruebas de ausencia de fuga de informacion (RF-E2).

La fuga es el riesgo R4 del PRD: produce metricas excelentes y un sistema
inservible, y no se nota mirando los resultados. Estas pruebas son la unica
defensa automatica que tenemos contra ella.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from contracts.config import ACTIVOS
from contracts.schema import CAMPOS_OHLCV, INDICE
from src.evaluacion.fuga import FugaDetectada, verificar_sin_fuga
from src.features.base import construir


def panel_falso(n: int = 400, semilla: int = 0) -> pd.DataFrame:
    """Panel con la forma del contrato pero valores inventados.

    Sirve para probar la maquinaria sin depender de que exista el panel real, que
    es lo que permite que las pruebas corran en CI sin descargar nada.
    """
    generador = np.random.default_rng(semilla)
    indice = pd.date_range("2021-01-01", periods=n, freq="D", tz="UTC", name=INDICE)
    columnas = {}
    for k, activo in enumerate(ACTIVOS):
        base = 100.0 * (k + 1) * np.exp(np.cumsum(generador.normal(0, 0.02, n)))
        for campo in CAMPOS_OHLCV:
            ruido = generador.normal(1.0, 0.005, n)
            columnas[f"{activo}_{campo}"] = base * ruido
    return pd.DataFrame(columnas, index=indice)


def test_las_features_actuales_no_miran_al_futuro():
    verificar_sin_fuga(construir, panel_falso())


def test_la_verificacion_detecta_una_fuga_deliberada():
    """Si esta prueba fallara, la verificacion no sirve: estaria aprobando todo.

    El constructor con fuga usa shift(-1), que trae el valor de la vela siguiente.
    Es exactamente el tipo de error de un caracter que la prueba tiene que atrapar.
    """

    def constructor_con_fuga(panel: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame({"mira_manana": panel["LTC_cierre"].shift(-1)}, index=panel.index)

    with pytest.raises(FugaDetectada):
        verificar_sin_fuga(constructor_con_fuga, panel_falso())


def test_una_media_movil_centrada_tambien_se_detecta():
    """El caso realista: rolling(center=True) parece inofensivo y usa el futuro."""

    def constructor_centrado(panel: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame(
            {"media_centrada": panel["LTC_cierre"].rolling(11, center=True).mean()},
            index=panel.index,
        )

    with pytest.raises(FugaDetectada):
        verificar_sin_fuga(constructor_centrado, panel_falso())
