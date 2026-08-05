"""Series sinteticas con puntos de inflexion conocidos por construccion.

Es la unica prueba del proyecto donde la verdad no esta en discusion: nosotros
ponemos los giros, asi que sabemos exactamente donde estan. Sirve para detectar
errores de implementacion que en datos reales pasarian por "el modelo no acerto".

Lo que NO sirve: estas series no son criptomonedas. No tienen heterocedasticidad,
ni colas pesadas, ni saltos. Un modelo que funcione aqui todavia no ha demostrado
nada sobre LTC, y decir lo contrario seria presentar lo construido como medido.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from contracts.labeling import Clase


def serie_zigzag(
    n: int,
    w: int,
    semilla: int = 0,
    separacion_minima: int | None = None,
    amplitud: float = 12.0,
    nivel: float = 100.0,
    ruido: float = 0.0,
) -> tuple[pd.Series, np.ndarray]:
    """Serie lineal a tramos cuyos vertices son los giros verdaderos.

    Devuelve (serie, indices_de_giro). Los vertices se separan al menos w+1
    posiciones para que cada uno sea un extremo estricto dentro de su ventana:
    con menos separacion, dos vertices caerian en la ventana del otro y ninguno
    seria detectable, que es justamente la cota que documentamos.

    El ruido se suma despues de construir los tramos. Con ruido alto los vertices
    pueden dejar de ser el maximo de su ventana; por eso las pruebas automaticas
    usan ruido=0 y el ruido queda para explorar la robustez del modelo.
    """
    if separacion_minima is None:
        separacion_minima = w + 1
    if separacion_minima < w + 1:
        raise ValueError(
            f"separacion_minima={separacion_minima} es menor que w+1={w + 1}: los "
            "vertices no serian extremos estrictos y la verdad de referencia seria falsa"
        )

    generador = np.random.default_rng(semilla)

    vertices = [0]
    while True:
        salto = int(generador.integers(separacion_minima, separacion_minima * 3))
        siguiente = vertices[-1] + salto
        if siguiente >= n - 1:
            break
        vertices.append(siguiente)
    vertices.append(n - 1)
    vertices_arr = np.array(vertices)

    # Los vertices alternan arriba y abajo; sin alternancia no habria giros.
    signos = np.where(np.arange(len(vertices_arr)) % 2 == 0, -1.0, 1.0)
    alturas = nivel + signos * amplitud * generador.uniform(0.6, 1.4, size=len(vertices_arr))

    valores = np.interp(np.arange(n), vertices_arr, alturas)
    if ruido > 0:
        valores = valores + generador.normal(0.0, ruido, size=n)

    indice = pd.date_range("2020-01-01", periods=n, freq="D", tz="UTC", name="fecha")
    serie = pd.Series(valores, index=indice, name="cierre")

    # Los extremos de los bordes no son giros verificables: les falta ventana.
    giros = vertices_arr[(vertices_arr >= w) & (vertices_arr < n - w)]
    return serie, giros


def etiquetas_esperadas(n: int, giros: np.ndarray, valores: np.ndarray, w: int) -> pd.Series:
    """Verdad de referencia construida a partir de los vertices, no del etiquetador.

    Se construye de forma independiente a proposito: si la verdad saliera de
    etiquetar(), la prueba compararia la funcion consigo misma y pasaria siempre.
    """
    esperadas = np.full(n, float(Clase.CONTINUIDAD))
    for i in giros:
        vecinos_izq = valores[i - 1]
        vecinos_der = valores[i + 1]
        if valores[i] > vecinos_izq and valores[i] > vecinos_der:
            esperadas[i] = float(Clase.MAXIMO)
        elif valores[i] < vecinos_izq and valores[i] < vecinos_der:
            esperadas[i] = float(Clase.MINIMO)
    esperadas[:w] = np.nan
    esperadas[n - w :] = np.nan
    return pd.Series(pd.array(esperadas, dtype="Int64"), name="etiqueta")


def serie_con_regimen(
    n: int,
    semilla: int = 0,
    nivel: float = 100.0,
    volatilidad_baja: float = 0.008,
    volatilidad_alta: float = 0.035,
    duracion_regimen: int = 120,
) -> pd.Series:
    """Camino aleatorio con volatilidad que cambia por tramos.

    Se parece mas a una cripto que el zigzag porque tiene heterocedasticidad, pero
    aqui NO conocemos los giros verdaderos: se obtienen aplicando el etiquetador.
    Sirve para probar rendimiento bajo cambios de regimen, no para verificar que el
    etiquetador funcione.
    """
    generador = np.random.default_rng(semilla)
    volatilidades = np.where(
        (np.arange(n) // duracion_regimen) % 2 == 0, volatilidad_baja, volatilidad_alta
    )
    retornos = generador.normal(0.0, volatilidades)
    valores = nivel * np.exp(np.cumsum(retornos))
    indice = pd.date_range("2020-01-01", periods=n, freq="D", tz="UTC", name="fecha")
    return pd.Series(valores, index=indice, name="cierre")
