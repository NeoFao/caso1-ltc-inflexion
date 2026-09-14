"""¿Y si el límite no era la señal, sino que solo teníamos 13 114 velas?

El hueco
--------
El informe concluye, después de siete intentos fallidos, que **el limite esta en los
datos y no en el modelado**. Esa conclusion se saco sin probar la forma mas obvia de
tener mas datos: **bajar la granularidad**.

`estudio-w-h.json` comparo **solo 1d y 4h**. Nunca se descargo 1h. Y la granularidad
se eligio como *"el mayor w que deja al menos 300 ejemplos de la clase minoritaria"*
-- una restriccion que con cuatro veces mas velas se afloja sola.

A 1 hora son del orden de **52 000 velas** en vez de 13 114.

La comparacion tiene que ser justa, y ahi esta el detalle
---------------------------------------------------------
A 1 hora con `w = 7` un giro se define mirando **±7 horas**; a 4 horas con `w = 7`
se mira **±28 horas**. **No son el mismo fenomeno**, y comparar esos dos numeros
responderia a otra pregunta.

Para preguntar *"¿ayuda tener mas datos del MISMO fenomeno?"* hay que fijar la
ventana en tiempo de reloj: **`w = 28` a 1 hora son las mismas ±28 horas** que
`w = 7` a 4 horas. Esa es la comparacion que este guion hace.

De paso, `w = 28` sobre 52 000 velas deja del orden de **1 800 ejemplos** por clase
extrema en vez de 420.

El criterio, fijado ANTES de correr
-----------------------------------
Para decir que bajar a 1 hora ayuda, sobre los nueve tramos:

1. La **ventaja sobre el azar** a 1 h con `w = 28` es **mayor** que la ventaja a 4 h
   con `w = 7`.
2. El signo es **estable en los nueve tramos**.

Se compara **ventaja sobre el azar**, no F1 absoluto: el F1 depende del balance de
clases, que cambia con la granularidad, y compararlo directamente seria comparar dos
problemas distintos.

Y la expectativa, tambien antes de mirar
----------------------------------------
**Se espera que ayude**, porque es exactamente la carencia que el informe declara. Si
NO ayuda, el resultado es mas fuerte que el actual: querria decir que el limite no es
la cantidad de ejemplos sino la senal, y eso convierte una conjetura del informe en
algo medido.

**Sea cual sea, se publica.**

Lo que NO hace
--------------
**No toca `panel_4h_v1.parquet`.** El panel del informe es intocable: de el salen
todas las cifras publicadas. Este guion escribe `panel_1h_v1.parquet` aparte.

Y no toca la reserva: nueve tramos de validacion deslizante sobre el panel nuevo.

Punto de entrada:
    uv run python scripts/granularidad_1h.py            # usa el panel si ya existe
    uv run python scripts/granularidad_1h.py --descargar
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from contracts.config import ACTIVO_OBJETIVO, ACTIVOS, HORIZONTE_H, VENTANA_W  # noqa: E402
from contracts.labeling import etiquetar, objetivo  # noqa: E402
from contracts.metrics import evaluar  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from src.features.base import construir  # noqa: E402
from src.modelos.base import BaselineAleatorio  # noqa: E402
from src.modelos.clasico import HIPERPARAMETROS, BosqueAleatorio  # noqa: E402
from src.panel.consolidacion import consolidar  # noqa: E402
from src.panel.descarga import descargar_activo  # noqa: E402

SALIDA = RAIZ / "docs" / "evidencias" / "m0-granularidad-1h.json"
PANEL_1H = RAIZ / "data" / "processed" / "panel_1h_v1.parquet"
PANEL_4H = RAIZ / "data" / "processed" / "panel_4h_v1.parquet"

N_TRAMOS = 9
#: w=28 a 1h son las mismas +-28 horas que w=7 a 4h. Fijado antes de correr.
W_1H = VENTANA_W * 4


def medir(panel: pd.DataFrame, w: int, h: int, etiqueta: str) -> dict:
    X = construir(panel, rezagos_relativos=True)
    y = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), w), h)

    validos = np.flatnonzero(y.notna().to_numpy())
    embargo = w + h
    corte = len(validos) // 2
    ancho = (len(validos) - corte) // N_TRAMOS

    ventajas, f1, f1_azar = [], [], []
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
            nombre=etiqueta,
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
        print(f"    tramo {i}: {mb['f1_macro']:.6f} vs {ma['f1_macro']:.6f}", flush=True)

    v = np.array(ventajas)
    yv = y.dropna().astype(int)
    return {
        "velas": int(len(panel)),
        "w": w,
        "horas_de_ventana": w * (1 if "1h" in etiqueta else 4),
        "columnas": int(X.shape[1]),
        "n_clase_maximo": int((yv == 1).sum()),
        "n_clase_minimo": int((yv == 2).sum()),
        "f1_macro": round(float(np.mean(f1)), 6),
        "f1_macro_azar": round(float(np.mean(f1_azar)), 6),
        "ventaja_sobre_azar": round(float(v.mean()), 6),
        "tramos_a_favor": int((v > 0).sum()),
        "tramos_medidos": int(len(v)),
        "signo_estable": bool((v > 0).all()),
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    analizador = argparse.ArgumentParser(description=__doc__)
    analizador.add_argument("--descargar", action="store_true", help="baja las velas de 1 hora")
    argumentos = analizador.parse_args()

    if argumentos.descargar or not PANEL_1H.exists():
        print("descargando velas de 1 hora de los seis activos...", flush=True)
        series = {}
        for a in ACTIVOS:
            series[a] = descargar_activo(a, "1h", desde="2020-08-01")
            print(f"  {a}: {len(series[a])} velas", flush=True)
        panel_1h = consolidar(series)
        PANEL_1H.parent.mkdir(parents=True, exist_ok=True)
        panel_1h.to_parquet(PANEL_1H)
        print(f"  panel de 1 hora: {len(panel_1h)} velas -> {PANEL_1H.name}", flush=True)
    else:
        panel_1h = pd.read_parquet(PANEL_1H)
        print(f"panel de 1 hora ya existe: {len(panel_1h)} velas", flush=True)

    panel_4h = pd.read_parquet(PANEL_4H)

    print(f"\n4 horas, w={VENTANA_W} (ventana de {VENTANA_W * 4} horas):", flush=True)
    a_4h = medir(panel_4h, VENTANA_W, HORIZONTE_H, "4h")
    print(f"\n1 hora, w={W_1H} (la MISMA ventana de {W_1H} horas):", flush=True)
    a_1h = medir(panel_1h, W_1H, HORIZONTE_H, "1h")

    mejora = a_1h["ventaja_sobre_azar"] > a_4h["ventaja_sobre_azar"]
    ayuda = bool(mejora and a_1h["signo_estable"])

    medido = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "que_mide": (
            "Si bajar la granularidad a 1 hora -- cuatro veces mas velas -- mejora la "
            "ventaja sobre el azar. El informe concluye que el limite esta en los datos "
            "sin haber probado esto: estudio-w-h comparo solo 1d y 4h."
        ),
        "por_que_w_28_y_no_w_7": (
            "A 1h con w=7 un giro se define mirando +-7 horas; a 4h con w=7 se miran "
            "+-28. No son el mismo fenomeno. Para preguntar si ayuda tener mas datos "
            "del MISMO fenomeno hay que fijar la ventana en tiempo de reloj: w=28 a 1h "
            "son las mismas +-28 horas."
        ),
        "por_que_se_compara_la_ventaja_y_no_el_F1": (
            "El F1 absoluto depende del balance de clases, que cambia con la "
            "granularidad. Compararlo directamente seria comparar dos problemas."
        ),
        "criterio_preregistrado": (
            "La ventaja sobre el azar a 1h con w=28 es MAYOR que la ventaja a 4h con "
            "w=7, y el signo es estable en los nueve tramos."
        ),
        "expectativa_declarada_antes": (
            "Se esperaba que ayude, porque es la carencia que el informe declara. Si NO "
            "ayuda, el resultado es mas fuerte que el actual: querria decir que el "
            "limite no es la cantidad de ejemplos sino la senal, y eso convierte una "
            "conjetura del informe en algo medido."
        ),
        "no_toca_el_panel_del_informe": (
            "panel_4h_v1.parquet es intocable: de el salen todas las cifras publicadas. "
            "Este guion escribe panel_1h_v1.parquet aparte."
        ),
        "a_4_horas": a_4h,
        "a_1_hora": a_1h,
        "veces_mas_velas": round(a_1h["velas"] / a_4h["velas"], 2),
        "veces_mas_ejemplos_raros": round(
            (a_1h["n_clase_maximo"] + a_1h["n_clase_minimo"])
            / (a_4h["n_clase_maximo"] + a_4h["n_clase_minimo"]),
            2,
        ),
        "ayuda": ayuda,
        "veredicto": (
            "Bajar a 1 hora SI mejora la ventaja sobre el azar."
            if ayuda
            else "Bajar a 1 hora NO mejora la ventaja sobre el azar: el limite no es la "
            "cantidad de ejemplos."
        ),
    }
    SALIDA.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        f"\n{'':10} {'velas':>7} {'raros':>7} {'F1':>10} {'azar':>9} {'ventaja':>9} {'tramos':>7}"
    )
    for nombre, d in (("4 horas", a_4h), ("1 hora", a_1h)):
        print(
            f"{nombre:10} {d['velas']:>7} "
            f"{d['n_clase_maximo'] + d['n_clase_minimo']:>7} "
            f"{d['f1_macro']:>10.6f} {d['f1_macro_azar']:>9.6f} "
            f"{d['ventaja_sobre_azar']:>+9.6f} "
            f"{d['tramos_a_favor']:>3}/{d['tramos_medidos']:<3}"
        )
    print(f"\n{medido['veredicto']}")
    print(f"constancia en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
