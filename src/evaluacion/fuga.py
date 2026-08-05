"""Verificacion automatica de ausencia de fuga de informacion (RF-E2).

La fuga es el riesgo R4 del PRD y el peor de todos, porque no se nota: produce
metricas excelentes y un sistema inservible. Como la etiqueta de un instante se
calcula mirando velas futuras, basta un rolling sin `closed` o un ffill hacia
atras para contaminar todo sin que ninguna prueba obvia falle.

La idea de la verificacion: si una caracteristica en el instante t solo usa
informacion hasta t, entonces cambiar los datos posteriores a t no puede alterarla.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd


class FugaDetectada(AssertionError):
    """Se lanza como AssertionError para que pytest la reporte como fallo de prueba."""


def verificar_sin_fuga(
    constructor: Callable[[pd.DataFrame], pd.DataFrame],
    datos: pd.DataFrame,
    cortes: int = 5,
    semilla: int = 0,
    tolerancia: float = 1e-9,
) -> None:
    """Comprueba que `constructor` no mira hacia el futuro. Lanza FugaDetectada si lo hace.

    Para varios cortes t: se calculan las caracteristicas sobre los datos
    originales, se perturban fuertemente todas las filas posteriores a t, se
    recalculan, y se exige que las filas hasta t no hayan cambiado.

    La perturbacion es multiplicativa y grande a proposito. Un cambio pequeno
    podria quedar por debajo de la tolerancia numerica y dejar pasar una fuga real.
    """
    if len(datos) < 20:
        raise ValueError("se necesitan al menos 20 filas para que la prueba sea significativa")

    original = constructor(datos)
    if not isinstance(original, pd.DataFrame):
        raise TypeError(
            f"el constructor debe devolver DataFrame, devolvio {type(original).__name__}"
        )

    generador = np.random.default_rng(semilla)
    n = len(datos)
    puntos = sorted(
        generador.choice(np.arange(n // 4, n - 2), size=min(cortes, n // 4), replace=False)
    )

    columnas_numericas = datos.select_dtypes(include=[np.number]).columns

    for t in puntos:
        alterado = datos.copy()
        futuro = alterado.index[t + 1 :]
        alterado.loc[futuro, columnas_numericas] = (
            alterado.loc[futuro, columnas_numericas] * 3.7 + 1000.0
        )

        recalculado = constructor(alterado)

        antes_original = original.iloc[: t + 1]
        antes_recalculado = recalculado.iloc[: t + 1]

        comunes = [c for c in antes_original.columns if c in antes_recalculado.columns]
        for columna in comunes:
            a = pd.to_numeric(antes_original[columna], errors="coerce").to_numpy(dtype=float)
            b = pd.to_numeric(antes_recalculado[columna], errors="coerce").to_numpy(dtype=float)
            distintos = ~(np.isclose(a, b, atol=tolerancia, equal_nan=True))
            if distintos.any():
                primera = int(np.argmax(distintos))
                raise FugaDetectada(
                    f"la columna {columna!r} cambia en la fila {primera} al modificar datos "
                    f"posteriores a la fila {t}: usa informacion del futuro. "
                    f"valor original={a[primera]!r}, tras perturbar el futuro={b[primera]!r}"
                )
