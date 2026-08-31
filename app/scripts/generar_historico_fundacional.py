"""Precalcula las predicciones del modelo fundacional para el panel de la app (S3-M1-01).

Por que precalculado y no en vivo: Chronos-Bolt mide ~12,6 ms/vela una vez cargado
(medido en esta maquina), y cargar el modelo la primera vez toma otros ~11 s. Sobre
el panel completo de LTC (13 114 velas) eso son minutos, muy por encima de cualquier
timeout razonable de una peticion HTTP. Y conectar un modelo cargado en memoria al
backend en vivo es un cambio de arquitectura de src/api/, que no es carpeta de M1.

Por eso este script -- que si es mio, vive en app/scripts/ -- corre el modelo UNA
VEZ, offline, sobre la misma ventana de validacion que ya midio M3
(contracts/splits.particionar, igual w y h que el contrato), y dejar el resultado
como snapshot estatico en app/public/datos/. La app lo consume igual que ya
consume historico-LTC.json: sin backend de por medio.

Se restringe a LTC y a la ventana de validacion (no a cualquier rango) a proposito:
es lo que se puede ofrecer sin tocar src/api/ ni esperar minutos por peticion. El
selector de modelo en la app fija el rango a esta misma ventana en los dos modelos
cuando se elige Fundacional, para que la comparacion sea sobre el mismo periodo.

Control de reproducibilidad: las metricas que calcula este script sobre la ventana
de validacion se comparan contra las ya publicadas en
docs/evidencias/m3-modelos-profundos-4h-w7-h1.json. Si no coinciden, el script
avisa en vez de escribir un numero que contradice la evidencia ya verificada.

Uso:
    uv run python app/scripts/generar_historico_fundacional.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

import pandas as pd  # noqa: E402

from contracts.config import GRANULARIDAD, HORIZONTE_H, VENTANA_W  # noqa: E402
from contracts.labeling import etiquetar, objetivo  # noqa: E402
from contracts.metrics import evaluar  # noqa: E402
from contracts.schema import cierre as serie_cierre  # noqa: E402
from contracts.splits import particionar  # noqa: E402
from src.modelos.fundacional import ChronosBolt  # noqa: E402

DESTINO = RAIZ / "app" / "public" / "datos" / "historico-fundacional-LTC.json"
EVIDENCIA_M3 = RAIZ / "docs" / "evidencias" / "m3-modelos-profundos-4h-w7-h1.json"
TOLERANCIA = 0.005


def _serializar(cierre: pd.Series, etiquetas: pd.Series, predichas: pd.Series) -> list[dict]:
    # Mismo formato que src/api/main.py._serializar (fecha ISO completa, no solo la
    # fecha): se reimplementa en vez de importarla porque src/api/ no es mi carpeta.
    marco = pd.DataFrame(
        {
            "fecha": cierre.index.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
            "cierre": cierre.to_numpy(),
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
    serie = serie_cierre(panel, "LTC")

    particion = particionar(len(serie), VENTANA_W, HORIZONTE_H)
    mascara = particion.validacion
    print(f"panel LTC: {len(serie)} velas totales, {int(mascara.sum())} en validacion")

    modelo = ChronosBolt(serie, w=VENTANA_W, h=HORIZONTE_H)
    print("cargando Chronos-Bolt (unico paso lento, ~11 s con pesos en cache)...")
    modelo.entrenar(pd.DataFrame(), pd.Series(dtype=int))

    X = serie.iloc[mascara].to_frame()
    predichas = pd.Series(modelo.predecir(X), index=X.index)

    etiquetas_completas = etiquetar(serie, VENTANA_W)
    objetivo_completo = objetivo(etiquetas_completas, HORIZONTE_H)

    cierre_val = serie.iloc[mascara]
    etiquetas_val = etiquetas_completas.iloc[mascara]
    objetivo_val = objetivo_completo.iloc[mascara]

    metricas = evaluar(objetivo_val, predichas)

    if EVIDENCIA_M3.exists():
        publicado = json.loads(EVIDENCIA_M3.read_text(encoding="utf-8"))["metricas"]["chronos_bolt"]
        for campo in ("f1_macro", "precision_direccional", "exactitud"):
            propio, conocido = metricas[campo], publicado[campo]
            if abs(propio - conocido) > TOLERANCIA:
                raise SystemExit(
                    f"{campo}={propio:.4f} no reproduce el {conocido:.4f} ya publicado en "
                    f"{EVIDENCIA_M3.relative_to(RAIZ)} (tolerancia {TOLERANCIA}). "
                    "No se escribe el snapshot con un numero que no cuadra."
                )
        print(f"control: los {3} campos comparados reproducen la evidencia de M3.")
    else:
        print(f"aviso: no encontre {EVIDENCIA_M3.relative_to(RAIZ)}; sigo sin el control cruzado.")

    salida = {
        "fuente": "historico",
        "activo": "LTC",
        "modelo": modelo.nombre,
        "generado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "serie": _serializar(cierre_val, etiquetas_val, predichas),
        "metricas": {k: (round(v, 4) if isinstance(v, float) else v) for k, v in metricas.items()},
        "ventana": {
            "desde": cierre_val.index.min().isoformat(),
            "hasta": cierre_val.index.max().isoformat(),
            "conjunto": "validacion",
            "nota": (
                "Ventana fija (particion de validacion del contrato). El modelo fundacional "
                "tarda demasiado para correr en vivo sobre un rango arbitrario; ver docstring."
            ),
        },
    }

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"escrito {DESTINO.relative_to(RAIZ)} con {len(salida['serie'])} velas")


if __name__ == "__main__":
    main()
