"""Donde caen los extremos que predice cada modelo en la prueba 2 sintetica.

Por que existe. La prueba 2 dio al iTransformer un F1 de maximos de exactamente cero,
y se explico asi: "una trayectoria demasiado suave nunca produce un maximo estricto
--hacen falta catorce desigualdades-- y el resultado es cero maximos, no pocos". Esa
explicacion es una afirmacion sobre lo que el modelo PREDICE, y el F1 no la mide: un
F1 de cero sale igual si el modelo no predice ningun maximo que si predice muchos y
ninguno cae en su sitio.

Aqui se mide lo que el F1 esconde: cuantos extremos predice cada modelo, cuantos caen
exactamente sobre uno real, y a que distancia caen los demas.

Reproduce la prueba publicada, no una parecida. Carga las funciones del propio guion
de M0 --la serie, el panel, la particion y las fabricas de modelos-- y antes de contar
nada comprueba que el F1 de maximos y de minimos coincida con el que registra
`pruebas-deteccion-profundos.json`. Si no coincide, se detiene: estaria midiendo otra
cosa.

Salidas:
    docs/evidencias/m3-desfase-puente-sintetico.json

Uso:
    uv sync --group dev --group modelos
    uv run python -m src.modelos.desfase_puente_sintetico
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from contracts.labeling import Clase, etiquetar, objetivo
from contracts.metrics import evaluar
from contracts.schema import cierre
from contracts.splits import particionar

RAIZ = Path(__file__).resolve().parents[2]
EVIDENCIAS = RAIZ / "docs" / "evidencias"
PUBLICADA = EVIDENCIAS / "pruebas-deteccion-profundos.json"
DESTINO = EVIDENCIAS / "m3-desfase-puente-sintetico.json"
GUION = RAIZ / "scripts" / "pruebas_deteccion_profundos.py"

TOLERANCIAS = (0, 1, 2, 3)
MODELOS = ("bosque_aleatorio", "chronos_bolt", "itransformer")


def _guion_publicado():
    """El guion de M0, cargado tal cual, para que la construccion sea la misma."""
    spec = importlib.util.spec_from_file_location("pruebas_deteccion_profundos", GUION)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _ubicacion(posiciones, verdad, prediccion, clase, opuesta) -> dict:
    """Cuantos extremos de `clase` predice, y a que distancia del real mas cercano."""
    reales = posiciones[verdad == clase]
    predichos = posiciones[prediccion == clase]
    distancias = np.array([np.min(np.abs(reales - q)) for q in predichos])
    # real menos predicho: negativo es que el modelo marca el giro DESPUES del real.
    desfases = np.array([reales[np.argmin(np.abs(reales - q))] - q for q in predichos])
    return {
        "reales": int(len(reales)),
        "predichos": int(len(predichos)),
        "aciertos_exactos": int(((prediccion == clase) & (verdad == clase)).sum()),
        "a_lo_sumo_k_velas_del_real_mas_cercano": {
            str(k): int((distancias <= k).sum()) for k in TOLERANCIAS
        },
        "caen_sobre_la_clase_opuesta": int(((prediccion == clase) & (verdad == opuesta)).sum()),
        "desfase_mediano_real_menos_predicho": (
            float(np.median(desfases)) if len(desfases) else None
        ),
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    guion = _guion_publicado()
    publicada = json.loads(PUBLICADA.read_text(encoding="utf-8"))["resultados"]

    indice = pd.date_range(
        "2020-01-01", periods=guion.N_SINTETICO, freq=guion.GRANULARIDAD, tz="UTC", name="fecha"
    )
    serie, _ = guion.serie_zigzag(n=guion.N_SINTETICO, w=guion.VENTANA_W, semilla=0, ruido=0.0)
    serie.index = indice
    panel = guion._panel_desde_serie(serie)
    X = guion.construir(panel)
    etiquetas = etiquetar(cierre(panel, guion.ACTIVO_OBJETIVO), guion.VENTANA_W)
    y = objetivo(etiquetas, guion.HORIZONTE_H)
    particion = particionar(n=len(y), w=guion.VENTANA_W, h=guion.HORIZONTE_H)
    entrenables = particion.entrenamiento & y.notna().to_numpy()
    evaluables = particion.validacion & y.notna().to_numpy()

    posiciones = np.flatnonzero(evaluables)
    verdad = y[evaluables].astype(int).to_numpy()
    maximo, minimo = int(Clase.MAXIMO), int(Clase.MINIMO)

    por_modelo = {}
    for nombre in MODELOS:
        modelo = guion._fabricas(panel)[nombre]()
        modelo.entrenar(X[entrenables], y[entrenables].astype(int).to_numpy())
        prediccion = np.asarray(modelo.predecir(X[evaluables]), dtype=int)

        # Control: si el F1 no es el publicado, esto no es la prueba 2 y no se sigue.
        r = evaluar(verdad, prediccion)
        esperado = publicada[nombre]["2_sintetico_modelo_completo"]
        for clave in ("f1_maximo", "f1_minimo"):
            if round(r[clave], 6) != esperado[clave]:
                raise SystemExit(
                    f"{nombre}: {clave} recalculado {round(r[clave], 6)} y publicado "
                    f"{esperado[clave]}. No se esta reproduciendo la prueba 2; no se mide."
                )

        por_modelo[nombre] = {
            "f1_maximo_coincide_con_la_publicada": esperado["f1_maximo"],
            "f1_minimo_coincide_con_la_publicada": esperado["f1_minimo"],
            "maximos": _ubicacion(posiciones, verdad, prediccion, maximo, minimo),
            "minimos": _ubicacion(posiciones, verdad, prediccion, minimo, maximo),
        }
        mx = por_modelo[nombre]["maximos"]
        print(
            f"  {nombre:18} predice {mx['predichos']} maximos, {mx['aciertos_exactos']} exactos, "
            f"{mx['a_lo_sumo_k_velas_del_real_mas_cercano']['1']} a <=1 vela"
        )

    it = por_modelo["itransformer"]["maximos"]
    medido = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "pregunta": (
            "El F1 de maximos cero del iTransformer en la prueba 2 es porque no predice "
            "maximos, o porque los predice y no caen en su sitio?"
        ),
        "metodo": (
            "Reproduce la prueba 2 con las funciones del guion publicado y comprueba que "
            "el F1 de maximos y de minimos de cada modelo coincida con "
            "pruebas-deteccion-profundos.json antes de contar. Solo cuenta predicciones; "
            "no toca la reserva."
        ),
        "filas_evaluadas": int(evaluables.sum()),
        "por_modelo": por_modelo,
        "veredicto": {
            "el_itransformer_predice_maximos": bool(it["predichos"] > 0),
            "lectura": (
                "Si predice maximos, la explicacion 'una trayectoria suave nunca produce un "
                "maximo estricto' no se sostiene: el puente si los produce, y el F1 cero "
                "viene de donde caen, no de que falten. Con 14 extremos reales por clase, "
                "la diferencia entre 0 y 2 aciertos tampoco distingue 'cero' de 'pocos'."
            ),
        },
    }
    EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nmedido: {DESTINO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
