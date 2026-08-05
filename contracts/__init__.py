"""Contratos congelados del proyecto.

Un contrato es una definicion que varios modulos consumen y que nadie cambia por
su cuenta. Para cambiar uno: se propone por escrito con la razon y que se rompe,
lo aprueban el PM y quien lo consume, se cambia en un solo lugar y se vuelve a
correr todo.
"""

from contracts.config import (
    ACTIVO_OBJETIVO,
    ACTIVOS,
    ACTIVOS_APOYO,
    GRANULARIDAD,
    HORIZONTE_H,
    SIMBOLOS,
    VENTANA_W,
)
from contracts.labeling import Clase, etiquetar, latencia_real, objetivo, resumen_clases
from contracts.metrics import evaluar, matriz_confusion
from contracts.schema import COLUMNAS_PANEL, cierre, columna, validar_panel
from contracts.splits import particionar

__all__ = [
    "ACTIVO_OBJETIVO",
    "ACTIVOS",
    "ACTIVOS_APOYO",
    "COLUMNAS_PANEL",
    "GRANULARIDAD",
    "HORIZONTE_H",
    "SIMBOLOS",
    "VENTANA_W",
    "Clase",
    "cierre",
    "columna",
    "etiquetar",
    "evaluar",
    "latencia_real",
    "matriz_confusion",
    "objetivo",
    "particionar",
    "resumen_clases",
    "validar_panel",
]
