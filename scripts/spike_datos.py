"""Primera medicion del proyecto: cuantos datos hay y como quedan las clases.

Responde con numeros las decisiones D1, D2 y D3 del PRD, que hasta ahora estaban
apoyadas en supuestos. Produce:

    data/processed/panel_<intervalo>_v1.parquet   artefacto congelado que consumen los cuatro
    data/raw/MANIFEST.json             fuente, fecha y hash de cada descarga
    docs/evidencias/spike-datos.json   la medicion completa
    docs/evidencias/*.png              figuras del balance y de la serie etiquetada

Uso:
    uv run python scripts/spike_datos.py
    uv run python scripts/spike_datos.py --intervalo 4h
    uv run python scripts/spike_datos.py --sin-descargar   (reusa lo ya bajado)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

# El proyecto no se instala como paquete, asi que un script ejecutado directamente
# no encuentra contracts/ ni src/. Anadir la raiz aqui hace que funcione desde
# cualquier directorio, que es una friccion menos para quien recien arranca.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from contracts.config import (  # noqa: E402
    ACTIVO_OBJETIVO,
    ACTIVOS,
    MINIMO_EJEMPLOS_CLASE_MINORITARIA,
)
from contracts.labeling import Clase, cota_superior_extremos, etiquetar, objetivo, resumen_clases
from contracts.schema import cierre as serie_cierre
from contracts.splits import particionar
from src.panel.consolidacion import consolidar, informe_huecos
from src.panel.descarga import descargar_todos
from src.visual import estilo

RAIZ = Path(__file__).resolve().parents[1]
CRUDO = RAIZ / "data" / "raw"
PROCESADO = RAIZ / "data" / "processed"
EVIDENCIAS = RAIZ / "docs" / "evidencias"

REJILLA_W = (3, 5, 7, 10, 15)
REJILLA_H = (1, 3, 5)


def cargar_crudo(intervalo: str) -> dict[str, pd.DataFrame]:
    series = {}
    for activo in ACTIVOS:
        ruta = CRUDO / f"{activo}_{intervalo}.parquet"
        if not ruta.exists():
            raise FileNotFoundError(f"falta {ruta}. Correr sin --sin-descargar.")
        series[activo] = pd.read_parquet(ruta)
    return series


def medir_rejilla(cierre: pd.Series, intervalo: str) -> list[dict]:
    """Balance de clases y ejemplos disponibles para cada (w, h) candidato.

    El conteo que decide es el de la clase minoritaria EN ENTRENAMIENTO, no en el
    total: es el unico numero que dice si el modelo tiene de donde aprender.
    """
    filas = []
    for w in REJILLA_W:
        etiquetas = etiquetar(cierre, w)
        resumen = resumen_clases(etiquetas)
        porcentajes = dict(zip(resumen["clase"], resumen["porcentaje"], strict=True))

        for h in REJILLA_H:
            y = objetivo(etiquetas, h)
            try:
                particion = particionar(n=len(y), w=w, h=h)
            except ValueError as error:
                filas.append({"intervalo": intervalo, "w": w, "h": h, "error": str(error)})
                continue

            entrenamiento = y[particion.entrenamiento].dropna().astype(int)
            conteos = {
                clase.name.lower(): int((entrenamiento == int(clase)).sum()) for clase in Clase
            }
            minoritaria = min(conteos.values())

            filas.append(
                {
                    "intervalo": intervalo,
                    "w": w,
                    "h": h,
                    "cota_teorica_extremos_pct": round(100 * cota_superior_extremos(w), 3),
                    "pct_maximo": porcentajes.get("Maximo", 0.0),
                    "pct_minimo": porcentajes.get("Minimo", 0.0),
                    "pct_continuidad": porcentajes.get("Continuidad", 0.0),
                    "n_entrenamiento": int(len(entrenamiento)),
                    **{f"n_train_{k}": v for k, v in conteos.items()},
                    "n_clase_minoritaria": minoritaria,
                    "cumple_criterio": minoritaria >= MINIMO_EJEMPLOS_CLASE_MINORITARIA,
                }
            )
    return filas


def aplicar_criterio(filas: list[dict]) -> dict:
    """Criterio fijado ANTES de medir (seccion 8 de docs/00-definicion-punto-inflexion.md):
    el w mas grande que deje al menos MINIMO_EJEMPLOS_CLASE_MINORITARIA en entrenamiento.

    Se prefiere el w mas grande porque detecta giros mas significativos; el piso
    existe para que el modelo tenga de donde aprender. Si ninguna combinacion
    cumple, se dice, no se baja el umbral para que salga algo.
    """
    validas = [f for f in filas if f.get("cumple_criterio")]
    if not validas:
        return {
            "recomendacion": None,
            "razon": (
                "ninguna combinacion alcanza el piso de "
                f"{MINIMO_EJEMPLOS_CLASE_MINORITARIA} ejemplos de la clase minoritaria "
                "en entrenamiento. Hay que bajar la granularidad o revisar el criterio, "
                "y la decision es del equipo."
            ),
        }
    mejor = max(validas, key=lambda f: (f["w"], f["h"]))
    return {
        "recomendacion": {"w": mejor["w"], "h": mejor["h"], "intervalo": mejor["intervalo"]},
        "razon": (
            f"w={mejor['w']} es el mayor que deja {mejor['n_clase_minoritaria']} ejemplos "
            f"de la clase minoritaria en entrenamiento, por encima del piso de "
            f"{MINIMO_EJEMPLOS_CLASE_MINORITARIA} acordado antes de medir."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intervalo", default="1d", help="1d, 4h, 1h")
    parser.add_argument("--desde", default="2017-01-01")
    parser.add_argument("--sin-descargar", action="store_true")
    argumentos = parser.parse_args()

    print(f"[1/5] Datos crudos ({argumentos.intervalo})")
    if argumentos.sin_descargar:
        series = cargar_crudo(argumentos.intervalo)
    else:
        series = descargar_todos(argumentos.intervalo, CRUDO, desde=argumentos.desde)

    huecos = informe_huecos(series, argumentos.intervalo)
    print(huecos.to_string(index=False))

    print("\n[2/5] Consolidacion")
    panel = consolidar(series)
    PROCESADO.mkdir(parents=True, exist_ok=True)
    ruta_panel = PROCESADO / f"panel_{argumentos.intervalo}_v1.parquet"
    panel.to_parquet(ruta_panel)
    print(f"  panel: {len(panel)} filas x {len(panel.columns)} columnas")
    print(f"  ventana comun: {panel.index.min().date()} -> {panel.index.max().date()}")
    print(f"  escrito: {ruta_panel.relative_to(RAIZ)}")

    print("\n[3/5] Balance de clases por (w, h)")
    cierre = serie_cierre(panel, ACTIVO_OBJETIVO)
    filas = medir_rejilla(cierre, argumentos.intervalo)
    tabla = pd.DataFrame([f for f in filas if "error" not in f])
    columnas = [
        "w", "h", "cota_teorica_extremos_pct", "pct_maximo", "pct_minimo",
        "n_entrenamiento", "n_clase_minoritaria", "cumple_criterio",
    ]
    print(tabla[columnas].to_string(index=False))

    print("\n[4/5] Criterio de decision")
    decision = aplicar_criterio(filas)
    print(f"  {decision['razon']}")
    if decision["recomendacion"]:
        print(f"  recomendacion: {decision['recomendacion']}")

    print("\n[5/5] Figuras")
    estilo.aplicar()
    w_figura = decision["recomendacion"]["w"] if decision["recomendacion"] else REJILLA_W[1]
    etiquetas = etiquetar(cierre, w_figura)

    figura_balance = estilo.grafico_distribucion_clases(
        resumen_clases(etiquetas),
        titulo=f"Balance de clases — {ACTIVO_OBJETIVO}, w={w_figura}, {argumentos.intervalo}",
    )
    estilo.guardar(figura_balance, f"balance-clases-{argumentos.intervalo}-w{w_figura}", EVIDENCIAS)

    ultimos = cierre.tail(220)
    figura_serie = estilo.grafico_serie_con_giros(
        ultimos,
        etiquetas.reindex(ultimos.index),
        titulo=f"{ACTIVO_OBJETIVO}: puntos de inflexion detectados (w={w_figura})",
    )
    estilo.guardar(figura_serie, f"serie-giros-{argumentos.intervalo}-w{w_figura}", EVIDENCIAS)

    informe = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "intervalo": argumentos.intervalo,
        "panel": {
            "filas": int(len(panel)),
            "columnas": int(len(panel.columns)),
            "desde": panel.index.min().isoformat(),
            "hasta": panel.index.max().isoformat(),
        },
        "cobertura_por_activo": huecos.astype(str).to_dict(orient="records"),
        "rejilla": filas,
        "decision": decision,
        "criterio_fijado_antes_de_medir": {
            "minimo_ejemplos_clase_minoritaria": MINIMO_EJEMPLOS_CLASE_MINORITARIA,
            "regla": "el w mas grande que cumpla el piso",
        },
    }
    EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    destino = EVIDENCIAS / f"spike-datos-{argumentos.intervalo}.json"
    destino.write_text(json.dumps(informe, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  informe: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
