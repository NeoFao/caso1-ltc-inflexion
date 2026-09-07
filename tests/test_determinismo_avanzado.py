"""Que la afirmacion medida que acota la D25 siga siendo cierta.

La D25 decide que la condicion 2 de la D16 no decide donde entre el iTransformer, y
ese alcance descansa en una afirmacion: **que ese modelo no se puede volver
reproducible entre procesos con las palancas habituales**. Si eso dejara de ser
cierto --otra version de torch, otra maquina-- el alcance de la D25 sobraria y
habria que rehacerlo.

Es la contraparte de `test_reproducibilidad.py`, que fija lo contrario sobre el
bosque y el azar. Las dos juntas son las que sostienen que el problema esta acotado
y que la regla de la seccion 5 del protocolo no esta afectada.

Solo lee la constancia. No entrena nada, asi que corre en CI sin el grupo `modelos`.
Volver a medirla es `uv run python -m src.modelos.determinismo_avanzado`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
EVIDENCIA = RAIZ / "docs" / "evidencias" / "m3-determinismo-avanzado.json"
DECISIONES = RAIZ / "docs" / "DECISIONES.md"

necesita_evidencia = pytest.mark.skipif(
    not EVIDENCIA.exists(), reason="todavia no se midio el determinismo del avanzado"
)


def _medido() -> dict:
    return json.loads(EVIDENCIA.read_text(encoding="utf-8"))


@necesita_evidencia
def test_las_tres_palancas_estan_medidas():
    """Si una desaparece, la D25 estaria citando una comprobacion que ya no se hace.

    Las tres no son decorativas: cada una cierra una causa distinta --hilos, orden de
    iteracion, semilla-- y descartarlas de a una es lo que vuelve la conclusion algo
    mas que "probamos y no salio".
    """
    palancas = _medido()["por_palanca"]
    faltan = {"semilla_sola", "hilos_y_algoritmos", "hash_fijo"} - set(palancas)
    assert not faltan, f"la evidencia de la D25 ya no mide {sorted(faltan)}"


@necesita_evidencia
def test_ninguna_palanca_vuelve_reproducible_al_avanzado():
    """El alcance de la D25 depende de esto.

    Si alguna pasara a reproducir, la via de hacer reproducible el avanzado estaria
    abierta y la condicion 2 podria volver a decidir en sus contrastes. Eso no se
    arregla editando el documento: hay que rehacer la decision.
    """
    medido = _medido()
    reproducen = [
        nombre
        for nombre, r in medido["por_palanca"].items()
        if r["reproduce_entre_procesos"]
    ]
    assert not reproducen, (
        f"{reproducen} ahora reproduce entre procesos. La D25 acota la condicion 2 "
        "porque esta via estaba cerrada; si se abrio, el alcance de esa decision hay "
        "que rehacerlo, no ajustarlo."
    )
    assert medido["veredicto"]["alguna_reproduce"] is False


@necesita_evidencia
def test_cada_palanca_se_midio_en_mas_de_un_proceso():
    """Medirlo dentro de un solo proceso daria estable siempre y no diria nada.

    La variabilidad que se investiga es justamente la que aparece ENTRE procesos, asi
    que una corrida por palanca convertiria esta evidencia en una que no puede fallar.
    """
    for nombre, r in _medido()["por_palanca"].items():
        assert r["corridas"] >= 2, f"{nombre} se midio con una sola corrida"
        assert len(r["perdidas"]) == r["corridas"]


@necesita_evidencia
def test_la_d25_cita_esta_evidencia():
    """La decision y su respaldo no pueden separarse: es lo que fallo antes, cuando la
    D24 apuntaba a un archivo que no tenia la cifra."""
    assert EVIDENCIA.name in DECISIONES.read_text(encoding="utf-8"), (
        f"la D25 afirma que esta via esta cerrada y no cita {EVIDENCIA.name}. "
        "Una afirmacion medida sin puntero a su constancia se lee igual que una "
        "supuesta."
    )
