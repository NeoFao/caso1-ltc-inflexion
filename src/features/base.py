"""Ingenieria de caracteristicas. Modulo de Alejandro (M2).

Aqui hay UN ejemplo de cada cosa, funcionando y verificado contra fuga. El resto
de las familias las construye M2 siguiendo el mismo patron; la guia paso a paso
esta en guias/alejandro.md.

Regla que gobierna todo este archivo: una caracteristica en el instante t solo
puede usar informacion hasta t. Cualquier funcion nueva tiene que pasar
verificar_sin_fuga() antes de entrar al pipeline (RF-E2).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from contracts.config import ACTIVO_OBJETIVO, ACTIVOS
from contracts.schema import columna

# Ordenes elegidos con medicion, no por convencion (issue S1-M2-04).
#
# El andamiaje traia (1, 2, 3, 5), que nadie habia medido. Sobre el panel de 4h los
# rezagos 2, 3 y 4 no son distinguibles de cero ni en la autocorrelacion de los
# retornos de LTC ni en la correlacion cruzada con los activos de apoyo. Los que si
# cruzan la banda al 95 % en las dos mediciones a la vez son 5, 6 y 7.
#
# El rezago 1 entra siempre, sea significativo o no: es el precio de la vela
# anterior, la entrada mas literal del enunciado.
#
# El corte en cuatro ordenes no es estetico. Cada orden agrega seis columnas —van
# los seis activos— y la clase minoritaria tiene 420 ejemplos en entrenamiento.
#
# Evidencia: docs/evidencias/m2-rezagos.json, regenerable con
#   uv run python -m src.features.seleccion_rezagos
REZAGOS_MEDIDOS: tuple[int, ...] = (1, 5, 6, 7)


def rezagos(
    panel: pd.DataFrame, activo: str, campo: str = "cierre", ordenes=REZAGOS_MEDIDOS
) -> pd.DataFrame:
    """Precios rezagados: el valor de hace k velas.

    Es la familia mas simple y la que el enunciado nombra explicitamente. shift(k)
    con k positivo mira hacia atras, que es la direccion segura.

    Devuelve el precio en NIVEL y no el retorno, porque el enunciado especifica "los
    precios historicos (rezagados)". El nivel no es estacionario y eso es un
    problema conocido: se resuelve en RF-F3, el escalado de la Semana 2. Queda
    anotado aqui para que no se parchee por la libre en dos lugares distintos.
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


# ---------------------------------------------------------------------------
# Indicadores tecnicos (RF-F1, issue S1-M2-02).
#
# Todos van sobre LTC solamente, no sobre los seis activos. Multiplicar por seis
# esta familia daria mas de sesenta columnas nuevas para 420 ejemplos de la clase
# minoritaria, y eso no es ingenieria de caracteristicas: es sobreajuste con pasos
# extra. Si la medicion de importancia de la Semana 3 muestra que alguno aporta, se
# extiende a los demas activos con ese numero en la mano.
#
# Ninguno depende de ta-lib ni de pandas-ta. Un RSI son seis lineas de pandas, y
# una dependencia nueva es una decision, no un detalle.
#
# Todos se emiten en forma RELATIVA —cocientes, porcentajes o indices acotados— y
# no en unidades de precio. Una media movil cruda es un nivel de precio: un modelo
# entrenado con LTC entre 40 y 390 dolares no sabe que hacer cuando el precio sale
# de ese rango. Es el mismo argumento que ya justifica usar retornos y no niveles.
# ---------------------------------------------------------------------------


def medias_moviles(
    panel: pd.DataFrame,
    activo: str = ACTIVO_OBJETIVO,
    ventanas_simple=(7, 25),
    ventanas_exponencial=(12, 26),
) -> pd.DataFrame:
    """Distancia relativa del precio a su media movil simple y exponencial.

    Se emite `precio / media - 1` y no la media: la distancia es comparable entre
    periodos y la media no. Ademas es la lectura que interesa para este problema
    —cuanto se aleja el precio de su promedio reciente— y no el promedio en si.

    `rolling()` y `ewm()` de pandas miran hacia atras e incluyen la fila actual, que
    es correcto: el cierre de hoy ya ocurrio cuando estamos parados hoy.
    """
    serie = panel[columna(activo, "cierre")]
    columnas = {}
    for v in ventanas_simple:
        columnas[f"{activo}_dist_sma_{v}"] = serie / serie.rolling(v).mean() - 1
    for v in ventanas_exponencial:
        columnas[f"{activo}_dist_ema_{v}"] = serie / serie.ewm(span=v, adjust=False).mean() - 1
    return pd.DataFrame(columnas, index=panel.index)


def rsi(panel: pd.DataFrame, activo: str = ACTIVO_OBJETIVO, ventana: int = 14) -> pd.DataFrame:
    """Indice de fuerza relativa de Wilder, acotado entre 0 y 100.

    Compara la magnitud media de las subidas contra la de las bajadas en la ventana.
    Es el indicador con mas historia en este dominio y el enunciado pide la familia
    explicitamente (RF-F1).

    Se usa el suavizado exponencial de Wilder (`alpha = 1/ventana`) y no una media
    simple, que es la definicion original. Con `adjust=False` el valor en t depende
    solo del valor previo y del dato de t, que es justo la propiedad que necesitamos.

    Para este problema tiene una lectura directa: un RSI alto dice que el precio
    lleva varias velas subiendo mas de lo que baja, que es la situacion en la que un
    maximo local se vuelve posible.
    """
    cambio = panel[columna(activo, "cierre")].diff()
    subidas = cambio.clip(lower=0)
    bajadas = -cambio.clip(upper=0)
    media_subidas = subidas.ewm(alpha=1 / ventana, adjust=False).mean()
    media_bajadas = bajadas.ewm(alpha=1 / ventana, adjust=False).mean()

    fuerza = media_subidas / media_bajadas.replace(0.0, np.nan)
    valores = 100 - 100 / (1 + fuerza)
    # Sin ninguna bajada en la ventana el cociente diverge y el RSI satura en 100.
    valores = valores.where(media_bajadas != 0, 100.0)
    # Sin subidas NI bajadas —serie perfectamente plana— el RSI no esta definido.
    # Devolverlo como 50 seria inventar un dato neutro que nadie midio.
    plana = (media_subidas == 0) & (media_bajadas == 0)
    valores = valores.mask(plana | cambio.isna())
    return pd.DataFrame({f"{activo}_rsi_{ventana}": valores.astype(float)}, index=panel.index)


def macd(
    panel: pd.DataFrame,
    activo: str = ACTIVO_OBJETIVO,
    rapida: int = 12,
    lenta: int = 26,
    senal: int = 9,
) -> pd.DataFrame:
    """Convergencia y divergencia de medias moviles, normalizada por el precio.

    La linea MACD cruda esta en unidades de precio, asi que un valor de 3 significa
    cosas distintas con LTC a 50 que a 350. Se divide entre el cierre para que sea
    comparable entre periodos.

    El histograma —MACD menos su senal— es el que interesa aqui: cambia de signo
    cuando el impulso se da vuelta, que es exactamente el fenomeno que el proyecto
    intenta pronosticar.
    """
    serie = panel[columna(activo, "cierre")]
    linea = serie.ewm(span=rapida, adjust=False).mean() - serie.ewm(span=lenta, adjust=False).mean()
    linea_senal = linea.ewm(span=senal, adjust=False).mean()
    return pd.DataFrame(
        {
            f"{activo}_macd": linea / serie,
            f"{activo}_macd_senal": linea_senal / serie,
            f"{activo}_macd_histograma": (linea - linea_senal) / serie,
        },
        index=panel.index,
    )


def bollinger(
    panel: pd.DataFrame,
    activo: str = ACTIVO_OBJETIVO,
    ventana: int = 20,
    desviaciones: float = 2.0,
) -> pd.DataFrame:
    """Bandas de Bollinger, emitidas como posicion y ancho en vez de como niveles.

    - `%B` es donde cae el precio entre la banda inferior (0) y la superior (1).
      Puede salirse de [0, 1] y esta bien que lo haga: eso es justamente el precio
      rompiendo la banda.
    - El ancho relativo de las bandas es una medida de volatilidad normalizada por
      el precio, util para distinguir tramos comprimidos de tramos agitados.

    Las dos son escalables entre periodos; los niveles de las bandas no lo serian.
    """
    serie = panel[columna(activo, "cierre")]
    media = serie.rolling(ventana).mean()
    desviacion = serie.rolling(ventana).std()
    superior = media + desviaciones * desviacion
    inferior = media - desviaciones * desviacion
    ancho = (superior - inferior).replace(0.0, np.nan)
    return pd.DataFrame(
        {
            f"{activo}_bollinger_pctb_{ventana}": (serie - inferior) / ancho,
            f"{activo}_bollinger_ancho_{ventana}": (superior - inferior) / media,
        },
        index=panel.index,
    )


# ---------------------------------------------------------------------------
# Ventana deslizante (RF-F1, issue S1-M2-03).
# ---------------------------------------------------------------------------


def ventana_deslizante(
    panel: pd.DataFrame, activo: str = ACTIVO_OBJETIVO, ventanas=(7, 20)
) -> pd.DataFrame:
    """Estadisticos sobre ventanas moviles del cierre y de los retornos.

    La columna que mas importa de todo este archivo es `posicion_rango`: donde cae
    el cierre actual entre el minimo y el maximo de sus ultimas v velas, escalado a
    [0, 1]. Vale la pena entender por que.

    La etiqueta del proyecto dice que t es Maximo si su cierre supera al de las w
    velas anteriores y las w posteriores. La mitad hacia atras de esa condicion
    —superar a las w anteriores— es computable en t sin mirar al futuro, y equivale
    exactamente a `posicion_rango == 1` con v = w+1. O sea que esta caracteristica
    es la parte de la definicion de la etiqueta que SI podemos observar. No es una
    variable mas: es la mitad conocida de la respuesta.

    Que este permitido usarla no es obvio y conviene dejarlo escrito: el maximo de
    la ventana hacia atras usa solo informacion hasta t, asi que no hay fuga.
    Es la mitad futura de la condicion la que no se puede tocar, y esa no aparece
    aqui. `verificar_sin_fuga()` lo comprueba de forma automatica.

    El rango relativo se emite dividido entre el cierre por la misma razon que todo
    lo demas en este archivo: un rango de 12 dolares no significa lo mismo con LTC a
    50 que a 350. La asimetria y la curtosis de los retornos ya son adimensionales.
    """
    serie = panel[columna(activo, "cierre")]
    retorno = serie.pct_change()
    columnas = {}
    for v in ventanas:
        minimo = serie.rolling(v).min()
        maximo = serie.rolling(v).max()
        rango = maximo - minimo
        columnas[f"{activo}_rango_rel_{v}"] = rango / serie
        # Con rango cero —v velas al mismo precio— la posicion es indefinida, no 0.
        columnas[f"{activo}_posicion_rango_{v}"] = (serie - minimo) / rango.replace(0.0, np.nan)
        columnas[f"{activo}_asimetria_retornos_{v}"] = retorno.rolling(v).skew()
        columnas[f"{activo}_curtosis_retornos_{v}"] = retorno.rolling(v).kurt()
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

    Las cuatro familias que exige RF-F1 estan cubiertas: rezagos, volatilidad,
    indicadores tecnicos y ventana deslizante. RF-F2 la cubre correlacion_cruzada.

    Los indicadores y la ventana deslizante van SOLO sobre LTC. Extenderlos a los
    seis activos daria mas de cien columnas para 420 ejemplos de la clase
    minoritaria, y con esa proporcion el sobreajuste esta garantizado. La decision
    de a cuales conviene extenderlos se toma en la Semana 3, con la medicion de
    importancia (RF-F4) encima de la mesa y no antes.

    PENDIENTE M2: falta el escalado de RF-F3 (Semana 2). Hasta entonces, los
    rezagos siguen saliendo en nivel de precio y ninguna columna esta normalizada
    entre si.
    """
    piezas = [
        retornos(panel, ACTIVO_OBJETIVO),
        volatilidad(panel, ACTIVO_OBJETIVO),
        correlacion_cruzada(panel),
        medias_moviles(panel),
        rsi(panel),
        macd(panel),
        bollinger(panel),
        ventana_deslizante(panel),
    ]
    for activo in ACTIVOS:
        piezas.append(rezagos(panel, activo))
        if activo != ACTIVO_OBJETIVO:
            piezas.append(retornos(panel, activo, periodos=(1, 3)))

    return pd.concat(piezas, axis=1)
