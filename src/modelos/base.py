"""Interfaz comun de los modelos y baselines obligatorios.

Todos los modelos exponen la misma interfaz (RF-M3) para que el arnes de
evaluacion y la aplicacion no sepan cual estan usando. Eso permite que M1 conecte
la aplicacion antes de que M3 termine el modelo real: contra el baseline, la app
funciona igual.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from contracts.labeling import Clase


class Modelo(ABC):
    """Contrato que cumple cualquier modelo del proyecto."""

    nombre: str = "modelo"

    @abstractmethod
    def entrenar(self, X: pd.DataFrame, y: pd.Series) -> Modelo:
        """Ajusta el modelo. Devuelve self para poder encadenar."""

    @abstractmethod
    def predecir(self, X: pd.DataFrame) -> np.ndarray:
        """Devuelve un array de codigos de Clase, uno por fila de X."""

    def __repr__(self) -> str:
        return f"<{type(self).__name__} nombre={self.nombre!r}>"


class BaselineTrivial(Modelo):
    """Siempre responde Continuidad.

    Es el piso obligatorio de comparacion (RF-V2). Con las clases desbalanceadas
    que produce el etiquetado, este modelo tiene exactitud alta y F1 macro bajo.
    Cualquier modelo que no lo supere en F1 macro no aporta nada, por mas que su
    exactitud impresione en una lamina.
    """

    nombre = "baseline_trivial"

    def entrenar(self, X: pd.DataFrame, y: pd.Series) -> BaselineTrivial:
        return self

    def predecir(self, X: pd.DataFrame) -> np.ndarray:
        return np.full(len(X), int(Clase.CONTINUIDAD), dtype=int)


class BaselineMayoritario(Modelo):
    """Responde siempre la clase mas frecuente del entrenamiento.

    Se distingue del trivial porque no asume cual es la mayoritaria: si con algun
    (w, h) la clase dominante dejara de ser Continuidad, este baseline lo refleja
    y el trivial no.
    """

    nombre = "baseline_mayoritario"

    def __init__(self) -> None:
        self._clase: int | None = None

    def entrenar(self, X: pd.DataFrame, y: pd.Series) -> BaselineMayoritario:
        conteo = pd.Series(y).dropna().astype(int).value_counts()
        if conteo.empty:
            raise ValueError("no hay etiquetas validas para entrenar")
        self._clase = int(conteo.idxmax())
        return self

    def predecir(self, X: pd.DataFrame) -> np.ndarray:
        if self._clase is None:
            raise RuntimeError("hay que llamar a entrenar() antes de predecir()")
        return np.full(len(X), self._clase, dtype=int)


class BaselineAleatorio(Modelo):
    """Responde al azar respetando las proporciones vistas en entrenamiento.

    Util para separar dos cosas que se confunden: un F1 alto porque el modelo
    aprendio, o un F1 alto porque la clase es facil de acertar por frecuencia.
    """

    nombre = "baseline_aleatorio"

    def __init__(self, semilla: int = 0) -> None:
        self.semilla = semilla
        self._clases: np.ndarray | None = None
        self._probabilidades: np.ndarray | None = None

    def entrenar(self, X: pd.DataFrame, y: pd.Series) -> BaselineAleatorio:
        proporciones = pd.Series(y).dropna().astype(int).value_counts(normalize=True)
        self._clases = proporciones.index.to_numpy()
        self._probabilidades = proporciones.to_numpy()
        return self

    def predecir(self, X: pd.DataFrame) -> np.ndarray:
        if self._clases is None:
            raise RuntimeError("hay que llamar a entrenar() antes de predecir()")
        generador = np.random.default_rng(self.semilla)
        return generador.choice(self._clases, size=len(X), p=self._probabilidades).astype(int)
