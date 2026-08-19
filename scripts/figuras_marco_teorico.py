"""Produce todas las figuras y mediciones del marco teorico de la Semana 1.

El profesor pidio ilustrar los conceptos con series sinteticas construidas por
nosotros, con volatilidad y correlacion controladas, ademas de los datos reales.
Este script genera cada par: primero el caso donde la respuesta correcta la
pusimos nosotros, despues LTC real.

Que hace y que no: produce la EVIDENCIA. El texto lo escriben M1 y M2, y tiene
que ser asi — un marco teorico copiado de figuras ajenas no se puede defender.

Salidas:
    docs/evidencias/mt-*.png                figuras numeradas por concepto
    docs/evidencias/marco-teorico.json      todos los numeros medidos, citables

Uso:
    uv run python scripts/figuras_marco_teorico.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from statsmodels.tsa.seasonal import seasonal_decompose  # noqa: E402

from contracts.config import ACTIVOS  # noqa: E402

# Anclados a proposito, y NO leidos de contracts/config.py.
#
# La evidencia de la Semana 1 se midio con velas diarias y w=5, y el documento
# entregado el 18/08/2026 cita esos numeros. El contrato se congelo despues en 4h
# y w=7, asi que leerlo desde aqui haria que re-ejecutar este guion cambiara la
# evidencia y dejara al entregable citando valores que ya no existen, en silencio.
#
# La evidencia de una entrega ya hecha es historia, no una vista del contrato
# vigente. Para producir las figuras de una entrega futura, se cambian estos dos
# valores a proposito y se declara en el documento con que se midio.
GRANULARIDAD = "1d"
VENTANA_W = 5
from contracts.labeling import Clase, etiquetar, resumen_clases  # noqa: E402
from contracts.metrics import evaluar, matriz_confusion  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from src.diagnostico.pruebas import (  # noqa: E402
    autocorrelacion,
    matriz_correlacion,
    tabla_estacionariedad,
)
from src.modelos.base import BaselineTrivial  # noqa: E402
from src.sintetico.generador import panel_correlacionado, serie_zigzag  # noqa: E402
from src.visual import estilo  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
EVIDENCIAS = RAIZ / "docs" / "evidencias"

medido: dict[str, object] = {}


def _correlaciones_cruzadas(panel: pd.DataFrame) -> np.ndarray:
    retornos = pd.DataFrame({a: cierre(panel, a).pct_change() for a in ACTIVOS}).dropna()
    matriz = retornos.corr().to_numpy()
    return matriz[np.triu_indices_from(matriz, k=1)]


def figura_01_serie(ltc: pd.Series) -> None:
    """Definicion de serie temporal: observaciones ordenadas en el tiempo."""
    fig, eje = plt.subplots()
    eje.plot(ltc.index, ltc.to_numpy(), color=estilo.NAVY)
    eje.set_title("Precio de cierre de LTC")
    eje.set_ylabel("USDT")
    fig.autofmt_xdate()
    estilo.guardar(fig, "mt-01-serie-temporal", EVIDENCIAS)
    plt.close(fig)
    medido["serie"] = {
        "n": int(len(ltc)),
        "desde": ltc.index.min().isoformat(),
        "hasta": ltc.index.max().isoformat(),
        "minimo": round(float(ltc.min()), 2),
        "maximo": round(float(ltc.max()), 2),
    }


def figura_02_componentes(ltc: pd.Series) -> None:
    """Componentes: tendencia, estacionalidad y residuo.

    Se usa periodo semanal (7 velas diarias) porque es la unica estacionalidad
    con sentido en un mercado que opera los siete dias.
    """
    descomposicion = seasonal_decompose(ltc, model="additive", period=7)
    fig, ejes = plt.subplots(4, 1, sharex=True, figsize=(9, 8))
    for eje, (serie, nombre) in zip(
        ejes,
        [
            (ltc, "Observado"),
            (descomposicion.trend, "Tendencia"),
            (descomposicion.seasonal, "Estacionalidad (7 velas)"),
            (descomposicion.resid, "Residuo"),
        ],
        strict=True,
    ):
        eje.plot(serie.index, serie.to_numpy(), color=estilo.NAVY, linewidth=1.1)
        eje.set_ylabel(nombre, fontsize=9)
    fig.suptitle("Componentes de la serie de LTC", color=estilo.NAVY, fontweight="bold")
    fig.autofmt_xdate()
    estilo.guardar(fig, "mt-02-componentes", EVIDENCIAS)
    plt.close(fig)

    estacional = descomposicion.seasonal.dropna()
    residuo = descomposicion.resid.dropna()
    medido["componentes"] = {
        "amplitud_estacional": round(float(estacional.max() - estacional.min()), 4),
        "desviacion_residuo": round(float(residuo.std()), 4),
        "peso_estacional_relativo_pct": round(
            100 * float(estacional.std()) / float(ltc.std()), 3
        ),
    }


def figura_03_estacionariedad(panel: pd.DataFrame, sintetico: pd.DataFrame) -> None:
    """ADF en nivel y en retornos, sobre datos reales y sobre una serie construida."""
    nivel = tabla_estacionariedad(panel, en_retornos=False)
    retornos = tabla_estacionariedad(panel, en_retornos=True)
    control = tabla_estacionariedad(sintetico, en_retornos=True)

    nivel.to_csv(EVIDENCIAS / "mt-03-adf-nivel.csv", index=False)
    retornos.to_csv(EVIDENCIAS / "mt-03-adf-retornos.csv", index=False)

    # Escala logaritmica: los p-valores de los retornos son practicamente cero y en
    # escala lineal sus barras desaparecen, dejando una leyenda que promete un color
    # que no se ve. En log se lee lo que importa, que estan a ordenes de magnitud.
    PISO = 1e-6
    fig, eje = plt.subplots(figsize=(8, 4.2))
    x = np.arange(len(ACTIVOS))
    eje.bar(x - 0.2, nivel["p_valor"].clip(lower=PISO), 0.4,
            label="Precio en nivel", color=estilo.MAXIMO,
            edgecolor="black", linewidth=0.7)
    eje.bar(x + 0.2, retornos["p_valor"].clip(lower=PISO), 0.4,
            label=f"Retornos (p < {PISO:g} en las seis)", color=estilo.MINIMO,
            edgecolor="black", linewidth=0.7, hatch="//")
    eje.set_yscale("log")
    eje.set_ylim(PISO / 2, 2)
    eje.axhline(0.05, color=estilo.GRIS, linestyle="--", linewidth=1.2)
    eje.text(-0.55, 0.065, "umbral 0.05", color=estilo.GRIS, fontsize=9)
    for posicion, valor in zip(x, nivel["p_valor"], strict=True):
        eje.text(posicion - 0.2, valor * 1.25, f"{valor:.3f}",
                 ha="center", fontsize=8, color=estilo.GRIS)
    eje.set_xticks(x, list(ACTIVOS))
    eje.set_ylabel("p-valor del test ADF (escala log)")
    eje.set_title("Estacionariedad: nivel contra retornos")
    eje.legend(loc="lower right")
    estilo.guardar(fig, "mt-03-estacionariedad", EVIDENCIAS)
    plt.close(fig)

    medido["estacionariedad"] = {
        "nivel": {
            f["serie"]: {
                "p_valor": round(f["p_valor"], 6),
                "rechaza": f["rechaza_raiz_unitaria_5pct"],
            }
            for _, f in nivel.iterrows()
        },
        "retornos": {
            f["serie"]: {
                "p_valor": round(f["p_valor"], 6),
                "rechaza": f["rechaza_raiz_unitaria_5pct"],
            }
            for _, f in retornos.iterrows()
        },
        "control_sintetico_rechaza_todos": bool(control["rechaza_raiz_unitaria_5pct"].all()),
    }


def figura_04_volatilidad(ltc: pd.Series) -> None:
    """Volatilidad movil y el cociente que demuestra heterocedasticidad."""
    retorno = ltc.pct_change()
    volatilidad = retorno.rolling(30).std().dropna()

    fig, (arriba, abajo) = plt.subplots(2, 1, sharex=True, figsize=(9, 6))
    arriba.plot(ltc.index, ltc.to_numpy(), color=estilo.NAVY)
    arriba.set_ylabel("Cierre")
    abajo.plot(volatilidad.index, volatilidad.to_numpy(), color=estilo.ACENTO)
    abajo.set_ylabel("Volatilidad movil (30)")
    fig.suptitle("LTC: precio y volatilidad", color=estilo.NAVY, fontweight="bold")
    fig.autofmt_xdate()
    estilo.guardar(fig, "mt-04-volatilidad", EVIDENCIAS)
    plt.close(fig)

    medido["volatilidad"] = {
        "maxima": round(float(volatilidad.max()), 5),
        "minima": round(float(volatilidad.min()), 5),
        "cociente_agitado_tranquilo": round(
            float(volatilidad.max() / volatilidad.min()), 1
        ),
        "ventana": 30,
    }


def figura_04b_volatilidad_construida() -> None:
    """Volatilidad baja y alta fijadas por nosotros antes de generar la serie.

    Es el mismo control que ya se aplica a la correlacion: se fija el parametro, se
    genera la serie, se mide, y se comprueba que la medicion recupera lo que se
    pidio. Sin este par, el documento afirma en la introduccion que la volatilidad
    se fija de antemano y luego nunca reporta que valor se fijo.

    Los dos niveles no son arbitrarios. Son los extremos de la volatilidad movil
    medida sobre LTC, de modo que la serie construida acota el rango que de verdad
    se observa en el mercado en lugar de ilustrar una escala inventada. Por eso
    esta funcion corre despues de figura_04_volatilidad, que es la que los mide.
    """
    baja = medido["volatilidad"]["minima"]
    alta = medido["volatilidad"]["maxima"]

    series = {}
    for etiqueta, objetivo in (("baja", baja), ("alta", alta)):
        panel = panel_correlacionado(n=1200, semilla=1, volatilidad=objetivo)
        series[etiqueta] = cierre(panel, "LTC").pct_change().dropna()

    # Un eje compartido es lo que hace visible la diferencia: con escalas
    # independientes las dos series se verian igual de agitadas.
    tope = float(max(s.abs().max() for s in series.values())) * 1.05
    fig, ejes = plt.subplots(2, 1, sharex=True, sharey=True, figsize=(9, 5.5))
    for eje, (etiqueta, retorno) in zip(ejes, series.items(), strict=True):
        eje.plot(range(len(retorno)), retorno.to_numpy(), color=estilo.NAVY, linewidth=0.6)
        eje.set_ylabel(f"Volatilidad {etiqueta}\n(construida)", fontsize=9)
        eje.set_ylim(-tope, tope)
    fig.suptitle(
        "Volatilidad fijada por nosotros: baja contra alta",
        color=estilo.NAVY, fontweight="bold",
    )
    estilo.guardar(fig, "mt-04b-volatilidad-construida", EVIDENCIAS)
    plt.close(fig)

    medida_baja = float(series["baja"].std())
    medida_alta = float(series["alta"].std())
    medido["volatilidad_construida"] = {
        "baja": {"pedida": baja, "medida": round(medida_baja, 5)},
        "alta": {"pedida": alta, "medida": round(medida_alta, 5)},
        "cociente_pedido": round(alta / baja, 1),
        "cociente_medido": round(medida_alta / medida_baja, 1),
    }


def figura_05_heterocedasticidad() -> None:
    """Contraste construido: misma generacion, con y sin regimenes de volatilidad."""
    sin_reg = panel_correlacionado(n=1200, semilla=1, regimenes=False)
    con_reg = panel_correlacionado(
        n=1200, semilla=1, regimenes=True, duracion_regimen=100, multiplicador_regimen=5.0
    )

    fig, (arriba, abajo) = plt.subplots(2, 1, sharex=True, figsize=(9, 5.5))
    for eje, panel, titulo in (
        (arriba, sin_reg, "Homocedastica (construida)"),
        (abajo, con_reg, "Heterocedastica (construida)"),
    ):
        retorno = cierre(panel, "LTC").pct_change()
        eje.plot(range(len(retorno)), retorno.to_numpy(), color=estilo.NAVY, linewidth=0.6)
        eje.set_ylabel(titulo, fontsize=9)
    fig.suptitle(
        "Heterocedasticidad: volatilidad constante contra volatilidad por tramos",
        color=estilo.NAVY, fontweight="bold",
    )
    estilo.guardar(fig, "mt-05-heterocedasticidad", EVIDENCIAS)
    plt.close(fig)

    def cociente(panel: pd.DataFrame) -> float:
        retorno = cierre(panel, "LTC").pct_change().dropna()
        return float(retorno.iloc[110:190].std() / retorno.iloc[10:90].std())

    medido["heterocedasticidad_construida"] = {
        "cociente_sin_regimenes": round(cociente(sin_reg), 2),
        "cociente_con_regimenes": round(cociente(con_reg), 2),
    }


def figura_06_autocorrelacion(ltc: pd.Series) -> None:
    """ACF en nivel y en retornos, con banda de confianza al 95 %."""
    acf_nivel = autocorrelacion(ltc, rezagos=40)
    acf_ret = autocorrelacion(ltc.pct_change().dropna(), rezagos=40)

    fig, (izq, der) = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    for eje, datos, titulo in (
        (izq, acf_nivel, "Precio en nivel"),
        (der, acf_ret, "Retornos"),
    ):
        banda_sup = datos["superior"] - datos["acf"]
        banda_inf = datos["inferior"] - datos["acf"]
        eje.bar(datos["rezago"], datos["acf"], color=estilo.NAVY, width=0.7)
        eje.fill_between(datos["rezago"], banda_inf, banda_sup,
                         color=estilo.ACENTO, alpha=0.18)
        eje.set_title(titulo)
        eje.set_xlabel("Rezago")
    izq.set_ylabel("Autocorrelacion")
    fig.suptitle("Autocorrelacion de LTC", color=estilo.NAVY, fontweight="bold")
    estilo.guardar(fig, "mt-06-autocorrelacion", EVIDENCIAS)
    plt.close(fig)

    significativos = acf_ret[
        (acf_ret["rezago"] > 0)
        & (acf_ret["acf"].abs() > (acf_ret["superior"] - acf_ret["acf"]).abs())
    ]
    medido["autocorrelacion"] = {
        "acf_nivel_rezago_1": round(float(acf_nivel["acf"].iloc[1]), 4),
        "acf_retornos_rezago_1": round(float(acf_ret["acf"].iloc[1]), 4),
        "rezagos_significativos_en_retornos": [int(r) for r in significativos["rezago"]][:12],
        "cuantos_significativos": int(len(significativos)),
    }


def figura_07_correlacion(panel: pd.DataFrame) -> None:
    """Correlacion real, y el contraste construido entre baja y alta."""
    real = matriz_correlacion(panel, en_retornos=True)
    espuria = matriz_correlacion(panel, en_retornos=False)
    real.to_csv(EVIDENCIAS / "mt-07-correlacion-retornos.csv")

    baja = panel_correlacionado(n=2000, correlacion=0.1, semilla=1)
    alta = panel_correlacionado(n=2000, correlacion=0.9, semilla=1)

    fig, ejes = plt.subplots(1, 3, figsize=(12, 3.6))
    for eje, matriz, titulo in (
        (ejes[0], matriz_correlacion(baja), "Construida: correlacion baja"),
        (ejes[1], matriz_correlacion(alta), "Construida: correlacion alta"),
        (ejes[2], real, "Real: retornos"),
    ):
        imagen = eje.imshow(matriz.to_numpy(), cmap="Blues", vmin=0, vmax=1)
        eje.set_xticks(range(len(ACTIVOS)), list(ACTIVOS), fontsize=8, rotation=45)
        eje.set_yticks(range(len(ACTIVOS)), list(ACTIVOS), fontsize=8)
        eje.set_title(titulo, fontsize=10)
        eje.grid(False)
    fig.colorbar(imagen, ax=ejes, shrink=0.8)
    estilo.guardar(fig, "mt-07-correlacion", EVIDENCIAS)
    plt.close(fig)

    fila = real.loc["LTC"].drop("LTC")
    medido["correlacion"] = {
        "mayor_con_ltc": {"activo": fila.idxmax(), "valor": round(float(fila.max()), 4)},
        "menor_con_ltc": {"activo": fila.idxmin(), "valor": round(float(fila.min()), 4)},
        "media_fuera_diagonal_retornos": round(float(_correlaciones_cruzadas(panel).mean()), 4),
        "media_fuera_diagonal_en_nivel_espuria": round(
            float(espuria.to_numpy()[np.triu_indices(len(ACTIVOS), k=1)].mean()), 4
        ),
        "control_construido_baja": round(float(_correlaciones_cruzadas(baja).mean()), 4),
        "control_construido_alta": round(float(_correlaciones_cruzadas(alta).mean()), 4),
        # La correlacion en nivel no es uniformemente alta: es ERRATICA. Dice que LTC
        # casi no se relaciona con BTC y que si lo hace con ADA, y las dos cosas son
        # artefactos de comparar trayectorias en vez de co-movimientos.
        "inestabilidad_en_nivel": {
            "LTC_BTC_nivel": round(float(espuria.loc["LTC", "BTC"]), 4),
            "LTC_BTC_retornos": round(float(real.loc["LTC", "BTC"]), 4),
            "LTC_ADA_nivel": round(float(espuria.loc["LTC", "ADA"]), 4),
            "LTC_ADA_retornos": round(float(real.loc["LTC", "ADA"]), 4),
            "rango_nivel": [
                round(float(espuria.to_numpy()[np.triu_indices(len(ACTIVOS), k=1)].min()), 4),
                round(float(espuria.to_numpy()[np.triu_indices(len(ACTIVOS), k=1)].max()), 4),
            ],
            "rango_retornos": [
                round(float(_correlaciones_cruzadas(panel).min()), 4),
                round(float(_correlaciones_cruzadas(panel).max()), 4),
            ],
        },
    }


def figura_08_puntos_inflexion(ltc: pd.Series) -> None:
    """Que es un punto de inflexion, primero donde la verdad la pusimos nosotros."""
    sintetica, giros = serie_zigzag(n=200, w=VENTANA_W, semilla=3, ruido=0.0)
    etiquetas_sin = etiquetar(sintetica, VENTANA_W)
    fig = estilo.grafico_serie_con_giros(
        sintetica, etiquetas_sin,
        titulo=f"Construida: giros conocidos por construccion (w={VENTANA_W})",
    )
    estilo.guardar(fig, "mt-08a-giros-construidos", EVIDENCIAS)
    plt.close(fig)

    ventana = ltc.tail(250)
    etiquetas_real = etiquetar(ltc, VENTANA_W).reindex(ventana.index)
    fig = estilo.grafico_serie_con_giros(
        ventana, etiquetas_real, titulo=f"LTC real: giros detectados (w={VENTANA_W})"
    )
    estilo.guardar(fig, "mt-08b-giros-ltc", EVIDENCIAS)
    plt.close(fig)

    detectados = np.where(
        etiquetas_sin.to_numpy(na_value=Clase.CONTINUIDAD) != int(Clase.CONTINUIDAD)
    )[0]
    medido["puntos_inflexion"] = {
        "w": VENTANA_W,
        "construida_giros_puestos": int(len(giros)),
        "construida_giros_detectados": int(len(detectados)),
        "construida_deteccion_exacta": bool(set(detectados) == set(giros)),
    }


def figura_09_metricas(ltc: pd.Series) -> None:
    """Por que la exactitud no sirve: el baseline trivial, medido."""
    etiquetas = etiquetar(ltc, VENTANA_W)
    resumen = resumen_clases(etiquetas)

    fig = estilo.grafico_distribucion_clases(
        resumen, titulo=f"Balance de clases en LTC (w={VENTANA_W}, {GRANULARIDAD})"
    )
    estilo.guardar(fig, "mt-09a-balance-clases", EVIDENCIAS)
    plt.close(fig)

    modelo = BaselineTrivial()
    predichas = pd.Series(modelo.predecir(ltc.to_frame()), index=ltc.index)
    resultado = evaluar(etiquetas, predichas)
    confusion = matriz_confusion(etiquetas, predichas)

    fig = estilo.grafico_matriz_confusion(
        confusion, titulo="Baseline trivial: siempre responde Continuidad"
    )
    estilo.guardar(fig, "mt-09b-confusion-baseline", EVIDENCIAS)
    plt.close(fig)

    medido["metricas"] = {
        "balance": resumen.to_dict(orient="records"),
        "baseline_trivial": {k: (round(v, 4) if isinstance(v, float) else v)
                             for k, v in resultado.items()},
    }


def main() -> None:
    ruta = RAIZ / "data" / "processed" / f"panel_{GRANULARIDAD}_v1.parquet"
    if not ruta.exists():
        raise SystemExit(f"falta {ruta}. Correr antes: uv run python scripts/spike_datos.py")

    EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    # El documento entregable va en blanco y negro, y APA 7 desaconseja transmitir
    # informacion solo por color. Las figuras se distinguen por forma y trama.
    estilo.modo_impresion()
    estilo.aplicar()

    panel = pd.read_parquet(ruta)
    ltc = cierre(panel, "LTC")
    sintetico = panel_correlacionado(n=2000, semilla=0)

    print(f"panel: {len(panel)} filas, {GRANULARIDAD}, w={VENTANA_W}")
    for numero, (nombre, funcion) in enumerate(
        [
            ("serie temporal", lambda: figura_01_serie(ltc)),
            ("componentes", lambda: figura_02_componentes(ltc)),
            ("estacionariedad", lambda: figura_03_estacionariedad(panel, sintetico)),
            ("volatilidad", lambda: figura_04_volatilidad(ltc)),
            ("volatilidad construida", figura_04b_volatilidad_construida),
            ("heterocedasticidad", figura_05_heterocedasticidad),
            ("autocorrelacion", lambda: figura_06_autocorrelacion(ltc)),
            ("correlacion cruzada", lambda: figura_07_correlacion(panel)),
            ("puntos de inflexion", lambda: figura_08_puntos_inflexion(ltc)),
            ("metricas", lambda: figura_09_metricas(ltc)),
        ],
        start=1,
    ):
        funcion()
        print(f"  [{numero}/10] {nombre}")

    medido["_meta"] = {
        "generado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "granularidad": GRANULARIDAD,
        "w": VENTANA_W,
        "panel_filas": int(len(panel)),
        "advertencia": (
            "Las series descritas como 'construida' las genero este script. No son "
            "Litecoin y no dicen nada sobre el mercado."
        ),
    }
    destino = EVIDENCIAS / "marco-teorico.json"
    destino.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nnumeros medidos: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
