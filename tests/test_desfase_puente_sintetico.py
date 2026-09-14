"""Que la explicacion del F1 cero del iTransformer siga respaldada por lo que predice.

La prueba 2 sintetica dio al iTransformer un F1 de maximos de cero, y se explico
diciendo que el puente "nunca produce un maximo estricto". Un F1 de cero no distingue
entre no predecir maximos y predecirlos mal ubicados, asi que la explicacion necesita
una medicion propia: `m3-desfase-puente-sintetico.json`.

Estas pruebas fijan lo que esa medicion dice, para que un texto no pueda volver a
afirmar lo contrario sin que falle algo. Solo leen la constancia: no entrenan nada y
corren en CI sin el grupo `modelos`. Volver a medir es
`uv run python -m src.modelos.desfase_puente_sintetico`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
EVIDENCIA = RAIZ / "docs" / "evidencias" / "m3-desfase-puente-sintetico.json"
PUBLICADA = RAIZ / "docs" / "evidencias" / "pruebas-deteccion-profundos.json"

necesita_evidencia = pytest.mark.skipif(
    not EVIDENCIA.exists(), reason="todavia no se midio el desfase del puente"
)


def _medido() -> dict:
    return json.loads(EVIDENCIA.read_text(encoding="utf-8"))


@necesita_evidencia
def test_la_medicion_es_la_prueba_2_publicada_y_no_otra():
    """Si el F1 no coincide con el publicado, se estaria midiendo otra cosa."""
    publicada = json.loads(PUBLICADA.read_text(encoding="utf-8"))["resultados"]
    for nombre, r in _medido()["por_modelo"].items():
        esperado = publicada[nombre]["2_sintetico_modelo_completo"]
        assert r["f1_maximo_coincide_con_la_publicada"] == esperado["f1_maximo"]
        assert r["f1_minimo_coincide_con_la_publicada"] == esperado["f1_minimo"]


@necesita_evidencia
def test_el_itransformer_predice_maximos_aunque_su_f1_sea_cero():
    """Lo que desmiente "el puente nunca produce un maximo estricto".

    El F1 de maximos es cero y aun asi el modelo predice maximos: el cero viene de donde
    caen, no de que falten. Si algun dia dejara de predecirlos, la explicacion original
    volveria a ser posible y esta prueba avisa.
    """
    it = _medido()["por_modelo"]["itransformer"]
    assert it["f1_maximo_coincide_con_la_publicada"] == 0.0
    assert it["maximos"]["predichos"] > 0, (
        "el iTransformer ya no predice ningun maximo. Si es asi, 'el puente no los produce' "
        "vuelve a ser una lectura posible y el texto que la descarta hay que revisarlo."
    )
    assert it["maximos"]["aciertos_exactos"] == 0


@necesita_evidencia
def test_el_puente_produce_extremos_estrictos_de_las_dos_clases():
    """Maximos y minimos exigen las mismas catorce desigualdades estrictas.

    Si el iTransformer produce extremos de las dos clases, la suavidad de la trayectoria
    no puede ser lo que le impide producir maximos.
    """
    it = _medido()["por_modelo"]["itransformer"]
    assert it["maximos"]["predichos"] > 0
    assert it["minimos"]["predichos"] > 0


@necesita_evidencia
def test_hay_pocos_extremos_reales_por_clase():
    """Con tan pocos extremos reales, 0 aciertos y 2 aciertos no se distinguen.

    Es lo que vuelve insostenible leer "cero, no poco" como una senal: la diferencia es
    de un par de velas sobre una clase con poco mas de una decena de casos.
    """
    it = _medido()["por_modelo"]["itransformer"]
    assert it["maximos"]["reales"] < 30
    assert it["minimos"]["reales"] < 30
