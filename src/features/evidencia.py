"""Figuras y mediciones de las caracteristicas. Modulo de Alejandro (M2).

Cubre el criterio de aceptacion de S1-M2-02 —una figura que muestre un indicador
sobre el precio, para que se vea que esta bien calculado— y la medicion de
`posicion_rango` que pide S1-M2-03.

Nada de aqui entra al pipeline: son diagnosticos. Se separan de base.py para que
el modulo de caracteristicas no cargue matplotlib.

Punto de entrada:  uv run python -m src.features.evidencia
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from contracts.config import ACTIVO_OBJETIVO
from contracts.labeling import Clase, etiquetar
from contracts.schema import cierre
from src.features.base import bollinger, construir, medias_moviles, rsi, ventana_deslizante


def figura_indicadores(panel: pd.DataFrame, velas: int = 300, activo: str = ACTIVO_OBJETIVO):
    """Bandas de Bollinger y medias moviles sobre el precio, con el RSI debajo.

    Es la verificacion visual del criterio de aceptacion: las bandas tienen que
    envolver al precio y estrecharse en los tramos tranquilos, y el RSI tiene que
    acercarse a sus extremos donde el precio hace maximos y minimos. Si una de esas
    dos cosas no se ve, el indicador esta mal calculado por mas que las pruebas
    pasen.

    Las bandas se reconstruyen a partir de las columnas relativas que produce
    `bollinger()` a proposito: si se recalcularan aqui con otra formula, la figura
    podria verse bien mientras la caracteristica que consume el modelo esta mal.
    """
    import matplotlib.pyplot as plt

    from src.visual import estilo

    serie = cierre(panel, activo)
    bandas = bollinger(panel, activo)
    medias = medias_moviles(panel, activo)
    indice_fuerza = rsi(panel, activo)

    ventana = 20
    pctb = bandas[f"{activo}_bollinger_pctb_{ventana}"]
    ancho_rel = bandas[f"{activo}_bollinger_ancho_{ventana}"]
    media = serie.rolling(ventana).mean()
    ancho = ancho_rel * media
    inferior = serie - pctb * ancho
    superior = inferior + ancho

    corte = slice(-velas, None)
    eje_x = serie.index[corte]

    fig, (arriba, abajo) = plt.subplots(
        2, 1, figsize=(10.5, 6.4), sharex=True, height_ratios=[2.4, 1]
    )

    arriba.fill_between(
        eje_x, inferior.iloc[corte], superior.iloc[corte],
        color=estilo.ACENTO, alpha=0.16, label="Bandas de Bollinger (20, 2σ)",
    )
    arriba.plot(eje_x, serie.iloc[corte], color=estilo.NAVY, linewidth=1.3, label="Cierre")
    for nombre, estilo_linea in (("dist_sma_25", "--"), ("dist_ema_12", ":")):
        periodo = int(nombre.split("_")[-1])
        reconstruida = serie / (1 + medias[f"{activo}_{nombre}"])
        arriba.plot(
            eje_x, reconstruida.iloc[corte], linestyle=estilo_linea,
            color=estilo.GRIS, linewidth=1.1,
            label=f"{'SMA' if 'sma' in nombre else 'EMA'} {periodo}",
        )
    arriba.set_ylabel("Precio de cierre")
    arriba.set_title(f"{activo}: indicadores sobre el precio (ultimas {velas} velas)")
    arriba.legend(loc="upper left", fontsize=8, ncols=2)

    valores_rsi = indice_fuerza[f"{activo}_rsi_14"]
    abajo.plot(eje_x, valores_rsi.iloc[corte], color=estilo.NAVY, linewidth=1.2)
    abajo.axhline(70, color=estilo.MAXIMO, linestyle="--", linewidth=1.0, label="70")
    abajo.axhline(30, color=estilo.MINIMO, linestyle="--", linewidth=1.0, label="30")
    abajo.axhline(50, color=estilo.GRIS, linewidth=0.7)
    abajo.set_ylim(0, 100)
    abajo.set_ylabel("RSI (14)")
    abajo.legend(loc="upper left", fontsize=8, ncols=2)

    fig.autofmt_xdate(rotation=30, ha="right")
    fig.tight_layout()
    return fig


def medir_posicion_rango(panel: pd.DataFrame, w: int, ventanas=(7, 20)) -> pd.DataFrame:
    """Cuanto informa `posicion_rango` sobre la etiqueta, en numeros.

    La hipotesis de la guia es que un precio cerca del maximo de sus ultimas velas
    esta estructuralmente mas cerca de ser un maximo local. Es plausible, y por eso
    mismo hay que medirla en vez de afirmarla.

    Se reporta la tasa de cada clase dentro de tramos de `posicion_rango`, contra la
    tasa base de toda la serie. El cociente entre las dos —el levantamiento— es lo
    que dice si la caracteristica aporta: un levantamiento de 1 significa que saber
    la posicion no cambia nada.

    OJO con como se lee esto. Que `posicion_rango == 1` prediga bien la clase Maximo
    NO es fuga: el maximo de la ventana hacia atras usa solo informacion hasta t.
    Lo que si es —y hay que decirlo en el informe— es que la caracteristica contiene
    la mitad computable de la definicion de la etiqueta, asi que un levantamiento
    alto es lo esperable y no un descubrimiento sobre el mercado.
    """
    etiquetas = etiquetar(cierre(panel, ACTIVO_OBJETIVO), w)
    caracteristicas = ventana_deslizante(panel, ventanas=ventanas)

    tramos = [
        ("[0,00 – 0,25)", 0.0, 0.25),
        ("[0,25 – 0,75)", 0.25, 0.75),
        ("[0,75 – 1,00)", 0.75, 1.0),
        ("= 1,00 (maximo de la ventana)", 1.0, 1.0001),
    ]

    validas = etiquetas.notna()
    base = {
        clase: float((etiquetas[validas] == int(clase)).mean()) for clase in Clase
    }

    filas = []
    for v in ventanas:
        posicion = caracteristicas[f"{ACTIVO_OBJETIVO}_posicion_rango_{v}"]
        for nombre, desde, hasta in tramos:
            mascara = validas & (posicion >= desde) & (posicion < hasta)
            n = int(mascara.sum())
            fila = {"ventana": v, "tramo": nombre, "n": n}
            for clase in Clase:
                tasa = float((etiquetas[mascara] == int(clase)).mean()) if n else float("nan")
                nombre_clase = clase.name.lower()
                fila[f"tasa_{nombre_clase}"] = tasa
                fila[f"levantamiento_{nombre_clase}"] = (
                    tasa / base[clase] if base[clase] else float("nan")
                )
            filas.append(fila)

    tabla = pd.DataFrame(filas)
    tabla.attrs["tasas_base"] = {c.name.lower(): base[c] for c in Clase}
    return tabla


def figura_posicion_rango(tabla: pd.DataFrame, w: int, ventana: int = 7):
    """Tasa de cada clase por tramo de posicion dentro del rango."""
    import matplotlib.pyplot as plt

    from src.visual import estilo

    datos = tabla[tabla["ventana"] == ventana]
    x = np.arange(len(datos))
    ancho = 0.38

    fig, eje = plt.subplots(figsize=(9, 4.2))
    eje.bar(
        x - ancho / 2, 100 * datos["tasa_maximo"], ancho,
        color=estilo.MAXIMO, edgecolor="black", linewidth=0.6, hatch="//", label="Maximo",
    )
    eje.bar(
        x + ancho / 2, 100 * datos["tasa_minimo"], ancho,
        color=estilo.MINIMO, edgecolor="black", linewidth=0.6, hatch="\\\\", label="Minimo",
    )
    base = tabla.attrs["tasas_base"]
    eje.axhline(
        100 * base["maximo"], color=estilo.MAXIMO, linestyle="--", linewidth=1.1,
        label=f"Tasa base de Maximo ({100 * base['maximo']:.2f} %)",
    )
    eje.set_xticks(x, datos["tramo"], fontsize=8)
    eje.set_xlabel(f"Posicion del cierre dentro del rango de las ultimas {ventana} velas")
    eje.set_ylabel("% de velas de esa clase")
    eje.set_title(f"Que tanto informa la posicion dentro del rango (w = {w})")
    eje.legend(fontsize=9)
    fig.tight_layout()
    return fig


def generar_evidencia(directorio=None) -> dict:
    """Figuras y mediciones sobre el panel y la ventana que fija el contrato.

    Granularidad y w salen de `contracts/config.py`, que desde el commit d8f9b8a esta
    congelado en 4h y w = 7 (PROVISIONAL = False). No se repiten aqui como constantes
    propias: serian una segunda fuente de verdad, y la primera vez que el contrato
    cambie sin que alguien se acuerde de este archivo, los numeros dejarian de ser
    comparables sin que nadie lo note.

    Esta funcion medía antes dos veces lo mismo —"el panel de 4h con w = 7" y "los
    valores del contrato"— porque cuando se escribio el contrato decia 1d y w = 5 y
    los dos casos eran distintos. Al congelarse coincidieron, de modo que la
    distincion dejo de existir y la segunda medicion era la primera con otro nombre.
    """
    import json
    from datetime import UTC, datetime

    from contracts.config import GRANULARIDAD, VENTANA_W
    from src.visual import estilo

    estilo.aplicar()
    destino = directorio or estilo.DIRECTORIO_EVIDENCIAS
    destino.mkdir(parents=True, exist_ok=True)

    panel = pd.read_parquet(f"data/processed/panel_{GRANULARIDAD}_v1.parquet")

    estilo.guardar(figura_indicadores(panel), "m2-indicadores-sobre-precio", destino)

    tabla = medir_posicion_rango(panel, w=VENTANA_W)
    tabla.round(6).to_csv(
        destino / f"m2-posicion-rango-{GRANULARIDAD}-w{VENTANA_W}.csv", index=False
    )
    estilo.guardar(figura_posicion_rango(tabla, w=VENTANA_W), "m2-posicion-rango", destino)

    # Aqui la llamada sin argumento es deliberada: el trabajo de este bloque es
    # documentar QUE produce construir() por omision, asi que tiene que seguir al
    # default y no fijarlo. Lo que si hace falta es decir cual fue, porque si no el
    # JSON cambia de significado en silencio cuando el default cambie — que es
    # exactamente lo que le paso a m2-ablacion.json al entrar el #58.
    columnas = construir(panel)
    rezagos_en_nivel = [
        c for c in columnas.columns if "_rezago_" in c and "_rezago_rel_" not in c
    ]
    evidencia = {
        "parametros": {
            "panel": GRANULARIDAD,
            "w": VENTANA_W,
            "representacion": (
                "rezagos en nivel de precio" if rezagos_en_nivel else "rezagos relativos"
            ),
        },
        "caracteristicas": {
            "n_columnas": int(columnas.shape[1]),
            "columnas": list(columnas.columns),
            "filas_sin_ningun_nan": int(columnas.notna().all(axis=1).sum()),
            "filas_totales": int(len(columnas)),
        },
        "posicion_rango": {
            "tasas_base": tabla.attrs["tasas_base"],
            "tramos": tabla.round(6).to_dict(orient="records"),
        },
        "_meta": {
            "generado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "issues": ["S1-M2-02", "S1-M2-03"],
            "advertencia": (
                "El levantamiento alto de posicion_rango sobre la clase Maximo es "
                "esperable: la caracteristica contiene la mitad hacia atras de la "
                "definicion de la etiqueta. No es fuga y no es un hallazgo sobre el "
                "mercado."
            ),
        },
    }
    (destino / "m2-caracteristicas.json").write_text(
        json.dumps(evidencia, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    return evidencia


if __name__ == "__main__":
    salida = generar_evidencia()
    print("columnas de construir():", salida["caracteristicas"]["n_columnas"])
    print(
        "filas sin ningun NaN:",
        salida["caracteristicas"]["filas_sin_ningun_nan"],
        "de", salida["caracteristicas"]["filas_totales"],
    )
    bloque = salida["posicion_rango"]
    parametros = salida["parametros"]
    print(f"\n===== posicion_rango — panel {parametros['panel']}, w = {parametros['w']} =====")
    print("tasas base:", {k: round(v, 5) for k, v in bloque["tasas_base"].items()})
    print(
        pd.DataFrame(bloque["tramos"])[
            ["ventana", "tramo", "n", "tasa_maximo", "levantamiento_maximo",
             "tasa_minimo", "levantamiento_minimo"]
        ].round(4).to_string(index=False)
    )
