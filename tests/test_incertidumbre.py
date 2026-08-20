"""Pruebas del bootstrap de metricas.

Lo que hay que probar de una herramienta estadistica no es que corra: es que diga
"no hay diferencia" cuando no la hay y "si la hay" cuando la hay. Un bootstrap mal
implementado devuelve intervalos con toda la pinta de correctos.
"""

from __future__ import annotations

import numpy as np
import pytest

from contracts.labeling import Clase
from contracts.metrics import f1_macro
from src.features.incertidumbre import (
    _indices_estratificados,
    intervalo_diferencia,
    intervalo_metrica,
    resumen_clases,
)

MAXIMO, MINIMO, CONTINUIDAD = int(Clase.MAXIMO), int(Clase.MINIMO), int(Clase.CONTINUIDAD)


@pytest.fixture
def etiquetas():
    """Desbalance parecido al real: ~5 % de cada clase extrema."""
    generador = np.random.default_rng(0)
    y = np.full(1000, CONTINUIDAD)
    posiciones = generador.choice(1000, size=100, replace=False)
    y[posiciones[:50]] = MAXIMO
    y[posiciones[50:]] = MINIMO
    return y


def test_dos_predicciones_identicas_dan_diferencia_cero_sin_incertidumbre(etiquetas):
    """La prueba mas importante del archivo. Si un bootstrap pareado devolviera un
    intervalo ancho comparando un modelo consigo mismo, estaria remuestreando las dos
    predicciones por separado, y entonces TODAS sus comparaciones estarian infladas."""
    generador = np.random.default_rng(1)
    pred = generador.choice([MAXIMO, MINIMO, CONTINUIDAD], size=len(etiquetas))

    resultado = intervalo_diferencia(etiquetas, pred, pred, remuestras=200)
    assert resultado["diferencia"] == 0.0
    assert resultado["ic_inferior"] == 0.0
    assert resultado["ic_superior"] == 0.0
    assert not resultado["excluye_el_cero"]


def test_un_modelo_claramente_mejor_produce_un_intervalo_que_excluye_el_cero(etiquetas):
    """Un modelo perfecto contra uno que responde siempre la mayoritaria."""
    perfecto = etiquetas.copy()
    trivial = np.full(len(etiquetas), CONTINUIDAD)

    resultado = intervalo_diferencia(etiquetas, perfecto, trivial, remuestras=200)
    assert resultado["diferencia"] > 0
    assert resultado["excluye_el_cero"]
    assert resultado["ic_inferior"] > 0
    assert resultado["fraccion_a_favor"] == 1.0


def test_dos_modelos_igual_de_malos_no_producen_una_diferencia_significativa(etiquetas):
    """El falso positivo que hay que evitar: dos modelos aleatorios distintos no
    pueden dar una diferencia distinguible de cero solo por remuestrear."""
    generador = np.random.default_rng(2)
    a = generador.choice([MAXIMO, MINIMO, CONTINUIDAD], size=len(etiquetas))
    b = generador.choice([MAXIMO, MINIMO, CONTINUIDAD], size=len(etiquetas))

    resultado = intervalo_diferencia(etiquetas, a, b, remuestras=400)
    assert not resultado["excluye_el_cero"]


def test_el_intervalo_contiene_al_valor_observado(etiquetas):
    generador = np.random.default_rng(3)
    pred = generador.choice([MAXIMO, MINIMO, CONTINUIDAD], size=len(etiquetas))

    resultado = intervalo_metrica(etiquetas, pred, f1_macro, remuestras=300)
    assert resultado["ic_inferior"] <= resultado["valor"] <= resultado["ic_superior"]
    assert resultado["ic_inferior"] < resultado["ic_superior"]


def test_un_modelo_determinista_no_tiene_incertidumbre_en_la_metrica(etiquetas):
    """El baseline trivial da siempre el mismo F1 macro sobre cualquier remuestra
    estratificada, porque el estrato conserva el tamano de cada clase. Es el control
    que detecta si el remuestreo esta alterando la composicion del conjunto."""
    trivial = np.full(len(etiquetas), CONTINUIDAD)
    resultado = intervalo_metrica(etiquetas, trivial, f1_macro, remuestras=100)
    assert resultado["ic_inferior"] == pytest.approx(resultado["ic_superior"], abs=1e-12)


def test_el_remuestreo_conserva_el_tamano_de_cada_clase(etiquetas):
    """Sin esto, una remuestra puede quedarse sin ejemplos de Maximo y el F1 de esa
    clase caeria por ausencia de casos, no por error del modelo."""
    generador = np.random.default_rng(4)
    idx = _indices_estratificados(etiquetas, generador)
    remuestreadas = etiquetas[idx]

    assert len(idx) == len(etiquetas)
    for clase in (MAXIMO, MINIMO, CONTINUIDAD):
        assert (remuestreadas == clase).sum() == (etiquetas == clase).sum()


def test_la_misma_semilla_da_el_mismo_intervalo(etiquetas):
    """Un intervalo que cambia entre corridas no se puede citar en un informe."""
    generador = np.random.default_rng(5)
    pred = generador.choice([MAXIMO, MINIMO, CONTINUIDAD], size=len(etiquetas))
    a = intervalo_metrica(etiquetas, pred, remuestras=100, semilla=7)
    b = intervalo_metrica(etiquetas, pred, remuestras=100, semilla=7)
    assert a == b


def test_el_resumen_de_clases_cuadra_con_el_total(etiquetas):
    tabla = resumen_clases(etiquetas)
    total = tabla.loc[tabla["clase"] == "TOTAL", "n"].iloc[0]
    assert total == len(etiquetas)
    assert tabla[tabla["clase"] != "TOTAL"]["n"].sum() == total
