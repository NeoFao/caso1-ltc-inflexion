"""Ingenieria de caracteristicas. Modulo de Alejandro (M2).

Aqui hay UN ejemplo de cada cosa, funcionando y verificado contra fuga. El resto
de las familias las construye M2 siguiendo el mismo patron; la guia paso a paso
esta en guias/alejandro.md.

Regla que gobierna todo este archivo: una caracteristica en el instante t solo
puede usar informacion hasta t. Cualquier funcion nueva tiene que pasar
verificar_sin_fuga() antes de entrar al pipeline (RF-E2).
"""

from __future__ import annotations

import pandas as pd

from contracts.config import ACTIVO_OBJETIVO, ACTIVOS
from contracts.schema import columna


def rezagos(
    panel: pd.DataFrame, activo: str, campo: str = "cierre", ordenes=(1, 2, 3, 5)
) -> pd.DataFrame:
    """Precios rezagados: el valor de hace k velas.

    Es la familia mas simple y la que el enunciado nombra explicitamente. shift(k)
    con k positivo mira hacia atras, que es la direccion segura.
    """
    serie = panel[columna(activo, campo)]
    return pd.DataFrame(
        {f"{activo}_{campo}_rezago_{k}": serie.shift(k) for k in ordenes},
        index=panel.index,
    )


def retornos(panel: pd.DataFrame, activo: str, periodos=(1, 3, 7)) -> pd.DataFrame:
    """Retorno porcentual sobre k velas.

    Se usan retornos y no precios en nivel porque el precio no es estacionario:
    un modelo entrenado sobre niveles aprende el rango de precios del periodo de
    entrenamiento y falla cuando el precio sale de ese rango.
    """
    serie = panel[columna(activo, "cierre")]
    return pd.DataFrame(
        {f"{activo}_retorno_{k}": serie.pct_change(k) for k in periodos},
        index=panel.index,
    )


def volatilidad(panel: pd.DataFrame, activo: str, ventanas=(7, 14, 30)) -> pd.DataFrame:
    """Desviacion estandar de los retornos en una ventana movil hacia atras.

    rolling() de pandas mira hacia atras por defecto, incluyendo la fila actual.
    Eso es correcto aqui: el retorno de hoy ya ocurrio cuando estamos parados hoy.
    """
    retorno = panel[columna(activo, "cierre")].pct_change()
    return pd.DataFrame(
        {f"{activo}_volatilidad_{v}": retorno.rolling(v).std() for v in ventanas},
        index=panel.index,
    )


def correlacion_cruzada(
    panel: pd.DataFrame,
    objetivo: str = ACTIVO_OBJETIVO,
    ventana: int = 30,
) -> pd.DataFrame:
    """Correlacion movil entre los retornos del objetivo y los de cada activo de apoyo.

    Es la familia que justifica que el problema sea multivariante: si LTC se moviera
    solo, estas columnas serian ruido y la medicion de importancia lo mostraria.
    """
    retorno_objetivo = panel[columna(objetivo, "cierre")].pct_change()
    columnas = {}
    for activo in ACTIVOS:
        if activo == objetivo:
            continue
        retorno_apoyo = panel[columna(activo, "cierre")].pct_change()
        columnas[f"corr_{objetivo}_{activo}_{ventana}"] = retorno_objetivo.rolling(ventana).corr(
            retorno_apoyo
        )
    return pd.DataFrame(columnas, index=panel.index)


def construir(panel: pd.DataFrame) -> pd.DataFrame:
    """Punto de entrada unico del modulo de caracteristicas.

    M3 y la aplicacion llaman a esta funcion y no a las de arriba, para que M2
    pueda reorganizar el interior sin romper a nadie.

    Los rezagos van para los SEIS activos, no solo para LTC. El enunciado define
    las variables de apoyo como "los precios historicos (rezagados) de las cinco
    criptomonedas": es la entrada especificada de forma mas literal en todo el
    documento, y sin ella el modelo no recibe lo que el enunciado dice que debe
    recibir.

    PENDIENTE M2: faltan las familias de indicadores tecnicos y de ventana
    deslizante que exige RF-F1, y el escalado de RF-F3. Ver guias/alejandro.md.
    """
    piezas = [
        retornos(panel, ACTIVO_OBJETIVO),
        volatilidad(panel, ACTIVO_OBJETIVO),
        correlacion_cruzada(panel),
    ]
    for activo in ACTIVOS:
        piezas.append(rezagos(panel, activo))
        if activo != ACTIVO_OBJETIVO:
            piezas.append(retornos(panel, activo, periodos=(1, 3)))

    return pd.concat(piezas, axis=1)
