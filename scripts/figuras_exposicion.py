"""Dos figuras para la exposicion de una hora: como se comportaron los modelos.

No son figuras nuevas del informe: son la misma evidencia ya publicada, dibujada
para proyectarse. Los numeros salen tal cual de `docs/evidencias/`, sin recalcular
nada, para que no puedan discrepar del documento.

Figura A — Los cuatro modelos contra el azar, con su margen de incertidumbre.
  Es la figura que contesta "como se comportaron": se ve de un vistazo que el
  margen del avanzado CRUZA EL CERO y el de los otros dos no.

Figura B — El avanzado contra el clasico, periodo por periodo.
  Nueve barras, las nueve por debajo. Muestra que no es un promedio que tapa
  tramos a favor: es consistente.

Punto de entrada:
    uv run python scripts/figuras_exposicion.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
EVIDENCIAS = RAIZ / "docs" / "evidencias"

TINTA = "#1A1D23"
TINTA_2 = "#5A6072"
LINEA = "#D4D7DE"
LATON = "#B08A1E"
VERDIN = "#3F7D74"
OXIDO = "#B04A34"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": LINEA,
        "text.color": TINTA,
        "axes.labelcolor": TINTA,
        "xtick.color": TINTA_2,
        "ytick.color": TINTA_2,
    }
)


def figura_a() -> Path:
    """Los tres modelos contra el azar, con intervalo. La que mas dice."""
    d = json.loads((EVIDENCIAS / "m0-profundos-agregado-4h-w7-h1.json").read_text(encoding="utf-8"))
    contra = d["contra_el_azar"]

    filas = [
        ("Bosque aleatorio\n(el clásico)", contra["bosque"], VERDIN),
        ("Chronos-Bolt\n(el fundacional)", contra["chronos"], VERDIN),
        ("iTransformer\n(el avanzado)", contra["itransformer"], OXIDO),
    ]

    fig, ax = plt.subplots(figsize=(11, 4.6))
    for i, (_nombre, c, color) in enumerate(filas):
        y = len(filas) - 1 - i
        bajo, alto, punto = c["ic_inferior"], c["ic_superior"], c["diferencia"]
        ax.plot([bajo, alto], [y, y], color=color, linewidth=2.4, solid_capstyle="butt", zorder=3)
        for x in (bajo, alto):
            ax.plot([x, x], [y - 0.12, y + 0.12], color=color, linewidth=2.4, zorder=3)
        ax.plot([punto], [y], "o", color=color, markersize=10, zorder=4)
        ax.text(
            alto + 0.0022, y, f"+{punto:.4f}".replace(".", ","),
            va="center", ha="left", fontsize=11, color=color, fontweight="bold",
        )
        veredicto = (
            "el margen excluye el cero" if c["excluye_el_cero"]
            else "el margen INCLUYE el cero"
        )
        ax.text(
            -0.0175, y - 0.28, veredicto, va="center", ha="left",
            fontsize=9.5, color=color, style="italic",
        )

    ax.axvline(0, color=OXIDO, linewidth=1.6, linestyle=(0, (5, 4)), zorder=2)
    ax.text(
        0, len(filas) - 0.32, "  cero: no hay diferencia",
        fontsize=10, color=OXIDO, va="bottom",
    )

    ax.set_yticks(range(len(filas)))
    ax.set_yticklabels([n for n, _, _ in reversed(filas)], fontsize=11.5)
    ax.set_xlim(-0.018, 0.075)
    ax.set_ylim(-0.7, len(filas) - 0.05)
    ax.set_xlabel(
        "Cuánto mejor que responder al azar  ·  medido sobre 7 311 observaciones fuera de muestra",
        fontsize=10.5, labelpad=10,
    )
    ax.set_title(
        "Los tres modelos contra el azar, con su margen de incertidumbre",
        fontsize=14, fontweight="bold", loc="left", pad=16,
    )
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=LINEA, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    fig.tight_layout()

    salida = EVIDENCIAS / "expo-a-modelos-contra-azar.png"
    fig.savefig(salida, dpi=170, bbox_inches="tight")
    plt.close(fig)
    return salida


def figura_b() -> Path:
    """El avanzado contra el clasico, tramo por tramo: nueve de nueve por debajo."""
    d = json.loads((EVIDENCIAS / "m0-walk-forward-4h-w7-h1.json").read_text(encoding="utf-8"))
    valores = d["avanzado_contra_bosque"]["por_tramo"]

    fig, ax = plt.subplots(figsize=(11, 4.2))
    x = list(range(1, len(valores) + 1))
    ax.bar(x, valores, color=OXIDO, width=0.62, zorder=3)
    for xi, v in zip(x, valores, strict=True):
        ax.text(xi, v - 0.0035, f"{v:.3f}".replace(".", ","), ha="center", va="top",
                fontsize=9.5, color=OXIDO)

    ax.axhline(0, color=TINTA, linewidth=1.4, zorder=4)
    # una sola etiqueta, arriba a la derecha: abajo la tapan las barras
    ax.text(
        len(valores) + 0.45, 0.0035,
        "la línea del cero es el clásico  ·  todas las barras quedan debajo",
        fontsize=10.5, color=TINTA_2, va="bottom", ha="right",
    )

    ax.set_xticks(x)
    ax.set_xticklabels([f"{i}" for i in x], fontsize=11)
    ax.set_xlabel(
        "Período de evaluación  ·  los nueve, en orden cronológico",
        fontsize=10.5, labelpad=10,
    )
    ax.set_ylabel("Diferencia contra el clásico", fontsize=10.5)
    ax.set_title(
        "El modelo avanzado contra el clásico, período por período: nueve de nueve por debajo",
        fontsize=14, fontweight="bold", loc="left", pad=16,
    )
    ax.set_ylim(min(valores) * 1.35, 0.012)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.grid(axis="y", color=LINEA, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    fig.tight_layout()

    salida = EVIDENCIAS / "expo-b-avanzado-por-tramo.png"
    fig.savefig(salida, dpi=170, bbox_inches="tight")
    plt.close(fig)
    return salida


def main() -> None:
    for f in (figura_a(), figura_b()):
        print(f"  {f.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
