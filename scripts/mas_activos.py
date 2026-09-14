"""Si el limite son los eventos, la salida es mas activos. Probemoslo.

De donde sale
-------------
`granularidad_1h.py` midio que cuatro veces mas velas dan **veintiseis giros mas**:
los puntos de inflexion que ocurrieron en seis anios son los que ocurrieron, y
muestrear mas fino no crea eventos. El limite no es el numero de observaciones, es
**el numero de eventos**.

De ahi salen dos caminos, y solo uno cabe en el tiempo que queda: **mas periodo** o
**mas activos**. Cada activo nuevo aporta sus propios ~1 200 giros.

Y encaja con lo unico que habia mostrado algo antes: el apilado de los seis activos
fue el **unico** de los siete primeros intentos con senal, 6 de 9 tramos. Nunca se
probo con mas de seis.

Que se prueba
-------------
Entrenar apilando las filas de **N activos** y evaluar **siempre sobre LTC**, que es
el objetivo del proyecto. Se comparan tres tamanos: **1** (solo LTC), **6** (los del
panel) y **12** (los seis mas seis nuevos).

Los seis nuevos se eligen por un criterio unico y declarado: **cotizar en Binance
contra USDT desde antes de agosto de 2020**, que es donde empieza el panel. Si su
historia empezara despues, cada activo nuevo recortaria la ventana comun y estariamos
cambiando dos cosas a la vez.

DOGE, LINK, TRX, BCH, XLM y ATOM cumplen. No se eligieron por rendimiento -- eso
seria elegir la respuesta.

Como se apila sin mover la evaluacion
-------------------------------------
Las caracteristicas de cada activo se construyen **sobre si mismo** y se le quita el
prefijo, de modo que los doce comparten el mismo espacio de columnas. Es la misma
maquinaria de `apilado_multiactivo.py`.

Cada activo nuevo se **realinea al indice del panel de 4 horas** en vez de
consolidarse con el resto: consolidar recorta a la ventana comun de todos, y eso
habria cambiado las filas sobre las que se evalua LTC. Asi la evaluacion es
identica en los tres tamanos y lo unico que cambia es de donde salen las filas de
entrenamiento.

El criterio, fijado ANTES de correr
-----------------------------------
Para decir que mas activos ayudan, sobre los nueve tramos:

1. La **ventaja sobre el azar** al apilar **12** es mayor que al apilar **6**.
2. Y la de 6 es mayor que la de 1. Si no hubiera esa gradacion, lo que se estaria
   midiendo no seria "mas eventos ayudan" sino el ruido de un tamano concreto.
3. El signo de la ventaja del apilado de 12 es **estable en los nueve tramos**.

Y la expectativa, tambien antes de mirar
----------------------------------------
**Se espera que ayude, y poco.** El apilado de seis dio 6 de 9 -- senal, no
demostracion -- y doblar el numero de activos deberia empujar en la misma direccion.

Pero hay una razon medida para dudar: los seis del panel **se mueven juntos**. La
correlacion entre los quince pares va de **+0,517489** a **+0,829963** y ningun par
es inversamente proporcional. Si los seis nuevos tambien son cripto grandes, sus
giros van a caer en los mismos sitios, y **mil doscientos giros repetidos no son dos
mil cuatrocientos giros distintos**.

**Si no ayuda, eso es lo que habra pasado**, y es informacion: querria decir que el
limite no es el numero de eventos sino el numero de eventos **independientes**.

No toca la reserva ni el panel del informe.

Punto de entrada:
    uv run python scripts/mas_activos.py --descargar
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

from contracts.config import (  # noqa: E402
    ACTIVO_OBJETIVO,
    ACTIVOS,
    HORIZONTE_H,
    SIMBOLOS,
    VENTANA_W,
)
from contracts.labeling import etiquetar, objetivo  # noqa: E402
from contracts.metrics import evaluar  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from src.features.base import (  # noqa: E402
    bollinger,
    macd,
    medias_moviles,
    retornos,
    rezagos,
    rsi,
    ventana_deslizante,
    volatilidad,
)
from src.modelos.base import BaselineAleatorio  # noqa: E402
from src.modelos.clasico import HIPERPARAMETROS, BosqueAleatorio  # noqa: E402
from src.panel.descarga import descargar_activo  # noqa: E402

SALIDA = RAIZ / "docs" / "evidencias" / "m0-mas-activos-4h-w7-h1.json"
CRUDOS = RAIZ / "data" / "processed" / "extra"

#: Los seis nuevos. Se anaden al mapa EN MEMORIA: contracts/config.py esta congelado
#: desde el 18/08 y un experimento no lo toca.
NUEVOS = {
    "DOGE": "DOGEUSDT",
    "LINK": "LINKUSDT",
    "TRX": "TRXUSDT",
    "BCH": "BCHUSDT",
    "XLM": "XLMUSDT",
    "ATOM": "ATOMUSDT",
}
SIMBOLOS.update(NUEVOS)

N_TRAMOS = 9


def construir_para(panel: pd.DataFrame, activo: str) -> pd.DataFrame:
    """Caracteristicas de un activo sobre si mismo, sin el prefijo.

    Es la misma funcion de `apilado_multiactivo.py`: sin prefijo, los doce activos
    comparten espacio de columnas y sus filas se pueden apilar.
    """
    piezas = [
        retornos(panel, activo),
        volatilidad(panel, activo),
        medias_moviles(panel, activo=activo),
        rsi(panel, activo=activo),
        macd(panel, activo=activo),
        bollinger(panel, activo=activo),
        ventana_deslizante(panel, activo=activo),
        rezagos(panel, activo, relativo=True),
    ]
    X = pd.concat(piezas, axis=1)
    X.columns = [c.replace(f"{activo}_", "", 1) for c in X.columns]
    return X


def mini_panel(crudo: pd.DataFrame, activo: str, indice: pd.Index) -> pd.DataFrame:
    """Un panel de un solo activo, realineado al indice del panel de 4 horas."""
    columnas = {
        f"{activo}_{campo}": crudo[campo]
        for campo in ("apertura", "maximo", "minimo", "cierre", "volumen")
    }
    return pd.DataFrame(columnas).reindex(indice)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    analizador = argparse.ArgumentParser(description=__doc__)
    analizador.add_argument("--descargar", action="store_true")
    argumentos = analizador.parse_args()

    panel = pd.read_parquet(RAIZ / "data" / "processed" / "panel_4h_v1.parquet")
    w, h = VENTANA_W, HORIZONTE_H
    CRUDOS.mkdir(parents=True, exist_ok=True)

    tandas: dict[str, tuple[pd.DataFrame, pd.Series]] = {}
    for a in ACTIVOS:
        tandas[a] = (construir_para(panel, a), objetivo(etiquetar(cierre(panel, a), w), h))

    cobertura = {}
    for a in NUEVOS:
        archivo = CRUDOS / f"{a}_4h.parquet"
        if argumentos.descargar or not archivo.exists():
            crudo = descargar_activo(a, "4h", desde="2020-08-01")
            crudo.to_parquet(archivo)
        else:
            crudo = pd.read_parquet(archivo)
        mp = mini_panel(crudo, a, panel.index)
        cubiertas = int(mp[f"{a}_cierre"].notna().sum())
        cobertura[a] = {
            "velas_descargadas": int(len(crudo)),
            "velas_alineadas_al_panel": cubiertas,
            "por_ciento_del_panel": round(100 * cubiertas / len(panel), 2),
            "desde": str(crudo.index.min()),
        }
        print(
            f"  {a}: {len(crudo)} velas, cubre {cobertura[a]['por_ciento_del_panel']} % del panel",
            flush=True,
        )
        tandas[a] = (construir_para(mp, a), objetivo(etiquetar(cierre(mp, a), w), h))

    XL, yL = tandas[ACTIVO_OBJETIVO]
    validos = np.flatnonzero(yL.notna().to_numpy())
    embargo = w + h
    corte = len(validos) // 2
    ancho = (len(validos) - corte) // N_TRAMOS

    grupos = {
        "1_solo_LTC": [ACTIVO_OBJETIVO],
        "6_los_del_panel": list(ACTIVOS),
        "12_con_los_nuevos": list(ACTIVOS) + list(NUEVOS),
    }
    resultados: dict[str, dict] = {}

    for nombre, activos in grupos.items():
        ventajas, f1, f1_azar, filas_entren = [], [], [], []
        for i in range(N_TRAMOS):
            inicio = corte + i * ancho
            fin = inicio + ancho if i < N_TRAMOS - 1 else len(validos)
            tramo = validos[inicio:fin]
            limite = validos[max(0, inicio - embargo)] if inicio > 0 else 0
            if len(tramo) == 0:
                continue

            # Entrenamiento: las filas de CADA activo anteriores al corte temporal.
            trozos_X, trozos_y = [], []
            for a in activos:
                Xa, ya = tandas[a]
                usables = ya.notna().to_numpy() & (np.arange(len(ya)) < limite)
                if usables.sum() == 0:
                    continue
                trozos_X.append(Xa[usables])
                trozos_y.append(ya[usables])
            if not trozos_X:
                continue
            Xe = pd.concat(trozos_X, axis=0)
            ye = pd.concat(trozos_y, axis=0)
            filas_entren.append(int(len(Xe)))

            bosque = BosqueAleatorio(
                n_arboles=HIPERPARAMETROS["n_estimators"],
                semilla=HIPERPARAMETROS["random_state"],
                nombre=nombre,
            )
            bosque.entrenar(Xe, ye)
            azar = BaselineAleatorio(semilla=HIPERPARAMETROS["random_state"])
            azar.entrenar(Xe, ye)

            verdad = yL.iloc[tramo].astype(int).to_numpy()
            mb = evaluar(verdad, np.asarray(bosque.predecir(XL.iloc[tramo]), dtype=int))
            ma = evaluar(verdad, np.asarray(azar.predecir(XL.iloc[tramo]), dtype=int))
            f1.append(mb["f1_macro"])
            f1_azar.append(ma["f1_macro"])
            ventajas.append(mb["f1_macro"] - ma["f1_macro"])

        v = np.array(ventajas)
        resultados[nombre] = {
            "activos": activos,
            "n_activos": len(activos),
            "filas_de_entrenamiento_ultimo_tramo": filas_entren[-1] if filas_entren else 0,
            "f1_macro": round(float(np.mean(f1)), 6),
            "f1_macro_azar": round(float(np.mean(f1_azar)), 6),
            "ventaja_sobre_azar": round(float(v.mean()), 6),
            "tramos_a_favor": int((v > 0).sum()),
            "tramos_medidos": int(len(v)),
            "signo_estable": bool((v > 0).all()),
        }
        d = resultados[nombre]
        print(
            f"\n{nombre:22} filas {d['filas_de_entrenamiento_ultimo_tramo']:>6}  "
            f"F1 {d['f1_macro']:.6f} vs {d['f1_macro_azar']:.6f}  "
            f"ventaja {d['ventaja_sobre_azar']:+.6f}  "
            f"tramos {d['tramos_a_favor']}/{d['tramos_medidos']}",
            flush=True,
        )

    v1 = resultados["1_solo_LTC"]["ventaja_sobre_azar"]
    v6 = resultados["6_los_del_panel"]["ventaja_sobre_azar"]
    v12 = resultados["12_con_los_nuevos"]["ventaja_sobre_azar"]
    ayuda = bool(v12 > v6 > v1 and resultados["12_con_los_nuevos"]["signo_estable"])

    medido = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "que_mide": (
            "Si apilar las filas de mas activos mejora la deteccion sobre LTC. Sale de "
            "que granularidad_1h midio que el limite no es el numero de observaciones "
            "sino el de eventos: cada activo nuevo aporta sus propios giros."
        ),
        "como_se_eligieron_los_nuevos": (
            "Criterio unico y declarado: cotizar en Binance contra USDT desde antes de "
            "agosto de 2020, que es donde empieza el panel. No se eligieron por "
            "rendimiento, que seria elegir la respuesta."
        ),
        "por_que_se_realinean_y_no_se_consolidan": (
            "Consolidar recorta a la ventana comun de todos los activos, y eso habria "
            "cambiado las filas sobre las que se evalua LTC. Realineando al indice del "
            "panel, la evaluacion es identica en los tres tamanos y lo unico que cambia "
            "es de donde salen las filas de entrenamiento."
        ),
        "criterio_preregistrado": (
            "La ventaja sobre el azar al apilar 12 es mayor que al apilar 6, y la de 6 "
            "mayor que la de 1; y el signo del apilado de 12 es estable en los nueve "
            "tramos. Sin esa gradacion, lo medido seria el ruido de un tamano concreto."
        ),
        "expectativa_declarada_antes": (
            "Que ayude, y poco. El apilado de seis dio 6 de 9. Pero hay razon medida "
            "para dudar: los seis del panel se mueven juntos, con correlaciones de "
            "+0,517489 a +0,829963 y ningun par inversamente proporcional. Si los nuevos "
            "tambien son cripto grandes, sus giros caen en los mismos sitios, y mil "
            "doscientos giros repetidos no son dos mil cuatrocientos distintos. Si no "
            "ayuda, el limite no es el numero de eventos sino el de eventos "
            "INDEPENDIENTES."
        ),
        "no_toca_nada_publicado": (
            "No modifica contracts/config.py, que esta congelado: los simbolos nuevos se "
            "anaden en memoria. No toca el panel del informe ni la reserva."
        ),
        "cobertura_de_los_nuevos": cobertura,
        "resultados": resultados,
        "ayuda": ayuda,
        "veredicto": (
            "Mas activos SI ayudan: la ventaja crece con el numero apilado."
            if ayuda
            else "Mas activos NO producen la gradacion esperada: el limite no es el "
            "numero de eventos sino el de eventos independientes."
        ),
    }
    SALIDA.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n{medido['veredicto']}")
    print(f"constancia en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
