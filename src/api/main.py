"""Backend de la aplicacion. Modulo del PM (M0).

Expone como JSON las funciones que ya existen en src/. No calcula nada: si una
metrica se calculara aqui y tambien en el arnes, tarde o temprano darian distinto
y nadie sabria cual va al informe (RF-U6).

Correr en desarrollo:
    uv run uvicorn src.api.main:app --reload --port 8000
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from contracts.config import ACTIVOS, GRANULARIDAD, HORIZONTE_H, PROVISIONAL, VENTANA_W
from contracts.labeling import etiquetar, latencia_real, objetivo, resumen_clases
from contracts.metrics import evaluar
from contracts.schema import cierre as serie_cierre
from src.modelos.base import BaselineTrivial
from src.sintetico.generador import serie_zigzag

# La ruta se deriva de GRANULARIDAD para que exista una sola fuente de verdad.
# Cuando el equipo congele la decision D1, cambiar contracts/config.py alcanza.
RUTA_PANEL = Path(f"data/processed/panel_{GRANULARIDAD}_v1.parquet")

app = FastAPI(title="Pronostico de puntos de inflexion en LTC", version="0.1.0")

# El frontend de Vite corre en otro puerto durante el desarrollo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _cargar_panel() -> pd.DataFrame:
    if not RUTA_PANEL.exists():
        raise HTTPException(
            status_code=503,
            detail=(
                f"todavia no existe {RUTA_PANEL}. Correr: uv run python scripts/spike_datos.py"
            ),
        )
    return pd.read_parquet(RUTA_PANEL)


@app.get("/api/config")
def configuracion() -> dict:
    """Parametros vigentes. La app los muestra para que nadie interprete un
    resultado sin saber con que w y h se produjo."""
    return {
        "activos": list(ACTIVOS),
        "granularidad": GRANULARIDAD,
        "w": VENTANA_W,
        "h": HORIZONTE_H,
        "latencia_real": latencia_real(VENTANA_W, HORIZONTE_H),
        "provisional": PROVISIONAL,
        "panel_disponible": RUTA_PANEL.exists(),
    }


@app.get("/api/sintetico")
def modo_sintetico(n: int = 300, semilla: int = 0, ruido: float = 0.0) -> dict:
    """Modo sintetico: serie con giros conocidos por construccion."""
    serie, _ = serie_zigzag(n=n, w=VENTANA_W, semilla=semilla, ruido=ruido)
    etiquetas = etiquetar(serie, VENTANA_W)
    modelo = BaselineTrivial()
    predichas = pd.Series(modelo.predecir(serie.to_frame()), index=serie.index)
    return {
        "fuente": "sintetico",
        "serie": _serializar(serie, etiquetas, predichas),
        "metricas": evaluar(objetivo(etiquetas, HORIZONTE_H), predichas),
    }


@app.get("/api/historico")
def modo_historico(activo: str = "LTC", desde: str | None = None, hasta: str | None = None) -> dict:
    """Modo historico: rango del panel real con etiquetas verdaderas."""
    if activo not in ACTIVOS:
        raise HTTPException(status_code=400, detail=f"activo desconocido: {activo}")

    panel = _cargar_panel()
    serie = serie_cierre(panel, activo)
    if desde:
        serie = serie[serie.index >= pd.Timestamp(desde, tz="UTC")]
    if hasta:
        serie = serie[serie.index <= pd.Timestamp(hasta, tz="UTC")]
    if serie.empty:
        raise HTTPException(status_code=404, detail="el rango pedido no tiene datos")

    etiquetas = etiquetar(serie, VENTANA_W)
    modelo = BaselineTrivial()
    predichas = pd.Series(modelo.predecir(serie.to_frame()), index=serie.index)
    return {
        "fuente": "historico",
        "activo": activo,
        "serie": _serializar(serie, etiquetas, predichas),
        "metricas": evaluar(objetivo(etiquetas, HORIZONTE_H), predichas),
        "balance": resumen_clases(etiquetas).to_dict(orient="records"),
    }


def _serializar(cierre: pd.Series, etiquetas: pd.Series, predichas: pd.Series) -> list[dict]:
    marco = pd.DataFrame(
        {
            "fecha": cierre.index.strftime("%Y-%m-%d"),
            "cierre": cierre.to_numpy(),
            "etiqueta": etiquetas.to_numpy(),
            "predicha": predichas.to_numpy(),
        }
    )
    return marco.astype(object).where(marco.notna(), None).to_dict(orient="records")
