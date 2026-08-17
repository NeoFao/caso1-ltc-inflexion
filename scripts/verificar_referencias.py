"""Comprueba contra Crossref si alguna referencia esta retractada.

Existe porque nos paso: M2 encontro que Corbet, Lucey, Urquhart y Yarovaya (2019),
uno de los articulos mas citados sobre criptoactivos, figura hoy en Crossref como
retractado por Elsevier. Lo tenia citado tres veces.

Revisar 80 referencias a mano antes de la entrega final no lo va a hacer nadie.
Asi se hace en un minuto y no depende de acordarse.

Uso:
    uv run python scripts/verificar_referencias.py docs/entregas/semana-1/*.md
    uv run python scripts/verificar_referencias.py --doi 10.1016/j.irfa.2018.09.003
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

import requests

CROSSREF = "https://api.crossref.org/works"
# Correo de contacto: Crossref da mejor servicio a quien se identifica.
CABECERAS = {"User-Agent": "caso1-ltc-inflexion/1.0 (proyecto academico)"}

PATRON_DOI = re.compile(r"\b10\.\d{4,9}/[-._;()/:a-z0-9A-Z]+\b")


def _limpiar_doi(doi: str) -> str:
    """Quita la puntuacion final que arrastra un DOI citado dentro de una frase."""
    return doi.rstrip(".,;)]}")


def consultar_doi(doi: str) -> dict | None:
    respuesta = requests.get(f"{CROSSREF}/{doi}", headers=CABECERAS, timeout=30)
    if respuesta.status_code == 404:
        return None
    respuesta.raise_for_status()
    return respuesta.json()["message"]


def esta_retractado(obra: dict) -> tuple[bool, str]:
    """Crossref marca la retractacion de dos formas y hay que mirar las dos.

    El titulo puede llevar el prefijo RETRACTED, y el registro puede traer un
    bloque update-to apuntando a la nota de retractacion. Ninguna de las dos
    aparece siempre, asi que revisar solo una deja casos afuera.
    """
    titulo = (obra.get("title") or [""])[0]
    if titulo.upper().startswith("RETRACTED"):
        return True, "el titulo en Crossref empieza con RETRACTED"
    for actualizacion in obra.get("update-to") or []:
        if actualizacion.get("type") in {"retraction", "withdrawal", "removal"}:
            return True, f"Crossref registra una {actualizacion.get('type')}"
    return False, ""


def buscar_por_titulo(titulo: str) -> list[dict]:
    respuesta = requests.get(
        CROSSREF, params={"query.bibliographic": titulo, "rows": 3},
        headers=CABECERAS, timeout=30,
    )
    respuesta.raise_for_status()
    return respuesta.json()["message"]["items"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archivos", nargs="*", help="markdown con referencias")
    parser.add_argument("--doi", action="append", default=[], help="DOI suelto")
    parser.add_argument("--titulo", action="append", default=[], help="titulo a buscar")
    argumentos = parser.parse_args()

    dois: list[tuple[str, str]] = [(d, "argumento") for d in argumentos.doi]
    for patron in argumentos.archivos:
        for ruta in Path().glob(patron) if "*" in patron else [Path(patron)]:
            if not ruta.is_file():
                continue
            texto = ruta.read_text(encoding="utf-8", errors="ignore")
            for encontrado in PATRON_DOI.findall(texto):
                dois.append((_limpiar_doi(encontrado), str(ruta)))

    if not dois and not argumentos.titulo:
        print("No se encontro ningun DOI. Si las referencias no traen DOI, el modo")
        print("--titulo revisa una a una, pero es menos fiable: conviene citar con DOI.")
        sys.exit(0)

    vistos: set[str] = set()
    retractadas = 0

    for doi, origen in dois:
        if doi.lower() in vistos:
            continue
        vistos.add(doi.lower())
        try:
            obra = consultar_doi(doi)
        except Exception as error:  # noqa: BLE001 - la red puede fallar de mil formas
            print(f"  ?  {doi}  no se pudo consultar: {error}")
            continue
        if obra is None:
            print(f"  !  {doi}  NO EXISTE en Crossref  ({origen})")
            retractadas += 1
            continue
        retractada, razon = esta_retractado(obra)
        titulo = (obra.get("title") or ["(sin titulo)"])[0][:70]
        if retractada:
            print(f"  X  {doi}  RETRACTADA — {razon}")
            print(f"       {titulo}  ({origen})")
            retractadas += 1
        else:
            print(f"  ok {doi}  {titulo}")
        time.sleep(0.2)

    for titulo in argumentos.titulo:
        print(f"\nbuscando: {titulo[:70]}")
        for obra in buscar_por_titulo(titulo):
            retractada, razon = esta_retractado(obra)
            marca = "X RETRACTADA" if retractada else "ok"
            encontrado = (obra.get("title") or [""])[0][:70]
            print(f"  {marca}  {obra.get('DOI')}  {encontrado}")
            if retractada:
                print(f"       {razon}")
                retractadas += 1

    print()
    if retractadas:
        print(f"{retractadas} referencia(s) con problema. NO entregar sin resolverlas.")
        sys.exit(1)
    print(f"{len(vistos)} referencia(s) revisadas, ninguna retractada.")


if __name__ == "__main__":
    main()
