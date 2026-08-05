"""Pruebas del contrato de etiquetado.

Verifican propiedades que tienen que valer siempre, no conteos concretos: una
prueba que cuenta 47 maximos se rompe con cualquier cambio correcto de w, y no
dice nada sobre si el etiquetado es correcto.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from contracts.labeling import (
    Clase,
    cota_superior_extremos,
    etiquetar,
    latencia_real,
    objetivo,
    resumen_clases,
)
from src.sintetico.generador import serie_zigzag


def test_detecta_los_giros_construidos():
    """Sobre una serie sin ruido cuyos vertices pusimos nosotros, el etiquetador
    tiene que encontrar exactamente esos vertices y ninguno mas."""
    w = 4
    serie, giros = serie_zigzag(n=400, w=w, semilla=7, ruido=0.0)
    etiquetas = etiquetar(serie, w)

    posiciones_extremas = np.where(
        etiquetas.to_numpy(na_value=Clase.CONTINUIDAD) != int(Clase.CONTINUIDAD)
    )[0]

    assert set(posiciones_extremas) == set(giros)


def test_maximos_alternan_con_minimos():
    """En una serie construida como zigzag, entre dos maximos siempre hay un minimo.
    Si el etiquetador produjera dos maximos seguidos, estaria inventando giros."""
    w = 3
    serie, _ = serie_zigzag(n=300, w=w, semilla=11, ruido=0.0)
    etiquetas = etiquetar(serie, w).dropna().astype(int)
    secuencia = [c for c in etiquetas.tolist() if c != int(Clase.CONTINUIDAD)]

    for anterior, siguiente in zip(secuencia, secuencia[1:], strict=False):
        assert anterior != siguiente


@pytest.mark.parametrize("w", [2, 5, 10])
def test_separacion_minima_entre_extremos_del_mismo_tipo(w):
    """Dos maximos no pueden estar a menos de w+1 velas.

    Es la propiedad de la que se deriva la cota de balance de clases que usamos en
    toda la documentacion. Si se rompiera, esa cota seria falsa.
    """
    serie, _ = serie_zigzag(n=600, w=w, semilla=3, ruido=0.0)
    etiquetas = etiquetar(serie, w)
    valores = etiquetas.to_numpy(na_value=Clase.CONTINUIDAD)

    for clase in (Clase.MAXIMO, Clase.MINIMO):
        posiciones = np.where(valores == int(clase))[0]
        if len(posiciones) > 1:
            assert np.diff(posiciones).min() >= w + 1


@pytest.mark.parametrize("w", [2, 5, 10])
def test_respeta_la_cota_superior_teorica(w):
    """La fraccion medida de cada clase extrema nunca puede superar 1/(w+1)."""
    serie, _ = serie_zigzag(n=800, w=w, semilla=5, ruido=0.0)
    resumen = resumen_clases(etiquetar(serie, w))
    cota = 100 * cota_superior_extremos(w)

    for clase in ("Maximo", "Minimo"):
        medido = resumen.loc[resumen["clase"] == clase, "porcentaje"].item()
        assert medido <= cota + 1e-9


def test_los_bordes_quedan_nulos_no_continuidad():
    """Las primeras y ultimas w velas no tienen ventana completa. Marcarlas como
    Continuidad seria afirmar algo que no sabemos, y sesgaria las metricas."""
    w = 6
    serie, _ = serie_zigzag(n=200, w=w, semilla=1, ruido=0.0)
    etiquetas = etiquetar(serie, w)

    assert etiquetas.iloc[:w].isna().all()
    assert etiquetas.iloc[-w:].isna().all()
    assert etiquetas.iloc[w:-w].notna().all()


def test_etiquetar_es_una_funcion_pura():
    """Dos llamadas con la misma entrada dan el mismo resultado, y la entrada no
    se modifica. Si mutara la serie, dos modulos que la comparten se romperian
    segun el orden en que corrieran."""
    w = 4
    serie, _ = serie_zigzag(n=150, w=w, semilla=2, ruido=0.0)
    copia = serie.copy()

    primera = etiquetar(serie, w)
    segunda = etiquetar(serie, w)

    pd.testing.assert_series_equal(primera, segunda)
    pd.testing.assert_series_equal(serie, copia)


def test_serie_mas_corta_que_la_ventana_no_revienta():
    serie = pd.Series([1.0, 2.0, 3.0])
    etiquetas = etiquetar(serie, w=5)
    assert etiquetas.isna().all()


def test_w_invalido_falla_rapido():
    serie = pd.Series(np.arange(50, dtype=float))
    with pytest.raises(ValueError):
        etiquetar(serie, w=0)


def test_objetivo_adelanta_h_posiciones():
    """La fila t tiene que contener la etiqueta de t+h: es lo que hay que anunciar
    estando parado en t."""
    etiquetas = pd.Series(pd.array([1, 2, 3, 1, 2, 3], dtype="Int64"))
    obtenido = objetivo(etiquetas, h=2)

    assert obtenido.iloc[0] == etiquetas.iloc[2]
    assert obtenido.iloc[3] == etiquetas.iloc[5]
    assert obtenido.iloc[-2:].isna().all()


def test_latencia_real_suma_ventana_y_horizonte():
    """Reportar solo h como anticipacion del sistema seria enganoso: la etiqueta de
    t+h no se conoce hasta t+h+w."""
    assert latencia_real(w=5, h=3) == 8
