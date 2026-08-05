"""Pruebas del esquema del panel.

validar_panel lanza en vez de devolver un booleano a proposito: un panel invalido
tiene que detener el script donde se produjo el error y no veinte pasos despues.
"""

from __future__ import annotations

import pandas as pd
import pytest

from contracts.schema import COLUMNAS_PANEL, columna, validar_panel
from tests.test_fuga import panel_falso


def test_un_panel_bien_formado_pasa():
    validar_panel(panel_falso())


def test_columna_rechaza_activos_y_campos_desconocidos():
    with pytest.raises(ValueError):
        columna("DOGE", "cierre")
    with pytest.raises(ValueError):
        columna("LTC", "precio")


def test_indice_sin_zona_horaria_es_rechazado():
    """Sin zona horaria explicita, dos personas en husos distintos alinean las
    velas de forma diferente y sus resultados dejan de ser comparables."""
    panel = panel_falso()
    panel.index = panel.index.tz_localize(None)
    with pytest.raises(ValueError, match="UTC"):
        validar_panel(panel)


def test_indice_desordenado_es_rechazado():
    panel = panel_falso().iloc[::-1]
    with pytest.raises(ValueError, match="cronologicamente"):
        validar_panel(panel)


def test_indice_con_duplicados_es_rechazado():
    panel = panel_falso()
    panel = pd.concat([panel, panel.iloc[[10]]]).sort_index()
    with pytest.raises(ValueError, match="duplicados"):
        validar_panel(panel)


def test_columna_faltante_es_rechazada():
    panel = panel_falso().drop(columns=["SOL_volumen"])
    with pytest.raises(ValueError, match="faltan"):
        validar_panel(panel)


def test_el_contrato_declara_treinta_columnas():
    """Seis activos por cinco campos. Si alguien anade un activo sin actualizar el
    resto del proyecto, esta prueba lo detecta antes que el panel real."""
    assert len(COLUMNAS_PANEL) == 30
