"""Deja el indice del .docx ya calculado y quita el cartel que Word muestra al abrir.

Por que existe
--------------
El ensamblador escribe el indice como un campo TOC vacio y marca el documento con
`<w:updateFields/>`. Esa marca es la que hace que Word pregunte al abrir:

    "Este documento contiene campos que pueden hacer referencia a otros archivos.
     Desea actualizar los campos de este documento?"

Contestar "Si" era el paso manual que rellenaba los numeros de pagina. Funciona, pero
el cartel asusta a quien recibe el archivo y suena a que el documento trae contenido de
fuera, que no es el caso: el unico campo es el indice y no hay ninguna referencia
externa.

Que hace
--------
1. Abre el documento con Word y **actualiza el indice de verdad**, con lo que los
   numeros de pagina quedan escritos dentro del archivo.
2. Quita `<w:updateFields/>` de `word/settings.xml`.

El resultado es un documento que se abre sin preguntar nada y con el indice completo.

Lo que NO hace
--------------
No toca el contenido. Si el documento cambia hay que volver a ensamblar y a correr
esto, en ese orden: el indice se calcula sobre la paginacion final.

Necesita Word instalado y el Python del sistema que tiene `pywin32`
(en esta maquina, `py -3.13`; el entorno del proyecto no lo trae).

Uso:
    py -3.13 scripts/fijar_indice.py "ruta/al/documento.docx" [mas.docx ...]
"""

from __future__ import annotations

import re
import shutil
import sys
import zipfile
from pathlib import Path


def actualizar_indice(ruta: Path) -> int:
    """Abre el documento en Word y actualiza sus indices. Devuelve cuantos actualizo."""
    import win32com.client  # noqa: PLC0415  (solo hace falta aqui, y solo en Windows)

    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        doc = word.Documents.Open(str(ruta), ConfirmConversions=False, ReadOnly=False)
        try:
            doc.Fields.Update()
            indices = doc.TablesOfContents
            for i in range(1, indices.Count + 1):
                indices(i).Update()
            # Repaginar antes de guardar: los numeros del indice salen de la
            # paginacion, y Word la calcula perezosamente.
            doc.Repaginate()
            doc.Save()
            return int(indices.Count)
        finally:
            doc.Close(SaveChanges=0)
    finally:
        word.Quit()


def quitar_marca(ruta: Path) -> bool:
    """Borra <w:updateFields/> de settings.xml. Devuelve si habia algo que borrar."""
    temporal = ruta.with_suffix(".docx.tmp")
    encontrada = False
    with (
        zipfile.ZipFile(ruta) as origen,
        zipfile.ZipFile(temporal, "w", zipfile.ZIP_DEFLATED) as destino,
    ):
        for elemento in origen.infolist():
            datos = origen.read(elemento.filename)
            if elemento.filename == "word/settings.xml":
                texto = datos.decode("utf-8")
                nuevo = re.sub(
                    r"<w:updateFields[^>]*/>|<w:updateFields[^>]*>.*?</w:updateFields>",
                    "",
                    texto,
                    flags=re.DOTALL,
                )
                encontrada = nuevo != texto
                datos = nuevo.encode("utf-8")
            destino.writestr(elemento, datos)
    shutil.move(str(temporal), str(ruta))
    return encontrada


def paginas_en_el_indice(ruta: Path) -> int:
    """Cuenta las entradas del indice que ya traen numero de pagina."""
    with zipfile.ZipFile(ruta) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    # Cada entrada resuelta del TOC deja un PAGEREF con su numero al lado.
    return len(re.findall(r"PAGEREF", xml))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for argumento in sys.argv[1:]:
        ruta = Path(argumento).resolve()
        if not ruta.exists():
            raise SystemExit(f"no existe: {ruta}")
        print(f"\n{ruta.name}")
        print(f"  entradas con pagina, antes: {paginas_en_el_indice(ruta)}")
        cuantos = actualizar_indice(ruta)
        print(f"  indices actualizados por Word: {cuantos}")
        habia = quitar_marca(ruta)
        print(f"  marca <w:updateFields/> {'quitada' if habia else 'no estaba'}")
        despues = paginas_en_el_indice(ruta)
        print(f"  entradas con pagina, despues: {despues}")
        if despues == 0:
            raise SystemExit(
                "  ERROR: el indice quedo vacio. No se sube asi: revisar que Word "
                "abriera el documento."
            )
