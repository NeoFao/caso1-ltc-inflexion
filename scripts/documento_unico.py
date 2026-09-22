"""Un solo Word con los cuatro puntos que el profesor califica, en orden.

El profesor califica por cuatro puntos --avance 1, avance 2, modelo fundacional y
modelo avanzado-- y pregunta sobre el documento. Tener cuatro archivos sueltos
obliga a cambiar de ventana en mitad de la exposicion; esto los une en uno, cada
uno empezando en pagina propia y precedido por una portadilla que dice que punto
es.

No reescribe nada: inserta los documentos ya entregados tal cual, con sus tablas
y figuras. Lo unico que agrega son las cuatro portadillas.

Al terminar imprime **en que pagina empieza cada punto**, que es lo que el guion
necesita para decir donde hay que estar.

Necesita Word instalado:
    py -3.13 scripts/documento_unico.py
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ENTREGA = Path("C:/Users/andre/Downloads/ENTREGA Caso 1/2 - Entregables de avances")
CARPETA = Path("C:/Users/andre/Downloads/Caso 1 - Exposicion de 1 hora")
DOCUMENTO = "Caso 1 -  Documento Conjunto.docx"
SALIDA = CARPETA / DOCUMENTO

PARTES = [
    (
        "Punto 1 · Avance N.º 1",
        "Marco teórico: series de tiempo y criptoactivos",
        ENTREGA / "Avance 1 - Marco teorico series de tiempo y criptoactivos"
        / "DOCUMENTO - Marco teorico Semana 1 (entregado 18-08).docx",
    ),
    (
        "Punto 2 · Avance N.º 2",
        "Marco teórico de modelos y procedimiento de desarrollo",
        ENTREGA / "Avance 2 - Marco teorico modelos"
        / "DOCUMENTO - Marco teorico Semana 2 (entregado 25-08).docx",
    ),
    (
        "Punto 3 · Modelo fundacional",
        "Chronos-Bolt, el puente y las cuatro pruebas de detección",
        ENTREGA / "Semana 3 - Modelo fundacional" / "DOCUMENTO - Semana 3.docx",
    ),
    (
        "Punto 4 · Modelo avanzado",
        "iTransformer, la comparación de los tres modelos y los límites",
        ENTREGA / "Semana 4 - Modelo avanzado" / "DOCUMENTO - Semana 4.docx",
    ),
]

WD_PAGE_BREAK = 7
WD_ACTIVE_END_PAGE = 3
WD_STORY_END = 6


def main() -> None:
    try:
        import win32com.client as win32
    except ImportError:  # pragma: no cover
        raise SystemExit("hace falta pywin32: usar `py -3.13`") from None

    faltan = [p for _, _, p in PARTES if not p.exists()]
    if faltan:
        raise SystemExit("no encuentro:\n  " + "\n  ".join(str(f) for f in faltan))

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    word = win32.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False

    try:
        doc = word.Documents.Add()
        seleccion = word.Selection
        paginas: list[tuple[str, int]] = []

        for i, (punto, subtitulo, ruta) in enumerate(PARTES):
            if i:
                seleccion.InsertBreak(WD_PAGE_BREAK)

            inicio = int(seleccion.Range.Information(WD_ACTIVE_END_PAGE))
            paginas.append((punto, inicio))

            estilo = "Título 1" if _existe(doc, "Título 1") else "Heading 1"
            seleccion.Style = doc.Styles(estilo)
            seleccion.TypeText(punto)
            seleccion.TypeParagraph()
            seleccion.Style = doc.Styles("Normal")
            seleccion.Font.Italic = True
            seleccion.TypeText(subtitulo)
            seleccion.Font.Italic = False
            seleccion.TypeParagraph()
            seleccion.InsertBreak(WD_PAGE_BREAK)

            seleccion.InsertFile(str(ruta))
            seleccion.EndKey(Unit=WD_STORY_END)

        doc.Repaginate()
        # las paginas reales se leen despues de repaginar
        finales = []
        for punto, _ in paginas:
            encontrado = None
            for p in doc.Paragraphs:
                if p.Range.Text.strip() == punto:
                    encontrado = int(p.Range.Information(WD_ACTIVE_END_PAGE))
                    break
            finales.append((punto, encontrado))

        doc.SaveAs(str(SALIDA), FileFormat=16)
        total = int(doc.ComputeStatistics(2))  # wdStatisticPages
        doc.Close(False)
    finally:
        word.Quit()

    print(f"{SALIDA.name} · {total} páginas\n")
    print(f"{'Punto':38s} empieza en la página")
    for punto, pagina in finales:
        print(f"  {punto:36s} {pagina}")


def _existe(doc, nombre: str) -> bool:
    try:
        doc.Styles(nombre)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    sys.exit(main())
