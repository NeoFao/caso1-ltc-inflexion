"""Congela un snapshot de datos para que la aplicacion funcione sin backend.

Cumple RF-U5: la app tiene que arrancar y ser usable sin conexion, con el ultimo
dato cacheado y mostrando su antiguedad. De paso permite publicarla en GitHub
Pages, que solo sirve archivos estaticos.

Lo importante: el snapshot lo produce Python llamando a los mismos contratos que
usa el backend. La aplicacion sigue sin calcular nada (RF-U6); solo cambia de
donde lee. Si esto se reimplementara en TypeScript, tendriamos dos definiciones
de punto de inflexion y dos de F1, y tarde o temprano darian distinto.

Uso:
    uv run python scripts/exportar_estatico.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from contracts.config import (  # noqa: E402
    ACTIVOS,
    GRANULARIDAD,
    HORIZONTE_H,
    PROVISIONAL,
    VENTANA_W,
)
from contracts.labeling import etiquetar, latencia_real, objetivo, resumen_clases  # noqa: E402
from contracts.metrics import evaluar  # noqa: E402
from contracts.schema import cierre as serie_cierre  # noqa: E402
from src.modelos.base import BaselineTrivial  # noqa: E402
from src.sintetico.generador import serie_zigzag  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
DESTINO = RAIZ / "app" / "public" / "datos"

# Cuantas velas se exportan por activo. Es un recorte de presentacion, no de
# analisis: las metricas del informe salen del panel completo, no de esto.
VELAS_EXPORTADAS = 1200


def _serie_a_puntos(cierre: pd.Series, etiquetas: pd.Series, predichas: pd.Series) -> list[dict]:
    marco = pd.DataFrame(
        {
            "fecha": cierre.index.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "cierre": cierre.round(6).to_numpy(),
            "etiqueta": etiquetas.to_numpy(),
            "predicha": predichas.to_numpy(),
        }
    )
    return marco.astype(object).where(marco.notna(), None).to_dict(orient="records")


def main() -> None:
    ruta_panel = RAIZ / "data" / "processed" / f"panel_{GRANULARIDAD}_v1.parquet"
    if not ruta_panel.exists():
        raise SystemExit(f"falta {ruta_panel}. Correr antes: uv run python scripts/spike_datos.py")

    panel = pd.read_parquet(ruta_panel)
    modelo = BaselineTrivial()
    generado = datetime.now(UTC).isoformat(timespec="seconds")

    DESTINO.mkdir(parents=True, exist_ok=True)

    configuracion = {
        "activos": list(ACTIVOS),
        "granularidad": GRANULARIDAD,
        "w": VENTANA_W,
        "h": HORIZONTE_H,
        "latencia_real": latencia_real(VENTANA_W, HORIZONTE_H),
        "provisional": PROVISIONAL,
        "panel_disponible": True,
        "modelo": modelo.nombre,
        "generado_utc": generado,
        "panel": {
            "filas_totales": int(len(panel)),
            "desde": panel.index.min().isoformat(),
            "hasta": panel.index.max().isoformat(),
            "velas_exportadas_por_activo": VELAS_EXPORTADAS,
        },
    }
    (DESTINO / "config.json").write_text(
        json.dumps(configuracion, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    serie, _ = serie_zigzag(n=300, w=VENTANA_W, semilla=0, ruido=0.0)
    etiquetas = etiquetar(serie, VENTANA_W)
    predichas = pd.Series(modelo.predecir(serie.to_frame()), index=serie.index)
    sintetico = {
        "fuente": "sintetico",
        "modelo": modelo.nombre,
        "generado_utc": generado,
        "serie": _serie_a_puntos(serie, etiquetas, predichas),
        "metricas": evaluar(objetivo(etiquetas, HORIZONTE_H), predichas),
    }
    (DESTINO / "sintetico.json").write_text(
        json.dumps(sintetico, ensure_ascii=False), encoding="utf-8"
    )

    for activo in ACTIVOS:
        cierre = serie_cierre(panel, activo).tail(VELAS_EXPORTADAS)
        etiquetas = etiquetar(cierre, VENTANA_W)
        predichas = pd.Series(modelo.predecir(cierre.to_frame()), index=cierre.index)
        historico = {
            "fuente": "historico",
            "activo": activo,
            "modelo": modelo.nombre,
            "generado_utc": generado,
            "serie": _serie_a_puntos(cierre, etiquetas, predichas),
            "metricas": evaluar(objetivo(etiquetas, HORIZONTE_H), predichas),
            "balance": resumen_clases(etiquetas).to_dict(orient="records"),
        }
        (DESTINO / f"historico-{activo}.json").write_text(
            json.dumps(historico, ensure_ascii=False), encoding="utf-8"
        )

    total = sum(f.stat().st_size for f in DESTINO.glob("*.json"))
    print(f"snapshot en {DESTINO.relative_to(RAIZ)}")
    print(f"  {len(list(DESTINO.glob('*.json')))} archivos, {total / 1024:.0f} KiB")
    print(f"  panel {GRANULARIDAD}: {len(panel)} filas, ultimas {VELAS_EXPORTADAS} por activo")
    print(f"  generado_utc: {generado}")


if __name__ == "__main__":
    main()
