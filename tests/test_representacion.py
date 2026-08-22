"""Pruebas del arnes de representaciones (S2-M2-02).

El arnes existe antes que el extractor real, asi que lo unico que puede avalarlo son
sus controles. Estas pruebas verifican sobre todo que esos controles **puedan fallar**.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from contracts.schema import COLUMNAS_PANEL
from src.features import representacion
from src.features.representacion import (
    CONTROL_SIN_REPRESENTACION,
    EXTRACTORES,
    Extractor,
    ExtractorEco,
    ExtractorNulo,
    matriz_con,
    verificar_arnes,
)


def _panel(n: int = 300) -> pd.DataFrame:
    indice = pd.date_range("2021-01-01", periods=n, freq="4h", tz="UTC")
    t = np.arange(n)
    precio = 100 + 20 * np.sin(2 * np.pi * t / 40) + 0.01 * t
    return pd.DataFrame({c: precio for c in COLUMNAS_PANEL}, index=indice)


def test_no_se_puede_implementar_un_extractor_a_medias():
    """La interfaz obliga a las dos mitades: ajustar y transformar."""

    class Incompleto(Extractor):
        nombre = "incompleto"

        def transformar(self, panel):
            return pd.DataFrame(index=panel.index)

    with pytest.raises(TypeError):
        Incompleto()


def test_el_extractor_nulo_no_agrega_nada():
    panel = _panel()
    nuevas = ExtractorNulo().ajustar(panel, np.ones(len(panel), dtype=bool)).transformar(panel)
    assert nuevas.shape[1] == 0
    assert nuevas.index.equals(panel.index)


def test_el_eco_exige_ajustar_antes_de_transformar():
    """Sin la mascara de entrenamiento no hay forma de saber que vio el extractor."""
    with pytest.raises(RuntimeError, match="ajustar"):
        ExtractorEco().transformar(_panel())


def test_el_eco_no_agrega_informacion_nueva():
    """Reemite columnas existentes: su correlacion con el original tiene que ser 1."""
    panel = _panel()
    eco = ExtractorEco(n_columnas=3).ajustar(panel, np.ones(len(panel), dtype=bool))
    nuevas = eco.transformar(panel)
    assert nuevas.shape[1] == 3
    clasicas = representacion.construir(panel)
    for columna in nuevas.columns:
        original = columna.removeprefix(f"{eco.nombre}_")
        assert original in clasicas.columns
        par = pd.concat([nuevas[columna], clasicas[original]], axis=1).dropna()
        if len(par) > 2 and par.iloc[:, 0].std() > 0:
            assert abs(par.corr().iloc[0, 1] - 1.0) < 1e-9


def test_el_arnes_rechaza_columnas_que_chocan_con_las_clasicas():
    """Dos columnas homonimas son el defecto que ya nos costo dos PR."""

    class Chocador(Extractor):
        nombre = "chocador"

        def ajustar(self, panel, mascara_entrenamiento):
            return self

        def transformar(self, panel):
            clasicas = representacion.construir(panel)
            return pd.DataFrame({clasicas.columns[0]: 0.0}, index=panel.index)

    panel = _panel()
    with pytest.raises(ValueError, match="chocan con las clasicas"):
        matriz_con(Chocador(), panel, np.ones(len(panel), dtype=bool))


def test_el_arnes_rechaza_un_indice_distinto():
    """Si el indice no coincide, la concatenacion alinea mal y nadie se entera."""

    class Desalineado(Extractor):
        nombre = "desalineado"

        def ajustar(self, panel, mascara_entrenamiento):
            return self

        def transformar(self, panel):
            return pd.DataFrame({"x": 0.0}, index=panel.index[:-5])

    panel = _panel()
    with pytest.raises(ValueError, match="indice distinto"):
        matriz_con(Desalineado(), panel, np.ones(len(panel), dtype=bool))


def test_el_control_del_arnes_detecta_que_las_ramas_no_coinciden():
    with pytest.raises(AssertionError, match="las dos ramas difieren"):
        verificar_arnes(
            {
                "f1_con_representacion": 0.5,
                "f1_sin_representacion": CONTROL_SIN_REPRESENTACION,
            }
        )


def test_el_control_del_arnes_detecta_que_no_reproduce_lo_publicado():
    with pytest.raises(AssertionError, match="lo publicado es"):
        verificar_arnes({"f1_con_representacion": 0.5, "f1_sin_representacion": 0.5})


def test_el_control_del_arnes_pasa_cuando_corresponde():
    verificar_arnes(
        {
            "f1_con_representacion": CONTROL_SIN_REPRESENTACION,
            "f1_sin_representacion": CONTROL_SIN_REPRESENTACION,
        }
    )


def test_el_relleno_no_es_ruido_aleatorio():
    """Fue una instruccion explicita, y con ruido el control no controlaria nada."""
    fuente = open(representacion.__file__, encoding="utf-8").read()
    cuerpo = fuente.split("class ExtractorEco")[1].split("\nEXTRACTORES")[0]
    for prohibido in ("normal(", "uniform(", "default_rng", "random"):
        assert prohibido not in cuerpo, (
            f"el extractor de relleno no puede usar {prohibido!r}: con ruido, un arnes "
            "roto y uno correcto darian resultados igual de plausibles"
        )


def test_los_extractores_de_control_estan_registrados():
    assert EXTRACTORES[ExtractorNulo.nombre] is ExtractorNulo
    assert EXTRACTORES[ExtractorEco.nombre] is ExtractorEco
    for clase in EXTRACTORES.values():
        assert issubclass(clase, Extractor)
