"""Convierte un markdown a PDF pasando por HTML y Word.

Los generadores de Word del proyecto (`scripts/ensamblar_semana1.js`) producen el
entregable con formato APA, que es rigido a proposito. Los documentos de estudio
—guia de defensa, guion de exposicion— necesitan lo contrario: tablas anchas,
bloques de codigo y jerarquia visual clara. Por eso van por otro camino.

No se usa pandoc porque no esta instalado en las maquinas del equipo y pedir que
lo instalen anade un paso que se puede evitar: Word ya esta, y abre HTML.

Uso:
    uv run python scripts/md_a_pdf.py docs/defensa/archivo.md
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

HOJA = """
body { font-family: Georgia, 'Times New Roman', serif; font-size: 11pt;
       line-height: 1.45; color: #111; margin: 2.2cm 2.0cm; }
h1 { font-size: 20pt; border-bottom: 2px solid #1B2A4A; padding-bottom: 4pt;
     color: #1B2A4A; page-break-before: always; }
h1:first-of-type { page-break-before: avoid; }
h2 { font-size: 15pt; color: #1B2A4A; margin-top: 18pt; }
h3 { font-size: 12.5pt; color: #345D9D; margin-top: 14pt; }
h4 { font-size: 11pt; color: #345D9D; }
table { border-collapse: collapse; width: 100%; margin: 10pt 0; font-size: 10pt; }
th { background: #1B2A4A; color: #fff; text-align: left; padding: 5pt 7pt; }
td { border-bottom: 1px solid #ccc; padding: 5pt 7pt; vertical-align: top; }
tr:nth-child(even) td { background: #f4f6f9; }
pre { background: #f4f6f9; border-left: 3px solid #345D9D; padding: 8pt 10pt;
      font-family: Consolas, 'Courier New', monospace; font-size: 9pt;
      line-height: 1.3; white-space: pre; }
code { font-family: Consolas, 'Courier New', monospace; font-size: 9.5pt;
       background: #eef1f6; padding: 0 3px; }
pre code { background: none; padding: 0; }
blockquote { border-left: 3px solid #345D9D; margin: 10pt 0; padding: 2pt 0 2pt 12pt;
             color: #333; background: #f8f9fb; }
hr { border: none; border-top: 1px solid #bbb; margin: 16pt 0; }
li { margin-bottom: 3pt; }
"""


def en_linea(texto: str) -> str:
    """Negrita, cursiva y codigo. El codigo se resuelve primero.

    Si se resolviera al final, un asterisco dentro de un fragmento de codigo se
    interpretaria como cursiva y partiria el fragmento.
    """
    piezas: list[str] = []

    def guardar(m: re.Match[str]) -> str:
        piezas.append(f"<code>{html.escape(m.group(1))}</code>")
        return f"\x00{len(piezas) - 1}\x00"

    texto = re.sub(r"`([^`]+)`", guardar, texto)
    texto = html.escape(texto)
    texto = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", texto)
    texto = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", texto)
    texto = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", texto)
    return re.sub(r"\x00(\d+)\x00", lambda m: piezas[int(m.group(1))], texto)


def convertir(md: str) -> str:
    salida: list[str] = []
    lineas = md.split("\n")
    i = 0
    while i < len(lineas):
        linea = lineas[i]

        if linea.startswith("```"):
            bloque = []
            i += 1
            while i < len(lineas) and not lineas[i].startswith("```"):
                bloque.append(html.escape(lineas[i]))
                i += 1
            salida.append("<pre><code>" + "\n".join(bloque) + "</code></pre>")
            i += 1
            continue

        # Una tabla se reconoce por la fila de guiones que sigue al encabezado, no
        # por la fila de encabezado sola: "| | |" es un encabezado valido y sin
        # guiones debajo no es una tabla.
        separador = i + 1 < len(lineas) and re.match(r"^\|[\s:|-]*-[\s:|-]*\|$", lineas[i + 1])
        if linea.startswith("|") and separador:
            def celdas(fila: str) -> list[str]:
                return [c.strip() for c in fila.strip().strip("|").split("|")]

            cab = celdas(linea)
            i += 2
            filas = []
            while i < len(lineas) and lineas[i].startswith("|"):
                filas.append(celdas(lineas[i]))
                i += 1
            th = "".join(f"<th>{en_linea(c)}</th>" for c in cab)
            cuerpo = "".join(
                "<tr>" + "".join(f"<td>{en_linea(c)}</td>" for c in f) + "</tr>" for f in filas
            )
            salida.append(f"<table><tr>{th}</tr>{cuerpo}</table>")
            continue

        if re.match(r"^#{1,6} ", linea):
            n = len(linea) - len(linea.lstrip("#"))
            salida.append(f"<h{n}>{en_linea(linea[n:].strip())}</h{n}>")
            i += 1
            continue

        if linea.startswith(">"):
            bloque = []
            while i < len(lineas) and lineas[i].startswith(">"):
                bloque.append(lineas[i].lstrip("> ").rstrip())
                i += 1
            salida.append("<blockquote>" + en_linea(" ".join(bloque)) + "</blockquote>")
            continue

        if re.match(r"^\s*([-*+]|\d+\.) ", linea):
            ordenada = bool(re.match(r"^\s*\d+\.", linea))
            puntos = []
            while i < len(lineas) and re.match(r"^\s*([-*+]|\d+\.) ", lineas[i]):
                puntos.append(re.sub(r"^\s*([-*+]|\d+\.)\s+", "", lineas[i]))
                i += 1
            etiqueta = "ol" if ordenada else "ul"
            cuerpo = "".join(f"<li>{en_linea(p)}</li>" for p in puntos)
            salida.append(f"<{etiqueta}>{cuerpo}</{etiqueta}>")
            continue

        if re.match(r"^---+\s*$", linea):
            salida.append("<hr>")
            i += 1
            continue

        if linea.strip():
            parrafo = [linea]
            i += 1
            while i < len(lineas) and lineas[i].strip() and not re.match(
                r"^(#{1,6} |```|\||>|---+\s*$|\s*([-*+]|\d+\.) )", lineas[i]
            ):
                parrafo.append(lineas[i])
                i += 1
            salida.append("<p>" + en_linea(" ".join(parrafo)) + "</p>")
            continue

        i += 1

    return "\n".join(salida)


def a_pdf(ruta_md: Path) -> Path:
    md = ruta_md.read_text(encoding="utf-8")
    titulo = next((ln[2:].strip() for ln in md.split("\n") if ln.startswith("# ")), ruta_md.stem)
    ruta_html = ruta_md.with_suffix(".html")
    ruta_html.write_text(
        "<html><head><meta charset='utf-8'>"
        f"<title>{html.escape(titulo)}</title><style>{HOJA}</style></head>"
        f"<body>{convertir(md)}</body></html>",
        encoding="utf-8",
    )

    import win32com.client  # noqa: PLC0415  (solo hace falta aqui, y solo en Windows)

    ruta_pdf = ruta_md.with_suffix(".pdf")
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(str(ruta_html.resolve()))
        doc.ExportAsFixedFormat(str(ruta_pdf.resolve()), 17)  # 17 = wdExportFormatPDF
        paginas = doc.ComputeStatistics(2)
        doc.Close(0)
    finally:
        word.Quit()
    ruta_html.unlink()
    print(f"  {ruta_pdf.relative_to(RAIZ)}  ({paginas} paginas)")
    return ruta_pdf


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)
    for argumento in sys.argv[1:]:
        a_pdf(Path(argumento).resolve())
