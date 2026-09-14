"""Cuando el sistema avisa, ¿cuantas veces acierta? La pregunta que falta.

El numero que el informe no tiene
---------------------------------
El informe reporta **precision direccional 0,104651**: de los giros que de verdad
ocurrieron, a cuantos les acerto el tipo. Eso es *recall*, y se mide sobre los giros.

Falta el complemento, que es lo que le importa a quien usaria esto: **de las veces que
el sistema avisa, cuantas acierta**. Hoy el sistema avisa en cada vela, porque
`predecir()` elige siempre la clase mas probable. Nunca se calla.

El eje que esto abre, y que no es ninguno de los siete
------------------------------------------------------
Los siete intentos de la Tabla C.11 tocaron la etiqueta, la estructura de clases, la
regla de decision, el volumen, la agregacion, la familia y el peso por ejemplo. Los
siete miden **con cobertura del 100 %**: el sistema responde siempre.

Este mide otra cosa: **dejar que se calle**. Se anuncia un giro solo cuando la
probabilidad de la clase rara supera un umbral; por debajo, silencio. Eso cambia el
punto de operacion, no el modelo, y es lo unico que puede convertir "de cada diez
giros detecta uno" en "cuando avisa, acierta X de cada diez" -- o demostrar que no.

No es el intento 3. El intento 3 corregia por frecuencia base **que clase gana**,
con el sistema respondiendo siempre igual. Aqui la opcion nueva es **no responder**.

El criterio, fijado ANTES de correr
-----------------------------------
Para decir que abstenerse sirve, hace falta que exista un umbral en el que se cumplan
las tres, sobre los nueve tramos:

1. La precision del aviso supera la **frecuencia base** de giros. Avisar al azar
   acierta esa fraccion, asi que por debajo el aviso no aporta nada.
2. La precision del aviso supera la del `baseline_aleatorio` **a la misma cobertura**.
   Es el piso que se mueve con los datos, como en el resto del proyecto.
3. El signo de esa ventaja es **estable en los nueve tramos**, no un promedio que
   tapa tramos en contra.

Y la expectativa, tambien antes de mirar
----------------------------------------
Se espera que la precision **suba** al bajar la cobertura: es lo normal en un
clasificador con probabilidades informativas. Lo que **no** se sabe es si sube lo
suficiente para ser util, ni si aguanta el criterio 3.

**Si sube pero no aguanta los nueve tramos, la conclusion es que no se establece**, y
se publica asi. Este guion no elige el umbral que mejor queda: publica la curva
entera y aplica el criterio escrito arriba.

Que NO hace
-----------
No toca el bloque de prueba, que se gasto el 07/09. Mide sobre los nueve tramos de la
validacion deslizante, que son datos fuera de muestra y que si se pueden volver a
mirar. Y **no reentrena nada**: usa el mismo bosque de siempre, solo le pide las
probabilidades en vez de la clase.

Punto de entrada:
    uv run python scripts/aviso_con_abstencion.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from contracts.config import ACTIVO_OBJETIVO, GRANULARIDAD, HORIZONTE_H, VENTANA_W  # noqa: E402
from contracts.labeling import Clase, etiquetar, objetivo  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from src.features.base import construir  # noqa: E402
from src.modelos.base import BaselineAleatorio  # noqa: E402
from src.modelos.clasico import HIPERPARAMETROS, BosqueAleatorio  # noqa: E402

SALIDA = RAIZ / "docs" / "evidencias" / "m0-aviso-con-abstencion-4h-w7-h1.json"

N_TRAMOS = 9
#: Los umbrales que se publican. Se fijan aqui, antes de correr, y se publican TODOS:
#: elegir despues el que mejor queda es exactamente el error que el proyecto persigue.
UMBRALES = [0.0, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.60]

RARAS = (int(Clase.MAXIMO), int(Clase.MINIMO))


def avisos(probabilidades: np.ndarray, clases: np.ndarray, umbral: float) -> np.ndarray:
    """Que anuncia el sistema en cada vela: una clase rara, o nada (0).

    Se anuncia la clase rara mas probable, y solo si esa probabilidad llega al
    umbral. `0` significa que el sistema se calla.
    """
    columnas = [int(np.flatnonzero(clases == c)[0]) for c in RARAS]
    p_raras = probabilidades[:, columnas]
    mejor = p_raras.argmax(axis=1)
    p_mejor = p_raras.max(axis=1)
    anuncio = np.where(p_mejor >= umbral, np.array(RARAS)[mejor], 0)
    return anuncio.astype(int)


def precision_del_aviso(anuncio: np.ndarray, verdad: np.ndarray) -> tuple[int, int]:
    """Cuantos avisos hubo y cuantos acertaron la clase exacta."""
    dio_aviso = anuncio != 0
    n = int(dio_aviso.sum())
    if n == 0:
        return 0, 0
    aciertos = int((anuncio[dio_aviso] == verdad[dio_aviso]).sum())
    return n, aciertos


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    panel = pd.read_parquet(RAIZ / "data" / "processed" / f"panel_{GRANULARIDAD}_v1.parquet")
    X = construir(panel, rezagos_relativos=True)
    y = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), VENTANA_W), HORIZONTE_H)

    validos = np.flatnonzero(y.notna().to_numpy())
    embargo = VENTANA_W + HORIZONTE_H
    # Ventana expansiva: la misma estructura de scripts/walk_forward.py.
    corte = len(validos) // 2
    ancho = (len(validos) - corte) // N_TRAMOS

    por_tramo: list[dict] = []
    todo_anuncio = {u: [] for u in UMBRALES}
    todo_azar = {u: [] for u in UMBRALES}
    todo_verdad: list[np.ndarray] = []

    print(f"{'tramo':>6} {'entrena':>8} {'evalua':>7} {'giros':>6}")
    for i in range(N_TRAMOS):
        inicio = corte + i * ancho
        fin = inicio + ancho if i < N_TRAMOS - 1 else len(validos)
        tramo = validos[inicio:fin]
        entrenar_en = validos[: max(0, inicio - embargo)]
        if len(entrenar_en) == 0 or len(tramo) == 0:
            continue

        bosque = BosqueAleatorio(
            n_arboles=HIPERPARAMETROS["n_estimators"],
            semilla=HIPERPARAMETROS["random_state"],
            nombre="bosque_aleatorio_rezagos_relativos",
        )
        bosque.entrenar(X.iloc[entrenar_en], y.iloc[entrenar_en])
        azar = BaselineAleatorio(semilla=HIPERPARAMETROS["random_state"])
        azar.entrenar(X.iloc[entrenar_en], y.iloc[entrenar_en])

        tuberia = bosque._tuberia
        clases = tuberia.named_steps["bosque"].classes_
        prob = tuberia.predict_proba(bosque._preparar(X.iloc[tramo], bosque._columnas))

        verdad = y.iloc[tramo].astype(int).to_numpy()
        todo_verdad.append(verdad)
        n_giros = int(np.isin(verdad, RARAS).sum())
        print(f"{i:>6} {len(entrenar_en):>8} {len(tramo):>7} {n_giros:>6}")

        # El azar no tiene probabilidades informativas: su "aviso" es su propia
        # prediccion. Para comparar a la MISMA cobertura se toma una muestra de sus
        # velas del tamano que el bosque anuncio en ese umbral.
        pred_azar = np.asarray(azar.predecir(X.iloc[tramo]), dtype=int)
        generador = np.random.default_rng(HIPERPARAMETROS["random_state"] + i)

        fila = {"tramo": i, "n": int(len(tramo)), "giros_reales": n_giros, "umbrales": {}}
        for u in UMBRALES:
            anuncio = avisos(prob, clases, u)
            n_avisos, aciertos = precision_del_aviso(anuncio, verdad)
            todo_anuncio[u].append(anuncio)

            # Piso: avisar en n_avisos velas elegidas al azar, con el tipo que el
            # baseline predijo ahi. Misma cobertura, sin informacion.
            anuncio_azar = np.zeros_like(anuncio)
            if n_avisos > 0:
                elegidas = generador.choice(len(tramo), size=n_avisos, replace=False)
                tipos = np.where(
                    np.isin(pred_azar[elegidas], RARAS),
                    pred_azar[elegidas],
                    generador.choice(RARAS, size=n_avisos),
                )
                anuncio_azar[elegidas] = tipos
            todo_azar[u].append(anuncio_azar)
            n_az, ac_az = precision_del_aviso(anuncio_azar, verdad)

            fila["umbrales"][f"{u:.2f}"] = {
                "avisos": n_avisos,
                "aciertos": aciertos,
                "precision": round(aciertos / n_avisos, 6) if n_avisos else None,
                "cobertura": round(n_avisos / len(tramo), 6),
                "precision_azar_misma_cobertura": round(ac_az / n_az, 6) if n_az else None,
            }
        por_tramo.append(fila)

    verdad_total = np.concatenate(todo_verdad)
    frecuencia_base = float(np.isin(verdad_total, RARAS).mean())

    agregado = {}
    for u in UMBRALES:
        anuncio = np.concatenate(todo_anuncio[u])
        anuncio_azar = np.concatenate(todo_azar[u])
        n_avisos, aciertos = precision_del_aviso(anuncio, verdad_total)
        n_az, ac_az = precision_del_aviso(anuncio_azar, verdad_total)
        prec = aciertos / n_avisos if n_avisos else None
        prec_az = ac_az / n_az if n_az else None

        # Criterio 3: el signo de la ventaja, tramo a tramo.
        a_favor = 0
        medidos = 0
        for fila in por_tramo:
            d = fila["umbrales"][f"{u:.2f}"]
            if d["precision"] is not None and d["precision_azar_misma_cobertura"] is not None:
                medidos += 1
                if d["precision"] > d["precision_azar_misma_cobertura"]:
                    a_favor += 1

        agregado[f"{u:.2f}"] = {
            "avisos": n_avisos,
            "aciertos": aciertos,
            "precision": round(prec, 6) if prec is not None else None,
            "cobertura": round(n_avisos / len(verdad_total), 6),
            "precision_azar_misma_cobertura": round(prec_az, 6) if prec_az is not None else None,
            "supera_frecuencia_base": bool(prec is not None and prec > frecuencia_base),
            "supera_al_azar": bool(prec is not None and prec_az is not None and prec > prec_az),
            "tramos_a_favor": a_favor,
            "tramos_medidos": medidos,
            "signo_estable": bool(medidos > 0 and a_favor == medidos),
        }

    cumplen = [
        u
        for u, d in agregado.items()
        if d["supera_frecuencia_base"] and d["supera_al_azar"] and d["signo_estable"]
    ]

    medido = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "que_mide": (
            "De las veces que el sistema AVISA, cuantas acierta. El informe reporta el "
            "complemento -- de los giros reales, a cuantos les acerto -- y esta cifra "
            "faltaba. Se obtiene dejando que el sistema se calle cuando no esta seguro."
        ),
        "por_que_no_es_ninguno_de_los_siete": (
            "Los siete intentos de la Tabla C.11 miden con cobertura del 100 %. El "
            "intento 3 corregia por frecuencia base QUE CLASE gana, con el sistema "
            "respondiendo siempre. Aqui la opcion nueva es NO RESPONDER."
        ),
        "criterio_preregistrado": (
            "Para decir que abstenerse sirve tiene que existir un umbral donde se "
            "cumplan las tres: (1) la precision del aviso supera la frecuencia base de "
            "giros, (2) supera la del baseline_aleatorio a la MISMA cobertura, y (3) el "
            "signo de esa ventaja es estable en los nueve tramos."
        ),
        "expectativa_declarada_antes": (
            "Se esperaba que la precision suba al bajar la cobertura. No se sabia si "
            "sube lo suficiente para ser util ni si aguanta el criterio 3. Si sube pero "
            "no aguanta los nueve tramos, la conclusion es que no se establece."
        ),
        "no_toca_la_reserva": (
            "Nueve tramos de validacion deslizante. El bloque de prueba se gasto el "
            "07/09 y no se vuelve a medir. Ninguna cifra del informe cambia."
        ),
        "no_se_reentrena": "Es el mismo bosque de siempre; solo se le piden las probabilidades.",
        "parametros": {
            "intervalo": GRANULARIDAD,
            "w": VENTANA_W,
            "h": HORIZONTE_H,
            "n_tramos": N_TRAMOS,
            "umbrales": UMBRALES,
        },
        "n_observaciones": int(len(verdad_total)),
        "frecuencia_base_de_giros": round(frecuencia_base, 6),
        "agregado": agregado,
        "por_tramo": por_tramo,
        "umbrales_que_cumplen_las_tres": cumplen,
        "veredicto": (
            "Abstenerse SI mejora el aviso y aguanta el criterio."
            if cumplen
            else "Ningun umbral cumple las tres condiciones: no se establece."
        ),
    }
    SALIDA.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nfrecuencia base de giros: {frecuencia_base:.6f}  ({len(verdad_total)} observaciones)")
    print(
        f"\n{'umbral':>7} {'avisos':>7} {'cobertura':>10} {'precision':>10} {'azar':>9} "
        f"{'tramos':>7}  cumple"
    )
    for u, d in agregado.items():
        if d["precision"] is None:
            print(f"{u:>7} {'0':>7}  (nunca avisa)")
            continue
        marca = (
            "SI"
            if (d["supera_frecuencia_base"] and d["supera_al_azar"] and d["signo_estable"])
            else ""
        )
        print(
            f"{u:>7} {d['avisos']:>7} {d['cobertura']:>10.4f} {d['precision']:>10.6f} "
            f"{d['precision_azar_misma_cobertura']:>9.6f} "
            f"{d['tramos_a_favor']:>3}/{d['tramos_medidos']:<3}  {marca}"
        )

    print(f"\n{medido['veredicto']}")
    print(f"constancia en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
