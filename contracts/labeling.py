"""Definicion operativa del punto de inflexion.

Este archivo es la interfaz compartida real del proyecto. Features, modelos y
evaluacion dependen de el. Si alguien implementa su propia version, los
resultados dejan de ser comparables y nadie se entera hasta que ya no hay tiempo.

El contexto de por que w y h no vienen dados en el enunciado esta en
docs/00-definicion-punto-inflexion.md.
"""

from __future__ import annotations

from enum import IntEnum

import numpy as np
import pandas as pd


class Clase(IntEnum):
    """Los valores coinciden con la numeracion del enunciado, no con el orden 0..n
    que preferiria scikit-learn. Se prioriza que el informe y el codigo usen los
    mismos numeros."""

    MAXIMO = 1
    MINIMO = 2
    CONTINUIDAD = 3


NOMBRES_CLASE = {
    Clase.MAXIMO: "Maximo",
    Clase.MINIMO: "Minimo",
    Clase.CONTINUIDAD: "Continuidad",
}


def etiquetar(cierre: pd.Series, w: int) -> pd.Series:
    """Asigna Maximo, Minimo o Continuidad a cada instante de la serie de cierre.

    Una vela t es Maximo si su cierre es estrictamente mayor que el de las w velas
    anteriores y las w posteriores. Minimo, al reves.

    La exigencia de desigualdad estricta contra las 2w vecinas (y no solo ser igual
    al maximo de la ventana) garantiza una propiedad que usamos en todo el proyecto:
    dos extremos del mismo tipo nunca quedan a menos de w+1 velas de distancia. Con
    empates permitidos esa propiedad se rompe y el balance de clases deja de tener
    la cota superior de 1/(w+1) que documentamos.

    Los primeros y ultimos w instantes quedan como nulos, no como Continuidad:
    no tienen ventana completa, asi que su etiqueta es desconocida, no neutra.

    Devuelve una serie Int64 nullable con el mismo indice que la entrada.
    """
    if w < 1:
        raise ValueError(f"w debe ser >= 1, se recibio {w}")
    if not isinstance(cierre, pd.Series):
        raise TypeError(f"cierre debe ser pd.Series, es {type(cierre).__name__}")

    valores = cierre.to_numpy(dtype=float)
    n = len(valores)
    etiquetas = np.full(n, Clase.CONTINUIDAD, dtype=float)

    if n <= 2 * w:
        # Serie mas corta que una ventana completa: nada es clasificable.
        return pd.Series(pd.array([pd.NA] * n, dtype="Int64"), index=cierre.index)

    for i in range(w, n - w):
        ventana = valores[i - w : i + w + 1]
        centro = valores[i]
        if np.isnan(ventana).any():
            etiquetas[i] = np.nan
            continue
        estrictamente_menores = int((ventana < centro).sum())
        estrictamente_mayores = int((ventana > centro).sum())
        if estrictamente_menores == 2 * w:
            etiquetas[i] = Clase.MAXIMO
        elif estrictamente_mayores == 2 * w:
            etiquetas[i] = Clase.MINIMO

    etiquetas[:w] = np.nan
    etiquetas[n - w :] = np.nan

    return pd.Series(
        pd.array(etiquetas, dtype="Int64"),
        index=cierre.index,
        name="etiqueta",
    )


def objetivo(etiquetas: pd.Series, h: int) -> pd.Series:
    """Variable a predecir: la etiqueta que tendra el instante t+h.

    Se resuelve con un desplazamiento hacia atras para que la fila t contenga lo
    que hay que anunciar estando parado en t. Las ultimas h filas quedan nulas
    porque su futuro todavia no existe en la serie.
    """
    if h < 0:
        raise ValueError(f"h debe ser >= 0, se recibio {h}")
    return etiquetas.shift(-h).rename("objetivo")


def latencia_real(w: int, h: int) -> int:
    """Cuantas velas hay que esperar para poder verificar una prediccion hecha en t.

    Para saber si t+h fue un extremo hacen falta las w velas posteriores a t+h.
    Este numero es lo que hay que reportar como anticipacion efectiva del sistema;
    reportar solo h seria enganoso. Ver seccion 5 de
    docs/00-definicion-punto-inflexion.md.
    """
    return h + w


def resumen_clases(etiquetas: pd.Series) -> pd.DataFrame:
    """Conteo y porcentaje por clase, ignorando los nulos de los bordes.

    Existe porque el balance de clases es la primera pregunta que hay que
    responder con datos y no con la cota teorica.
    """
    validas = etiquetas.dropna().astype(int)
    total = len(validas)
    filas = []
    for clase in Clase:
        n = int((validas == clase).sum())
        filas.append(
            {
                "clase": NOMBRES_CLASE[clase],
                "codigo": int(clase),
                "n": n,
                "porcentaje": round(100 * n / total, 3) if total else 0.0,
            }
        )
    return pd.DataFrame(filas)


def cota_superior_extremos(w: int) -> float:
    """Fraccion maxima teorica que puede alcanzar cada clase extrema.

    Dos maximos no pueden estar a menos de w+1 velas: si lo estuvieran, cada uno
    caeria dentro de la ventana del otro y cada uno tendria que ser estrictamente
    mayor que el otro. De ahi que como mucho 1 de cada w+1 velas sea Maximo.

    Es aritmetica, no una medicion. El valor real siempre sera menor.
    """
    return 1.0 / (w + 1)
