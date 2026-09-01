"""Comprueba que el sitio desplegado sirva las mismas cifras que la evidencia (issue #88).

Por que existe: tests/test_coherencia_entre_capas.py comprueba los artefactos del
REPOSITORIO. Nada comprobaba lo que esta SERVIDO en produccion. Si un build de
GitHub Pages falla, o falla a medias, el sitio sigue mostrando la version
anterior sin que nada avise: la app funciona, las pruebas pasan, el repositorio
esta sincronizado, y el sitio muestra cifras viejas. Es el unico artefacto del
proyecto que ve alguien de fuera.

Por que NO es parte de `uv run pytest`: depende de la red y de que el
despliegue de Pages ya haya terminado. Una prueba que puede fallar sin que el
codigo tenga nada malo se acaba desactivando a la semana. Este script se corre
a mano, o como paso aparte del workflow de Pages, despues de publicar -- nunca
dentro de la suite. La logica de comparacion si esta cubierta por
tests/test_verificar_produccion.py, con la respuesta de red simulada.

Uso:
    uv run python app/scripts/verificar_produccion.py
    uv run python app/scripts/verificar_produccion.py --sitio https://otra-url/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[2]
EVIDENCIA_M3 = RAIZ / "docs" / "evidencias" / "m3-modelos-profundos-4h-w7-h1.json"
SITIO_POR_DEFECTO = "https://neofao.github.io/caso1-ltc-inflexion/"
# Las cifras servidas vienen redondeadas a 4 decimales al generarse; la
# tolerancia cubre ese redondeo y nada mas.
TOLERANCIA = 0.0005

CAMPOS = (
    "f1_macro",
    "precision_direccional",
    "exactitud",
    "f1_maximo",
    "f1_minimo",
    "f1_continuidad",
)


def _traer_json(url: str) -> dict:
    respuesta = requests.get(url, timeout=15)
    respuesta.raise_for_status()
    return respuesta.json()


def _cargar_evidencia() -> dict:
    if not EVIDENCIA_M3.exists():
        raise FileNotFoundError(f"falta {EVIDENCIA_M3.relative_to(RAIZ)}")
    return json.loads(EVIDENCIA_M3.read_text(encoding="utf-8"))["metricas"]


def verificar_comparacion(servido: dict, evidencia: dict) -> list[str]:
    """Los 4 modelos x 6 metricas de comparacion-modelos.json contra la evidencia de M3."""
    discrepancias = []
    for modelo in servido["modelos"]:
        clave = modelo["clave"]
        if clave not in evidencia:
            discrepancias.append(
                f"comparacion-modelos.json: modelo {clave!r} servido no esta en la evidencia"
            )
            continue
        conocido = evidencia[clave]
        for campo in CAMPOS:
            propio, esperado = modelo[campo], conocido[campo]
            if abs(propio - esperado) > TOLERANCIA:
                discrepancias.append(
                    f"comparacion-modelos.json: {clave}.{campo} = {propio} "
                    f"(evidencia: {esperado})"
                )
    return discrepancias


def verificar_historico_fundacional(servido: dict, evidencia: dict) -> list[str]:
    """Metricas y tamano de historico-fundacional-LTC.json contra chronos_bolt en la evidencia."""
    if "chronos_bolt" not in evidencia:
        return ["historico-fundacional-LTC.json: 'chronos_bolt' no esta en la evidencia"]
    conocido = evidencia["chronos_bolt"]

    discrepancias = []
    for campo in CAMPOS:
        propio, esperado = servido["metricas"][campo], conocido[campo]
        if abs(propio - esperado) > TOLERANCIA:
            discrepancias.append(
                f"historico-fundacional-LTC.json: metricas.{campo} = {propio} "
                f"(evidencia: {esperado})"
            )

    n_servido, n_evidencia = len(servido["serie"]), conocido["n"]
    if n_servido != n_evidencia:
        discrepancias.append(
            f"historico-fundacional-LTC.json: {n_servido} velas servidas, "
            f"la evidencia mide n={n_evidencia}"
        )
    return discrepancias


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--sitio", default=SITIO_POR_DEFECTO, help="raiz del sitio desplegado")
    args = parser.parse_args()
    sitio = args.sitio if args.sitio.endswith("/") else args.sitio + "/"

    evidencia = _cargar_evidencia()

    discrepancias: list[str] = []
    for nombre, archivo, verificacion in (
        ("comparacion-modelos.json", "comparacion-modelos.json", verificar_comparacion),
        (
            "historico-fundacional-LTC.json",
            "historico-fundacional-LTC.json",
            verificar_historico_fundacional,
        ),
    ):
        try:
            servido = _traer_json(f"{sitio}datos/{archivo}")
        except Exception as error:  # noqa: BLE001 - la red puede fallar de mil formas
            sys.exit(f"no se pudo descargar {nombre} de {sitio}: {error}")
        encontradas = verificacion(servido, evidencia)
        discrepancias += encontradas
        print(f"  {'!' if encontradas else 'ok'}  {nombre} ({len(encontradas)} discrepancia(s))")

    if discrepancias:
        ruta_evidencia = EVIDENCIA_M3.relative_to(RAIZ)
        print(f"\n{len(discrepancias)} discrepancia(s) entre {sitio} y {ruta_evidencia}:")
        for d in discrepancias:
            print(f"  ! {d}")
        sys.exit(1)
    print(f"\nTodo lo servido en {sitio} coincide con la evidencia del commit desplegado.")


if __name__ == "__main__":
    main()
