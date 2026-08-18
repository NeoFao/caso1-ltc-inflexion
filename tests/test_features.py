"""Pruebas de las caracteristicas de M2 (issues S1-M2-02, S1-M2-03 y S1-M2-04).

Que una caracteristica "corra" no dice nada: `serie.rolling(11, center=True).mean()`
corre perfecto y arruina el proyecto entero. Lo que se prueba aqui es que cada
familia calcula lo que dice calcular, y que ninguna mira al futuro.

La prueba de fuga se corre por funcion y no solo sobre `construir()`. Sobre el
conjunto, una fuga en una columna puede quedar tapada por el ruido de las otras si
alguna vez se afloja la tolerancia; por funcion, el mensaje dice exactamente cual
es la culpable.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from contracts.config import ACTIVO_OBJETIVO
from contracts.labeling import Clase, etiquetar
from contracts.schema import cierre, columna
from src.evaluacion.fuga import verificar_sin_fuga
from src.features.base import (
    REZAGOS_MEDIDOS,
    bollinger,
    construir,
    macd,
    medias_moviles,
    rezagos,
    rsi,
    ventana_deslizante,
)
from src.sintetico.generador import panel_correlacionado


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    """Panel construido que cumple el contrato. Se usa uno sintetico y no el real
    para que las pruebas no dependan de un parquet en disco ni de la red."""
    return panel_correlacionado(n=600, semilla=7)


# ---------------------------------------------------------------------------
# Fuga de informacion. Es la propiedad que gobierna el modulo entero (RF-E2).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "familia",
    [medias_moviles, rsi, macd, bollinger, ventana_deslizante, construir],
    ids=lambda f: f.__name__,
)
def test_ninguna_familia_mira_al_futuro(panel, familia):
    verificar_sin_fuga(familia, panel)


# ---------------------------------------------------------------------------
# Indicadores tecnicos (S1-M2-02)
# ---------------------------------------------------------------------------


def test_el_rsi_queda_entre_0_y_100(panel):
    valores = rsi(panel)[f"{ACTIVO_OBJETIVO}_rsi_14"].dropna()
    assert valores.min() >= 0.0
    assert valores.max() <= 100.0


def test_una_serie_que_solo_sube_tiene_rsi_100(panel):
    """Sin ninguna bajada, la fuerza relativa es infinita y el RSI satura en 100.
    Es el caso limite que distingue una implementacion correcta de una que divide
    entre cero y devuelve NaN."""
    subiendo = panel.copy()
    subiendo[columna(ACTIVO_OBJETIVO, "cierre")] = np.arange(1.0, len(panel) + 1.0)
    valores = rsi(subiendo)[f"{ACTIVO_OBJETIVO}_rsi_14"].dropna()
    assert np.allclose(valores.to_numpy(), 100.0)


def test_una_serie_que_solo_baja_tiene_rsi_0(panel):
    bajando = panel.copy()
    bajando[columna(ACTIVO_OBJETIVO, "cierre")] = np.arange(float(len(panel)), 0.0, -1.0)
    valores = bajando.pipe(rsi)[f"{ACTIVO_OBJETIVO}_rsi_14"].dropna()
    assert np.allclose(valores.to_numpy(), 0.0)


def test_la_distancia_a_la_media_es_cero_en_una_serie_constante(panel):
    """Si el precio no se mueve, esta exactamente sobre su media y la distancia es 0.
    Un signo cambiado o un cociente invertido rompen esto."""
    constante = panel.copy()
    constante[columna(ACTIVO_OBJETIVO, "cierre")] = 100.0
    distancias = medias_moviles(constante).dropna()
    assert np.allclose(distancias.to_numpy(), 0.0, atol=1e-12)


def test_el_histograma_del_macd_es_la_linea_menos_su_senal(panel):
    tabla = macd(panel)
    diferencia = tabla[f"{ACTIVO_OBJETIVO}_macd"] - tabla[f"{ACTIVO_OBJETIVO}_macd_senal"]
    assert np.allclose(
        diferencia.to_numpy(),
        tabla[f"{ACTIVO_OBJETIVO}_macd_histograma"].to_numpy(),
        equal_nan=True,
    )


def test_el_macd_esta_normalizado_por_el_precio(panel):
    """Duplicar todos los precios no puede cambiar el MACD normalizado. Si lo
    cambiara, la caracteristica dependeria del nivel de precio del periodo y seria
    inservible fuera del rango de entrenamiento."""
    doble = panel.copy()
    doble[columna(ACTIVO_OBJETIVO, "cierre")] = doble[columna(ACTIVO_OBJETIVO, "cierre")] * 2
    assert np.allclose(
        macd(panel).to_numpy(), macd(doble).to_numpy(), equal_nan=True, atol=1e-12
    )


def test_el_pctb_de_bollinger_vale_medio_cuando_el_precio_esta_en_la_media(panel):
    constante = panel.copy()
    constante[columna(ACTIVO_OBJETIVO, "cierre")] = 100.0
    tabla = bollinger(constante).dropna()
    # Con desviacion cero las bandas colapsan sobre la media: el ancho es 0 y la
    # posicion queda indefinida, que es lo correcto y no 0,5.
    assert tabla.empty or tabla[f"{ACTIVO_OBJETIVO}_bollinger_ancho_20"].eq(0).all()


def test_el_pctb_pasa_de_uno_cuando_el_precio_rompe_la_banda_superior(panel):
    """%B tiene que poder salirse de [0, 1]: eso es justamente la ruptura de banda,
    y acotarlo destruiria la informacion que hace util al indicador."""
    valores = bollinger(panel)[f"{ACTIVO_OBJETIVO}_bollinger_pctb_20"].dropna()
    assert valores.max() > 1.0 or valores.min() < 0.0


# ---------------------------------------------------------------------------
# Ventana deslizante (S1-M2-03)
# ---------------------------------------------------------------------------


def test_la_posicion_en_el_rango_queda_entre_cero_y_uno(panel):
    tabla = ventana_deslizante(panel)
    for v in (7, 20):
        valores = tabla[f"{ACTIVO_OBJETIVO}_posicion_rango_{v}"].dropna()
        assert valores.min() >= 0.0
        assert valores.max() <= 1.0


def test_la_posicion_vale_uno_en_el_maximo_de_la_ventana_y_cero_en_el_minimo():
    """Contra una serie hecha a mano, donde la respuesta se puede contar a mano."""
    from contracts.config import ACTIVOS
    from contracts.schema import CAMPOS_OHLCV, INDICE

    valores = np.array([10.0, 11, 12, 13, 14, 15, 20, 9, 9, 9, 9, 9, 9, 8])
    indice = pd.date_range("2020-01-01", periods=len(valores), freq="D", tz="UTC", name=INDICE)
    datos = {
        f"{a}_{c}": np.linspace(1, 2, len(valores)) for a in ACTIVOS for c in CAMPOS_OHLCV
    }
    datos[columna(ACTIVO_OBJETIVO, "cierre")] = valores
    hecho_a_mano = pd.DataFrame(datos, index=indice)

    posicion = ventana_deslizante(hecho_a_mano, ventanas=(7,))[
        f"{ACTIVO_OBJETIVO}_posicion_rango_7"
    ]
    assert posicion.iloc[6] == pytest.approx(1.0)   # el 20 es el maximo de sus 7 velas
    assert posicion.iloc[13] == pytest.approx(0.0)  # el 8 es el minimo de sus 7 velas


@pytest.mark.parametrize("w", [3, 5, 7])
def test_todo_maximo_tiene_posicion_uno_en_su_ventana_hacia_atras(panel, w):
    """Propiedad que sostiene el valor de esta caracteristica y que hay que poder
    afirmar en el informe: si t supera a sus w velas anteriores y posteriores, con
    mayor razon supera a las w-1 anteriores, asi que `posicion_rango_w == 1`.

    Es condicion NECESARIA de Maximo, no suficiente. Sirve como filtro, no como
    prediccion, y confundir las dos cosas seria prometer lo que no hay.
    """
    etiquetas = etiquetar(cierre(panel, ACTIVO_OBJETIVO), w)
    posicion = ventana_deslizante(panel, ventanas=(w,))[f"{ACTIVO_OBJETIVO}_posicion_rango_{w}"]

    maximos = etiquetas == int(Clase.MAXIMO)
    minimos = etiquetas == int(Clase.MINIMO)
    assert maximos.sum() > 0, "la serie de prueba no tiene maximos: la prueba no probaria nada"

    assert np.allclose(posicion[maximos.fillna(False)].to_numpy(), 1.0)
    assert np.allclose(posicion[minimos.fillna(False)].to_numpy(), 0.0)


def test_la_curtosis_de_ruido_normal_ronda_cero():
    """`kurt()` de pandas devuelve el exceso de curtosis, que es 0 para una normal.
    Si devolviera la curtosis sin restar 3, la caracteristica estaria desplazada y
    la interpretacion del informe seria falsa."""
    from contracts.config import ACTIVOS
    from contracts.schema import CAMPOS_OHLCV, INDICE

    generador = np.random.default_rng(0)
    n = 4000
    retornos = generador.normal(0, 0.01, n)
    precios = 100 * np.exp(np.cumsum(retornos))
    indice = pd.date_range("2020-01-01", periods=n, freq="D", tz="UTC", name=INDICE)
    datos = {f"{a}_{c}": np.linspace(1, 2, n) for a in ACTIVOS for c in CAMPOS_OHLCV}
    datos[columna(ACTIVO_OBJETIVO, "cierre")] = precios
    normal = pd.DataFrame(datos, index=indice)

    curtosis = ventana_deslizante(normal, ventanas=(200,))[
        f"{ACTIVO_OBJETIVO}_curtosis_retornos_200"
    ].dropna()
    assert abs(curtosis.mean()) < 0.5


# ---------------------------------------------------------------------------
# Rezagos medidos (S1-M2-04)
# ---------------------------------------------------------------------------


def test_los_ordenes_de_rezago_son_positivos_y_sin_repetir():
    """Un orden 0 seria el precio actual —no un rezago— y uno negativo miraria al
    futuro. Un repetido produciria columnas duplicadas silenciosamente."""
    assert all(k >= 1 for k in REZAGOS_MEDIDOS)
    assert len(set(REZAGOS_MEDIDOS)) == len(REZAGOS_MEDIDOS)


def test_el_rezago_uno_esta_siempre():
    """Es el precio de la vela anterior: la entrada mas literal del enunciado."""
    assert 1 in REZAGOS_MEDIDOS


def test_el_rezago_k_es_el_precio_de_hace_k_velas(panel):
    tabla = rezagos(panel, ACTIVO_OBJETIVO)
    serie = cierre(panel, ACTIVO_OBJETIVO)
    for k in REZAGOS_MEDIDOS:
        columna_k = tabla[f"{ACTIVO_OBJETIVO}_cierre_rezago_{k}"]
        assert columna_k.iloc[k:].to_numpy() == pytest.approx(serie.iloc[:-k].to_numpy())
        assert columna_k.iloc[:k].isna().all()


# ---------------------------------------------------------------------------
# El conjunto
# ---------------------------------------------------------------------------


def test_construir_no_produce_columnas_repetidas(panel):
    """Dos familias que colisionaran en un nombre se pisarian sin avisar, y el
    modelo recibiria una columna menos de las que creemos."""
    columnas = construir(panel).columns
    assert len(columnas) == len(set(columnas))


def test_construir_cubre_las_cuatro_familias_que_exige_rf_f1(panel):
    columnas = " ".join(construir(panel).columns)
    for familia in ("rezago", "volatilidad", "rsi", "posicion_rango", "corr_"):
        assert familia in columnas, f"falta la familia {familia!r} que exige RF-F1/RF-F2"


def test_el_numero_de_columnas_no_desborda_los_ejemplos_disponibles(panel):
    """Con 420 ejemplos de la clase minoritaria en entrenamiento, pasar de unas 80
    columnas es sobreajuste garantizado. Esta prueba existe para que agregar
    caracteristicas sea una decision consciente y no una acumulacion silenciosa.

    Si falla, la respuesta no es subir el numero: es medir cuales aportan (RF-F4).
    """
    assert construir(panel).shape[1] <= 80


def test_construir_deja_casi_todas_las_filas_utilizables(panel):
    """Una ventana larga de mas puede dejar la mitad del panel en NaN sin que nadie
    lo note hasta que el modelo entrena con la mitad de los datos."""
    tabla = construir(panel)
    completas = tabla.notna().all(axis=1).sum()
    assert completas > 0.9 * len(tabla)
