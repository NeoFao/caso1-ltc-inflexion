"""Particion temporal de los datos. Fija, nunca aleatoria.

Si cada persona parte los datos distinto, comparar el modelo fundacional con el
avanzado no significa nada, y el error no se nota hasta que los numeros no cuadran.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

FRACCION_ENTRENAMIENTO = 0.70
FRACCION_VALIDACION = 0.15
# El resto (0.15) es prueba.


@dataclass(frozen=True)
class Particion:
    """Mascaras booleanas alineadas al indice del panel."""

    entrenamiento: np.ndarray
    validacion: np.ndarray
    prueba: np.ndarray
    embargo: np.ndarray

    def resumen(self, indice: pd.DatetimeIndex) -> pd.DataFrame:
        filas = []
        for nombre, mascara in (
            ("entrenamiento", self.entrenamiento),
            ("validacion", self.validacion),
            ("prueba", self.prueba),
            ("embargo (descartado)", self.embargo),
        ):
            fechas = indice[mascara]
            filas.append(
                {
                    "conjunto": nombre,
                    "n": int(mascara.sum()),
                    "desde": fechas.min() if len(fechas) else pd.NaT,
                    "hasta": fechas.max() if len(fechas) else pd.NaT,
                }
            )
        return pd.DataFrame(filas)


def particionar(n: int, w: int, h: int) -> Particion:
    """Divide n instantes en tres bloques cronologicos con embargo entre ellos.

    El embargo descarta w+h velas en cada frontera. Sin el hay fuga: la etiqueta
    de las ultimas velas de entrenamiento se calcula mirando velas que pertenecen
    a validacion, asi que el modelo vería indirectamente datos de evaluacion. Es
    el error mas caro de este tipo de proyecto porque produce resultados
    excelentes y falsos, y no se nota mirando las metricas.

    El costo es perder 2*(w+h) observaciones. Con los valores provisionales del
    contrato eso es una fraccion despreciable del total.
    """
    if n <= 0:
        raise ValueError(f"n debe ser positivo, se recibio {n}")

    hueco = w + h
    corte_1 = int(n * FRACCION_ENTRENAMIENTO)
    corte_2 = int(n * (FRACCION_ENTRENAMIENTO + FRACCION_VALIDACION))

    if corte_1 - hueco <= 0 or corte_2 - hueco <= corte_1:
        raise ValueError(
            f"la serie de {n} observaciones es demasiado corta para un embargo de "
            f"{hueco} velas en cada frontera"
        )

    indices = np.arange(n)
    entrenamiento = indices < (corte_1 - hueco)
    validacion = (indices >= corte_1) & (indices < corte_2 - hueco)
    prueba = indices >= corte_2
    embargo = ~(entrenamiento | validacion | prueba)

    return Particion(
        entrenamiento=entrenamiento,
        validacion=validacion,
        prueba=prueba,
        embargo=embargo,
    )
