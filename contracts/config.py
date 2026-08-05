"""Parametros que definen el problema.

Todo lo que este aqui es consumido por los cuatro modulos. Cambiarlo sin acuerdo
rompe la comparabilidad de resultados entre personas.
"""

from __future__ import annotations

ACTIVO_OBJETIVO = "LTC"
ACTIVOS_APOYO = ("BTC", "ETH", "SOL", "XRP", "ADA")
ACTIVOS = (ACTIVO_OBJETIVO, *ACTIVOS_APOYO)

# Mapa a los simbolos del exchange. Vive aqui y no en el modulo de descarga
# porque cambiar de fuente no debe cambiar el resto del proyecto.
SIMBOLOS = {
    "LTC": "LTCUSDT",
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "SOL": "SOLUSDT",
    "XRP": "XRPUSDT",
    "ADA": "ADAUSDT",
}

# ---------------------------------------------------------------------------
# PROVISIONAL — decisiones D1, D2 y D3 del PRD.
#
# Estos tres numeros los fija el equipo con la medicion de scripts/spike_datos.py
# encima de la mesa, no por intuicion. Criterio acordado de antemano: el w mas
# grande que deje al menos 300 ejemplos de la clase minoritaria en entrenamiento.
#
# Mientras esta seccion diga PROVISIONAL, ningun resultado que dependa de ella
# entra al informe como definitivo.
# ---------------------------------------------------------------------------
PROVISIONAL = True

GRANULARIDAD = "1d"
VENTANA_W = 5
HORIZONTE_H = 3

# Piso de ejemplos por clase minoritaria en entrenamiento. Es una propuesta del
# PM para que la decision tenga criterio explicito, no un valor de la literatura.
MINIMO_EJEMPLOS_CLASE_MINORITARIA = 300

# Umbral de decision entre modelo fundacional y avanzado (seccion 3.3 del PRD).
# Fijado antes de medir a proposito: cambiarlo despues de ver resultados hay que
# declararlo explicitamente en el informe.
DELTA_F1_DECISIVO = 0.02
