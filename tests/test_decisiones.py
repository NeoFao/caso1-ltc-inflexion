"""Fija las decisiones del equipo que se pueden romper en silencio.

Un documento que nadie lee no cambia lo que hace la gente. Estas pruebas existen
para que las decisiones de docs/DECISIONES.md no dependan de que alguien las
recuerde: si se cambia un valor acordado sin pasar por el documento, falla el CI y
el PR no entra limpio.

No pretenden cubrir todas las decisiones. Solo las que son un valor concreto en el
codigo y que, cambiadas por descuido, producirian resultados que parecen correctos
y no lo son. Las decisiones de proceso —fusionar con squash, no regenerar la
evidencia de una entrega hecha— no se pueden fijar asi y viven solo en el
documento.

Si una decision cambia de verdad: se anade la fila nueva en DECISIONES.md, se
marca la anterior como reemplazada, y recien entonces se actualiza esta prueba.
Ese orden es el punto.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from contracts.config import (
    ACTIVO_OBJETIVO,
    ACTIVOS,
    DELTA_F1_DECISIVO,
    GRANULARIDAD,
    HORIZONTE_H,
    MINIMO_EJEMPLOS_CLASE_MINORITARIA,
    PROVISIONAL,
    VENTANA_W,
)

RAIZ = Path(__file__).resolve().parents[1]
DECISIONES = RAIZ / "docs" / "DECISIONES.md"


def _texto() -> str:
    return DECISIONES.read_text(encoding="utf-8")


def test_el_documento_de_decisiones_existe():
    """Sin el, el resto de las pruebas fijaria valores sin razon escrita al lado."""
    assert DECISIONES.exists(), (
        "falta docs/DECISIONES.md. Es la unica fuente de verdad sobre que decidio el "
        "equipo; estas pruebas no tienen sentido sin el."
    )


@pytest.mark.parametrize("identificador", [f"D{n}" for n in range(1, 15)])
def test_cada_decision_fijada_tiene_su_fila(identificador: str):
    """El documento y las pruebas no pueden separarse.

    Si alguien borra una decision del documento pero deja la prueba, o al reves,
    quedaria una restriccion en el codigo sin razon escrita, que es justo lo que
    este archivo trata de evitar.
    """
    assert re.search(rf"^## {identificador} · ", _texto(), re.M), (
        f"{identificador} esta fijada por una prueba pero no aparece en "
        f"docs/DECISIONES.md. Una restriccion sin razon escrita al lado se vuelve "
        f"folclore: nadie sabe si se puede tocar."
    )


def test_d1_granularidad_de_cuatro_horas():
    """D1. Con velas diarias ninguna combinacion alcanza el piso de 300 ejemplos."""
    assert GRANULARIDAD == "4h", (
        "D1 fija velas de 4 horas. Con diarias la mejor combinacion deja 149 ejemplos "
        "de la clase minoritaria, la mitad del piso acordado. Si de verdad cambia, "
        "primero se actualiza docs/DECISIONES.md."
    )


def test_d2_ventana_siete():
    """D2. El w mas grande que cumple el piso; w=10 quedo en 299."""
    assert VENTANA_W == 7, (
        "D2 fija w = 7 por ser el mayor que cumple el piso de 300. Cambiarlo altera "
        "las etiquetas, y con ellas todo lo que se haya medido sobre ellas."
    )


def test_d3_horizonte_uno():
    """D3. La informacion mutua cae 4,2 veces de h=1 a h=3 y despues se aplana."""
    assert HORIZONTE_H == 1, (
        "D3 fija h = 1 por medicion de informacion mutua, corrigiendo una propuesta "
        "previa de h = 5 hecha por juicio. Volver a subirlo sin evidencia nueva "
        "repetiria el error que esa decision corrigio."
    )


def test_el_contrato_dejo_de_ser_provisional():
    """D1, D2 y D3 se congelaron juntas: la marca no puede volver sola."""
    assert PROVISIONAL is False, (
        "el contrato se congelo el 18/08/2026. Si vuelve a marcarse PROVISIONAL, "
        "ningun resultado medido despues es citable como definitivo, y eso tiene que "
        "ser una decision consciente y no un efecto secundario."
    )


def test_d4_piso_de_la_clase_minoritaria():
    """D4. Es una propuesta del equipo, no un umbral de la literatura."""
    assert MINIMO_EJEMPLOS_CLASE_MINORITARIA == 300, (
        "D4 fija el piso en 300. No sale de la literatura: existe para que la eleccion "
        "de granularidad y ventana tuviera un criterio explicito antes de medir."
    )


def test_d5_umbral_de_decision_entre_modelos():
    """D5. Convencion acordada de antemano, no un contraste estadistico."""
    assert DELTA_F1_DECISIVO == 0.02, (
        "D5 fija el margen minimo en 0,02. Es una convencion del equipo fijada antes "
        "de medir; bajarlo despues de ver un resultado seria elegir el criterio "
        "conociendo el desenlace."
    )


def test_d5_declara_que_el_umbral_no_es_una_prueba_estadistica():
    """La distincion importa mas que el valor, y se pierde con facilidad."""
    texto = _texto()
    assert "no un contraste estadístico" in texto, (
        "docs/DECISIONES.md tiene que seguir declarando que DELTA_F1_DECISIVO es una "
        "convencion y no un contraste. Sin esa frase, el umbral se lee como si fuera "
        "una prueba de significancia, que es exactamente lo que no es."
    )


def test_d8_los_seis_activos_y_el_objetivo():
    """D8. El enunciado los fija; cambiarlos cambia el problema."""
    assert ACTIVO_OBJETIVO == "LTC"
    assert set(ACTIVOS) == {"LTC", "BTC", "ETH", "SOL", "XRP", "ADA"}, (
        "D8. Los seis activos los fija el enunciado. Anadir o quitar uno cambia el "
        "problema que nos pusieron, no la implementacion."
    )


def test_las_tres_reglas_del_proyecto_siguen_escritas():
    """Son la conclusion del incidente de atribuciones del PR #60.

    Se fijan porque son lo que evita que se repita, y porque una leccion que se
    borra del documento se pierde con la persona que la aprendio.
    """
    texto = _texto()
    for fragmento in (
        "reproducir uno conocido antes de publicarse",
        "señalar dónde se acordó",
        "nunca\n   en un mensaje suelto",
    ):
        assert fragmento in texto, (
            f"falta en docs/DECISIONES.md la regla que contiene: {fragmento!r}. "
            f"Las tres salieron de un incidente real y estan para que no se repita."
        )
