"""Comprueba que todo numero citado en las entregas exista en la evidencia medida.

Existe porque pasó: en el esqueleto de la Semana 1 aparecian "maxima 0,0774;
minima 0,0088" para la volatilidad de LTC. El cociente 8,8 estaba medido, pero
esos dos extremos no salian de ninguna ejecucion. El valor real es 0,1220 y
0,0138. Nadie lo habria notado hasta que el profesor sumara y no cuadrara.

El documento generado por script no tenia el error, porque lee del JSON. El error
estaba en la parte escrita a mano. Esa es toda la leccion, y este script la vuelve
mecanica.

No pretende ser exhaustivo: marca candidatos y una persona decide. Un falso
positivo cuesta diez segundos; un numero inventado en una entrega, mucho mas.

Uso:
    uv run python scripts/verificar_numeros.py
    uv run python scripts/verificar_numeros.py docs/entregas/semana-2
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
EVIDENCIAS = RAIZ / "docs" / "evidencias"

# Numeros que aparecen en el texto sin ser mediciones: umbrales acordados,
# porcentajes de la rubrica, versiones. Ampliar cuando aparezca un falso positivo
# recurrente, nunca para silenciar uno legitimo.
CONOCIDOS = {"0,05", "0,02", "16,66", "16,7", "0,5", "1,96", "0,000001"}

PATRON = re.compile(r"\b(\d+[.,]\d{2,6})\b")


def _variantes(valor: float) -> set[str]:
    """Todas las escrituras plausibles de un mismo numero medido.

    Un valor de 0.7395 puede citarse como 0,74 o como 0,740, y las dos son
    correctas. Sin contemplar los ceros finales, el verificador marcaria como
    inventado un numero bien redondeado.
    """
    salida: set[str] = set()
    for decimales in range(1, 7):
        for candidato in (round(valor, decimales), round(abs(valor), decimales)):
            texto = f"{candidato:.{decimales}f}"
            salida.add(texto)
            salida.add(texto.replace(".", ","))
            recortado = texto.rstrip("0").rstrip(".")
            if recortado:
                salida.add(recortado)
                salida.add(recortado.replace(".", ","))
    return salida


def numeros_medidos() -> set[str]:
    """Aplana todos los JSON de evidencia y devuelve sus valores como texto."""
    validos: set[str] = set()

    def recorrer(nodo) -> None:
        if isinstance(nodo, dict):
            for valor in nodo.values():
                recorrer(valor)
        elif isinstance(nodo, list):
            for valor in nodo:
                recorrer(valor)
        elif isinstance(nodo, bool):
            return
        elif isinstance(nodo, (int, float)):
            validos.update(_variantes(float(nodo)))

    archivos = sorted(EVIDENCIAS.glob("*.json"))
    if not archivos:
        sys.exit(f"no hay evidencia en {EVIDENCIAS.relative_to(RAIZ)}")
    for archivo in archivos:
        recorrer(json.loads(archivo.read_text(encoding="utf-8")))
    return validos


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "docs" / "entregas"
    validos = numeros_medidos()

    revisados = sospechosos = 0
    for archivo in sorted(destino.rglob("*.md")):
        encabezado = False
        for numero_linea, linea in enumerate(
            archivo.read_text(encoding="utf-8").splitlines(), 1
        ):
            for encontrado in PATRON.finditer(linea):
                texto = encontrado.group(1)
                revisados += 1
                if texto in CONOCIDOS or texto in validos:
                    continue
                if not encabezado:
                    print(f"\n--- {archivo.relative_to(RAIZ)}")
                    encabezado = True
                sospechosos += 1
                print(f"  L{numero_linea:<4} {texto:>10}   {linea.strip()[:84]}")

    print(f"\n{revisados} numeros revisados en {destino.relative_to(RAIZ)}.")
    if sospechosos:
        print(f"{sospechosos} sin respaldo en docs/evidencias/*.json.")
        print("Revisar uno a uno: o se mide y se corrige, o se agrega a CONOCIDOS si")
        print("es un umbral acordado y no una medicion.")
        sys.exit(1)
    print("Todos respaldados por una medicion.")


if __name__ == "__main__":
    main()
