"""El volumen esta en los datos y ninguna de las 63 columnas lo usa.

El hueco
--------
`src/features/base.py` no menciona el volumen ni una vez: las 63 columnas son
rezagos, retornos, volatilidad, indicadores tecnicos, ventana deslizante y
correlacion cruzada, **todas derivadas del precio**. El panel trae
`LTC_volumen` y las cinco columnas equivalentes de los activos de apoyo, y estan
sin tocar.

Y el volumen es la senal clasica para giros: **agotamiento** en techos -- el precio
sube con volumen cada vez menor -- y **capitulacion** en suelos -- la caida termina
con un pico de volumen. Si eso no aparece en estos datos, conviene saberlo; si
aparece, es senal gratis.

Que se prueba
-------------
Seis columnas nuevas, **solo sobre LTC**, comparadas contra las 63 de siempre:

- `volumen_rel_7` y `volumen_rel_24`: volumen sobre su media movil. Un pico vale 2 o 3.
- `volumen_z_24`: a cuantas desviaciones esta el volumen de su media reciente.
- `volumen_cambio_1`: variacion respecto de la vela anterior.
- `volumen_posicion_24`: donde cae el volumen actual dentro de su rango reciente,
  entre 0 y 1. Es el analogo de `posicion_rango` pero sobre volumen.
- `corr_retorno_volumen_24`: si el precio y el volumen se mueven juntos o al reves.
  Es la que mas directamente mira agotamiento.

**Seis y no sesenta, y solo sobre LTC**, por la razon que el propio
`src/features/base.py` documenta: con 420 ejemplos de la clase minoritaria, anadir
cien columnas garantiza el sobreajuste. Si seis no mueven nada, sesenta tampoco lo
habrian movido por la via limpia.

Esto NO cambia el contrato de caracteristicas
---------------------------------------------
Las caracteristicas son el modulo de M2. Este guion **mide** si el volumen aporta,
construyendo las columnas aqui mismo; **no toca `src/features/base.py`**. Si el
resultado es positivo, adoptarlo es decision de M2, no de este experimento.

El criterio, fijado ANTES de correr
-----------------------------------
Para decir que el volumen aporta, sobre los nueve tramos:

1. La ventaja del bosque **con volumen** sobre el bosque **sin volumen** es positiva
   en F1 macro.
2. Y **el signo es estable en los nueve tramos**. El umbral de la D5 no aplica: eso
   es una convencion para elegir entre configuraciones, no para responder si algo
   aporta.

Se mide con los dos objetivos: el **exacto** (k=0), que es el del informe, y el de
**proximidad a una vela** (k=1), que es donde el modelo tiene mas senal. Si el
volumen ayudara en uno y no en el otro, eso tambien es informacion.

Y la expectativa, tambien antes de mirar
----------------------------------------
**Se espera que no aporte de forma estable.** Siete de los nueve ejes probados hasta
ahora no dieron nada, y los dos que dieron no tocaban las caracteristicas. Ademas
`m2-importancia-permutacion` ya midio que 17 de las 63 columnas actuales no superan
el piso de ruido: el problema no parece ser falta de columnas.

**Si no aporta, se publica que no aporta**, y sirve para cerrar la pregunta en vez de
dejarla como "algo que no probamos".

No toca la reserva. Nueve tramos de validacion deslizante.

Punto de entrada:
    uv run python scripts/caracteristicas_volumen.py
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
from contracts.labeling import etiquetar, objetivo  # noqa: E402
from contracts.metrics import evaluar  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from src.features.base import construir  # noqa: E402
from src.modelos.base import BaselineAleatorio  # noqa: E402
from src.modelos.clasico import HIPERPARAMETROS, BosqueAleatorio  # noqa: E402

sys.path.insert(0, str(RAIZ / "scripts"))
from objetivo_proximidad import objetivo_cercano  # noqa: E402

SALIDA = RAIZ / "docs" / "evidencias" / "m0-caracteristicas-volumen-4h-w7-h1.json"
N_TRAMOS = 9


def columnas_de_volumen(panel: pd.DataFrame, activo: str = ACTIVO_OBJETIVO) -> pd.DataFrame:
    """Las seis columnas de volumen, solo sobre el activo objetivo.

    Todas son relativas o normalizadas: el volumen en bruto crece con los anios y
    seria un reloj, el mismo defecto que tenian los rezagos de precio en nivel.
    """
    v = panel[f"{activo}_volumen"].astype("float64")
    c = panel[f"{activo}_cierre"].astype("float64")
    retorno = c.pct_change()

    fuera = {}
    for ventana in (7, 24):
        media = v.rolling(ventana, min_periods=ventana).mean()
        fuera[f"{activo}_volumen_rel_{ventana}"] = v / media

    media24 = v.rolling(24, min_periods=24).mean()
    desvio24 = v.rolling(24, min_periods=24).std()
    fuera[f"{activo}_volumen_z_24"] = (v - media24) / desvio24
    fuera[f"{activo}_volumen_cambio_1"] = v.pct_change()

    minimo = v.rolling(24, min_periods=24).min()
    maximo = v.rolling(24, min_periods=24).max()
    fuera[f"{activo}_volumen_posicion_24"] = (v - minimo) / (maximo - minimo)

    fuera[f"{activo}_corr_retorno_volumen_24"] = retorno.rolling(24, min_periods=24).corr(
        v.pct_change()
    )
    return pd.DataFrame(fuera, index=panel.index)


def medir(X: pd.DataFrame, y: pd.Series, etiqueta: str) -> dict:
    """Nueve tramos con ventana expansiva, contra el azar de la misma corrida."""
    validos = np.flatnonzero(y.notna().to_numpy())
    embargo = VENTANA_W + HORIZONTE_H
    corte = len(validos) // 2
    ancho = (len(validos) - corte) // N_TRAMOS

    f1, f1_azar, por_tramo = [], [], []
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
        por_tramo.append(
            {
                "tramo": i,
                "f1_macro": round(mb["f1_macro"], 6),
                "f1_maximo": round(mb["f1_maximo"], 6),
                "f1_minimo": round(mb["f1_minimo"], 6),
            }
        )

    return {
        "columnas": int(X.shape[1]),
        "f1_macro": round(float(np.mean(f1)), 6),
        "f1_macro_azar": round(float(np.mean(f1_azar)), 6),
        "ventaja_sobre_azar": round(float(np.mean(f1) - np.mean(f1_azar)), 6),
        "por_tramo": por_tramo,
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    panel = pd.read_parquet(RAIZ / "data" / "processed" / f"panel_{GRANULARIDAD}_v1.parquet")
    sin = construir(panel, rezagos_relativos=True)
    vol = columnas_de_volumen(panel)
    con = pd.concat([sin, vol], axis=1)
    print(f"sin volumen: {sin.shape[1]} columnas   con volumen: {con.shape[1]}")

    exacto = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), VENTANA_W), HORIZONTE_H)

    resultados = {}
    for k, nombre in ((0, "exacto"), (1, "proximidad_1_vela")):
        y = objetivo_cercano(exacto, k)
        a = medir(sin, y, "sin_volumen")
        b = medir(con, y, "con_volumen")

        diferencias = [
            fb["f1_macro"] - fa["f1_macro"]
            for fa, fb in zip(a["por_tramo"], b["por_tramo"], strict=True)
        ]
        d = np.array(diferencias)
        resultados[nombre] = {
            "objetivo": nombre,
            "velas_de_margen": k,
            "sin_volumen": a,
            "con_volumen": b,
            "diferencia_media": round(float(d.mean()), 6),
            "tramos_a_favor": int((d > 0).sum()),
            "tramos_medidos": int(len(d)),
            "signo_estable": bool((d > 0).all()),
            "aporta": bool((d > 0).all() and d.mean() > 0),
        }
        r = resultados[nombre]
        print(
            f"\n{nombre}:  sin {a['f1_macro']:.6f}   con {b['f1_macro']:.6f}   "
            f"diferencia {r['diferencia_media']:+.6f}   "
            f"tramos {r['tramos_a_favor']}/{r['tramos_medidos']}   "
            f"{'APORTA' if r['aporta'] else 'no aporta'}"
        )

    medido = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "que_mide": (
            "Si anadir seis columnas derivadas del volumen aporta sobre las 63 de "
            "siempre. El panel trae el volumen de los seis activos y ninguna de las 63 "
            "columnas actuales lo usa."
        ),
        "las_seis_columnas": list(vol.columns),
        "por_que_seis_y_solo_LTC": (
            "Por la razon que documenta src/features/base.py: con 420 ejemplos de la "
            "clase minoritaria, anadir cien columnas garantiza el sobreajuste. Si seis "
            "no mueven nada, sesenta tampoco lo habrian movido por la via limpia."
        ),
        "no_cambia_el_contrato": (
            "Las caracteristicas son el modulo de M2. Este guion mide; no toca "
            "src/features/base.py. Adoptarlo es decision de M2."
        ),
        "criterio_preregistrado": (
            "La ventaja del bosque con volumen sobre el bosque sin volumen es positiva "
            "en F1 macro Y el signo es estable en los nueve tramos. El umbral de la D5 "
            "no aplica: es una convencion para elegir entre configuraciones, no para "
            "responder si algo aporta."
        ),
        "expectativa_declarada_antes": (
            "Se esperaba que NO aporte de forma estable: siete de los nueve ejes "
            "probados no dieron nada y los dos que dieron no tocaban las "
            "caracteristicas. Ademas m2-importancia-permutacion ya midio que 17 de las "
            "63 columnas no superan el piso de ruido."
        ),
        "no_toca_la_reserva": "Nueve tramos de validacion deslizante.",
        "resultados": resultados,
        "veredicto": {
            nombre: ("aporta" if r["aporta"] else "no aporta") for nombre, r in resultados.items()
        },
    }
    SALIDA.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nconstancia en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
