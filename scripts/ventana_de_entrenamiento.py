"""Entrenar con todo el pasado, o solo con lo reciente. El eje numero veinte.

Por que este eje, y por que no estaba
-------------------------------------
Los diecinueve ejes medidos hasta ahora tocaron la etiqueta, los datos, el umbral,
las familias, la regla de decision y los hiperparametros. **Ninguno toco cuanta
historia usa el modelo para entrenar.** La validacion deslizante del proyecto usa
**ventana expansiva**: cada tramo entrena con *todo* el pasado disponible, y eso
nunca se puso a prueba -- se heredo como parte del arnes.

Y el diagnostico del proyecto lo senala directamente. Medimos que la relacion entre
lo que el modelo ve y el giro que viene **no aguanta entre periodos**, y medimos que
anadir veintisiete meses de historia **empeora**. Si las dos cosas son ciertas,
entrenar con todo el pasado esta metiendo regimen viejo que ya no aplica, y la
consecuencia directa es **entrenar solo con lo reciente**: ventana deslizante.

Ese razonamiento es una prediccion falsable, no una mejora garantizada. Puede fallar
por un motivo igual de concreto: recortar la historia deja **menos giros** para
aprender, y el desbalance de este problema (4,6 % de clase rara) castiga mucho quitar
ejemplos. Las dos fuerzas tiran en direcciones opuestas y por eso hay que medirlo.

El criterio, fijado ANTES de correr
-----------------------------------
Se adopta la ventana deslizante **solo si se cumplen las tres**, sobre los nueve
tramos de la validacion deslizante:

1. Su **media de F1 macro** supera a la de la ventana expansiva.
2. La diferencia supera **0,02**, que es el umbral de decision del proyecto: por
   debajo de eso no distinguimos configuraciones del ruido entre semillas.
3. El signo de la diferencia es **estable en al menos 8 de los 9 tramos**. Una media
   que tapa tramos en contra no sirve para decidir.

Si mejora pero no llega al umbral, la conclusion es **que no se establece**, y se
publica asi. Si empeora, es **evidencia directa** a favor del diagnostico que hoy se
sostiene sobre evidencia indirecta, y tambien vale.

La expectativa, tambien antes de mirar
--------------------------------------
Se espera que **las ventanas muy cortas empeoren** (se quedan sin giros) y que exista
un punto intermedio donde el recorte de regimen viejo compense la perdida de
ejemplos. Si ese punto intermedio **no aparece** -- si la curva es monotona y la
expansiva gana -- entonces la historia vieja **no estorba**, y el diagnostico habra
que decirlo de otra forma: no es que el pasado lejano confunda, es que el pasado
cercano tampoco informa.

Que NO hace
-----------
**No toca el bloque de prueba.** Mide sobre los nueve tramos de validacion, que son
datos fuera de muestra y que si se pueden volver a mirar. No cambia el modelo ni sus
hiperparametros: cambia unicamente **que filas ve al entrenar**.

Punto de entrada:
    uv run python scripts/ventana_de_entrenamiento.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from contracts.config import ACTIVO_OBJETIVO, GRANULARIDAD, HORIZONTE_H, VENTANA_W  # noqa: E402
from contracts.labeling import Clase, etiquetar, objetivo  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from src.features.base import construir  # noqa: E402
from src.modelos.clasico import HIPERPARAMETROS, BosqueAleatorio  # noqa: E402

SALIDA = RAIZ / "docs" / "evidencias" / "m0-ventana-entrenamiento-4h-w7-h1.json"

N_TRAMOS = 9
UMBRAL_DECISION = 0.02
TRAMOS_MINIMOS = 8

#: `None` es la ventana expansiva que usa hoy el proyecto: todo el pasado.
#: Las demas son ventanas deslizantes de largo fijo, en velas de 4 horas.
#: 1 500 velas son unos 8 meses; 6 000, unos 33.
VENTANAS: list[int | None] = [None, 1500, 3000, 4500, 6000]

RARAS = (int(Clase.MAXIMO), int(Clase.MINIMO))


def nombre(ventana: int | None) -> str:
    return "expansiva" if ventana is None else f"deslizante_{ventana}"


def filas_de_entrenamiento(
    validos: np.ndarray, inicio: int, embargo: int, ventana: int | None
) -> np.ndarray:
    """Que filas ve el modelo: todo el pasado, o solo las ultimas `ventana`."""
    fin = max(0, inicio - embargo)
    if ventana is None:
        return validos[:fin]
    return validos[max(0, fin - ventana) : fin]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    panel = pd.read_parquet(RAIZ / "data" / "processed" / f"panel_{GRANULARIDAD}_v1.parquet")
    X = construir(panel, rezagos_relativos=True)
    y = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), VENTANA_W), HORIZONTE_H)

    validos = np.flatnonzero(y.notna().to_numpy())
    embargo = VENTANA_W + HORIZONTE_H
    corte = len(validos) // 2
    ancho = (len(validos) - corte) // N_TRAMOS

    por_ventana: dict[str, dict] = {
        nombre(v): {"f1_por_tramo": [], "filas_por_tramo": []} for v in VENTANAS
    }

    cabecera = " ".join(f"{nombre(v):>18}" for v in VENTANAS)
    print(f"{'tramo':>6} {'evalua':>7} {'giros':>6} " + cabecera)
    for i in range(N_TRAMOS):
        inicio = corte + i * ancho
        fin = inicio + ancho if i < N_TRAMOS - 1 else len(validos)
        tramo = validos[inicio:fin]
        verdad = y.iloc[tramo].astype(int).to_numpy()
        n_giros = int(np.isin(verdad, RARAS).sum())

        celdas = []
        for v in VENTANAS:
            entrenar_en = filas_de_entrenamiento(validos, inicio, embargo, v)
            clave = nombre(v)
            if len(entrenar_en) == 0:
                por_ventana[clave]["f1_por_tramo"].append(None)
                por_ventana[clave]["filas_por_tramo"].append(0)
                celdas.append(f"{'sin datos':>18}")
                continue
            bosque = BosqueAleatorio(
                n_arboles=HIPERPARAMETROS["n_estimators"],
                semilla=HIPERPARAMETROS["random_state"],
                nombre=f"bosque_{clave}",
            )
            bosque.entrenar(X.iloc[entrenar_en], y.iloc[entrenar_en])
            pred = np.asarray(bosque.predecir(X.iloc[tramo]), dtype=int)
            f1 = float(f1_score(verdad, pred, average="macro", zero_division=0))
            por_ventana[clave]["f1_por_tramo"].append(round(f1, 6))
            por_ventana[clave]["filas_por_tramo"].append(int(len(entrenar_en)))
            celdas.append(f"{f1:>18.6f}")
        print(f"{i:>6} {len(tramo):>7} {n_giros:>6} " + " ".join(celdas))

    base = por_ventana["expansiva"]["f1_por_tramo"]
    for clave, datos in por_ventana.items():
        valores = [f for f in datos["f1_por_tramo"] if f is not None]
        datos["media"] = round(float(np.mean(valores)), 6) if valores else None
        datos["filas_medianas"] = int(np.median(datos["filas_por_tramo"]))
        if clave == "expansiva":
            continue
        diferencias = [
            round(a - b, 6)
            for a, b in zip(datos["f1_por_tramo"], base, strict=True)
            if a is not None and b is not None
        ]
        datos["diferencia_por_tramo"] = diferencias
        datos["diferencia_media"] = round(float(np.mean(diferencias)), 6) if diferencias else None
        datos["tramos_a_favor"] = int(sum(1 for d in diferencias if d > 0))
        datos["cumple_criterio"] = bool(
            datos["diferencia_media"] is not None
            and datos["diferencia_media"] > UMBRAL_DECISION
            and datos["tramos_a_favor"] >= TRAMOS_MINIMOS
        )

    candidatas = [c for c, d in por_ventana.items() if d.get("cumple_criterio")]
    if candidatas:
        mejor = max(candidatas, key=lambda c: por_ventana[c]["diferencia_media"])
        veredicto = (
            f"Se adopta {mejor}: supera a la expansiva por "
            f"{por_ventana[mejor]['diferencia_media']:.6f} en la media y le gana en "
            f"{por_ventana[mejor]['tramos_a_favor']} de {N_TRAMOS} tramos."
        )
    else:
        mejores = sorted(
            (c for c in por_ventana if c != "expansiva"),
            key=lambda c: por_ventana[c]["diferencia_media"] or -9,
            reverse=True,
        )
        arriba = mejores[0]
        veredicto = (
            "No se adopta ninguna ventana deslizante: ninguna cumple las tres condiciones. "
            f"La mejor es {arriba}, con una diferencia media de "
            f"{por_ventana[arriba]['diferencia_media']:.6f} y "
            f"{por_ventana[arriba]['tramos_a_favor']} de {N_TRAMOS} tramos a favor."
        )

    print()
    print(veredicto)

    SALIDA.write_text(
        json.dumps(
            {
                "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                "que_mide": (
                    "Si entrenar solo con lo reciente (ventana deslizante) mejora sobre "
                    "entrenar con todo el pasado (ventana expansiva), que es lo que usa hoy "
                    "el arnes del proyecto. Es el unico eje que toca que filas ve el modelo "
                    "al entrenar."
                ),
                "por_que_este_eje": (
                    "El diagnostico del proyecto dice que la relacion no aguanta entre "
                    "periodos, y que mas historia empeora. La consecuencia directa de las dos "
                    "cosas es recortar la historia de entrenamiento, y eso no se habia medido."
                ),
                "criterio_preregistrado": (
                    f"Media de F1 macro mayor que la expansiva, diferencia mayor que "
                    f"{UMBRAL_DECISION}, y signo estable en al menos {TRAMOS_MINIMOS} de "
                    f"{N_TRAMOS} tramos."
                ),
                "expectativa_declarada_antes": (
                    "Que las ventanas muy cortas empeoren por falta de giros, y que exista un "
                    "punto intermedio donde recortar regimen viejo compense. Si no aparece, la "
                    "historia vieja no estorba y el diagnostico hay que decirlo de otra forma."
                ),
                "no_toca_la_reserva": "Nueve tramos de validacion deslizante.",
                "umbral_decision": UMBRAL_DECISION,
                "tramos_minimos": TRAMOS_MINIMOS,
                "resultados": por_ventana,
                "veredicto": veredicto,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nEvidencia en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
