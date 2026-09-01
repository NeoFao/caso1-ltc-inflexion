"""Pruebas de la medicion del aporte multivariante (S4-M2-01)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from contracts.config import ACTIVO_OBJETIVO, ACTIVOS_APOYO
from src.features import multivariante
from src.features.ablacion import es_de_activo_de_apoyo


def test_los_fragmentos_seleccionan_lo_mismo_que_la_funcion():
    """Las dos definiciones de 'columna de apoyo' no pueden separarse.

    `BosqueAleatorio.excluir` filtra por subcadena y `es_de_activo_de_apoyo()` por
    prefijo. Si dejaran de coincidir, `solo_LTC` mediria otra cosa sin que fallara
    nada — el mismo tipo de error que retiene el PR #58.
    """
    columnas = pd.Index(
        [
            f"{ACTIVO_OBJETIVO}_cierre_rezago_rel_1",
            f"{ACTIVO_OBJETIVO}_rsi_14",
            *(f"{activo}_cierre_rezago_rel_1" for activo in ACTIVOS_APOYO),
            f"corr_{ACTIVO_OBJETIVO}_{ACTIVOS_APOYO[0]}_30",
        ]
    )
    multivariante._verificar_equivalencia_del_filtro(columnas)

    por_fragmento = {
        c for c in columnas if any(f in c for f in multivariante.FRAGMENTOS_DE_APOYO)
    }
    assert por_fragmento == {c for c in columnas if es_de_activo_de_apoyo(c)}
    assert f"{ACTIVO_OBJETIVO}_rsi_14" not in por_fragmento


def test_la_verificacion_del_filtro_puede_fallar():
    """Un control que no se ve fallar no controla nada."""
    columnas = pd.Index(["INVENTADO_corr_algo", "LTC_rsi_14"])
    with pytest.raises(AssertionError, match="ya no seleccionan lo mismo"):
        multivariante._verificar_equivalencia_del_filtro(columnas)


def test_el_control_contra_m3_puede_fallar():
    """Si el bosque completo dejara de reproducir la cifra de M3, hay que enterarse."""
    falseado = {"metricas": {"completo": {"f1_macro": 0.5}}}
    with pytest.raises(AssertionError, match="No se publica nada"):
        multivariante.verificar_control(falseado)


def test_el_control_pasa_cuando_reproduce():
    exacto = {"metricas": {"completo": {"f1_macro": multivariante.CONTROL_BOSQUE_M3}}}
    multivariante.verificar_control(exacto)


def test_el_veredicto_no_afirma_aporte_si_el_intervalo_cruza_el_cero():
    medicion = {
        "diferencias": {
            "completo_vs_solo_LTC": {
                "diferencia": 0.009,
                "ic_inferior": -0.0229,
                "ic_superior": 0.0417,
                "excluye_el_cero": False,
                "fraccion_a_favor": 0.71,
            },
            "completo_vs_baseline_aleatorio": {"excluye_el_cero": True},
        }
    }
    veredicto = multivariante._veredicto(medicion)
    assert veredicto["se_puede_afirmar_que_aporta"] is False
    assert veredicto["supera_el_umbral_del_equipo"] is False


def test_el_veredicto_tampoco_afirma_aporte_con_diferencia_negativa():
    """Un intervalo que excluye el cero por el lado negativo no es un aporte."""
    medicion = {
        "diferencias": {
            "completo_vs_solo_LTC": {
                "diferencia": -0.0352,
                "ic_inferior": -0.0625,
                "ic_superior": -0.008,
                "excluye_el_cero": True,
                "fraccion_a_favor": 0.01,
            },
            "completo_vs_baseline_aleatorio": {"excluye_el_cero": False},
        }
    }
    veredicto = multivariante._veredicto(medicion)
    assert veredicto["se_puede_afirmar_que_aporta"] is False
    assert veredicto["supera_el_umbral_del_equipo"] is True


def test_cambia_de_signo_detecta_el_cruce():
    """La bandera que decide si el efecto sobrevive al cambio de semilla."""
    diferencias = np.array([0.009, 0.0005, -0.0037, 0.0047, -0.0066])
    assert bool(diferencias.min() < 0 < diferencias.max()) is True
    solo_positivas = np.array([0.02, 0.03, 0.025])
    assert bool(solo_positivas.min() < 0 < solo_positivas.max()) is False


def test_comparar_modelos_de_contraste_exige_la_representacion():
    """No puede heredar el default de construir(): asi fue como se desincronizo.

    Antes del arreglo, `comparar_modelos_de_contraste` tomaba la representacion del
    default de `construir()`. Al cambiar ese default en el #58, esa funcion paso a
    medir rezagos relativos mientras el bloque `resultados` del mismo JSON seguia
    midiendo rezagos en nivel, sin que ninguna linea de codigo cambiara.
    """
    import inspect

    from src.features.ablacion import comparar_modelos_de_contraste

    parametro = inspect.signature(comparar_modelos_de_contraste).parameters[
        "rezagos_relativos"
    ]
    assert parametro.default is inspect.Parameter.empty, (
        "rezagos_relativos no puede tener valor por omision: un default lo vuelve a "
        "atar al de construir(), que es lo que produjo la desincronizacion"
    )
    assert parametro.kind is inspect.Parameter.KEYWORD_ONLY
