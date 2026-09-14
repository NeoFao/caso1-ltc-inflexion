"""Las pruebas de deteccion, ahora sobre el modelo fundacional y el avanzado.

Por que existe este guion
-------------------------
`scripts/pruebas_deteccion.py` corre las cuatro pruebas que pide el enunciado, pero
**las cuatro con el modelo clasico**: en `pruebas-deteccion.json` las claves son
`f1_macro_bosque`, `f1_maximo_bosque` y `f1_minimo_bosque`.

El enunciado pide pruebas de deteccion en las semanas 3 **y** 4, y la semana 4 es la
del modelo avanzado. Faltaban. Esto las corre.

Que se repite y que no
----------------------
La **prueba 1** (el etiquetador solo, 187/187 vertices) **no se repite**: no interviene
ningun modelo, solo `etiquetar()`. Repetirla con otro modelo mediria lo mismo.

Las **pruebas 2, 3 y 4** si dependen del modelo y se corren para los tres:

- **2. Sintetico, circuito completo.** Serie en zigzag sin ruido, por el mismo canal
  que los datos reales.
- **3. Entrenamiento.** Sobre el bloque que el modelo ya vio.
- **4. Tiempo real.** Las velas de a una frente al bloque entero. Sobre los profundos
  esta prueba dice algo que no decia antes: los dos leen su contexto de la serie de
  precios por posicion, asi que **es aqui donde se comprueba que ese contexto es
  causal** y no mira hacia adelante.

El criterio, fijado ANTES de correr
-----------------------------------
El mismo que se aplico al clasico, sin aflojarlo: el modelo tiene que superar al
`baseline_aleatorio` **de la misma corrida** en el F1 de **las dos** clases extremas
(guardarrail del issue #51 -- "> 0" no alcanza).

Y la expectativa, tambien antes de mirar
----------------------------------------
Esto se escribe de antemano para que el resultado no se pueda leer como que elegimos
la lectura despues.

**Esperamos que los dos profundos fallen la prueba 2 o la 3, o las dos.** La razon no
es nueva: sobre validacion ninguno de los dos supera al azar de forma distinguible con
1 959 observaciones, y el informe ya lo reporta. Si ademas fallan aqui, lo que eso
senala es **el puente** -- pronosticar una trayectoria y etiquetarla -- y no el canal,
porque el canal es el mismo que el clasico recorre con exito.

**Esperamos que los dos pasen la prueba 4**, porque su contexto esta construido para
ser causal. Si fallara, seria un hallazgo grave y hay que publicarlo igual.

Un fallo aqui **no invalida nada de lo ya medido**: no toca el bloque de prueba, que
se gasto el 07/09, ni cambia una sola cifra del informe. Anade la medicion que faltaba.

Punto de entrada:
    uv run python scripts/pruebas_deteccion_profundos.py
"""

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from contracts.config import ACTIVO_OBJETIVO, GRANULARIDAD, HORIZONTE_H, VENTANA_W  # noqa: E402
from contracts.labeling import etiquetar, latencia_real, objetivo  # noqa: E402
from contracts.metrics import evaluar  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from contracts.splits import particionar  # noqa: E402
from src.features.base import construir  # noqa: E402
from src.modelos.avanzado import ITransformerAvanzado, cierres_del_panel  # noqa: E402
from src.modelos.base import BaselineAleatorio  # noqa: E402
from src.modelos.clasico import BosqueAleatorio  # noqa: E402
from src.modelos.experimento import detecta_mejor_que_azar  # noqa: E402
from src.modelos.fundacional import ChronosBolt  # noqa: E402
from src.sintetico.generador import serie_zigzag  # noqa: E402

RUTA = RAIZ / "docs" / "evidencias" / "pruebas-deteccion-profundos.json"
N_SINTETICO = 3000
N_TIEMPO_REAL = 200  # menos que las 500 del clasico: Chronos infiere vela a vela

CRITERIO = (
    "El modelo supera al baseline_aleatorio de la MISMA corrida en el F1 de las dos "
    "clases extremas (guardarrail del #51: '> 0' no alcanza). Es el mismo criterio "
    "que se le aplico al clasico, sin aflojarlo."
)


def _panel_desde_serie(serie: pd.Series) -> pd.DataFrame:
    """Igual que en `pruebas_deteccion.py`: el mismo canal, no uno propio."""
    columnas = {}
    for i, activo in enumerate(("LTC", "BTC", "ETH", "SOL", "XRP", "ADA")):
        desplazada = serie.shift(i).bfill()
        for campo, factor in (
            ("apertura", 0.999),
            ("maximo", 1.002),
            ("minimo", 0.998),
            ("cierre", 1.0),
        ):
            columnas[f"{activo}_{campo}"] = desplazada * factor
        columnas[f"{activo}_volumen"] = pd.Series(1_000.0, index=serie.index)
    return pd.DataFrame(columnas, index=serie.index)


def _fabricas(panel: pd.DataFrame) -> dict:
    """Los tres modelos, construidos sobre el mismo panel.

    El clasico va incluido a proposito, como **control**: si en esta corrida diera
    algo distinto de lo que ya dice `pruebas-deteccion.json`, el problema estaria en
    este guion y no en los modelos.
    """
    return {
        "bosque_aleatorio": lambda: BosqueAleatorio(semilla=0),
        "chronos_bolt": lambda: ChronosBolt(
            cierre(panel, ACTIVO_OBJETIVO), w=VENTANA_W, h=HORIZONTE_H
        ),
        "itransformer": lambda: ITransformerAvanzado(
            cierres_del_panel(panel), w=VENTANA_W, h=HORIZONTE_H, semilla=0
        ),
    }


def margenes(medida: dict) -> dict:
    """Cuanto le gana al azar en cada clase.

    Es una **resta** de dos cifras de la misma corrida, no una medicion nueva. Se
    guarda en la evidencia porque el verificador exige que todo numero citado exista
    ahi, y citar una resta hecha a mano en un documento es exactamente por donde se
    colaron errores antes.
    """
    return {
        "f1_macro": round(medida["f1_macro"] - medida["f1_macro_azar"], 6),
        "f1_maximo": round(medida["f1_maximo"] - medida["f1_maximo_azar"], 6),
        "f1_minimo": round(medida["f1_minimo"] - medida["f1_minimo_azar"], 6),
    }


def _medir(modelo, X, y, entrenables, evaluables) -> dict:
    """Entrena con `entrenables` y evalua sobre `evaluables`, contra el azar."""
    verdad_entrenamiento = y[entrenables].astype(int).to_numpy()
    inicio = time.perf_counter()
    modelo.entrenar(X[entrenables], verdad_entrenamiento)
    segundos = time.perf_counter() - inicio

    azar = BaselineAleatorio(semilla=0)
    azar.entrenar(X[entrenables], verdad_entrenamiento)

    verdad = y[evaluables].astype(int).to_numpy()
    r_modelo = evaluar(verdad, np.asarray(modelo.predecir(X[evaluables]), dtype=int))
    r_azar = evaluar(verdad, np.asarray(azar.predecir(X[evaluables]), dtype=int))

    medida = {
        "n": int(evaluables.sum()),
        "segundos_entrenamiento": round(segundos, 1),
        "f1_macro": round(r_modelo["f1_macro"], 6),
        "f1_macro_azar": round(r_azar["f1_macro"], 6),
        "f1_maximo": round(r_modelo["f1_maximo"], 6),
        "f1_maximo_azar": round(r_azar["f1_maximo"], 6),
        "f1_minimo": round(r_modelo["f1_minimo"], 6),
        "f1_minimo_azar": round(r_azar["f1_minimo"], 6),
        "precision_direccional": round(r_modelo["precision_direccional"], 6),
        "supera": bool(detecta_mejor_que_azar(r_modelo, r_azar)),
    }
    medida["margen_sobre_azar"] = margenes(medida)
    return medida


def prueba_2_sintetico(fabrica) -> dict:
    indice = pd.date_range(
        "2020-01-01", periods=N_SINTETICO, freq=GRANULARIDAD, tz="UTC", name="fecha"
    )
    serie, _ = serie_zigzag(n=N_SINTETICO, w=VENTANA_W, semilla=0, ruido=0.0)
    serie.index = indice

    panel = _panel_desde_serie(serie)
    X = construir(panel)
    y = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), VENTANA_W), HORIZONTE_H)
    particion = particionar(n=len(y), w=VENTANA_W, h=HORIZONTE_H)

    entrenables = particion.entrenamiento & y.notna().to_numpy()
    evaluables = particion.validacion & y.notna().to_numpy()
    return _medir(fabrica(panel), X, y, entrenables, evaluables)


def prueba_3_entrenamiento(panel, X, y, particion, fabrica) -> dict:
    entrenables = particion.entrenamiento & y.notna().to_numpy()
    medida = _medir(fabrica(panel), X, y, entrenables, entrenables)
    medida["advertencia"] = (
        "Alto aqui NO es evidencia de que el modelo sirva: el modelo ya vio estas "
        "etiquetas. Lo informativo seria un resultado bajo."
    )
    return medida


def prueba_4_tiempo_real(panel, X, y, particion, fabrica) -> dict:
    """De a una contra el bloque entero. En los profundos comprueba la causalidad."""
    entrenables = particion.entrenamiento & y.notna().to_numpy()
    modelo = fabrica(panel)
    modelo.entrenar(X[entrenables], y[entrenables].astype(int).to_numpy())

    tramo = np.flatnonzero(particion.validacion)[-N_TIEMPO_REAL:]
    una_por_una = np.array(
        [int(np.asarray(modelo.predecir(X.iloc[[i]]), dtype=int)[0]) for i in tramo]
    )
    en_bloque = np.asarray(modelo.predecir(X.iloc[tramo]), dtype=int)

    identicas = bool(np.array_equal(una_por_una, en_bloque))
    return {
        "que_comprueba": (
            "Que el modelo predice lo mismo recibiendo las velas de a una que "
            "procesando el bloque. En los profundos esto comprueba ademas que el "
            "contexto que leen de la serie de precios es causal: si tomaran una sola "
            "vela de mas hacia adelante, las dos formas no coincidirian."
        ),
        "n_velas_simuladas": int(len(tramo)),
        "predicciones_identicas": identicas,
        "discrepancias": int((una_por_una != en_bloque).sum()),
        "latencia_de_confirmacion_velas": latencia_real(VENTANA_W, HORIZONTE_H),
        "supera": identicas,
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    panel = pd.read_parquet(RAIZ / "data" / "processed" / f"panel_{GRANULARIDAD}_v1.parquet")
    X = construir(panel)
    y = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), VENTANA_W), HORIZONTE_H)
    particion = particionar(n=len(y), w=VENTANA_W, h=HORIZONTE_H)

    resultados: dict[str, dict] = {}

    for nombre in ("bosque_aleatorio", "chronos_bolt", "itransformer"):
        fabrica = lambda p, _n=nombre: _fabricas(p)[_n]()  # noqa: E731
        print(f"\n=== {nombre} ===", flush=True)

        print("  2. sintetico, circuito completo...", flush=True)
        p2 = prueba_2_sintetico(fabrica)
        print(
            f"     F1 macro {p2['f1_macro']} contra {p2['f1_macro_azar']} -> {p2['supera']}",
            flush=True,
        )

        print("  3. entrenamiento...", flush=True)
        p3 = prueba_3_entrenamiento(panel, X, y, particion, fabrica)
        print(
            f"     F1 macro {p3['f1_macro']} contra {p3['f1_macro_azar']} -> {p3['supera']}",
            flush=True,
        )

        print("  4. tiempo real...", flush=True)
        p4 = prueba_4_tiempo_real(panel, X, y, particion, fabrica)
        print(
            f"     {p4['n_velas_simuladas']} velas, discrepancias "
            f"{p4['discrepancias']} -> {p4['supera']}",
            flush=True,
        )

        resultados[nombre] = {
            "2_sintetico_modelo_completo": p2,
            "3_entrenamiento": p3,
            "4_tiempo_real": p4,
        }

    medido = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "que_es": (
            "Las pruebas de deteccion 2, 3 y 4 corridas sobre el modelo fundacional y "
            "el avanzado, que hasta ahora solo se habian corrido con el clasico. El "
            "clasico se incluye como control de este guion."
        ),
        "no_se_repite_la_1": (
            "La prueba 1 (el etiquetador solo, 187/187) no interviene ningun modelo: "
            "repetirla mediria lo mismo. Sigue en pruebas-deteccion.json."
        ),
        "criterio_preregistrado": CRITERIO,
        "expectativa_declarada_antes": (
            "Se esperaba que los dos profundos fallaran la 2 o la 3, o las dos, porque "
            "sobre validacion ninguno supera al azar de forma distinguible con 1 959 "
            "observaciones. Un fallo ahi senala EL PUENTE -- pronosticar trayectoria y "
            "etiquetarla -- y no el canal, que es el mismo que el clasico recorre con "
            "exito. Se esperaba que los dos pasaran la 4, porque su contexto esta "
            "construido para ser causal."
        ),
        "no_toca_la_reserva": (
            "Todo esto es sintetico, entrenamiento y validacion. El bloque de prueba se "
            "gasto el 07/09 y no se vuelve a medir. Ninguna cifra del informe cambia."
        ),
        "parametros": {
            "intervalo": GRANULARIDAD,
            "w": VENTANA_W,
            "h": HORIZONTE_H,
            "n_sintetico": N_SINTETICO,
            "n_tiempo_real": N_TIEMPO_REAL,
            "por_que_200_y_no_500": (
                "El clasico simulo 500 velas. Chronos-Bolt infiere vela a vela sobre el "
                "panel completo, asi que 500 multiplicarian el costo sin cambiar lo que "
                "la prueba responde: una sola discrepancia ya la haria fallar."
            ),
        },
        "resultados": resultados,
        "veredicto": {
            "causalidad_los_tres": bool(
                all(r["4_tiempo_real"]["supera"] for r in resultados.values())
            ),
            "detectan_sobre_sintetico": {
                n: r["2_sintetico_modelo_completo"]["supera"] for n, r in resultados.items()
            },
            "detectan_sobre_entrenamiento": {
                n: r["3_entrenamiento"]["supera"] for n, r in resultados.items()
            },
        },
    }

    RUTA.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nconstancia en {RUTA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
