"""Pruebas de las tres tablas de metricas y, sobre todo, de su control.

Lo que se prueba aqui no es tanto que los numeros salgan, sino que el control que
los avala **pueda fallar**. Un control que no se vio fallar nunca no avala nada.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from contracts.labeling import Clase
from contracts.schema import COLUMNAS_PANEL
from src.features import tablas_metricas


def _panel_sintetico(n: int = 400) -> pd.DataFrame:
    """Panel con una onda limpia: los giros estan donde se sabe."""
    indice = pd.date_range("2021-01-01", periods=n, freq="4h", tz="UTC")
    t = np.arange(n)
    precio = 100 + 20 * np.sin(2 * np.pi * t / 40)
    columnas = {nombre: precio for nombre in COLUMNAS_PANEL}
    return pd.DataFrame(columnas, index=indice)


def test_el_balance_suma_las_etiquetas_validas():
    panel = _panel_sintetico()
    tabla = tablas_metricas.tabla_balance(panel, w=7)
    assert tabla["n"].sum() == tabla.attrs["n_etiquetadas"]
    assert tabla.attrs["n_etiquetadas"] <= tabla.attrs["n_serie"]


def test_las_clases_extremas_respetan_la_cota_aritmetica():
    """Con ventana w no puede haber mas de 1/(w+1) de maximos: es aritmetica."""
    panel = _panel_sintetico()
    w = 7
    tabla = tablas_metricas.tabla_balance(panel, w=w)
    cota = tabla.attrs["cota_superior_extremos_pct"]
    assert cota == pytest.approx(100 / (w + 1), abs=1e-3)
    for clase in ("Maximo", "Minimo"):
        obtenido = float(tabla.loc[tabla["clase"] == clase, "porcentaje"].iloc[0])
        assert obtenido <= cota + 1e-6, (
            f"{clase} da {obtenido} %, por encima de la cota aritmetica {cota} %"
        )


def test_el_trivial_no_acierta_ningun_extremo():
    """El argumento entero de la seccion depende de esto: exactitud alta, F1 bajo."""
    panel = _panel_sintetico()
    resultado = tablas_metricas.medir_trivial_serie_completa(panel, w=7)
    assert resultado["f1_maximo"] == 0.0
    assert resultado["f1_minimo"] == 0.0
    assert resultado["precision_direccional"] == 0.0
    assert resultado["exactitud"] > resultado["f1_macro"], (
        "si la exactitud no supera al F1 macro, el ejemplo deja de ilustrar nada"
    )


def test_el_trivial_solo_responde_continuidad():
    panel = _panel_sintetico()
    resultado = tablas_metricas.medir_trivial_serie_completa(panel, w=7)
    assert resultado["f1_continuidad"] > 0.0
    assert int(Clase.CONTINUIDAD) == 3


def test_el_control_se_compara_contra_valores_escritos_y_no_contra_los_json():
    """Si leyera los JSON del repo, el control se compararia consigo mismo."""
    fuente = (tablas_metricas.__file__).replace(".pyc", ".py")
    texto = open(fuente, encoding="utf-8").read()
    bloque = texto.split("def verificar_control")[1].split("def generar_evidencia")[0]
    assert "marco-teorico.json" not in bloque
    assert "m2-baselines.json" not in bloque
    assert isinstance(tablas_metricas.CONTROL_SEMANA_1["balance"]["Maximo"], int)


def test_el_control_falla_cuando_las_cifras_no_coinciden(monkeypatch):
    """La prueba que importa: que el control pueda fallar de verdad.

    Se le cambia una sola cifra de referencia. Si `verificar_control()` siguiera
    pasando, no estaria comprobando nada y todas las cifras publicadas a traves de
    el quedarian sin aval.
    """
    falseado = {
        **tablas_metricas.CONTROL_SEMANA_1,
        "balance": {"Maximo": 999, "Minimo": 141, "Continuidad": 1891},
    }
    monkeypatch.setattr(tablas_metricas, "CONTROL_SEMANA_1", falseado)
    with pytest.raises(AssertionError, match="no reproduce las cifras publicadas"):
        tablas_metricas.verificar_control()


def test_el_control_reproduce_la_semana_1():
    """Lento pero es el punto entero del modulo: leer el panel real y comprobar."""
    obtenido = tablas_metricas.verificar_control()
    assert obtenido["parametros"] == {"intervalo": "1d", "w": 5, "h": 3}
