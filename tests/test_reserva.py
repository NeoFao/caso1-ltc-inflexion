"""Pruebas del pestillo del bloque de prueba (D18).

Ninguna toca `docs/evidencias/prueba-consumida.json`: todas inyectan una ruta
temporal. Una prueba que gastara la reserva de verdad para comprobar que la reserva
no se gasta seria un chiste malo, y ademas dejaria el archivo escrito en el
repositorio de quien corriera la suite.
"""

from __future__ import annotations

import inspect
import json

import pytest

from src.evaluacion.arnes import evaluar_modelo
from src.evaluacion.reserva import ReservaYaConsumida, consumir, esta_consumida


def test_la_primera_corrida_deja_constancia(tmp_path):
    ruta = tmp_path / "prueba-consumida.json"
    assert not esta_consumida(ruta)

    corrida = consumir(["bosque_aleatorio"], ruta=ruta)

    assert esta_consumida(ruta)
    assert corrida["modelos"] == ["bosque_aleatorio"]
    registro = json.loads(ruta.read_text(encoding="utf-8"))
    assert registro["n_corridas"] == 1


def test_la_segunda_corrida_sin_motivo_falla(tmp_path):
    """La que da sentido al pestillo.

    Si repetir la medicion fuera tan facil como repetirla, el archivo seria un
    registro y no una guarda.
    """
    ruta = tmp_path / "prueba-consumida.json"
    consumir(["bosque_aleatorio"], ruta=ruta)

    with pytest.raises(ReservaYaConsumida) as fallo:
        consumir(["chronos_bolt"], ruta=ruta)

    mensaje = str(fallo.value)
    assert "ya se midio" in mensaje
    assert "bosque_aleatorio" in mensaje, "el mensaje tiene que decir que se midio antes"
    assert "motivo" in mensaje, "y como repetirla si de verdad hace falta"


def test_con_motivo_se_permite_y_se_acumula(tmp_path):
    """El historial se acumula, no se reemplaza.

    Guardar solo la ultima corrida haria que repetir la medicion borrara la
    evidencia de que se repitio, que es justo lo que hay que poder ver.
    """
    ruta = tmp_path / "prueba-consumida.json"
    consumir(["bosque_aleatorio"], ruta=ruta)
    consumir(["chronos_bolt"], motivo="se corrigio un defecto del etiquetador", ruta=ruta)

    registro = json.loads(ruta.read_text(encoding="utf-8"))
    assert registro["n_corridas"] == 2
    assert registro["corridas"][0]["motivo"] is None
    assert registro["corridas"][1]["motivo"] == "se corrigio un defecto del etiquetador"
    assert registro["corridas"][0]["modelos"] == ["bosque_aleatorio"], (
        "la primera corrida no puede cambiar: es la que el informe cita"
    )


def test_se_registra_el_commit_y_si_el_arbol_estaba_limpio(tmp_path):
    """Una cifra medida sobre un arbol sucio no es reproducible desde su commit."""
    ruta = tmp_path / "prueba-consumida.json"
    corrida = consumir(["bosque_aleatorio"], ruta=ruta)

    assert corrida["commit"], "sin commit, la cifra del informe no se puede reproducir"
    assert "arbol_limpio" in corrida


def test_el_conjunto_es_obligatorio_y_solo_por_nombre():
    """Antes tenia "prueba" por omision: la reserva era lo que salia sin decir nada.

    Se comprueba por introspeccion y no llamando a la funcion, porque el valor de
    esta prueba es vigilar la FIRMA. Volver a ponerle un default seria facil y
    silencioso, que es como llegamos aca.
    """
    parametro = inspect.signature(evaluar_modelo).parameters["conjunto"]
    assert parametro.default is inspect.Parameter.empty, (
        "`conjunto` volvio a tener valor por omision. Si ese valor es 'prueba', la "
        "reserva se gasta sin que nadie lo pida."
    )
    assert parametro.kind is inspect.Parameter.KEYWORD_ONLY, (
        "`conjunto` tiene que ir por nombre: pasarlo por posicion lo vuelve facil de "
        "confundir con `particion`."
    )
