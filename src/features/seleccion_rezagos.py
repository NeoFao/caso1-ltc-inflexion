"""Eleccion medida de los ordenes de rezago. Modulo de Alejandro (M2), issue S1-M2-04.

El andamiaje traia `ordenes=(1, 2, 3, 5)` elegidos sin ninguna medicion detras. Este
archivo mide cuales aportan y cuales son ruido, para que la eleccion tenga un numero
en vez de una convencion.

Dos preguntas distintas, porque los seis activos no juegan el mismo papel:

1. **LTC contra si mismo.** Autocorrelacion de sus retornos. Un rezago aporta si su
   ACF cae fuera de la banda de confianza; los de adentro son indistinguibles de
   cero y meterlos como columna solo agrega sobreajuste.

2. **Los cinco de apoyo contra LTC.** Aqui la autocorrelacion no sirve: la pregunta
   es si el retorno de BTC de hace k velas informa sobre el retorno de LTC de hoy.
   Eso es correlacion cruzada rezagada, y es la que justifica —o no— que el
   enunciado pida los precios rezagados de las cinco criptomonedas.

Si las correlaciones cruzadas rezagadas dieran cerca de cero, ese es un resultado
publicable y no un fracaso: significaria que el mercado cripto incorpora la
informacion dentro de la misma vela, y que lo que importa es la correlacion
contemporanea. Se reporta igual.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from contracts.config import ACTIVO_OBJETIVO, ACTIVOS
from contracts.schema import cierre

# 1,96 sigma. La banda de una correlacion muestral con n observaciones y verdadera
# correlacion cero es aproximadamente +-1,96/raiz(n).
Z_95 = 1.959964


def autocorrelacion_retornos(panel: pd.DataFrame, activo: str = ACTIVO_OBJETIVO,
                             rezagos: int = 20) -> pd.DataFrame:
    """ACF de los retornos con su banda al 95 %, y el veredicto por rezago.

    Se usa la funcion de M1 (`src/diagnostico/pruebas.py`) y no una propia: si cada
    modulo implementara su ACF, dos secciones del informe podrian reportar numeros
    distintos para lo mismo.
    """
    from src.diagnostico.pruebas import autocorrelacion

    retorno = cierre(panel, activo).pct_change()
    tabla = autocorrelacion(retorno, rezagos=rezagos)
    tabla = tabla[tabla["rezago"] > 0].copy()
    # statsmodels devuelve el intervalo centrado en la ACF estimada; para decidir
    # significancia hace falta saber si el cero queda dentro.
    tabla["significativo"] = ~((tabla["inferior"] <= 0) & (tabla["superior"] >= 0))
    tabla["activo"] = activo
    return tabla.reset_index(drop=True)


def correlacion_cruzada_rezagada(panel: pd.DataFrame, objetivo: str = ACTIVO_OBJETIVO,
                                 rezagos_max: int = 10) -> pd.DataFrame:
    """corr(retorno_objetivo_t, retorno_apoyo_{t-k}) para cada activo de apoyo y cada k.

    Incluye k = 0 —la correlacion contemporanea— a proposito, aunque no sea usable
    como caracteristica: es la referencia contra la que hay que leer las demas. Sin
    ella, un 0,05 en k = 1 parece poco o mucho segun el animo del lector; al lado de
    un 0,72 contemporaneo se interpreta solo.
    """
    retorno_objetivo = cierre(panel, objetivo).pct_change()
    filas = []
    for activo in ACTIVOS:
        if activo == objetivo:
            continue
        retorno_apoyo = cierre(panel, activo).pct_change()
        for k in range(0, rezagos_max + 1):
            par = pd.concat([retorno_objetivo, retorno_apoyo.shift(k)], axis=1).dropna()
            n = len(par)
            correlacion = float(par.iloc[:, 0].corr(par.iloc[:, 1])) if n > 2 else float("nan")
            banda = Z_95 / np.sqrt(n) if n > 2 else float("nan")
            filas.append(
                {
                    "activo": activo,
                    "rezago": k,
                    "n": n,
                    "correlacion": correlacion,
                    "banda_95": banda,
                    "significativo": bool(abs(correlacion) > banda) if n > 2 else False,
                }
            )
    return pd.DataFrame(filas)


def ordenes_recomendados(acf: pd.DataFrame, cruzada: pd.DataFrame,
                         maximo_ordenes: int = 4) -> dict:
    """Traduce las dos mediciones en la tupla de ordenes que va a `rezagos()`.

    El criterio se escribe aqui, antes de mirar las tablas:

    - Un rezago entra si es significativo en la ACF de LTC, o si lo es en la
      correlacion cruzada de al menos DOS activos de apoyo. Se exigen dos y no uno
      porque probando 5 activos x 10 rezagos, unos pocos cruces de la banda al 95 %
      son lo esperable por azar.
    - El rezago 1 entra siempre, sea significativo o no: es el precio de la vela
      anterior, la entrada mas literal del enunciado, y quitarlo dejaria al modelo
      sin la informacion mas basica disponible.
    - Se cortan en `maximo_ordenes` porque cada orden multiplica por seis el numero
      de columnas —van los seis activos— y la clase minoritaria tiene 420 ejemplos
      en entrenamiento. Mas columnas que evidencia es sobreajuste garantizado.
    """
    significativos_acf = set(acf.loc[acf["significativo"], "rezago"].astype(int))

    votos = (
        cruzada[(cruzada["rezago"] > 0) & cruzada["significativo"]]
        .groupby("rezago")["activo"]
        .nunique()
    )
    significativos_cruzada = set(votos[votos >= 2].index.astype(int))

    candidatos = sorted(significativos_acf | significativos_cruzada | {1})
    return {
        "significativos_acf_ltc": sorted(significativos_acf),
        "significativos_cruzada_2_o_mas_activos": sorted(significativos_cruzada),
        "candidatos": candidatos,
        "ordenes": tuple(candidatos[:maximo_ordenes]),
        "criterio": (
            "significativo en la ACF de LTC, o en la correlacion cruzada de >= 2 activos "
            f"de apoyo; el rezago 1 entra siempre; corte en {maximo_ordenes} ordenes"
        ),
    }


def medir(panel: pd.DataFrame, etiqueta_panel: str, rezagos: int = 20) -> dict:
    """Las dos mediciones y la recomendacion, para un panel."""
    acf = autocorrelacion_retornos(panel, rezagos=rezagos)
    cruzada = correlacion_cruzada_rezagada(panel, rezagos_max=min(rezagos, 10))
    return {
        "panel": etiqueta_panel,
        "n_filas": int(len(panel)),
        "acf_ltc": acf.round(6).to_dict(orient="records"),
        "correlacion_cruzada": cruzada.round(6).to_dict(orient="records"),
        "recomendacion": ordenes_recomendados(acf, cruzada),
    }


def figura_rezagos(acf: pd.DataFrame, cruzada: pd.DataFrame, titulo: str = ""):
    """ACF de LTC y correlacion cruzada rezagada, con sus bandas."""
    import matplotlib.pyplot as plt

    from src.visual import estilo

    fig, (izq, der) = plt.subplots(1, 2, figsize=(11.5, 4.2))

    izq.fill_between(
        acf["rezago"],
        acf["inferior"] - acf["acf"],
        acf["superior"] - acf["acf"],
        color=estilo.ACENTO, alpha=0.18, label="Banda al 95 %", zorder=1,
    )
    izq.bar(acf["rezago"], acf["acf"], color=estilo.NAVY, width=0.6, zorder=3)
    izq.axhline(0, color=estilo.GRIS, linewidth=0.8)
    izq.set_xlabel("Rezago (velas)")
    izq.set_ylabel("Autocorrelacion")
    izq.set_title("Retornos de LTC contra si mismos")
    izq.legend(fontsize=9)

    contemporanea = cruzada[cruzada["rezago"] == 0]
    rezagada = cruzada[cruzada["rezago"] > 0]
    for activo, grupo in rezagada.groupby("activo"):
        der.plot(
            grupo["rezago"], grupo["correlacion"],
            marker="o", markersize=3.5,
            color=estilo.PALETA_ACTIVOS.get(activo, estilo.ACENTO), label=activo,
        )
    banda = float(rezagada["banda_95"].iloc[0])
    der.axhspan(-banda, banda, color=estilo.GRIS, alpha=0.15, label="Banda al 95 %")
    der.axhline(0, color=estilo.GRIS, linewidth=0.8)
    if len(contemporanea):
        media_contemporanea = float(contemporanea["correlacion"].mean())
        der.axhline(
            media_contemporanea, color=estilo.MAXIMO, linestyle="--", linewidth=1.2,
            label=f"Contemporanea, media = {media_contemporanea:.2f}",
        )
    der.set_xlabel("Rezago (velas)")
    der.set_ylabel("Correlacion con el retorno de LTC")
    der.set_title("Activos de apoyo rezagados contra LTC")
    der.legend(fontsize=8, ncols=2)

    if titulo:
        fig.suptitle(titulo, color=estilo.NAVY, fontweight="bold")
    fig.tight_layout()
    return fig


def generar_evidencia(directorio=None) -> dict:
    """Mide sobre los dos paneles y deja figuras, CSV y JSON en docs/evidencias/.

    Se miden los dos —1d y 4h— y no solo el del contrato porque `GRANULARIDAD`
    sigue marcada PROVISIONAL. Si el equipo congela 4 horas, la medicion ya esta
    hecha y no hay que rehacer el trabajo.

    Punto de entrada:  uv run python -m src.features.seleccion_rezagos
    """
    import json
    from datetime import UTC, datetime

    from src.visual import estilo

    estilo.aplicar()
    destino = directorio or estilo.DIRECTORIO_EVIDENCIAS
    destino.mkdir(parents=True, exist_ok=True)

    resultados = {}
    for granularidad in ("1d", "4h"):
        panel = pd.read_parquet(f"data/processed/panel_{granularidad}_v1.parquet")
        resultado = medir(panel, granularidad)
        resultados[granularidad] = resultado

        acf = pd.DataFrame(resultado["acf_ltc"])
        cruzada = pd.DataFrame(resultado["correlacion_cruzada"])
        acf.to_csv(destino / f"m2-rezagos-acf-{granularidad}.csv", index=False)
        cruzada.to_csv(destino / f"m2-rezagos-cruzada-{granularidad}.csv", index=False)
        estilo.guardar(
            figura_rezagos(acf, cruzada, f"Seleccion de rezagos — panel de {granularidad}"),
            f"m2-rezagos-{granularidad}",
            destino,
        )

    evidencia = {
        "resultados": resultados,
        "_meta": {
            "generado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "issue": "S1-M2-04",
            "nota": (
                "La banda al 95 % es aproximada (+-1,96/raiz(n)) y supone independencia. "
                "Con retornos financieros esa suposicion no es exacta, asi que un cruce "
                "apenas por encima de la banda no es evidencia fuerte."
            ),
        },
    }
    (destino / "m2-rezagos.json").write_text(
        json.dumps(evidencia, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    return evidencia


if __name__ == "__main__":
    salida = generar_evidencia()
    for granularidad, resultado in salida["resultados"].items():
        print(f"===== panel {granularidad} ({resultado['n_filas']} filas) =====")
        acf = pd.DataFrame(resultado["acf_ltc"])
        print("ACF de LTC, rezagos significativos:")
        print(acf[acf["significativo"]][["rezago", "acf", "inferior", "superior"]]
              .to_string(index=False) or "  ninguno")
        cruzada = pd.DataFrame(resultado["correlacion_cruzada"])
        print("\nCorrelacion cruzada, contemporanea (k=0):")
        print(cruzada[cruzada["rezago"] == 0][["activo", "correlacion"]].to_string(index=False))
        print("\nCorrelacion cruzada rezagada significativa (k>=1):")
        significativas = cruzada[(cruzada["rezago"] > 0) & cruzada["significativo"]]
        print(significativas[["activo", "rezago", "correlacion", "banda_95"]].to_string(index=False)
              if len(significativas) else "  ninguna")
        print("\nRecomendacion:", resultado["recomendacion"])
        print()
