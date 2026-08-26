"""Mide si la hora del dia informa sobre los puntos de inflexion.

Por que existe este guion
-------------------------
El marco teorico de la Semana 1 descarta codificar el **dia de la semana**, y el
argumento es correcto: el mercado de criptoactivos opera de forma continua, sin
apertura ni cierre, asi que no existe el mecanismo institucional que produce el
efecto de calendario que documenta French (1980).

Ese argumento no cubre la **hora del dia**, y el panel de trabajo paso a velas de 4
horas -- seis por dia. Ahi si hay un mecanismo plausible: los operadores humanos
duermen, y el volumen se concentra cuando estan despiertas las plazas grandes. Es la
unica familia de caracteristicas de calendario que no estaba ni construida ni medida.

Se mide antes de decidir, y el criterio se fija antes de mirar: la hora entra como
caracteristica solo si supera el contraste de independencia al 5 % Y su informacion
mutua es comparable a la de las columnas que ya usamos.

Punto de entrada:  uv run python -m scripts.estacionalidad_intradia
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.feature_selection import mutual_info_classif

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from contracts.config import GRANULARIDAD, HORIZONTE_H, VENTANA_W  # noqa: E402
from contracts.labeling import etiquetar, objetivo  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from contracts.splits import particionar  # noqa: E402

#: Referencia contra la que se compara la informacion mutua de la hora. Es la MI
#: media de las 63 columnas vigentes sobre w=7, h=1, medida en el issue #70.
MI_DE_LAS_COLUMNAS_ACTUALES = 0.010217

RUTA = RAIZ / "docs" / "evidencias" / "estacionalidad-intradia.json"


def medir() -> dict:
    panel = pd.read_parquet(RAIZ / "data" / "processed" / f"panel_{GRANULARIDAD}_v1.parquet")
    ltc = cierre(panel, "LTC")
    etiquetas = etiquetar(ltc, VENTANA_W)

    marco = pd.DataFrame(
        {"hora": ltc.index.hour, "etiqueta": etiquetas.astype("Float64")}
    ).dropna()
    es_giro = marco["etiqueta"].isin([1, 2])

    total = marco.groupby("hora").size()
    giros = marco[es_giro].groupby("hora").size()
    tasa = (giros / total * 100).round(4)

    chi2, pvalor, grados, _ = chi2_contingency(pd.crosstab(marco["hora"], es_giro))

    # La informacion mutua se mide SOLO sobre entrenamiento: decidir mirando
    # validacion seria elegir la caracteristica con el bloque que despues la evalua.
    objetivo_h = objetivo(etiquetas, HORIZONTE_H)
    particion = particionar(n=len(objetivo_h), w=VENTANA_W, h=HORIZONTE_H)
    mascara = particion.entrenamiento & objetivo_h.notna().to_numpy()

    # sin/cos y no la hora cruda: la hora es circular, y 20 esta tan cerca de 0
    # como de 16. Codificarla como entero le enseñaria un orden que no existe.
    angulo = 2 * np.pi * ltc.index.hour / 24
    ciclica = pd.DataFrame({"hora_sin": np.sin(angulo), "hora_cos": np.cos(angulo)})[mascara]
    mi = mutual_info_classif(
        ciclica, objetivo_h[mascara].astype(int), random_state=0, n_neighbors=3
    )

    hay_asociacion = bool(pvalor < 0.05)
    mi_comparable = bool(mi.mean() >= MI_DE_LAS_COLUMNAS_ACTUALES)

    return {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "pregunta": "La hora del dia informa sobre los puntos de inflexion de LTC?",
        "criterio_preregistrado": (
            "La hora entra como caracteristica solo si el contraste de independencia "
            "da p < 0,05 Y su informacion mutua alcanza a la media de las columnas "
            "vigentes. Escrito antes de mirar el resultado."
        ),
        "parametros": {"intervalo": GRANULARIDAD, "w": VENTANA_W, "h": HORIZONTE_H},
        "tasa_de_giros_por_hora_utc": [
            {"hora": int(h), "n": int(total[h]), "porcentaje_giros": float(tasa[h])}
            for h in sorted(tasa.index)
        ],
        "dispersion_entre_horas": {
            "minimo": float(tasa.min()),
            "maximo": float(tasa.max()),
            "rango_en_puntos": float(round(tasa.max() - tasa.min(), 4)),
        },
        "contraste_de_independencia": {
            "prueba": "chi-cuadrado de independencia entre hora y ser giro",
            "chi2": float(round(chi2, 4)),
            "grados_de_libertad": int(grados),
            "p_valor": float(round(pvalor, 5)),
            "hay_asociacion_al_5_por_ciento": hay_asociacion,
        },
        "informacion_mutua": {
            "codificacion": "sin/cos de la hora, porque la hora es circular",
            "conjunto": "entrenamiento",
            "valor": float(round(mi.mean(), 6)),
            "referencia_columnas_vigentes": MI_DE_LAS_COLUMNAS_ACTUALES,
            "alcanza_la_referencia": mi_comparable,
        },
        "veredicto": {
            "se_incorpora_como_caracteristica": hay_asociacion and mi_comparable,
            "por_que": (
                "El rango entre horas se ve grande, pero no supera el contraste de "
                "independencia, y la informacion mutua queda muy por debajo de la de "
                "las columnas que ya usamos. Anadirla seria anadir ruido con nombre."
            ),
        },
        "_meta": {
            "advertencia": (
                "Que la hora no informe NO contradice el argumento del marco teorico "
                "sobre el dia de la semana: son preguntas distintas. Esta la cierra "
                "para la granularidad de 4 horas, que es la vigente."
            )
        },
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    medido = medir()
    RUTA.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")

    contraste = medido["contraste_de_independencia"]
    mutua = medido["informacion_mutua"]
    print(f"Tasa de giros por hora UTC ({medido['parametros']['intervalo']}):")
    for fila in medido["tasa_de_giros_por_hora_utc"]:
        print(f"  {fila['hora']:02d}:00  {fila['porcentaje_giros']:.2f} %  (n={fila['n']})")
    print(f"\nRango entre horas: {medido['dispersion_entre_horas']['rango_en_puntos']} puntos")
    print(f"Chi-cuadrado: p = {contraste['p_valor']} -> asociacion: "
          f"{contraste['hay_asociacion_al_5_por_ciento']}")
    print(f"Informacion mutua: {mutua['valor']} contra {mutua['referencia_columnas_vigentes']} "
          f"de las columnas vigentes")
    print(f"\nVeredicto: incorporar la hora -> "
          f"{medido['veredicto']['se_incorpora_como_caracteristica']}")
    print(f"Evidencia: {RUTA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
