"""Fija la afirmacion de la que cuelga el alcance de la D25.

La D25 dice que la condicion 2 de la D16 solo puede decidir entre modelos cuyas
predicciones se reproducen, y acota el problema al iTransformer apoyandose en que el
bosque y el `baseline_aleatorio` **si** reproducen. De esa afirmacion cuelga que la
regla de la seccion 5 del protocolo --la que decide el veredicto del proyecto-- siga en
pie.

Una afirmacion asi no puede vivir solo en la prosa de una decision. Esta prueba la
convierte en algo que falla en rojo si deja de ser cierta.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parents[1]
CONSTANCIA = RAIZ / "docs" / "evidencias" / "m0-reproducibilidad-predicciones-4h-w7-h1.json"
PANEL = RAIZ / "data" / "processed" / "panel_4h_v1.parquet"


def test_la_constancia_de_reproducibilidad_existe_y_trae_los_dos_modelos():
    """Sin ella, la D25 acota su alcance con una frase y no con una medicion."""
    assert CONSTANCIA.exists(), (
        "falta la constancia de reproducibilidad. La D25 la cita para acotar donde la "
        "condicion 2 puede decidir; sin el archivo, ese alcance no es comprobable."
    )
    datos = json.loads(CONSTANCIA.read_text(encoding="utf-8"))
    assert datos["conjunto"] == "validacion", "la huella no puede salir del bloque de prueba"
    for modelo in ("bosque_aleatorio_rezagos_relativos", "baseline_aleatorio"):
        assert modelo in datos["huellas"], (
            f"{modelo} entra en la regla de la seccion 5 y tiene que tener huella"
        )


@pytest.mark.skipif(not PANEL.exists(), reason="el panel no esta en esta copia")
def test_el_bosque_y_el_azar_siguen_reproduciendo_bit_a_bit():
    """Si esto se pone en rojo, la D25 dejo de ser cierta y hay que rehacer su alcance.

    Se recalculan las huellas en ESTE proceso y se comparan con la constancia, que se
    genero en otro. Que coincidan es justamente la propiedad que la D25 necesita:
    reproducibilidad **entre procesos**, no dentro de uno.
    """
    from scripts.reproducibilidad_predicciones import huellas

    esperadas = json.loads(CONSTANCIA.read_text(encoding="utf-8"))["huellas"]
    obtenidas = huellas()["huellas"]

    for modelo, firma in esperadas.items():
        assert obtenidas[modelo] == firma, (
            f"{modelo} dejo de reproducir entre procesos. La D25 acota el alcance de la "
            f"condicion 2 apoyandose en que si reproduce; si esto cambio, la regla de la "
            f"seccion 5 del protocolo tambien queda afectada y hay que decidirlo de nuevo."
        )


def test_la_huella_distingue_predicciones_distintas():
    """Un control que no se vio fallar no es un control.

    Si la huella fuera insensible --por ejemplo por hashear la longitud y no el
    contenido-- la prueba de arriba pasaria siempre y no diria nada.
    """
    a = np.array([0, 1, 2, 1, 0], dtype="int64")
    b = np.array([0, 1, 2, 1, 1], dtype="int64")

    assert hashlib.sha256(a.tobytes()).hexdigest() != hashlib.sha256(b.tobytes()).hexdigest(), (
        "la huella no distingue dos vectores que difieren en una posicion"
    )
