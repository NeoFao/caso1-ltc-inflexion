"""¿El mejor resultado del trabajo predice, o reconoce lo que acaba de pasar?

La objecion contra nuestro propio hallazgo
------------------------------------------
El objetivo de proximidad que dio el mejor resultado del proyecto -- F1 macro
**0,567778** contra 0,337697 del azar -- es **simetrico**: una vela cuenta como
"Maximo" si hay un maximo real en `[i-k, i+k]`.

Esa ventana **incluye el pasado**. Y si el modelo pudiera *reconocer* un giro que
acaba de ocurrir en vez de *predecir* uno que viene, la cifra estaria inflada: seria
un detector de historia disfrazado de pronosticador.

Es la primera pregunta que hace un lector cuidadoso y no la habiamos comprobado.

El argumento de por que NO deberia estar inflado
------------------------------------------------
Con `h = 1`, la etiqueta de la fila `i` es la del instante `i+1`. La ventana
simetrica con `k = 1` abarca las etiquetas de los instantes `i` a `i+2`.

Y confirmar que el instante `i` fue un maximo **exige las `w = 7` velas
posteriores**, o sea precios hasta `i+7`. Estando parado en `i`, eso no se conoce.
**Ni el extremo mas "pasado" de la ventana es observable** en el momento de predecir.

Pero eso es un argumento, no una medicion. Y este proyecto ya se ha equivocado con
argumentos elegantes: la explicacion del cero del iTransformer sonaba igual de bien.

Que se mide
-----------
La misma comparacion con una etiqueta **solo hacia adelante**: la fila `i` cuenta
como "Maximo" si hay un maximo real en los instantes `i+h` a `i+h+k`, **sin mirar
ni una vela hacia atras**. Es, literalmente, "va a haber un giro en las proximas k
velas".

Tres columnas: el objetivo exacto, el simetrico (el del hallazgo) y el de solo
adelante.

El criterio, fijado ANTES de correr
-----------------------------------
El hallazgo se sostiene si, con la etiqueta de solo adelante:

1. La **ventaja sobre el azar** sigue siendo claramente mayor que la del objetivo
   exacto (+0,044619), y no una fraccion pequena de la del simetrico (+0,230081).
2. El signo aguanta en los **nueve tramos**.

**Si la ventaja se derrumbara** -- por ejemplo, si quedara mas cerca del exacto que
del simetrico -- la conclusion seria que buena parte del hallazgo era **reconocer un
giro reciente, no anticiparlo**, y habria que reescribirlo diciendo eso.

Y la expectativa, tambien antes de mirar
----------------------------------------
**Se espera que se sostenga**, por el argumento de la latencia: ninguna vela de la
ventana simetrica es confirmable en el momento de predecir.

**Pero se espera que baje algo**, porque la etiqueta de solo adelante es mas exigente:
cubre menos instantes para el mismo `k`, asi que hay menos velas positivas y menos
margen para acertar.

**Cualquiera de los dos resultados se publica**, y el segundo obligaria a corregir el
hallazgo principal del trabajo. Por eso esto se mide antes de contarlo en la
exposicion y no despues.

No toca la reserva. Nueve tramos de validacion deslizante.

Punto de entrada:
    uv run python scripts/proximidad_solo_adelante.py
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
from contracts.labeling import Clase, etiquetar, latencia_real, objetivo  # noqa: E402
from contracts.metrics import evaluar  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from src.features.base import construir  # noqa: E402
from src.modelos.base import BaselineAleatorio  # noqa: E402
from src.modelos.clasico import HIPERPARAMETROS, BosqueAleatorio  # noqa: E402

sys.path.insert(0, str(RAIZ / "scripts"))
from objetivo_proximidad import objetivo_cercano  # noqa: E402

SALIDA = RAIZ / "docs" / "evidencias" / "m0-proximidad-solo-adelante-4h-w7-h1.json"
N_TRAMOS = 9
MAXIMO, MINIMO, CONTINUIDAD = int(Clase.MAXIMO), int(Clase.MINIMO), int(Clase.CONTINUIDAD)

#: Las dos referencias, medidas antes: la ventaja del objetivo exacto y la del
#: simetrico a una vela, sobre estos mismos nueve tramos.
VENTAJA_EXACTO = 0.044619
VENTAJA_SIMETRICO = 0.230081


def objetivo_solo_adelante(exacto: pd.Series, k: int) -> pd.Series:
    """ "Va a haber un giro en las proximas k velas", sin mirar hacia atras.

    La fila `i` mira las etiquetas de `i` a `i+k` de la serie `exacto` -- que ya esta
    desplazada `h`, asi que son los instantes `i+h` a `i+h+k`. Con `k = 0` es la
    etiqueta exacta.

    A diferencia de `objetivo_cercano`, **no incluye ninguna posicion anterior a
    `i`**: no puede premiar el reconocimiento de un giro reciente.
    """
    if k == 0:
        return exacto.copy()

    v = exacto.to_numpy(dtype=float)
    n = len(v)
    salida = np.full(n, np.nan)
    for i in range(n):
        if np.isnan(v[i]):
            continue
        hasta = min(n, i + k + 1)
        ventana = v[i:hasta]
        if np.isnan(ventana).any():
            continue  # sin ventana completa hacia adelante, la etiqueta es desconocida
        etiqueta = CONTINUIDAD
        mejor = None
        for clase in (MAXIMO, MINIMO):
            donde = np.flatnonzero(ventana == clase)
            if len(donde):
                d = int(donde.min())
                if mejor is None or d < mejor:
                    mejor, etiqueta = d, clase
        salida[i] = etiqueta
    return pd.Series(salida, index=exacto.index, name="objetivo").astype("Int64")


def medir(X: pd.DataFrame, y: pd.Series) -> dict:
    validos = np.flatnonzero(y.notna().to_numpy())
    embargo = VENTANA_W + HORIZONTE_H
    corte = len(validos) // 2
    ancho = (len(validos) - corte) // N_TRAMOS

    f1, f1_azar, ventajas = [], [], []
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

        verdad = y.iloc[tramo].astype(int).to_numpy()
        mb = evaluar(verdad, np.asarray(bosque.predecir(X.iloc[tramo]), dtype=int))
        ma = evaluar(verdad, np.asarray(azar.predecir(X.iloc[tramo]), dtype=int))
        f1.append(mb["f1_macro"])
        f1_azar.append(ma["f1_macro"])
        ventajas.append(mb["f1_macro"] - ma["f1_macro"])

    v = np.array(ventajas)
    yv = y.dropna().astype(int)
    return {
        "n_evaluables": int(len(yv)),
        "por_ciento_velas_con_giro": round(float(100 * (yv != CONTINUIDAD).mean()), 2),
        "f1_macro": round(float(np.mean(f1)), 6),
        "f1_macro_azar": round(float(np.mean(f1_azar)), 6),
        "ventaja_sobre_azar": round(float(v.mean()), 6),
        "tramos_a_favor": int((v > 0).sum()),
        "tramos_medidos": int(len(v)),
        "signo_estable": bool((v > 0).all()),
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    panel = pd.read_parquet(RAIZ / "data" / "processed" / f"panel_{GRANULARIDAD}_v1.parquet")
    X = construir(panel, rezagos_relativos=True)
    exacto = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), VENTANA_W), HORIZONTE_H)

    casos = {
        "exacto": exacto,
        "simetrico_1_vela": objetivo_cercano(exacto, 1),
        "solo_adelante_1_vela": objetivo_solo_adelante(exacto, 1),
        "solo_adelante_2_velas": objetivo_solo_adelante(exacto, 2),
    }

    resultados = {}
    for nombre, y in casos.items():
        print(f"midiendo {nombre}...", flush=True)
        resultados[nombre] = medir(X, y)
        d = resultados[nombre]
        print(
            f"  giros {d['por_ciento_velas_con_giro']:>5.2f} %  "
            f"F1 {d['f1_macro']:.6f} vs {d['f1_macro_azar']:.6f}  "
            f"ventaja {d['ventaja_sobre_azar']:+.6f}  "
            f"tramos {d['tramos_a_favor']}/{d['tramos_medidos']}",
            flush=True,
        )

    adelante = resultados["solo_adelante_1_vela"]
    # A medio camino entre el exacto y el simetrico: si queda por debajo de eso, buena
    # parte del hallazgo era reconocer y no anticipar.
    punto_medio = (VENTAJA_EXACTO + VENTAJA_SIMETRICO) / 2
    se_sostiene = bool(adelante["ventaja_sobre_azar"] > punto_medio and adelante["signo_estable"])

    medido = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "que_comprueba": (
            "Si el mejor resultado del trabajo predice o reconoce. El objetivo de "
            "proximidad que dio F1 0,567778 es SIMETRICO: cuenta como giro cercano si "
            "hay uno en [i-k, i+k], y esa ventana incluye el pasado. Si el modelo "
            "reconociera un giro recien ocurrido en vez de anticipar uno, la cifra "
            "estaria inflada."
        ),
        "el_argumento_de_por_que_no_deberia_estar_inflado": (
            f"Con h=1 la etiqueta de la fila i es la del instante i+1, y la ventana "
            f"simetrica con k=1 abarca los instantes i a i+2. Confirmar que el instante i "
            f"fue un maximo exige las w={VENTANA_W} velas posteriores, o sea precios hasta "
            f"i+{VENTANA_W}: estando parado en i eso no se conoce. Ni el extremo mas "
            f"'pasado' de la ventana es observable al predecir. La latencia de "
            f"confirmacion es {latencia_real(VENTANA_W, HORIZONTE_H)} velas. Pero eso es un "
            "argumento, no una medicion, y este proyecto ya se equivoco con argumentos "
            "elegantes."
        ),
        "criterio_preregistrado": (
            f"El hallazgo se sostiene si la ventaja con la etiqueta de solo adelante "
            f"supera el punto medio entre la del exacto ({VENTAJA_EXACTO}) y la del "
            f"simetrico ({VENTAJA_SIMETRICO}) -- es decir {punto_medio:.6f} -- y el signo "
            "aguanta en los nueve tramos. Si quedara mas cerca del exacto que del "
            "simetrico, buena parte del hallazgo era reconocer y no anticipar."
        ),
        "expectativa_declarada_antes": (
            "Que se sostenga, por el argumento de la latencia. Pero que baje algo, porque "
            "la etiqueta de solo adelante es mas exigente: cubre menos instantes para el "
            "mismo k, asi que hay menos velas positivas y menos margen para acertar."
        ),
        "no_toca_la_reserva": "Nueve tramos de validacion deslizante.",
        "referencias": {
            "ventaja_objetivo_exacto": VENTAJA_EXACTO,
            "ventaja_objetivo_simetrico": VENTAJA_SIMETRICO,
            "punto_medio_del_criterio": round(punto_medio, 6),
        },
        "resultados": resultados,
        "el_hallazgo_se_sostiene": se_sostiene,
        "veredicto": (
            "El hallazgo SE SOSTIENE: con la etiqueta de solo adelante la ventaja sigue "
            "muy por encima de la del objetivo exacto. El modelo anticipa, no reconoce."
            if se_sostiene
            else "El hallazgo NO se sostiene con la etiqueta de solo adelante: buena parte "
            "de la mejora venia de reconocer un giro reciente, no de anticiparlo."
        ),
    }
    SALIDA.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{'objetivo':24} {'giros':>7} {'F1':>10} {'azar':>9} {'ventaja':>9} {'tramos':>7}")
    for nombre, d in resultados.items():
        print(
            f"{nombre:24} {d['por_ciento_velas_con_giro']:>6.2f}% {d['f1_macro']:>10.6f} "
            f"{d['f1_macro_azar']:>9.6f} {d['ventaja_sobre_azar']:>+9.6f} "
            f"{d['tramos_a_favor']:>3}/{d['tramos_medidos']:<3}"
        )
    print(f"\ncriterio: la ventaja de solo-adelante tiene que superar {punto_medio:.6f}")
    print(medido["veredicto"])
    print(f"constancia en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
