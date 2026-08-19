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
# CONGELADO el 18 de agosto de 2026. Estudio y justificacion en
# docs/04-decision-w-h-granularidad.md, numeros en docs/evidencias/estudio-w-h.json.
#
# Los tres valores salen de medicion, no de intuicion, y cada uno de un criterio
# distinto fijado antes de mirar el resultado:
#
#   GRANULARIDAD  Con velas diarias NINGUNA combinacion de w alcanza el piso de
#                 300 ejemplos de clase minoritaria; la mejor deja 149. Con 4h,
#                 w=7 deja 420. Las dos granularidades cubren el mismo periodo:
#                 bajar no anade historia, subdivide la que hay.
#   VENTANA_W     El w mas grande que cumple el piso, porque un w grande produce
#                 etiquetas mas significativas. w=10 quedo en 299, uno por debajo.
#   HORIZONTE_H   La informacion mutua entre lo observable en t y la etiqueta en
#                 t+h cae 4,2 veces de h=1 a h=3 y despues se aplana, en las
#                 cuatro configuraciones medidas. Corrige una propuesta previa de
#                 h=5 que se habia hecho por juicio y no por medicion.
#
# La anticipacion real del sistema es h+w, no h: 8 velas de 4 horas, 32 horas.
# Reportar solo h seria enganoso.
#
# Cambiar cualquiera de los tres obliga a regenerar toda la evidencia que dependa
# de etiquetas y a re-correr las comparaciones entre modelos, porque dejan de ser
# comparables con las anteriores.
# ---------------------------------------------------------------------------
PROVISIONAL = False

GRANULARIDAD = "4h"
VENTANA_W = 7
HORIZONTE_H = 1

# Piso de ejemplos por clase minoritaria en entrenamiento. Es una propuesta del
# PM para que la decision tenga criterio explicito, no un valor de la literatura.
MINIMO_EJEMPLOS_CLASE_MINORITARIA = 300

# Umbral de decision entre modelo fundacional y avanzado (seccion 3.3 del PRD).
# Fijado antes de medir a proposito: cambiarlo despues de ver resultados hay que
# declararlo explicitamente en el informe.
DELTA_F1_DECISIVO = 0.02
