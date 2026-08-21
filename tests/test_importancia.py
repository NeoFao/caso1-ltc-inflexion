"""Pruebas de la importancia por permutacion (S3-M2-01).

Lo que se prueba sobre todo es que el metodo **pueda dar cero**: si una columna que
por construccion no informa nada saliera importante, la tabla entera no significaria
nada.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.features import importancia


class _ModeloDeJuguete:
    """Predice mirando UNA sola columna. Lo demas le da igual, y eso es el punto."""

    def __init__(self, columna: str) -> None:
        self.columna = columna

    def predecir(self, X: pd.DataFrame) -> np.ndarray:
        return np.where(X[self.columna] > 0, 1, 3).astype(int)


def _marco(n: int = 200) -> pd.DataFrame:
    generador = np.random.default_rng(0)
    return pd.DataFrame(
        {
            "util": generador.normal(size=n),
            "ignorada_1": generador.normal(size=n),
            "ignorada_2": generador.uniform(size=n),
        }
    )


def test_la_columna_que_el_modelo_usa_sale_primera():
    X = _marco()
    modelo = _ModeloDeJuguete("util")
    y = modelo.predecir(X)
    tabla = importancia.importancia_por_permutacion(modelo, X.copy(), y, repeticiones=5)
    assert tabla.iloc[0]["columna"] == "util"
    assert tabla.iloc[0]["caida_media"] > 0.1


def test_las_columnas_que_el_modelo_no_mira_dan_cero():
    """El control que decide: permutar algo que el modelo ignora no puede cambiar nada."""
    X = _marco()
    modelo = _ModeloDeJuguete("util")
    y = modelo.predecir(X)
    tabla = importancia.importancia_por_permutacion(modelo, X.copy(), y, repeticiones=5)
    ignoradas = tabla[tabla["columna"].str.startswith("ignorada_")]
    assert (ignoradas["caida_media"].abs() < 1e-12).all(), (
        "una columna que el modelo no mira tiene que dar exactamente cero"
    )


def test_la_permutacion_deja_la_matriz_como_estaba():
    """Si no restaurara la columna, cada medicion contaminaria a la siguiente."""
    X = _marco()
    copia = X.copy(deep=True)
    modelo = _ModeloDeJuguete("util")
    importancia.importancia_por_permutacion(modelo, X, modelo.predecir(X), repeticiones=3)
    pd.testing.assert_frame_equal(X, copia)


def test_las_centinelas_son_reproducibles_y_distintas_entre_si():
    indice = pd.RangeIndex(50)
    primera = importancia.columnas_centinela(indice, n=4)
    segunda = importancia.columnas_centinela(indice, n=4)
    pd.testing.assert_frame_equal(primera, segunda)
    assert primera.shape[1] == 4
    assert primera.nunique().min() > 1, "una centinela constante no controlaria nada"
    assert not primera.corr().abs().where(
        ~np.eye(4, dtype=bool)
    ).gt(0.5).any().any(), "las centinelas no pueden estar correlacionadas entre si"


def test_el_piso_necesita_centinelas():
    tabla = pd.DataFrame(
        {"columna": ["LTC_rsi_14"], "caida_media": [0.01], "caida_desviacion": [0.001]}
    )
    with pytest.raises(ValueError, match="no hay piso que calcular"):
        importancia.piso_de_ruido(tabla)


def test_el_piso_es_el_maximo_de_las_centinelas():
    tabla = pd.DataFrame(
        {
            "columna": ["centinela_ruido_1", "centinela_ruido_2", "LTC_rsi_14"],
            "caida_media": [0.001, 0.004, 0.02],
            "caida_desviacion": [0.001, 0.001, 0.002],
        }
    )
    resultado = importancia.piso_de_ruido(tabla)
    assert resultado["piso"] == 0.004
    assert resultado["piso_columna"] == "centinela_ruido_2"
    assert resultado["n_centinelas"] == 2


def test_la_metrica_es_f1_macro_y_no_exactitud():
    """Con 90 % de Continuidad, ordenar por exactitud daria un orden sin sentido."""
    fuente = open(importancia.__file__, encoding="utf-8").read()
    cuerpo = fuente.split("def importancia_por_permutacion")[1].split("\ndef ")[0]
    assert "f1_macro" in cuerpo
    assert "exactitud" not in cuerpo, (
        "la caida se mide en F1 macro: con 90 % de Continuidad, ordenar por exactitud "
        "daria un orden sin sentido"
    )
