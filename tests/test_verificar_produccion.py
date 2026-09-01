"""Pruebas de la logica de comparacion de app/scripts/verificar_produccion.py (issue #88).

El script en si no corre aqui -- depende de la red y de que un despliegue de
Pages haya terminado, y eso vive fuera de `uv run pytest` a proposito (ver el
docstring del script). Lo que se prueba es la logica de comparacion, que es una
funcion pura: recibe el JSON que "serviria" el sitio y el JSON de evidencia, y
devuelve la lista de discrepancias. Se le da esa entrada a mano, sin tocar la
red, y regla 10 del proyecto exige comprobar que las pruebas fallan cuando
deben: por eso cada caso de discrepancia tiene su contraparte que no la tiene.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
RUTA_SCRIPT = RAIZ / "app" / "scripts" / "verificar_produccion.py"

_spec = importlib.util.spec_from_file_location("verificar_produccion", RUTA_SCRIPT)
verificar_produccion = importlib.util.module_from_spec(_spec)
sys.modules["verificar_produccion"] = verificar_produccion
_spec.loader.exec_module(verificar_produccion)

CAMPOS = verificar_produccion.CAMPOS


def _modelo(clave: str, **valores: float) -> dict:
    base = {c: 0.5 for c in CAMPOS}
    base.update(valores)
    base["clave"] = clave
    return base


def test_comparacion_sin_discrepancias_cuando_coincide():
    evidencia = {"chronos_bolt": _modelo("chronos_bolt", f1_macro=0.369)}
    servido = {"modelos": [_modelo("chronos_bolt", f1_macro=0.369)]}
    assert verificar_produccion.verificar_comparacion(servido, evidencia) == []


def test_comparacion_detecta_un_valor_falseado():
    """El caso central del issue: falsear una cifra y comprobar que se detecta."""
    evidencia = {"chronos_bolt": _modelo("chronos_bolt", f1_macro=0.369)}
    servido = {"modelos": [_modelo("chronos_bolt", f1_macro=0.500)]}  # falseado

    discrepancias = verificar_produccion.verificar_comparacion(servido, evidencia)

    assert len(discrepancias) == 1
    # El criterio de aceptacion pide que diga que cifra y en que archivo.
    assert "chronos_bolt.f1_macro" in discrepancias[0]
    assert "comparacion-modelos.json" in discrepancias[0]


def test_comparacion_tolera_el_redondeo_de_publicacion():
    """Una diferencia de redondeo (4 decimales) no es una discrepancia real."""
    evidencia = {"chronos_bolt": _modelo("chronos_bolt", f1_macro=0.36855)}
    servido = {"modelos": [_modelo("chronos_bolt", f1_macro=0.3686)]}  # redondeado al servir
    assert verificar_produccion.verificar_comparacion(servido, evidencia) == []


def test_comparacion_detecta_modelo_que_no_esta_en_la_evidencia():
    evidencia = {"chronos_bolt": _modelo("chronos_bolt")}
    servido = {"modelos": [_modelo("un_modelo_inventado")]}

    discrepancias = verificar_produccion.verificar_comparacion(servido, evidencia)

    assert len(discrepancias) == 1
    assert "un_modelo_inventado" in discrepancias[0]


def test_historico_fundacional_sin_discrepancias_cuando_coincide():
    evidencia = {"chronos_bolt": {**{c: 0.5 for c in CAMPOS}, "n": 1959}}
    servido = {"metricas": {c: 0.5 for c in CAMPOS}, "serie": [{}] * 1959}
    assert verificar_produccion.verificar_historico_fundacional(servido, evidencia) == []


def test_historico_fundacional_detecta_metrica_falseada():
    evidencia = {
        "chronos_bolt": {**{c: 0.5 for c in CAMPOS}, "n": 1959, "precision_direccional": 0.093}
    }
    servido = {
        "metricas": {**{c: 0.5 for c in CAMPOS}, "precision_direccional": 0.2},
        "serie": [{}] * 1959,
    }

    discrepancias = verificar_produccion.verificar_historico_fundacional(servido, evidencia)

    assert any("precision_direccional" in d for d in discrepancias)


def test_historico_fundacional_detecta_velas_faltantes():
    """Es el caso concreto del issue: un build a medias sirve menos velas de las que hay."""
    evidencia = {"chronos_bolt": {**{c: 0.5 for c in CAMPOS}, "n": 1959}}
    servido = {"metricas": {c: 0.5 for c in CAMPOS}, "serie": [{}] * 300}  # build truncado

    discrepancias = verificar_produccion.verificar_historico_fundacional(servido, evidencia)

    assert any("300" in d and "1959" in d for d in discrepancias)
