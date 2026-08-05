"""Pruebas de la particion temporal."""

from __future__ import annotations

import numpy as np
import pytest

from contracts.splits import particionar


@pytest.mark.parametrize(("w", "h"), [(2, 1), (5, 3), (10, 5)])
def test_los_conjuntos_no_se_solapan(w, h):
    p = particionar(n=2000, w=w, h=h)
    assert not (p.entrenamiento & p.validacion).any()
    assert not (p.entrenamiento & p.prueba).any()
    assert not (p.validacion & p.prueba).any()


@pytest.mark.parametrize(("w", "h"), [(2, 1), (5, 3), (10, 5)])
def test_todo_indice_cae_en_exactamente_un_bloque(w, h):
    p = particionar(n=2000, w=w, h=h)
    total = (
        p.entrenamiento.astype(int)
        + p.validacion.astype(int)
        + p.prueba.astype(int)
        + p.embargo.astype(int)
    )
    assert (total == 1).all()


@pytest.mark.parametrize(("w", "h"), [(2, 1), (5, 3), (10, 5)])
def test_el_orden_es_cronologico(w, h):
    """Entrenamiento antes que validacion, validacion antes que prueba. Si se
    mezclaran, el modelo se entrenaria con el futuro de lo que evalua."""
    p = particionar(n=2000, w=w, h=h)
    assert np.where(p.entrenamiento)[0].max() < np.where(p.validacion)[0].min()
    assert np.where(p.validacion)[0].max() < np.where(p.prueba)[0].min()


@pytest.mark.parametrize(("w", "h"), [(2, 1), (5, 3), (10, 5)])
def test_hay_embargo_suficiente_en_cada_frontera(w, h):
    """Sin al menos w+h de separacion, la etiqueta de las ultimas velas de
    entrenamiento se calcula mirando velas de validacion: fuga silenciosa."""
    p = particionar(n=2000, w=w, h=h)
    hueco = w + h

    fin_entrenamiento = np.where(p.entrenamiento)[0].max()
    inicio_validacion = np.where(p.validacion)[0].min()
    assert inicio_validacion - fin_entrenamiento > hueco

    fin_validacion = np.where(p.validacion)[0].max()
    inicio_prueba = np.where(p.prueba)[0].min()
    assert inicio_prueba - fin_validacion > hueco


def test_una_serie_demasiado_corta_falla_con_mensaje_claro():
    with pytest.raises(ValueError, match="demasiado corta"):
        particionar(n=20, w=10, h=5)
