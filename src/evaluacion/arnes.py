"""Arnes de evaluacion: el unico lugar donde se producen numeros comparables.

Cualquier modelo entra por aqui, con la misma particion y las mismas metricas.
Un resultado obtenido fuera de este modulo no entra al informe.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from contracts.config import DELTA_F1_DECISIVO
from contracts.metrics import evaluar
from contracts.splits import Particion
from src.evaluacion.reserva import consumir
from src.modelos.base import Modelo

RUTA_RESULTADOS = Path("docs/evidencias/resultados.csv")


def evaluar_modelo(
    modelo: Modelo,
    X: pd.DataFrame,
    y: pd.Series,
    particion: Particion,
    *,
    conjunto: str,
    motivo_reserva: str | None = None,
) -> dict:
    """Entrena con el bloque de entrenamiento y mide sobre el conjunto pedido.

    El entrenamiento siempre usa solo el bloque de entrenamiento, incluso cuando se
    mide sobre validacion: de otro modo la comparacion entre modelos dependeria de
    cuantos datos vio cada uno y no de su calidad.

    `conjunto` es obligatorio y solo por nombre. Antes tenia "prueba" por omision, o
    sea que la reserva era lo que salia si no se decia nada. Ningun llamador la
    omitia, pero un valor por omision que gasta el unico bloque no visto es una
    trampa esperando: la misma forma que `rezagos_relativos` en el PR #68, donde
    heredar el default desincronizo dos mitades de un archivo sin que cambiara una
    linea. Si equivocarse es silencioso, el parametro se pide.

    Medir sobre `prueba` pasa por el pestillo de `reserva.py`: la primera vez deja
    constancia y las siguientes fallan salvo que se pase `motivo_reserva`. Es la D18
    hecha comprobable en vez de afirmada.
    """
    mascaras = {
        "entrenamiento": particion.entrenamiento,
        "validacion": particion.validacion,
        "prueba": particion.prueba,
    }
    if conjunto not in mascaras:
        raise ValueError(f"conjunto desconocido: {conjunto!r}. Esperado uno de {list(mascaras)}")

    if conjunto == "prueba":
        consumir([modelo.nombre], motivo=motivo_reserva)

    entrenables = particion.entrenamiento & y.notna().to_numpy()
    modelo.entrenar(X[entrenables], y[entrenables])

    mascara = mascaras[conjunto] & y.notna().to_numpy()
    predicciones = modelo.predecir(X[mascara])

    resultado = evaluar(y[mascara], predicciones)
    resultado.update(
        {
            "modelo": modelo.nombre,
            "conjunto": conjunto,
            "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        }
    )
    return resultado


def comparar(resultados: list[dict]) -> pd.DataFrame:
    """Tabla ordenada por F1 macro, que es la metrica que decide (seccion 3.3 del PRD)."""
    tabla = pd.DataFrame(resultados)
    columnas = ["modelo", "conjunto", "n", "f1_macro", "precision_direccional", "exactitud"]
    resto = [c for c in tabla.columns if c not in columnas]
    return tabla[columnas + resto].sort_values("f1_macro", ascending=False).reset_index(drop=True)


def decidir(f1_fundacional: float, f1_avanzado: float) -> dict:
    """Aplica el criterio de decision fijado ANTES de medir.

    Si la diferencia es menor al umbral acordado gana el fundacional por simple.
    Esta funcion existe para que la decision no dependa de quien mire la tabla.
    """
    diferencia = f1_avanzado - f1_fundacional
    if abs(diferencia) < DELTA_F1_DECISIVO:
        ganador = "fundacional"
        razon = (
            f"diferencia de F1 macro ({diferencia:+.4f}) menor al umbral acordado "
            f"({DELTA_F1_DECISIVO}); se prefiere el modelo mas simple"
        )
    elif diferencia > 0:
        ganador = "avanzado"
        razon = f"el avanzado supera al fundacional por {diferencia:+.4f} de F1 macro"
    else:
        ganador = "fundacional"
        razon = f"el fundacional supera al avanzado por {-diferencia:+.4f} de F1 macro"
    return {"ganador": ganador, "diferencia_f1_macro": diferencia, "razon": razon}


def guardar_resultado(resultado: dict, ruta: Path = RUTA_RESULTADOS) -> None:
    """Anade una fila al historico versionado (RF-V3).

    Se anade en vez de sobrescribir para que quede el rastro de cada ejecucion con
    su fecha. Un resultado sin fecha no se puede auditar contra la version de los
    datos que lo produjo.
    """
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fila = pd.DataFrame([resultado])
    if ruta.exists():
        fila.to_csv(ruta, mode="a", header=False, index=False)
    else:
        fila.to_csv(ruta, index=False)


def guardar_json(datos: dict, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
