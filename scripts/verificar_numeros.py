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
    uv run python scripts/verificar_numeros.py docs/entregas --procedencia
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
# 0,51 / 0,039 / 1,00 / 0,02 son un ejemplo aritmetico del texto sobre por que el
# F1 usa media armonica, no afirmaciones sobre los datos. Comprobados a mano.
CONOCIDOS = {
    "0,05", "0,02", "16,66", "16,7", "0,5", "1,96", "0,000001",
    "0,51", "0,039", "1,00",
}

PATRON = re.compile(r"\b(\d+[.,]\d{2,6})\b")

# Un DOI o una URL estan llenos de digitos con puntos que no son mediciones:
# 10.1016/j.irfa.2018.09.003 aporta cuatro falsos positivos el solo. Se recortan
# antes de buscar, en vez de ir anadiendolos a CONOCIDOS uno por uno.
# Lo que parece un numero y no lo es. Una URL, un DOI, una version de paquete y un
# nombre de archivo son identificadores: nombran algo, no miden nada, y exigirles
# respaldo marcaria como inventado un dato que es correcto. Las versiones se
# reconocen por tener tres componentes (2.13.0) o por ir precedidas del paquete.
#
# El nombre de archivo va entre comillas invertidas y termina en una extension
# conocida. Se agrego al toparse con la marca (entregada18.8.26).docx, donde la
# fecha esta pegada a una palabra: el patron de version no la alcanza porque
# necesita un limite de palabra a la izquierda y "a18" no lo tiene.
RUIDO = re.compile(
    r"https?://\S+"
    r"|\b10\.\d{4,9}/\S+"
    r"|`[^`\n]*\.(?:docx|json|md|py|csv|png|txt|js|parquet|toml|lock)[^`\n]*`"
    r"|\b\d+\.\d+\.\d+(?:[.\w-]*)?\b"
    r"|\b(?:torch|python|pandas|numpy|scikit-learn|matplotlib)\s+[\d.]+",
    re.IGNORECASE,
)


def _mostrar(ruta: Path) -> Path:
    """La ruta relativa a la raiz si esta dentro, y la absoluta si no.

    relative_to() a secas revienta cuando la ruta cae fuera del proyecto. Rompio
    tres veces en dos dias --el resumen, el mensaje de error del pestillo y el
    encabezado por archivo-- y siempre al imprimir algo. Un mensaje que falla al
    construirse esconde lo que iba a decir.
    """
    return ruta.relative_to(RAIZ) if ruta.is_relative_to(RAIZ) else ruta


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


def procedencias() -> dict[str, list[str]]:
    """Cada escritura aceptada, con el origen de donde sale.

    Antes esto era un `set` y solo respondia si/no. La pregunta util no es esa: es
    **de donde** sale un verde, porque el espacio de cadenas aceptadas satura
    (ver `calibrar()`), y un si sin origen no se puede auditar.
    """
    origen: dict[str, list[str]] = {}

    def recorrer(nodo, archivo: str, ruta: str) -> None:
        if isinstance(nodo, dict):
            for clave, valor in nodo.items():
                recorrer(valor, archivo, f"{ruta}.{clave}")
        elif isinstance(nodo, list):
            for i, valor in enumerate(nodo):
                recorrer(valor, archivo, f"{ruta}[{i}]")
        elif isinstance(nodo, bool):
            return
        elif isinstance(nodo, (int, float)):
            etiqueta = f"{archivo}{ruta} = {nodo}"
            for texto in _variantes(float(nodo)):
                origen.setdefault(texto, []).append(etiqueta)

    archivos = sorted(EVIDENCIAS.glob("*.json"))
    if not archivos:
        sys.exit(f"no hay evidencia en {EVIDENCIAS.relative_to(RAIZ)}")
    for archivo in archivos:
        recorrer(json.loads(archivo.read_text(encoding="utf-8")), archivo.name, "")
    return origen


def numeros_medidos() -> set[str]:
    """Las escrituras aceptadas, sin su origen. Se conserva por compatibilidad."""
    return set(procedencias())


def calibrar(validos: set[str]) -> dict[int, tuple[int, int]]:
    """Cuantas cifras POSIBLES pasan a cada precision, sin haberse medido nunca.

    Es la medida honesta de lo que vale un "respaldado". Con ~2400 valores de
    evidencia y seis redondeos cada uno, el espacio de dos decimales se satura: casi
    cualquier cifra que alguien escriba con dos decimales pasa.

    Se calcula y se imprime en vez de dejarlo implicito, porque quien lee "todos
    respaldados" tiene derecho a saber cuanto discrimina esa afirmacion.
    """
    salida = {}
    for decimales in (2, 3, 4):
        total = 10**decimales
        pasan = sum(
            1
            for i in range(total)
            if f"0,{str(i).zfill(decimales)}" in validos
            or f"0.{str(i).zfill(decimales)}" in validos
        )
        salida[decimales] = (pasan, total)
    return salida


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    # Se resuelve contra la raiz del proyecto y no contra el directorio actual:
    # el ejemplo de uso del docstring pasa una ruta relativa, y sin esto
    # reventaba al imprimir el resumen.
    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]
    con_procedencia = "--procedencia" in sys.argv

    destino = RAIZ / "docs" / "entregas"
    if argumentos:
        pedido = Path(argumentos[0])
        destino = pedido if pedido.is_absolute() else (RAIZ / pedido).resolve()
    # Que la ruta exista y contenga algo NO es una comprobacion de cortesia. Sin
    # ella, este guion respondia "Todos respaldados por una medicion" sobre cero
    # archivos y salia con codigo 0: una ruta mal escrita, un directorio movido o un
    # CI apuntando a un sitio viejo quedaban en verde para siempre sin revisar una
    # sola linea.
    #
    # Es el mismo defecto que el guion existe para atrapar -- una etiqueta que dejo
    # de describir lo que hay debajo -- dentro del guion que lo atrapa.
    if not destino.exists():
        print(f"ERROR: {destino} no existe. No se reviso nada.")
        sys.exit(2)

    archivos = [destino] if destino.is_file() else sorted(destino.rglob("*.md"))
    archivos = [a for a in archivos if a.suffix == ".md"]
    if not archivos:
        print(f"ERROR: no hay ningun .md en {destino}. No se reviso nada.")
        sys.exit(2)

    origen = procedencias()
    validos = set(origen)

    revisados = sospechosos = 0
    for archivo in archivos:
        encabezado = False
        if con_procedencia:
            print(f"\n--- {_mostrar(archivo)}")
        for numero_linea, linea in enumerate(
            archivo.read_text(encoding="utf-8").splitlines(), 1
        ):
            for encontrado in PATRON.finditer(RUIDO.sub(" ", linea)):
                texto = encontrado.group(1)
                revisados += 1
                if texto in CONOCIDOS or texto in validos:
                    if con_procedencia:
                        de_donde = (
                            ["umbral acordado, no medicion"]
                            if texto in CONOCIDOS
                            else origen[texto]
                        )
                        print(f"  L{numero_linea:<4} {texto:>10}  <- {de_donde[0]}")
                        for extra in de_donde[1:3]:
                            print(f"  {'':<6} {'':>10}     tambien {extra}")
                        if len(de_donde) > 3:
                            print(
                                f"  {'':<6} {'':>10}     y {len(de_donde) - 3} origen(es) mas "
                                "-- cuantos mas haya, menos discrimina la coincidencia"
                            )
                    continue
                if not encabezado:
                    print(f"\n--- {_mostrar(archivo)}")
                    encabezado = True
                sospechosos += 1
                print(f"  L{numero_linea:<4} {texto:>10}   {linea.strip()[:84]}")

    ubicacion = _mostrar(destino)
    print(f"\n{revisados} numeros revisados en {len(archivos)} archivo(s) de {ubicacion}.")
    if revisados == 0:
        print("ERROR: no se encontro ningun numero. Un 'todo respaldado' sobre cero")
        print("numeros no dice nada, asi que se reporta como fallo y no como exito.")
        sys.exit(2)
    if sospechosos:
        print(f"{sospechosos} sin respaldo en docs/evidencias/*.json.")
        print("Revisar uno a uno: o se mide y se corrige, o se agrega a CONOCIDOS si")
        print("es un umbral acordado y no una medicion.")
        sys.exit(1)
    calibracion = calibrar(validos)
    debiles, total_d = calibracion[2]
    print(
        f"Todos coinciden con algun valor de la evidencia.\n"
        f"\nLo que eso discrimina, medido: a dos decimales pasan {debiles} de "
        f"{total_d} cifras posibles\nsin haberse medido nunca, a tres "
        f"{calibracion[3][0]} de {calibracion[3][1]}, a cuatro "
        f"{calibracion[4][0]} de {calibracion[4][1]}.\n"
        "Una coincidencia a dos decimales casi no es evidencia. Usa --procedencia\n"
        "para ver de que medicion sale cada una."
    )


if __name__ == "__main__":
    main()
