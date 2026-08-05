"""Union de las seis series en el panel canonico (RF-D3, RF-D4).

El resultado de este modulo es el unico artefacto de datos que los cuatro modulos
consumen. Si dos personas trabajan sobre paneles distintos, sus resultados no son
comparables y el error es invisible.
"""

from __future__ import annotations

import pandas as pd

from contracts.config import ACTIVOS
from contracts.schema import CAMPOS_OHLCV, INDICE, validar_panel

# Maximo de velas consecutivas que se rellenan hacia adelante. Un hueco corto es
# una caida puntual del exchange; uno largo es que el activo no cotizaba, y
# rellenarlo inventaria precios que nunca existieron.
MAXIMO_RELLENO = 3


def consolidar(series: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Combina las seis series en formato ancho, recortado a la ventana comun.

    El recorte a la interseccion de fechas no es una opcion de diseno: si SOL
    empieza en 2020, cualquier fila anterior tendria las columnas de SOL vacias, y
    un modelo multivariante no puede aprender de filas incompletas.
    """
    faltantes = [a for a in ACTIVOS if a not in series]
    if faltantes:
        raise ValueError(f"faltan series para: {faltantes}")

    piezas = []
    for activo in ACTIVOS:
        marco = series[activo][list(CAMPOS_OHLCV)].copy()
        marco.columns = [f"{activo}_{campo}" for campo in CAMPOS_OHLCV]
        piezas.append(marco)

    panel = pd.concat(piezas, axis=1, join="inner").sort_index()
    panel.index.name = INDICE

    panel = rellenar_huecos(panel)
    validar_panel(panel)
    return panel


def rellenar_huecos(panel: pd.DataFrame, maximo: int = MAXIMO_RELLENO) -> pd.DataFrame:
    """Rellena hacia adelante hasta `maximo` velas y descarta el resto de filas.

    Se rellena solo hacia adelante, nunca hacia atras: un relleno hacia atras
    copiaria un precio futuro sobre un instante pasado, que es exactamente la
    fuga de informacion que el proyecto tiene que evitar.
    """
    relleno = panel.ffill(limit=maximo)
    return relleno.dropna()


def informe_huecos(series: dict[str, pd.DataFrame], intervalo: str) -> pd.DataFrame:
    """Cuantas velas faltan en cada activo respecto de una rejilla regular.

    Existe para poder afirmar en el informe cuantos huecos habia, en vez de decir
    "se limpiaron los datos" sin numero detras.
    """
    filas = []
    for activo, marco in series.items():
        esperado = pd.date_range(marco.index.min(), marco.index.max(), freq=intervalo, tz="UTC")
        faltan = len(esperado) - len(marco.index.intersection(esperado))
        filas.append(
            {
                "activo": activo,
                "n_observado": int(len(marco)),
                "n_esperado": int(len(esperado)),
                "huecos": int(faltan),
                "desde": marco.index.min(),
                "hasta": marco.index.max(),
            }
        )
    return pd.DataFrame(filas)
