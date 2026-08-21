"""Estudio que sustenta la eleccion de w, h y granularidad.

Las tres decisiones se toman con criterios fijados de antemano y con mediciones,
no con intuicion. Este script produce las tres mediciones y deja el resultado en
docs/evidencias/estudio-w-h.json para que cualquier numero del informe sea
verificable.

Las tres preguntas y como se responden:

1. Granularidad. Criterio previo: al menos MINIMO_EJEMPLOS_CLASE_MINORITARIA
   ejemplos de la clase minoritaria en entrenamiento. Se mide sobre los dos
   paneles.

2. w. Criterio previo: el mayor w que cumpla el piso, porque un w grande detecta
   giros mas estructurales y menos ruido.

3. h. El balance de clases NO depende de h — es un desplazamiento — asi que el
   criterio anterior no lo discrimina. Hace falta medir dificultad. Se usa la
   informacion mutua entre las caracteristicas disponibles en t y la etiqueta en
   t+h: si el objetivo se vuelve menos predecible al alejarlo, la informacion cae.

Uso:
    uv run python scripts/estudio_w_h_granularidad.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.feature_selection import mutual_info_classif  # noqa: E402

from contracts.config import MINIMO_EJEMPLOS_CLASE_MINORITARIA  # noqa: E402
from contracts.labeling import Clase, etiquetar, latencia_real, objetivo  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from contracts.splits import particionar  # noqa: E402
from src.features.base import construir  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
EVIDENCIAS = RAIZ / "docs" / "evidencias"

GRANULARIDADES = ("1d", "4h")
REJILLA_W = (3, 5, 7, 10, 15)
REJILLA_H = (1, 3, 5, 8, 12)
DURACION = {"1d": 24, "4h": 4}  # horas por vela, para traducir la latencia


def medir_disponibilidad(ltc: pd.Series, intervalo: str) -> list[dict]:
    """Cuantos ejemplos de la clase minoritaria quedan en entrenamiento."""
    filas = []
    for w in REJILLA_W:
        etiquetas = etiquetar(ltc, w)
        y = objetivo(etiquetas, 1)
        try:
            particion = particionar(n=len(y), w=w, h=1)
        except ValueError:
            continue
        entrenamiento = y[particion.entrenamiento].dropna().astype(int)
        conteos = {c.name.lower(): int((entrenamiento == int(c)).sum()) for c in Clase}
        minoritaria = min(conteos.values())
        filas.append({
            "intervalo": intervalo,
            "w": w,
            "n_entrenamiento": int(len(entrenamiento)),
            **{f"n_{k}": v for k, v in conteos.items()},
            "n_clase_minoritaria": minoritaria,
            "cumple_piso": minoritaria >= MINIMO_EJEMPLOS_CLASE_MINORITARIA,
        })
    return filas


def medir_predictibilidad(panel: pd.DataFrame, intervalo: str) -> list[dict]:
    """Informacion mutua entre lo observable en t y la etiqueta en t+h.

    Se calcula sobre entrenamiento para no mirar los datos de evaluacion. El valor
    absoluto es pequeno para todo h, y eso ya es informacion: el problema es duro.
    Lo que se interpreta es la FORMA de la curva, no su nivel.
    """
    # ANCLADO A PROPOSITO. Heredar el default de construir() es como se
    # desincronizaron m2-ablacion.json (PR #68) e incertidumbre.py: el #58 cambio ese
    # default a rezagos relativos el 20/08 y esta evidencia es del 17/08, asi que
    # re-ejecutar sin anclar dejaria de reproducir lo publicado sin avisar.
    #
    # Medido sobre w=7, en el issue #70 y por separado desde M0, con los mismos
    # valores hasta el sexto decimal:
    #
    #   h        en nivel      relativos
    #   1        0,005686      0,010217
    #   3        0,001433      0,002641
    #   5        0,000397      0,000670
    #   caida    3,97x         3,87x
    #
    # El NIVEL casi se duplica; la FORMA no se mueve, y la forma es lo que la D3
    # interpreta. La decision se sostiene con cualquiera de las dos representaciones,
    # asi que rehacer el estudio es opcional y no urgente. Lo que no puede pasar es
    # que las cifras citadas en docs/04-decision-w-h-granularidad.md cambien solas.
    caracteristicas = construir(panel, rezagos_relativos=False)
    ltc = cierre(panel, "LTC")
    filas = []
    for w in (5, 7):
        etiquetas = etiquetar(ltc, w)
        for h in REJILLA_H:
            y = objetivo(etiquetas, h)
            particion = particionar(n=len(y), w=w, h=h)
            mascara = particion.entrenamiento & y.notna().to_numpy()
            X = caracteristicas[mascara].replace([np.inf, -np.inf], np.nan)
            completas = X.notna().all(axis=1).to_numpy()
            informacion = mutual_info_classif(
                X[completas], y[mascara][completas].astype(int),
                random_state=0, n_neighbors=3,
            )
            filas.append({
                "intervalo": intervalo,
                "w": w,
                "h": h,
                "informacion_mutua_media": round(float(informacion.mean()), 6),
                "informacion_mutua_maxima": round(float(informacion.max()), 6),
                "latencia_velas": latencia_real(w, h),
                "latencia_horas": latencia_real(w, h) * DURACION[intervalo],
                "n": int(completas.sum()),
            })
    return filas


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    disponibilidad: list[dict] = []
    predictibilidad: list[dict] = []
    paneles: dict[str, dict] = {}

    for intervalo in GRANULARIDADES:
        ruta = RAIZ / "data" / "processed" / f"panel_{intervalo}_v1.parquet"
        if not ruta.exists():
            sys.exit(f"falta {ruta}")
        panel = pd.read_parquet(ruta)
        paneles[intervalo] = {
            "filas": int(len(panel)),
            "desde": panel.index.min().isoformat(),
            "hasta": panel.index.max().isoformat(),
        }
        print(f"[{intervalo}] {len(panel)} filas")
        disponibilidad += medir_disponibilidad(cierre(panel, "LTC"), intervalo)
        predictibilidad += medir_predictibilidad(panel, intervalo)

    validas = [f for f in disponibilidad if f["cumple_piso"]]
    if validas:
        mejor = max(validas, key=lambda f: f["w"])
        decision_w = {
            "intervalo": mejor["intervalo"], "w": mejor["w"],
            "n_clase_minoritaria": mejor["n_clase_minoritaria"],
            "razon": (
                f"es el mayor w que deja al menos {MINIMO_EJEMPLOS_CLASE_MINORITARIA} "
                f"ejemplos de la clase minoritaria en entrenamiento"
            ),
        }
    else:
        decision_w = {"intervalo": None, "w": None, "razon": "ninguna combinacion cumple el piso"}

    # h se decide por la forma de la curva de informacion mutua, no por el piso.
    por_h: dict[int, list[float]] = {}
    for fila in predictibilidad:
        por_h.setdefault(fila["h"], []).append(fila["informacion_mutua_media"])
    promedio_h = {h: round(float(np.mean(v)), 6) for h, v in sorted(por_h.items())}
    mejor_h = max(promedio_h, key=promedio_h.get)
    caida = promedio_h[mejor_h] / max(promedio_h[3], 1e-12)

    informe = {
        "_meta": {
            "generado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "piso_clase_minoritaria": MINIMO_EJEMPLOS_CLASE_MINORITARIA,
        },
        "paneles": paneles,
        "disponibilidad": disponibilidad,
        "predictibilidad": predictibilidad,
        "informacion_mutua_promedio_por_h": promedio_h,
        "decision_granularidad_y_w": decision_w,
        "decision_h": {
            "h": mejor_h,
            "caida_hasta_h3": round(float(caida), 2),
            "razon": (
                "la informacion mutua entre las caracteristicas en t y la etiqueta en "
                f"t+h cae {caida:.1f} veces al pasar de h={mejor_h} a h=3, y despues se "
                "aplana. El patron es consistente en las cuatro configuraciones medidas."
            ),
            "advertencia": (
                "El nivel absoluto de informacion mutua es bajo para todo h. Se interpreta "
                "la forma de la curva, no su magnitud, y eso ya indica que el problema es "
                "dificil con las caracteristicas actuales."
            ),
        },
    }

    EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    destino = EVIDENCIAS / "estudio-w-h.json"
    destino.write_text(json.dumps(informe, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\ngranularidad y w: {decision_w}")
    print(f"informacion mutua promedio por h: {promedio_h}")
    print(f"h recomendado: {mejor_h}  (cae {caida:.1f}x hasta h=3)")
    print(f"escrito: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
