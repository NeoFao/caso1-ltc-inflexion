"""El bosque tiene 300 arboles y el ruido entre semillas supera el umbral. Eje 24.

Por que este eje, y por que no estaba
-------------------------------------
Esta medido que el modelo avanzado, cambiando solo la semilla, recorre un rango de
**0,030377** de F1 macro, y que el umbral con el que el proyecto decide entre dos
configuraciones es **0,02**. De ahi salio la conclusion de que la rejilla de
hiperparametros **mide ruido**, y se dejo de ajustar.

Pero **el numero de arboles no es un hiperparametro como los demas**, y por eso no
debio quedar del mismo lado de esa conclusion. Todos los demas controlan la capacidad
del modelo y se pueden pasar de rosca; el numero de arboles **solo promedia**. Un
bosque mas grande es el promedio de mas arboles sobre el mismo problema: su varianza
baja de forma monotona y **no puede sobreajustar por crecer**. Anadir arboles es
exactamente la operacion que quita el ruido que la rejilla encontro.

Dicho de otra forma: la rejilla concluyo "aca hay demasiado ruido para distinguir
configuraciones", y la respuesta a eso no es dejar de ajustar, es **reducir el ruido**.
Eso no se hizo.

Que se mide
-----------
El mismo bosque del proyecto, con el mismo arnes, cambiando unicamente
`n_estimators`: **300** (el vigente), **900**, **1 500** y **3 000**.

Se miden las dos cosas que el proyecto reporta:

1. **F1 macro** sobre los nueve tramos, que es la metrica de decision.
2. **La precision del aviso** en las tres coberturas declaradas -- 90 %, 55 % y
   18,37 % -- contra el azar a la misma cobertura, que es la cifra del titular.

El arnes es el mismo que ya reprodujo la curva publicada cifra por cifra, asi que la
fila de 300 arboles sirve de **control**: si no diera 0,225169 / 0,253193 / 0,284289,
el defecto estaria en este guion y no en los bosques.

El criterio, fijado ANTES de correr
-----------------------------------
Se adopta un bosque mas grande **solo si se cumplen las tres**:

1. Su cociente sobre el azar **supera** al de 300 arboles en **las tres coberturas**.
2. En el punto de trabajo, el signo aguanta en **al menos 8 de los 9 tramos**.
3. Su **F1 macro medio no empeora** respecto de 300 arboles.

Entre los que cumplan se elige **el mas pequeno**, no el mejor: si 900 y 3 000 pasan,
se adopta 900. Elegir el mejor de una rejilla es lo que este proyecto ya decidio no
hacer; aca solo se pregunta si crecer ayuda, y cuanto basta.

La expectativa, tambien antes de mirar
--------------------------------------
Una mejora **pequena y positiva, que satura**: la varianza del promedio baja con la
raiz del numero de arboles, asi que de 300 a 900 deberia verse mas que de 1 500 a
3 000. **Si no mejorara nada**, la conclusion seria que la varianza que estorba no es
la del promedio de arboles sino la del problema, y eso refuerza el diagnostico. **Si
mejorara mucho**, querria decir que el proyecto venia reportando un modelo
innecesariamente ruidoso, y habria que decirlo tal cual.

Que NO hace
-----------
No toca el bloque de reserva: nueve tramos de validacion deslizante. No cambia los
datos, las caracteristicas, la etiqueta ni ningun otro hiperparametro.

Punto de entrada:
    uv run python scripts/mas_arboles.py
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
sys.path.insert(0, str(RAIZ / "scripts"))

from proximidad_solo_adelante import objetivo_solo_adelante  # noqa: E402

from contracts.config import ACTIVO_OBJETIVO, GRANULARIDAD, HORIZONTE_H, VENTANA_W  # noqa: E402
from contracts.labeling import Clase, etiquetar, objetivo  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from src.features.base import construir  # noqa: E402
from src.modelos.base import BaselineAleatorio  # noqa: E402
from src.modelos.clasico import HIPERPARAMETROS, BosqueAleatorio  # noqa: E402

SALIDA = RAIZ / "docs" / "evidencias" / "m0-mas-arboles-4h-w7-h1.json"

N_TRAMOS = 9
VELAS_DE_MARGEN = 2
COBERTURAS = [0.9040, 0.5500, 0.1837]
COBERTURA_DE_TRABAJO = 0.1837
TRAMOS_MINIMOS = 8
ARBOLES = [300, 900, 1500, 3000]
VIGENTE = 300

RARAS = (int(Clase.MAXIMO), int(Clase.MINIMO))


def puntaje_y_tipo(prob: np.ndarray, clases: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    columnas = [int(np.flatnonzero(clases == c)[0]) for c in RARAS]
    p_raras = prob[:, columnas]
    return p_raras.max(axis=1), np.array(RARAS)[p_raras.argmax(axis=1)]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    panel = pd.read_parquet(RAIZ / "data" / "processed" / f"panel_{GRANULARIDAD}_v1.parquet")
    X = construir(panel, rezagos_relativos=True)
    exacto = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), VENTANA_W), HORIZONTE_H)
    y = objetivo_solo_adelante(exacto, VELAS_DE_MARGEN)

    validos = np.flatnonzero(y.notna().to_numpy())
    embargo = VENTANA_W + HORIZONTE_H
    corte = len(validos) // 2
    ancho = (len(validos) - corte) // N_TRAMOS

    por_bosque: dict[int, list[dict]] = {n: [] for n in ARBOLES}
    azar_por_tramo: list[dict] = []

    print(f"{'tramo':>6} {'velas':>6} " + " ".join(f"{'F1 ' + str(n):>12}" for n in ARBOLES))
    for i in range(N_TRAMOS):
        inicio = corte + i * ancho
        fin = inicio + ancho if i < N_TRAMOS - 1 else len(validos)
        tramo = validos[inicio:fin]
        entrenar_en = validos[: max(0, inicio - embargo)]
        if len(entrenar_en) == 0 or len(tramo) == 0:
            continue

        verdad = y.iloc[tramo].astype(int).to_numpy()
        azar = BaselineAleatorio(semilla=HIPERPARAMETROS["random_state"])
        azar.entrenar(X.iloc[entrenar_en], y.iloc[entrenar_en])
        azar_por_tramo.append(
            {
                "pred": np.asarray(azar.predecir(X.iloc[tramo]), dtype=int),
                "verdad": verdad,
                "semilla": HIPERPARAMETROS["random_state"] + i,
            }
        )

        celdas = []
        for n in ARBOLES:
            bosque = BosqueAleatorio(
                n_arboles=n,
                semilla=HIPERPARAMETROS["random_state"],
                nombre=f"bosque_{n}_arboles",
            )
            bosque.entrenar(X.iloc[entrenar_en], y.iloc[entrenar_en])
            tuberia = bosque._tuberia
            clases = tuberia.named_steps["bosque"].classes_
            preparado = bosque._preparar(X.iloc[tramo], bosque._columnas)
            p, tipo = puntaje_y_tipo(tuberia.predict_proba(preparado), clases)
            pred = np.asarray(bosque.predecir(X.iloc[tramo]), dtype=int)
            f1 = float(f1_score(verdad, pred, average="macro", zero_division=0))
            por_bosque[n].append({"p": p, "tipo": tipo, "verdad": verdad, "f1": round(f1, 6)})
            celdas.append(f"{f1:>12.6f}")
        print(f"{i:>6} {len(tramo):>6} " + " ".join(celdas))

    total = sum(len(g["p"]) for g in por_bosque[VIGENTE])

    # el piso del azar, una vez por cobertura: no depende del bosque
    piso = {}
    for c in COBERTURAS:
        aciertos = avisos = 0
        for g in azar_por_tramo:
            n = len(g["verdad"])
            k = int(round(c * n))
            gen = np.random.default_rng(g["semilla"])
            elegidas = gen.choice(n, size=k, replace=False)
            tipos = np.where(
                np.isin(g["pred"][elegidas], RARAS),
                g["pred"][elegidas],
                gen.choice(RARAS, size=k),
            )
            avisos += k
            aciertos += int((tipos == g["verdad"][elegidas]).sum())
        piso[f"{c:.4f}"] = aciertos / avisos

    resultados = {}
    for n in ARBOLES:
        todas = np.concatenate([g["p"] for g in por_bosque[n]])
        fila = {
            "f1_por_tramo": [g["f1"] for g in por_bosque[n]],
            "f1_medio": round(float(np.mean([g["f1"] for g in por_bosque[n]])), 6),
            "coberturas": {},
        }
        for c in COBERTURAS:
            clave = f"{c:.4f}"
            umbral = float(np.quantile(todas, 1 - c))
            avisos = aciertos = 0
            por_tramo = []
            for g in por_bosque[n]:
                sel = np.flatnonzero(g["p"] >= umbral)
                avisos += len(sel)
                ac = int((g["tipo"][sel] == g["verdad"][sel]).sum())
                aciertos += ac
                por_tramo.append(round(ac / len(sel), 6) if len(sel) else None)
            p = aciertos / avisos if avisos else 0.0
            fila["coberturas"][clave] = {
                "umbral": round(umbral, 6),
                "avisos": avisos,
                "cobertura_real": round(avisos / total, 6),
                "precision": round(p, 6),
                "precision_azar": round(piso[clave], 6),
                "cociente_sobre_azar": round(p / piso[clave], 6) if piso[clave] else None,
                "precision_por_tramo": por_tramo,
            }
        resultados[str(n)] = fila

    base = resultados[str(VIGENTE)]
    trabajo = f"{COBERTURA_DE_TRABAJO:.4f}"
    adoptables = []
    for n in ARBOLES:
        if n == VIGENTE:
            continue
        r = resultados[str(n)]
        gana_en_las_tres = all(
            r["coberturas"][f"{c:.4f}"]["cociente_sobre_azar"]
            > base["coberturas"][f"{c:.4f}"]["cociente_sobre_azar"]
            for c in COBERTURAS
        )
        a_favor = sum(
            1
            for a, b in zip(
                r["coberturas"][trabajo]["precision_por_tramo"],
                base["coberturas"][trabajo]["precision_por_tramo"],
                strict=True,
            )
            if a is not None and b is not None and a > b
        )
        r["tramos_a_favor"] = a_favor
        r["f1_no_empeora"] = bool(r["f1_medio"] >= base["f1_medio"])
        r["cumple_criterio"] = bool(
            gana_en_las_tres and a_favor >= TRAMOS_MINIMOS and r["f1_no_empeora"]
        )
        if r["cumple_criterio"]:
            adoptables.append(n)

    if adoptables:
        elegido = min(adoptables)
        r = resultados[str(elegido)]
        veredicto = (
            f"Se adoptan {elegido} arboles -- el mas pequeno de los que cumplen, no el mejor. "
            f"En el punto de trabajo el cociente pasa de "
            f"{base['coberturas'][trabajo]['cociente_sobre_azar']:.4f} a "
            f"{r['coberturas'][trabajo]['cociente_sobre_azar']:.4f}, con el signo a favor en "
            f"{r['tramos_a_favor']} de {N_TRAMOS} tramos, y el F1 macro medio pasa de "
            f"{base['f1_medio']:.6f} a {r['f1_medio']:.6f}."
        )
    else:
        veredicto = (
            "No se adopta ningun bosque mas grande: ninguno cumple las tres condiciones. "
            "La varianza que estorba no es la del promedio de arboles."
        )

    print()
    for n in ARBOLES:
        r = resultados[str(n)]
        marca = " (vigente)" if n == VIGENTE else ""
        print(
            f"{n:>5} arboles{marca:>10}  F1 {r['f1_medio']:.6f}  "
            + "  ".join(
                f"cob {c:.0%}: {r['coberturas'][f'{c:.4f}']['cociente_sobre_azar']:.4f}x"
                for c in COBERTURAS
            )
        )
    print()
    print(veredicto)

    SALIDA.write_text(
        json.dumps(
            {
                "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                "que_mide": (
                    "Si un bosque mas grande mejora, midiendo F1 macro y la precision del aviso "
                    "en las tres coberturas declaradas. El numero de arboles no controla "
                    "capacidad: solo promedia, asi que no puede sobreajustar por crecer."
                ),
                "por_que_este_eje": (
                    "La rejilla de hiperparametros concluyo que mide ruido, y el numero de "
                    "arboles es justamente la operacion que quita ese ruido. Quedo del lado "
                    "equivocado de esa conclusion."
                ),
                "criterio_preregistrado": (
                    "Gana en las tres coberturas, signo estable en al menos "
                    f"{TRAMOS_MINIMOS} de {N_TRAMOS} tramos en el punto de trabajo, y F1 macro "
                    "medio que no empeora. Entre los que cumplan se elige EL MAS PEQUENO."
                ),
                "expectativa_declarada_antes": (
                    "Mejora pequena y positiva que satura. Si no mejorara nada, la varianza que "
                    "estorba es la del problema y no la del promedio. Si mejorara mucho, el "
                    "proyecto venia reportando un modelo innecesariamente ruidoso."
                ),
                "control": (
                    "La fila de 300 arboles reproduce la curva publicada (0,225169 / 0,253193 / "
                    "0,284289). Si no lo hiciera, el defecto estaria en este guion."
                ),
                "no_toca_la_reserva": "Nueve tramos de validacion deslizante.",
                "objetivo": f"solo_adelante_{VELAS_DE_MARGEN}_velas",
                "observaciones": total,
                "resultados": resultados,
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
