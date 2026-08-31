"""La primera prueba que cruza dos capas del proyecto.

Todos los controles que tenemos reproducen un numero **dentro de la misma capa**: el
bosque contra el bosque, el arnes de representaciones contra el F1 publicado, el
control de `tablas_metricas` contra lo que se entrego. Ninguno comprueba que una cifra
conocida en un extremo del sistema siga siendo la misma en el otro extremo.

Ese hueco ya nos costo un defecto real. El backend serializaba la marca de tiempo sin
la hora, con velas de 4 horas; M1 lo compenso con un filtro en su capa; cada frontera
"funcionaba" vista de a una, y el grafico perdia el 84,4 % de los giros. Nadie tenia un
control que fuera de punta a punta, asi que el defecto vivio en el hueco entre dos capas
que se probaban por separado.

Aqui esta el mismo riesgo, vivo y sin vigilar
----------------------------------------------
`app/scripts/generar_comparacion.py` copia metricas de `docs/evidencias/` al panel de
la aplicacion. Su propio docstring lo dice: *"Si M3 remide y el JSON de origen cambia,
correr este script de nuevo actualiza el panel"*.

**Correr el script de nuevo es un paso manual.** Si M3 remide y nadie se acuerda, el
panel sigue mostrando las cifras viejas, la aplicacion funciona, las pruebas pasan y
nada avisa. Es la misma forma exacta del defecto anterior: algo dejo de estar
sincronizado, no fallo de manera visible, y siguio pareciendo correcto desde afuera.

Por que se compara regenerando y no releyendo
----------------------------------------------
La comprobacion no reimplementa la logica del generador: **importa el generador y lo
ejecuta** contra un destino temporal. Reimplementarla crearia una segunda fuente de
verdad que puede separarse de la primera, que es el defecto que estas pruebas existen
para impedir.

Solo lee. No modifica el panel ni la evidencia.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
GENERADOR = RAIZ / "app" / "scripts" / "generar_comparacion.py"
PANEL = RAIZ / "app" / "public" / "datos" / "comparacion-modelos.json"

necesita_panel = pytest.mark.skipif(
    not (GENERADOR.exists() and PANEL.exists()),
    reason="la aplicacion todavia no publica el panel de comparacion",
)


def _cargar_generador():
    """Importa el guion de M1 por ruta: no es un paquete y no tiene __init__."""
    especificacion = importlib.util.spec_from_file_location("generar_comparacion", GENERADOR)
    modulo = importlib.util.module_from_spec(especificacion)
    sys.modules["generar_comparacion"] = modulo
    especificacion.loader.exec_module(modulo)
    return modulo


@necesita_panel
def test_el_panel_de_la_app_esta_al_dia_con_la_evidencia(monkeypatch):
    """Regenerar el panel tiene que dar exactamente el archivo que esta versionado.

    Falla en los dos casos que importan, y ninguno de los dos falla hoy por otra via:

    - alguien remidio la evidencia y no volvio a correr el generador, o
    - alguien edito una cifra del panel a mano.
    """
    generador = _cargar_generador()
    if not generador.ORIGEN.exists():
        pytest.skip("falta la evidencia de M3 que alimenta el panel")

    # El destino va DENTRO del repositorio a proposito: el generador imprime
    # `DESTINO.relative_to(RAIZ)` al terminar, y una ruta de fuera revienta ahi. Se
    # borra siempre, y no se parchea RAIZ porque el campo `fuente` del panel se
    # calcula con ella y quedaria distinto del versionado por culpa de la prueba.
    destino = RAIZ / ".comparacion-regenerada-por-la-prueba.json"
    monkeypatch.setattr(generador, "DESTINO", destino)
    try:
        generador.main()
        regenerado = json.loads(destino.read_text(encoding="utf-8"))
    finally:
        destino.unlink(missing_ok=True)

    versionado = json.loads(PANEL.read_text(encoding="utf-8"))

    assert regenerado == versionado, (
        "El panel de la aplicacion no coincide con la evidencia que dice citar. "
        "O se remidio y no se regenero el panel, o se edito una cifra a mano. "
        "Correr: uv run python app/scripts/generar_comparacion.py"
    )


@necesita_panel
def test_el_panel_declara_de_donde_salio_y_ese_archivo_existe():
    """Una cifra sin procedencia comprobable no es evidencia."""
    panel = json.loads(PANEL.read_text(encoding="utf-8"))
    fuente = RAIZ / panel["fuente"]
    assert fuente.exists(), (
        f"el panel dice venir de {panel['fuente']!r} y ese archivo no existe"
    )


@necesita_panel
def test_el_panel_no_muestra_cifras_del_bloque_de_prueba():
    """La reserva no se muestra en ningun lado hasta que se decida tocarla.

    Es facil que una cifra de prueba llegue al panel sin que nadie lo note, porque el
    panel copia lo que le den. Mientras el conjunto declarado sea validacion, esto
    tambien documenta en el codigo que la reserva sigue sin usarse.
    """
    panel = json.loads(PANEL.read_text(encoding="utf-8"))
    assert panel["particion"]["conjunto"] == "validacion", (
        "el panel esta mostrando cifras de un conjunto distinto de validacion: "
        f"{panel['particion']['conjunto']!r}. Si es prueba, tiene que haber una "
        "decision escrita que lo autorice."
    )


@necesita_panel
def test_los_parametros_del_panel_son_los_del_contrato():
    """Si el panel dijera otra granularidad o ventana, estaria describiendo otro modelo."""
    from contracts.config import GRANULARIDAD, HORIZONTE_H, VENTANA_W

    panel = json.loads(PANEL.read_text(encoding="utf-8"))["particion"]
    assert panel["intervalo"] == GRANULARIDAD
    assert panel["w"] == VENTANA_W
    assert panel["h"] == HORIZONTE_H


# ---------------------------------------------------------------- historico
# El panel de comparacion no era el unico artefacto precalculado. El PR #79 anadio
# un segundo -- la serie historica con el fundacional ya aplicado -- que se genera
# aparte y se versiona igual. La guarda de arriba no lo cubria, asi que el hueco que
# esta prueba existe para cerrar quedaba reabierto un PR despues.
#
# Aqui la comparacion es contra la evidencia REDONDEADA a cuatro decimales, porque
# ese archivo publica cifras para mostrar y no para recalcular. Lo que se exige no es
# precision completa: es que sigan siendo las mismas cifras.
HISTORICO = RAIZ / "app" / "public" / "datos" / "historico-fundacional-LTC.json"
EVIDENCIA_PROFUNDOS = RAIZ / "docs" / "evidencias" / "m3-modelos-profundos-4h-w7-h1.json"

necesita_historico = pytest.mark.skipif(
    not (HISTORICO.exists() and EVIDENCIA_PROFUNDOS.exists()),
    reason="la aplicacion todavia no publica el historico con el fundacional",
)


@necesita_historico
def test_el_historico_precalculado_cita_las_metricas_de_la_evidencia():
    """Las metricas que muestra la vista historica son las que midio M3.

    Si M3 remide y nadie regenera este archivo, la aplicacion sigue mostrando cifras
    viejas: funciona, las pruebas de su capa pasan, y nada avisa. Es exactamente la
    forma del defecto de la marca de tiempo.
    """
    publicado = json.loads(HISTORICO.read_text(encoding="utf-8"))
    medido = json.loads(EVIDENCIA_PROFUNDOS.read_text(encoding="utf-8"))["metricas"]

    modelo = publicado["modelo"]
    assert modelo in medido, (
        f"el historico publica el modelo {modelo!r}, que no existe en la evidencia de M3"
    )

    discrepan = {
        clave: (valor, medido[modelo][clave])
        for clave, valor in publicado["metricas"].items()
        if clave != "n" and clave in medido[modelo]
        and round(medido[modelo][clave], 4) != valor
    }
    assert not discrepan, (
        f"el historico de la app y la evidencia de M3 discrepan en {sorted(discrepan)}: "
        f"{discrepan}. Hay que regenerarlo con app/scripts/generar_historico_fundacional.py."
    )


@necesita_historico
def test_el_historico_no_muestra_cifras_del_bloque_de_prueba():
    """La misma guarda que para el panel: la reserva no llega a la vista sin decision."""
    publicado = json.loads(HISTORICO.read_text(encoding="utf-8"))
    n_publicado = publicado["metricas"]["n"]
    medido = json.loads(EVIDENCIA_PROFUNDOS.read_text(encoding="utf-8"))
    n_validacion = medido["parametros"].get("n_validacion") or len(publicado["serie"])
    assert n_publicado == n_validacion, (
        f"el historico reporta {n_publicado} observaciones y validacion tiene "
        f"{n_validacion}. Si esta mostrando otro conjunto, tiene que haber una "
        "decision escrita que lo autorice (D18)."
    )
