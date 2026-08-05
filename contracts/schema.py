"""Esquema del panel combinado de las seis criptomonedas.

Formato ancho: una fila por instante, una columna por (activo, campo). Se eligio
ancho sobre largo porque el formato largo obliga a pivotar en cada script de
feature engineering, y eso es friccion diaria para quien esta aprendiendo pandas.
"""

from __future__ import annotations

import pandas as pd

from contracts.config import ACTIVOS

INDICE = "fecha"

CAMPOS_OHLCV = ("apertura", "maximo", "minimo", "cierre", "volumen")


def columna(activo: str, campo: str) -> str:
    """Nombre canonico de una columna del panel. Ej.: columna("LTC", "cierre")."""
    if activo not in ACTIVOS:
        raise ValueError(f"activo desconocido: {activo!r}. Esperado uno de {ACTIVOS}")
    if campo not in CAMPOS_OHLCV:
        raise ValueError(f"campo desconocido: {campo!r}. Esperado uno de {CAMPOS_OHLCV}")
    return f"{activo}_{campo}"


COLUMNAS_PANEL: tuple[str, ...] = tuple(
    f"{activo}_{campo}" for activo in ACTIVOS for campo in CAMPOS_OHLCV
)


def cierre(panel: pd.DataFrame, activo: str) -> pd.Series:
    """Serie de cierre de un activo. Atajo para el uso mas frecuente del panel."""
    return panel[columna(activo, "cierre")]


def validar_panel(panel: pd.DataFrame) -> None:
    """Verifica que un DataFrame cumple el contrato. Lanza ValueError si no.

    Lanza en vez de devolver un booleano para que un panel invalido detenga el
    script donde se produjo el error, y no veinte pasos despues.
    """
    if not isinstance(panel.index, pd.DatetimeIndex):
        raise ValueError(f"el indice debe ser DatetimeIndex, es {type(panel.index).__name__}")

    if panel.index.tz is None:
        raise ValueError("el indice debe tener zona horaria UTC explicita, no naive")

    if panel.index.name != INDICE:
        raise ValueError(f"el indice debe llamarse {INDICE!r}, se llama {panel.index.name!r}")

    if not panel.index.is_monotonic_increasing:
        raise ValueError("el indice debe estar ordenado cronologicamente")

    if panel.index.has_duplicates:
        duplicados = panel.index[panel.index.duplicated()].tolist()[:5]
        raise ValueError(f"el indice tiene instantes duplicados, por ejemplo: {duplicados}")

    faltantes = [c for c in COLUMNAS_PANEL if c not in panel.columns]
    if faltantes:
        raise ValueError(f"faltan {len(faltantes)} columnas del contrato: {faltantes[:8]}")

    no_numericas = [
        c for c in COLUMNAS_PANEL if not pd.api.types.is_numeric_dtype(panel[c])
    ]
    if no_numericas:
        raise ValueError(f"columnas no numericas: {no_numericas[:8]}")
