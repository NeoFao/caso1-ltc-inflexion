"""Diagnostico estadistico de las series. Modulo de Jose Pablo (M1).

Aqui hay UN ejemplo funcionando de cada tipo de prueba. El resto las construye M1
siguiendo el mismo patron; la guia paso a paso esta en guias/monestel.md.

Estas funciones producen los numeros del marco teorico de la Semana 1: no se
escribe "las series no son estacionarias" sin la tabla que lo demuestre.
"""

from __future__ import annotations

import pandas as pd
from statsmodels.tsa.stattools import acf, adfuller

from contracts.config import ACTIVOS
from contracts.schema import columna


def prueba_estacionariedad(serie: pd.Series, nombre: str = "") -> dict:
    """Dickey-Fuller aumentado.

    Hipotesis nula: la serie tiene raiz unitaria, es decir NO es estacionaria.
    Un p-valor alto significa que no podemos rechazar esa hipotesis, o sea que la
    evidencia es compatible con una serie no estacionaria.

    Cuidado al redactar el informe: no rechazar la nula no es lo mismo que
    demostrar que la serie no es estacionaria. Es la diferencia entre "no hay
    evidencia en contra" y "hay evidencia a favor".
    """
    limpia = serie.dropna()
    if len(limpia) < 20:
        raise ValueError(f"serie demasiado corta para ADF: {len(limpia)} observaciones")

    estadistico, p_valor, rezagos, n, criticos, _ = adfuller(limpia, autolag="AIC")
    return {
        "serie": nombre or serie.name,
        "n": int(n),
        "estadistico_adf": float(estadistico),
        "p_valor": float(p_valor),
        "rezagos_usados": int(rezagos),
        "critico_5pct": float(criticos["5%"]),
        "rechaza_raiz_unitaria_5pct": bool(p_valor < 0.05),
    }


def tabla_estacionariedad(panel: pd.DataFrame, en_retornos: bool = False) -> pd.DataFrame:
    """ADF sobre los seis cierres, en nivel o en retornos.

    Correrla en las dos formas es lo que sostiene el argumento del marco teorico:
    los precios en nivel no son estacionarios y sus retornos si, que es la razon
    por la que las caracteristicas se construyen sobre retornos.
    """
    filas = []
    for activo in ACTIVOS:
        serie = panel[columna(activo, "cierre")]
        if en_retornos:
            serie = serie.pct_change()
        filas.append(prueba_estacionariedad(serie, nombre=activo))
    return pd.DataFrame(filas)


def autocorrelacion(serie: pd.Series, rezagos: int = 30) -> pd.DataFrame:
    """Funcion de autocorrelacion con su intervalo de confianza al 95 %."""
    limpia = serie.dropna()
    valores, intervalos = acf(limpia, nlags=rezagos, alpha=0.05, fft=True)
    return pd.DataFrame(
        {
            "rezago": range(len(valores)),
            "acf": valores,
            "inferior": intervalos[:, 0],
            "superior": intervalos[:, 1],
        }
    )


def matriz_correlacion(panel: pd.DataFrame, en_retornos: bool = True) -> pd.DataFrame:
    """Correlacion entre los seis activos.

    Se calcula sobre retornos y no sobre precios en nivel: dos series con
    tendencia comparten tendencia, y su correlacion en nivel es alta aunque no
    tengan ninguna relacion. Es la trampa clasica de la correlacion espuria.
    """
    cierres = pd.DataFrame(
        {activo: panel[columna(activo, "cierre")] for activo in ACTIVOS}
    )
    if en_retornos:
        cierres = cierres.pct_change()
    return cierres.dropna().corr()
