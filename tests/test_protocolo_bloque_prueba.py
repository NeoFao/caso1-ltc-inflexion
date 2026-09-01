"""Que la tabla que gobierna la corrida final siga diciendo lo que la evidencia mide.

La seccion 3 del protocolo (D18) declara **una configuracion por familia y su F1 macro
en validacion**, congeladas antes de tocar la reserva. Esas tres cifras no son
decorativas: son la referencia contra la que se va a leer el resultado sobre prueba, y
la seccion 4 manda comparar validacion contra prueba para cada modelo.

Hoy nada comprueba que sigan siendo las medidas. Si M3 remide, si alguien corrige una
celda a mano, o si una evidencia se regenera con otro valor, el protocolo sigue
diciendo lo de antes: el documento se lee bien, las pruebas pasan, y la comparacion
final parte de una cifra que ya no describe nada. Es la misma forma del defecto de la
marca de tiempo y del panel de la aplicacion -- algo dejo de estar sincronizado, no
fallo de manera visible, y siguio pareciendo correcto desde afuera.

El caso ya ocurrio una vez, en este mismo documento
-----------------------------------------------------
La fila del clasico decia 0,3905, que es la corrida de la semilla 0 y resulta ser la
mas alta de las cinco. La media es 0,380975. Lo corrigio el commit 79d145b despues de
que se midiera la media en el #85, pero **nada impide que vuelva a pasar**: quien
edite la tabla no tiene forma de saber que ese numero no es el que corresponde.

Por que se comprueba la CADENA del documento y no un valor calculado
---------------------------------------------------------------------
Porque lo que hay que vigilar es lo que el documento dice, no lo que nosotros
creemos que dice. La prueba lee la tabla de la seccion 3 tal cual esta escrita, saca
la cifra de cada fila, y exige que coincida con la evidencia que la respalda al
redondeo con que se publico.

Solo lee. No toca el documento ni la evidencia.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
PROTOCOLO = RAIZ / "docs" / "09-protocolo-bloque-prueba.md"
EVIDENCIAS = RAIZ / "docs" / "evidencias"

#: De donde sale la cifra de cada familia. La ruta es literal dentro del JSON para que
#: el fallo diga exactamente que archivo mirar, en vez de "algo no cuadra".
#:
#: El clasico y el avanzado se entrenan, asi que declaran la MEDIA de cinco semillas
#: (D16). El fundacional es zero-shot y no muestrea: su unica corrida es su valor.
DECLARADAS = {
    "Clásico": (
        "m2-incertidumbre-vigente-4h-w7-h1.json",
        ("sensibilidad_a_la_semilla", "f1_por_modelo",
         "bosque_aleatorio_rezagos_relativos", "media"),
    ),
    "Fundacional": (
        "m3-hiperparametros-fundacional-4h-w7-h1.json",
        ("por_defecto", "f1_macro"),
    ),
    "Avanzado": (
        "m3-sensibilidad-avanzado-4h-w7-h1.json",
        ("resumen_f1_completo", "media"),
    ),
}

necesita_protocolo = pytest.mark.skipif(
    not PROTOCOLO.exists(), reason="el protocolo del bloque de prueba todavia no existe"
)


def _valor(archivo: str, ruta: tuple[str, ...]) -> float:
    nodo = json.loads((EVIDENCIAS / archivo).read_text(encoding="utf-8"))
    for clave in ruta:
        nodo = nodo[clave]
    return float(nodo)


def _filas_declaradas() -> dict[str, str]:
    """La cifra escrita en cada fila de la tabla de la seccion 3, tal cual.

    Se toma el primer numero con coma decimal de la fila, que es la columna del F1
    macro. Lo que venga entre parentesis despues --"(media de cinco semillas)"-- es
    prosa y no se compara aqui.
    """
    texto = PROTOCOLO.read_text(encoding="utf-8")
    filas: dict[str, str] = {}
    for familia in DECLARADAS:
        patron = rf"^\|\s*{familia}\s*\|.*?\|\s*(\d+,\d+)"
        encontrado = re.search(patron, texto, re.MULTILINE)
        if encontrado:
            filas[familia] = encontrado.group(1)
    return filas


@necesita_protocolo
def test_la_tabla_del_protocolo_declara_las_tres_familias():
    """Si una fila desaparece o cambia de nombre, la comprobacion de abajo no protege nada.

    Sin esto, borrar una fila haria pasar la prueba en vez de fallarla, que es la forma
    mas facil de que un control deje de controlar sin que nadie se entere.
    """
    filas = _filas_declaradas()
    faltan = sorted(set(DECLARADAS) - set(filas))
    assert not faltan, (
        f"la seccion 3 del protocolo ya no declara una cifra para {faltan}. "
        "O se renombro la familia, o la fila se borro: las dos cosas dejan la corrida "
        "final sin referencia de validacion."
    )


@necesita_protocolo
@pytest.mark.parametrize("familia", sorted(DECLARADAS))
def test_la_cifra_declarada_sigue_siendo_la_medida(familia: str):
    """Cada cifra de la tabla tiene que ser la de su evidencia, al redondeo publicado."""
    escrita = _filas_declaradas().get(familia)
    if escrita is None:
        pytest.skip("la fila no esta; lo reporta la otra prueba")

    archivo, ruta = DECLARADAS[familia]
    medido = _valor(archivo, ruta)
    decimales = len(escrita.split(",")[1])
    esperada = f"{round(medido, decimales):.{decimales}f}".replace(".", ",")

    assert escrita == esperada, (
        f"el protocolo declara {escrita} para {familia} y la evidencia mide {esperada} "
        f"({medido!r}, en {archivo} → {'.'.join(ruta)}). "
        "La seccion 4 compara validacion contra prueba con esta cifra, asi que una "
        "referencia desactualizada mueve la caida final sin que nada falle."
    )


@necesita_protocolo
def test_las_dos_familias_que_se_entrenan_declaran_su_media_y_no_una_corrida():
    """La D18 exige que las tres cifras sean comparables entre si.

    El clasico y el avanzado se entrenan, asi que su cifra tiene que ser la media de
    cinco semillas y no una corrida. La prueba lo comprueba **contra el maximo**: si la
    tabla trajera el maximo de las cinco, seria exactamente el error que el commit
    79d145b corrigio, y volveria a exagerar la caida validacion → prueba.
    """
    filas = _filas_declaradas()
    for familia, (archivo, ruta) in DECLARADAS.items():
        if ruta[-1] != "media" or familia not in filas:
            continue
        maximo = _valor(archivo, (*ruta[:-1], "maximo"))
        decimales = len(filas[familia].split(",")[1])
        como_maximo = f"{round(maximo, decimales):.{decimales}f}".replace(".", ",")
        assert filas[familia] != como_maximo, (
            f"{familia} declara {filas[familia]}, que es el MAXIMO de sus cinco "
            f"semillas y no la media. Partir del maximo exagera la caida contra "
            f"prueba sin que nada falle: es el error que corrigio 79d145b."
        )
