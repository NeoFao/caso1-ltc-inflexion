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
from src.evaluacion.reserva import SESION, ReservaYaConsumida, consumir, esta_consumida


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

    Las dos sesiones se declaran explicitamente porque la unidad del pestillo es la
    SESION y no el modelo: sin eso, esta prueba estaria midiendo dos modelos de una
    misma corrida, que es justamente lo que ahora tiene que estar permitido. Antes
    pasaba por la razon equivocada (#100).
    """
    ruta = tmp_path / "prueba-consumida.json"
    consumir(["bosque_aleatorio"], ruta=ruta, sesion="proceso-del-sabado")

    with pytest.raises(ReservaYaConsumida) as fallo:
        consumir(["chronos_bolt"], ruta=ruta, sesion="otro-proceso-del-domingo")

    mensaje = str(fallo.value)
    assert "ya se midio" in mensaje
    assert "bosque_aleatorio" in mensaje, "el mensaje tiene que decir que se midio antes"
    assert "motivo" in mensaje, "y como repetirla si de verdad hace falta"


def test_una_corrida_de_varios_modelos_es_UNA_sola_medicion(tmp_path):
    """El defecto del #100, reproducido: la corrida del sabado moria en el modelo 2.

    `evaluar_modelo` llama al pestillo una vez por modelo, y el guion evalua una
    LISTA de modelos en un bucle. Con la unidad puesta en el modelo, el primero
    dejaba la constancia y el segundo la encontraba puesta y reventaba -- con el
    archivo ya escrito, asi que a partir de ahi cualquier arreglo obligaba a declarar
    un motivo y el registro diria para siempre que la reserva se toco dos veces.

    La seccion 8 del protocolo pide "los modelos evaluados", en plural y en una sola
    corrida. Esta prueba fija esa lectura.
    """
    ruta = tmp_path / "prueba-consumida.json"
    modelos = [
        "baseline_trivial",
        "baseline_mayoritario",
        "baseline_aleatorio",
        "bosque_aleatorio_rezagos_relativos",
        "chronos_bolt",
        "itransformer",
    ]
    for nombre in modelos:  # tal cual el bucle de experimento.py
        consumir([nombre], ruta=ruta, sesion="la-corrida-del-sabado")

    registro = json.loads(ruta.read_text(encoding="utf-8"))
    assert registro["n_corridas"] == 1, (
        "seis modelos en una corrida son UNA medicion, no seis. Si esto da 6, el "
        "informe tendria que declarar que la reserva se toco seis veces."
    )
    assert registro["corridas"][0]["modelos"] == sorted(modelos), (
        "el registro tiene que decir QUE modelos se midieron, que es lo que la "
        "seccion 8 del protocolo pide y lo que hace auditable la corrida."
    )


def test_el_registro_se_escribe_aunque_la_corrida_muera_a_la_mitad(tmp_path):
    """Una corrida que revienta en el modelo 3 igual toco la reserva.

    Si el pestillo se escribiera al final de la sesion, un fallo a mitad de camino
    dejaria la reserva gastada y el archivo sin escribir: el informe podria decir de
    buena fe que nunca se toco. Se escribe en cada llamada por esto.
    """
    ruta = tmp_path / "prueba-consumida.json"
    consumir(["baseline_trivial"], ruta=ruta, sesion="corrida-que-va-a-morir")
    consumir(["baseline_mayoritario"], ruta=ruta, sesion="corrida-que-va-a-morir")
    # aqui revienta el guion, antes de llegar a los otros cuatro

    registro = json.loads(ruta.read_text(encoding="utf-8"))
    assert registro["corridas"][0]["modelos"] == ["baseline_mayoritario", "baseline_trivial"]

    # Y la corrida siguiente sigue exigiendo motivo, porque la reserva SI se toco.
    with pytest.raises(ReservaYaConsumida):
        consumir(["baseline_trivial"], ruta=ruta, sesion="el-reintento")


def test_con_motivo_se_permite_y_se_acumula(tmp_path):
    """El historial se acumula, no se reemplaza.

    Guardar solo la ultima corrida haria que repetir la medicion borrara la
    evidencia de que se repitio, que es justo lo que hay que poder ver.
    """
    ruta = tmp_path / "prueba-consumida.json"
    consumir(["bosque_aleatorio"], ruta=ruta, sesion="primera")
    consumir(
        ["chronos_bolt"],
        motivo="se corrigio un defecto del etiquetador",
        ruta=ruta,
        sesion="segunda",
    )

    registro = json.loads(ruta.read_text(encoding="utf-8"))
    assert registro["n_corridas"] == 2
    assert registro["corridas"][0]["motivo"] is None
    assert registro["corridas"][1]["motivo"] == "se corrigio un defecto del etiquetador"
    assert registro["corridas"][0]["modelos"] == ["bosque_aleatorio"], (
        "la primera corrida no puede cambiar: es la que el informe cita"
    )


def test_la_sesion_por_omision_queda_registrada(tmp_path):
    """Nadie pasa `sesion` en produccion: sale de SESION, una por proceso.

    Se comprueba que el campo llegue al archivo, porque es el que distingue "seis
    modelos de una corrida" de "seis corridas". Un registro sin el volveria a leerse
    con la unidad vieja.
    """
    ruta = tmp_path / "prueba-consumida.json"
    corrida = consumir(["bosque_aleatorio"], ruta=ruta)

    assert corrida["sesion"] == SESION
    assert SESION, "sin identificador de sesion no se puede saber que corrida es cual"


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
