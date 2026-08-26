"""Pruebas del generador de series sinteticas.

El profesor pidio explicitamente construir series con volatilidad y correlacion
controladas para el marco teorico. Que sean controladas significa que el valor
que pedimos y el que sale medido tienen que coincidir; si no, ilustrar un
concepto con ellas seria ensenar algo falso.

Las tolerancias son anchas a proposito: la correlacion de una muestra finita no
es la de la poblacion, y una prueba que exigiera igualdad exacta fallaria por
azar. Lo que se verifica es que el generador acierta, no que es magico.
"""

from __future__ import annotations

import numpy as np
import pytest

from contracts.config import ACTIVOS
from contracts.labeling import Clase, etiquetar
from contracts.schema import cierre, validar_panel
from src.sintetico.generador import etiquetas_esperadas, panel_correlacionado, serie_zigzag


def _correlaciones_cruzadas(panel) -> np.ndarray:
    """Correlaciones entre pares distintos de activos, medidas sobre retornos."""
    import pandas as pd

    retornos = pd.DataFrame({a: cierre(panel, a).pct_change() for a in ACTIVOS}).dropna()
    matriz = retornos.corr().to_numpy()
    return matriz[np.triu_indices_from(matriz, k=1)]


def test_el_panel_generado_cumple_el_contrato():
    """Si no cumpliera el esquema, no se podria pasar a las mismas funciones que el
    panel real, y el banco de pruebas dejaria de probar el sistema de verdad."""
    validar_panel(panel_correlacionado(n=300, semilla=0))


@pytest.mark.parametrize("objetivo", [0.0, 0.4, 0.8])
def test_la_correlacion_medida_se_acerca_a_la_pedida(objetivo):
    medidas = _correlaciones_cruzadas(panel_correlacionado(n=4000, correlacion=objetivo, semilla=1))
    assert abs(medidas.mean() - objetivo) < 0.05


def test_correlacion_alta_y_baja_quedan_bien_separadas():
    """Es el uso concreto que pidio el profesor: mostrar el contraste entre baja y
    alta correlacion. Si los dos casos salieran parecidos, la figura no ensenaria
    nada."""
    baja = _correlaciones_cruzadas(panel_correlacionado(n=3000, correlacion=0.1, semilla=2)).mean()
    alta = _correlaciones_cruzadas(panel_correlacionado(n=3000, correlacion=0.9, semilla=2)).mean()

    assert alta - baja > 0.6


@pytest.mark.parametrize("objetivo", [0.01, 0.05])
def test_la_volatilidad_medida_se_acerca_a_la_pedida(objetivo):
    panel = panel_correlacionado(n=4000, volatilidad=objetivo, semilla=3)
    medida = cierre(panel, "LTC").pct_change().std()

    assert abs(medida - objetivo) / objetivo < 0.15


def test_volatilidad_distinta_por_activo():
    """Permite construir el caso donde LTC es tranquilo y BTC agitado, que es lo que
    hace visible el concepto de volatilidad comparada."""
    panel = panel_correlacionado(
        n=4000,
        volatilidad={"LTC": 0.01, "BTC": 0.05, "ETH": 0.02, "SOL": 0.02, "XRP": 0.02, "ADA": 0.02},
        semilla=4,
    )
    tranquilo = cierre(panel, "LTC").pct_change().std()
    agitado = cierre(panel, "BTC").pct_change().std()

    assert agitado > tranquilo * 3


def test_los_regimenes_producen_heterocedasticidad_medible():
    """Heterocedasticidad es que la volatilidad cambie con el tiempo. Se verifica
    comparando la de un tramo tranquilo contra la de uno agitado, no a ojo."""
    panel = panel_correlacionado(
        n=1200, semilla=5, regimenes=True, duracion_regimen=100, multiplicador_regimen=5.0
    )
    retorno = cierre(panel, "LTC").pct_change().dropna()

    tranquilo = retorno.iloc[10:90].std()
    agitado = retorno.iloc[110:190].std()

    assert agitado > tranquilo * 2


def test_sin_regimenes_la_volatilidad_es_estable():
    """El contraste del caso anterior solo significa algo si el caso base no lo tiene."""
    panel = panel_correlacionado(n=1200, semilla=5, regimenes=False)
    retorno = cierre(panel, "LTC").pct_change().dropna()

    primero = retorno.iloc[10:90].std()
    segundo = retorno.iloc[110:190].std()

    assert 0.4 < primero / segundo < 2.5


def test_es_reproducible_con_la_misma_semilla():
    import pandas as pd

    pd.testing.assert_frame_equal(
        panel_correlacionado(n=200, semilla=7),
        panel_correlacionado(n=200, semilla=7),
    )


def test_correlacion_imposible_falla_con_mensaje_util():
    """Con seis activos equicorrelacionados no existe correlacion -0.9: la matriz
    deja de ser definida positiva. Mejor un error que explique el limite que una
    excepcion de algebra lineal."""
    with pytest.raises(ValueError, match="minimo posible"):
        panel_correlacionado(n=200, correlacion=-0.9)


def test_correlacion_fuera_de_rango_se_rechaza():
    with pytest.raises(ValueError):
        panel_correlacionado(n=200, correlacion=1.5)


def test_el_etiquetador_recupera_todos_los_vertices_plantados():
    """La prueba de deteccion sobre sintetico, en version rapida para CI.

    Es el piso del proyecto: si `etiquetar()` no encuentra los vertices que pusimos
    nosotros -- sin ruido y con separacion mayor que w+1, o sea cada uno un extremo
    estricto de su ventana -- entonces cualquier cifra sobre datos reales es ruido
    con formato.

    La verdad de referencia sale de `etiquetas_esperadas()`, que se construye desde
    los vertices y no desde `etiquetar()`: comparar la funcion consigo misma pasaria
    siempre.

    El guion completo, con el modelo entrenado encima, esta en
    `scripts/pruebas_deteccion.py`. Aqui va solo la parte barata.
    """
    w = 7
    n = 1500
    serie, giros = serie_zigzag(n=n, w=w, semilla=0, ruido=0.0)
    esperadas = etiquetas_esperadas(n, giros, serie.to_numpy(), w).to_numpy()
    obtenidas = etiquetar(serie, w).to_numpy()

    # Por posicion y no por indice: las dos series llevan indices de distinto origen.
    es_giro = np.isin(esperadas, [int(Clase.MAXIMO), int(Clase.MINIMO)])
    assert es_giro.sum() > 0, "la serie de prueba no planto ningun giro"

    fallados = int((obtenidas[es_giro] != esperadas[es_giro]).sum())
    assert fallados == 0, (
        f"{fallados} de {int(es_giro.sum())} vertices plantados no se recuperaron. "
        "Con ruido cero y separacion suficiente, eso no es dificultad: es un "
        "corrimiento de indices en alguna parte del canal."
    )
