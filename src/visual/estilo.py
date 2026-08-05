"""Estandar de figuras del proyecto (RF-I2, RF-I4).

Cada modulo genera sus propias figuras, pero llamando a este archivo. Un estandar
escrito en un documento se pudre en dos semanas porque nadie lo relee; uno que es
codigo se cumple solo.

La paleta es la misma del PRD y la que usa la aplicacion web. El demo y el
documento tienen que parecer el mismo proyecto.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd

NAVY = "#1B2A4A"
ACENTO = "#345D9D"
MAXIMO = "#C0392B"
MINIMO = "#1E8449"
CONTINUIDAD = "#98A2B3"
GRIS = "#5A6675"
REJILLA = "#E3E8EF"

PALETA_CLASES = {
    "Maximo": MAXIMO,
    "Minimo": MINIMO,
    "Continuidad": CONTINUIDAD,
}

PALETA_ACTIVOS = {
    "LTC": NAVY,
    "BTC": "#F2A900",
    "ETH": "#6F7CBA",
    "SOL": "#14B8A6",
    "XRP": "#7C8794",
    "ADA": "#0F5FBF",
}

DIRECTORIO_EVIDENCIAS = Path("docs/evidencias")


def aplicar() -> None:
    """Instala el estilo. Llamar una vez al inicio de cada script o notebook."""
    mpl.rcParams.update(
        {
            "figure.figsize": (9, 4.5),
            "figure.dpi": 110,
            "savefig.dpi": 200,
            "savefig.bbox": "tight",
            "font.family": "sans-serif",
            "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "axes.titlecolor": NAVY,
            "axes.labelcolor": GRIS,
            "axes.edgecolor": REJILLA,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": REJILLA,
            "grid.linewidth": 0.8,
            "xtick.color": GRIS,
            "ytick.color": GRIS,
            "legend.frameon": False,
            "lines.linewidth": 1.4,
        }
    )


def guardar(fig: plt.Figure, nombre: str, directorio: Path = DIRECTORIO_EVIDENCIAS) -> Path:
    """Guarda una figura y devuelve su ruta.

    Escribe junto a la figura un .txt con la fecha de generacion. Sin eso es facil
    pasar horas mirando una figura vieja creyendo que se regenero, que es un error
    que ya nos costo tiempo antes.
    """
    directorio.mkdir(parents=True, exist_ok=True)
    ruta = directorio / f"{nombre}.png"
    fig.savefig(ruta)
    marca = directorio / f"{nombre}.generado.txt"
    marca.write_text(
        f"generado_utc: {datetime.now(UTC).isoformat(timespec='seconds')}\n",
        encoding="utf-8",
    )
    return ruta


def grafico_serie_con_giros(
    cierre: pd.Series,
    etiquetas: pd.Series | None = None,
    predichas: pd.Series | None = None,
    titulo: str = "",
) -> plt.Figure:
    """Serie de precio con los giros reales y, si se pasan, los predichos.

    Los reales van como marcadores rellenos y los predichos como circulos huecos
    encima. Superponerlos en el mismo eje es lo que hace visible de un vistazo
    donde el modelo acerta y donde inventa.
    """
    from contracts.labeling import Clase

    fig, eje = plt.subplots()
    eje.plot(cierre.index, cierre.to_numpy(), color=NAVY, label="Cierre")

    if etiquetas is not None:
        alineadas = etiquetas.reindex(cierre.index)
        for clase, color, etiqueta in (
            (Clase.MAXIMO, MAXIMO, "Maximo real"),
            (Clase.MINIMO, MINIMO, "Minimo real"),
        ):
            mascara = (alineadas == int(clase)).fillna(False).to_numpy()
            if mascara.any():
                eje.scatter(
                    cierre.index[mascara],
                    cierre.to_numpy()[mascara],
                    color=color, s=34, zorder=3, label=etiqueta,
                )

    if predichas is not None:
        alineadas = predichas.reindex(cierre.index)
        for clase, color, etiqueta in (
            (Clase.MAXIMO, MAXIMO, "Maximo predicho"),
            (Clase.MINIMO, MINIMO, "Minimo predicho"),
        ):
            mascara = (alineadas == int(clase)).fillna(False).to_numpy()
            if mascara.any():
                eje.scatter(
                    cierre.index[mascara],
                    cierre.to_numpy()[mascara],
                    facecolors="none", edgecolors=color, s=86, linewidths=1.3,
                    zorder=4, label=etiqueta,
                )

    eje.set_title(titulo)
    eje.set_ylabel("Precio de cierre")
    eje.legend(loc="upper left", ncols=2)
    fig.autofmt_xdate(rotation=30, ha="right")
    fig.tight_layout()
    return fig


def grafico_matriz_confusion(
    matriz: pd.DataFrame, titulo: str = "Matriz de confusion"
) -> plt.Figure:
    fig, eje = plt.subplots(figsize=(5.2, 4.4))
    imagen = eje.imshow(matriz.to_numpy(), cmap="Blues")
    eje.set_xticks(range(len(matriz.columns)), matriz.columns)
    eje.set_yticks(range(len(matriz.index)), matriz.index)
    eje.set_xlabel("Predicho")
    eje.set_ylabel("Real")
    eje.set_title(titulo)
    eje.grid(False)

    maximo = matriz.to_numpy().max()
    for i in range(matriz.shape[0]):
        for j in range(matriz.shape[1]):
            valor = matriz.iloc[i, j]
            eje.text(
                j, i, f"{valor}", ha="center", va="center",
                color="white" if valor > maximo * 0.55 else NAVY, fontweight="bold",
            )
    fig.colorbar(imagen, ax=eje, shrink=0.8)
    fig.tight_layout()
    return fig


def grafico_distribucion_clases(
    resumen: pd.DataFrame, titulo: str = "Balance de clases"
) -> plt.Figure:
    fig, eje = plt.subplots(figsize=(6.4, 3.6))
    colores = [PALETA_CLASES.get(c, ACENTO) for c in resumen["clase"]]
    barras = eje.bar(resumen["clase"], resumen["porcentaje"], color=colores)
    eje.set_ylabel("% de observaciones")
    eje.set_title(titulo)
    for barra, (_, fila) in zip(barras, resumen.iterrows(), strict=True):
        eje.text(
            barra.get_x() + barra.get_width() / 2,
            barra.get_height() + 0.8,
            f"{fila['porcentaje']:.1f}%\n(n={fila['n']})",
            ha="center", va="bottom", fontsize=9, color=GRIS,
        )
    eje.set_ylim(0, max(resumen["porcentaje"]) * 1.28)
    fig.tight_layout()
    return fig
