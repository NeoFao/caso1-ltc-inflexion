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


def panel_correlacionado(
    n: int,
    correlacion: float = 0.7,
    volatilidad: float | dict[str, float] = 0.02,
    semilla: int = 0,
    regimenes: bool = False,
    duracion_regimen: int = 120,
    multiplicador_regimen: float = 4.0,
    nivel: float = 100.0,
) -> pd.DataFrame:
    """Panel de las seis criptomonedas con correlacion y volatilidad que fijamos nosotros.

    Es el complemento del zigzag: alli conocemos los giros, aqui conocemos la
    estructura de dependencia. Sirve para el marco teorico, porque permite ilustrar
    correlacion cruzada, volatilidad y heterocedasticidad sobre series donde la
    respuesta correcta no esta en discusion, y recien despues mostrar la real.

    Los retornos se generan con la descomposicion de Cholesky de la matriz de
    correlacion objetivo: si R = L L', entonces Z L' con Z normal independiente
    tiene correlacion R. Es exacto en poblacion; en una muestra finita la
    correlacion medida difiere un poco, y esa diferencia es justamente lo que las
    pruebas acotan.

    `regimenes=True` multiplica la volatilidad por tramos alternos, que es como se
    construye heterocedasticidad a proposito.

    Devuelve un panel que cumple el contrato de contracts/schema.py, asi que se
    puede pasar a cualquier funcion del proyecto igual que el panel real.

    ESTO NO ES LITECOIN. Es un banco de pruebas construido por nosotros; cualquier
    numero que salga de aqui se presenta como tal.
    """
    from contracts.config import ACTIVOS
    from contracts.schema import CAMPOS_OHLCV, INDICE

    if not -1.0 < correlacion < 1.0:
        raise ValueError(f"correlacion debe estar en (-1, 1), se recibio {correlacion}")

    k = len(ACTIVOS)
    generador = np.random.default_rng(semilla)

    objetivo_corr = np.full((k, k), float(correlacion))
    np.fill_diagonal(objetivo_corr, 1.0)
    try:
        factor = np.linalg.cholesky(objetivo_corr)
    except np.linalg.LinAlgError as error:  # correlacion negativa muy fuerte entre 6 series
        raise ValueError(
            f"correlacion={correlacion} no produce una matriz valida para {k} activos. "
            f"Con equicorrelacion el minimo posible es -1/({k}-1) = {-1 / (k - 1):.3f}"
        ) from error

    if isinstance(volatilidad, dict):
        faltantes = [a for a in ACTIVOS if a not in volatilidad]
        if faltantes:
            raise ValueError(f"falta volatilidad para: {faltantes}")
        sigmas = np.array([volatilidad[a] for a in ACTIVOS])
    else:
        sigmas = np.full(k, float(volatilidad))

    independientes = generador.standard_normal((n, k))
    retornos = independientes @ factor.T

    if regimenes:
        agitado = (np.arange(n) // duracion_regimen) % 2 == 1
        escala = np.where(agitado, multiplicador_regimen, 1.0)[:, None]
        retornos = retornos * escala

    retornos = retornos * sigmas

    indice = pd.date_range("2020-08-11", periods=n, freq="D", tz="UTC", name=INDICE)
    columnas: dict[str, np.ndarray] = {}
    for j, activo in enumerate(ACTIVOS):
        cierre = nivel * (j + 1) * np.exp(np.cumsum(retornos[:, j]))
        # Los otros campos OHLCV se derivan del cierre porque el proyecto solo usa
        # cierre; existen para que el panel cumpla el contrato sin fingir realismo.
        ruido = np.abs(generador.normal(0.0, sigmas[j] / 2, size=n))
        columnas[f"{activo}_cierre"] = cierre
        columnas[f"{activo}_apertura"] = cierre * (1 - ruido)
        columnas[f"{activo}_maximo"] = cierre * (1 + ruido)
        columnas[f"{activo}_minimo"] = cierre * (1 - ruido)
        columnas[f"{activo}_volumen"] = np.abs(generador.normal(1e5, 2e4, size=n))

    orden = [f"{a}_{c}" for a in ACTIVOS for c in CAMPOS_OHLCV]
    return pd.DataFrame(columnas, index=indice)[orden]


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
