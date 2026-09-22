"""Saca del documento unico cada titulo con su pagina real, para anclar el guion."""

from __future__ import annotations

import json
from pathlib import Path

CARPETA = Path("C:/Users/andre/Downloads/Caso 1 - Exposicion de 1 hora")
DOCUMENTO = "Caso 1 -  Documento Conjunto.docx"
RUTA = CARPETA / DOCUMENTO
SALIDA = Path(__file__).resolve().parents[1] / "docs" / "evidencias" / "indice-documento-unico.json"

WD_ACTIVE_END_PAGE = 3


def main() -> None:
    import win32com.client as win32

    word = win32.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    try:
        doc = word.Documents.Open(str(RUTA), ReadOnly=True)
        doc.Repaginate()
        titulos = []
        for p in doc.Paragraphs:
            estilo = str(p.Style.NameLocal)
            if not (estilo.startswith("Titulo") or estilo.startswith("Título")
                    or estilo.startswith("Heading")):
                continue
            texto = " ".join(p.Range.Text.split())
            if not texto:
                continue
            titulos.append({
                "titulo": texto,
                "pagina": int(p.Range.Information(WD_ACTIVE_END_PAGE)),
                "nivel": estilo,
            })
        doc.Close(False)
    finally:
        word.Quit()

    SALIDA.write_text(json.dumps(titulos, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(titulos)} titulos")
    for t in titulos:
        print(f"{t['pagina']:>4}  {t['titulo'][:76]}")


if __name__ == "__main__":
    main()
