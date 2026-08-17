"""Sensibilidad del etiquetador al ruido. Modulo de Alejandro (M2), issue S1-M2-01.

La pregunta que responde este archivo es una sola:

    El etiquetador encuentra los giros perfectamente en una serie limpia.
    Con ruido, cuanto tolera antes de empezar a inventar giros que no existen?

Se puede responder porque en `serie_zigzag` los giros los ponemos nosotros: la
verdad de referencia no sale de `etiquetar()`, sale de los vertices con los que
se construyo la serie. Es la unica medicion del proyecto donde la respuesta
correcta no esta en discusion.

QUE NO ES ESTO. La serie es lineal a tramos con ruido gaussiano. No es Litecoin:
no tiene heterocedasticidad, ni colas pesadas, ni saltos. Los numeros de aqui
caracterizan al ETIQUETADOR, no al mercado, y asi hay que presentarlos.

Detalle que hace valida la comparacion: la serie limpia y la ruidosa de una misma
semilla comparten vertices y alturas, porque `serie_zigzag` suma el ruido despues
de construir los tramos y sobre el mismo generador. Por eso la verdad se toma de
la serie limpia y la deteccion de la ruidosa, y las dos hablan de la misma serie.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from contracts.labeling import Clase, etiquetar
from src.sintetico.generador import etiquetas_esperadas, serie_zigzag

NIVELES_RUIDO_POR_DEFECTO: tuple[float, ...] = (0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0)
SEMILLAS_POR_DEFECTO: tuple[int, ...] = tuple(range(10))

_EXTREMAS = (int(Clase.MAXIMO), int(Clase.MINIMO))


def _posiciones_extremas(etiquetas: pd.Series) -> dict[int, int]:
    """Mapa posicion -> clase, solo para Maximo y Minimo. Las posiciones son
    enteras (no fechas) porque la verdad de referencia son indices de vertice."""
    valores = etiquetas.to_numpy(dtype="float64", na_value=np.nan)
    return {
        int(i): int(valores[i])
        for i in np.flatnonzero(np.isin(valores, _EXTREMAS))
    }


def comparar_giros(
    verdaderos: dict[int, int],
    detectados: dict[int, int],
    tolerancia: int = 0,
) -> dict[str, int]:
    """Empareja giros detectados contra giros verdaderos y cuenta aciertos y errores.

    Con `tolerancia=0` se exige que el giro caiga en la vela exacta. Con
    `tolerancia=1` se acepta un desplazamiento de una vela hacia cualquier lado.
    Las dos lecturas hacen falta y dicen cosas distintas: la exacta mide si el
    etiquetado sirve como verdad de entrenamiento vela a vela, y la tolerante
    separa "perdio el giro" de "lo corrio un poco". Confundirlas seria reportar
    como fracaso lo que es un desplazamiento de una vela.

    El emparejamiento es codicioso y uno a uno: un giro detectado no puede
    justificar dos giros verdaderos. Sin esa restriccion, con tolerancia alta un
    solo acierto taparia varios fallos.

    Se exige ademas que coincida el TIPO. Confundir un maximo con un minimo no es
    una deteccion parcial, es el peor error posible en este problema: el sistema
    anunciaria comprar donde habia que vender.
    """
    if tolerancia < 0:
        raise ValueError(f"tolerancia debe ser >= 0, se recibio {tolerancia}")

    disponibles = dict(detectados)
    aciertos = 0
    invertidos = 0

    for posicion, clase in sorted(verdaderos.items()):
        candidatas = [
            p
            for d in range(tolerancia + 1)
            for p in ((posicion - d, posicion + d) if d else (posicion,))
            if p in disponibles
        ]
        emparejada = next((p for p in candidatas if disponibles[p] == clase), None)
        if emparejada is not None:
            aciertos += 1
            del disponibles[emparejada]
            continue
        # Hay un giro detectado en el lugar correcto pero del tipo contrario.
        if candidatas:
            invertidos += 1
            del disponibles[candidatas[0]]

    return {
        "verdaderos": len(verdaderos),
        "detectados": len(detectados),
        "aciertos": aciertos,
        "invertidos": invertidos,
        "falsos_positivos": len(disponibles),
        "no_detectados": len(verdaderos) - aciertos - invertidos,
    }


def _senal_por_vela(valores: np.ndarray) -> float:
    """Cambio tipico de precio entre dos velas consecutivas de la serie limpia.

    Existe porque un nivel de ruido en unidades absolutas no significa nada por si
    solo: sigma=0,5 es enorme en una serie que se mueve 0,2 por vela e
    irrelevante en una que se mueve 20. El cociente ruido/senal es lo que hace
    comparable esta medicion con cualquier otra serie, incluida LTC.
    """
    return float(np.median(np.abs(np.diff(valores))))


def medir_sensibilidad(
    niveles_ruido: Sequence[float] = NIVELES_RUIDO_POR_DEFECTO,
    semillas: Sequence[int] = SEMILLAS_POR_DEFECTO,
    n: int = 800,
    w: int = 7,
    amplitud: float = 12.0,
    tolerancia: int = 1,
) -> pd.DataFrame:
    """Barrido de niveles de ruido. Una fila por (nivel, semilla).

    Se promedia sobre varias semillas porque una sola serie no distingue el efecto
    del ruido del azar de esa serie concreta. Con una semilla, el punto de quiebre
    que se reporte seria una anecdota.

    Devuelve columnas crudas (conteos), no solo tasas, para que quien lea la tabla
    pueda recalcular cualquier razon sin volver a correr el barrido.
    """
    filas = []
    for ruido in niveles_ruido:
        for semilla in semillas:
            limpia, giros = serie_zigzag(n=n, w=w, semilla=semilla, amplitud=amplitud, ruido=0.0)
            ruidosa, giros_ruidosa = serie_zigzag(
                n=n, w=w, semilla=semilla, amplitud=amplitud, ruido=ruido
            )
            if not np.array_equal(giros, giros_ruidosa):
                raise AssertionError(
                    "la serie limpia y la ruidosa de la misma semilla no comparten vertices: "
                    "la verdad de referencia no seria comparable con la deteccion"
                )

            verdad = etiquetas_esperadas(n, giros, limpia.to_numpy(), w)
            deteccion = etiquetar(ruidosa, w)

            conteos = comparar_giros(
                _posiciones_extremas(verdad),
                _posiciones_extremas(deteccion),
                tolerancia=tolerancia,
            )
            exactos = comparar_giros(
                _posiciones_extremas(verdad),
                _posiciones_extremas(deteccion),
                tolerancia=0,
            )

            senal = _senal_por_vela(limpia.to_numpy())
            filas.append(
                {
                    "ruido": ruido,
                    "semilla": semilla,
                    "senal_por_vela": senal,
                    "ruido_relativo": ruido / senal if senal else float("nan"),
                    **conteos,
                    "aciertos_exactos": exactos["aciertos"],
                }
            )

    tabla = pd.DataFrame(filas)
    tabla["recall"] = tabla["aciertos"] / tabla["verdaderos"]
    tabla["recall_exacto"] = tabla["aciertos_exactos"] / tabla["verdaderos"]
    tabla["precision"] = np.where(
        tabla["detectados"] > 0, tabla["aciertos"] / tabla["detectados"], np.nan
    )
    tabla["falsos_por_giro_verdadero"] = tabla["falsos_positivos"] / tabla["verdaderos"]
    return tabla


def resumir(tabla: pd.DataFrame) -> pd.DataFrame:
    """Promedia el barrido por nivel de ruido. Es la tabla que va al documento."""
    agregado = (
        tabla.groupby("ruido")
        .agg(
            semillas=("semilla", "nunique"),
            ruido_relativo=("ruido_relativo", "mean"),
            giros_verdaderos=("verdaderos", "sum"),
            giros_detectados=("detectados", "sum"),
            aciertos=("aciertos", "sum"),
            aciertos_exactos=("aciertos_exactos", "sum"),
            invertidos=("invertidos", "sum"),
            falsos_positivos=("falsos_positivos", "sum"),
            recall=("recall", "mean"),
            recall_exacto=("recall_exacto", "mean"),
            precision=("precision", "mean"),
            falsos_por_giro_verdadero=("falsos_por_giro_verdadero", "mean"),
        )
        .reset_index()
    )
    return agregado.round(4)


def punto_de_quiebre(resumen: pd.DataFrame, caida_recall: float = 0.05) -> dict:
    """Primer nivel de ruido donde el recall cae mas de `caida_recall` respecto del
    caso limpio, o donde aparece el primer falso positivo.

    El criterio se fija aqui, en codigo, y no se elige mirando la tabla. Elegirlo
    despues de ver los resultados seria justificar el numero que ya queriamos.

    Devuelve NaN en un umbral si el barrido no llego a cruzarlo: no medimos mas
    alla del ruido maximo probado y decir un valor seria inventarlo.
    """
    if resumen.empty:
        raise ValueError("el resumen esta vacio")

    base = float(resumen.iloc[0]["recall"])
    degradado = resumen[resumen["recall"] < base - caida_recall]
    con_falsos = resumen[resumen["falsos_positivos"] > 0]

    return {
        "recall_sin_ruido": base,
        "criterio_caida_recall": caida_recall,
        "ruido_donde_cae_el_recall": (
            float(degradado.iloc[0]["ruido"]) if len(degradado) else float("nan")
        ),
        "ruido_relativo_donde_cae_el_recall": (
            float(degradado.iloc[0]["ruido_relativo"]) if len(degradado) else float("nan")
        ),
        "ruido_del_primer_falso_positivo": (
            float(con_falsos.iloc[0]["ruido"]) if len(con_falsos) else float("nan")
        ),
        "ruido_relativo_del_primer_falso_positivo": (
            float(con_falsos.iloc[0]["ruido_relativo"]) if len(con_falsos) else float("nan")
        ),
        "ruido_maximo_probado": float(resumen["ruido"].max()),
    }


# ---------------------------------------------------------------------------
# Figuras y evidencia. Todo lo de abajo produce archivos en docs/evidencias/ y
# existe para que ningun numero del informe dependa de una sesion de notebook.
# ---------------------------------------------------------------------------

NIVELES_FINOS: tuple[float, ...] = (0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.25, 1.5)


def figura_curvas(resumen: pd.DataFrame, resumen_fino: pd.DataFrame | None = None):
    """Recall y falsos positivos contra ruido relativo.

    El eje x es el ruido RELATIVO a la senal por vela y no el sigma absoluto: en
    unidades absolutas la curva solo valdria para esta amplitud concreta.
    """
    import matplotlib.pyplot as plt

    from src.visual import estilo

    fig, (izq, der) = plt.subplots(1, 2, figsize=(11, 4.2))

    izq.plot(
        resumen["ruido_relativo"], resumen["recall"],
        marker="o", color=estilo.NAVY, label="Deteccion con tolerancia de 1 vela",
    )
    izq.plot(
        resumen["ruido_relativo"], resumen["recall_exacto"],
        marker="s", linestyle="--", color=estilo.ACENTO, label="Deteccion en la vela exacta",
    )
    izq.set_xlabel("Ruido relativo  (sigma / cambio tipico por vela)")
    izq.set_ylabel("Fraccion de giros verdaderos recuperados")
    izq.set_title("Cuantos giros verdaderos sobreviven")
    izq.set_ylim(0, 1.05)
    izq.legend(loc="lower left", fontsize=9)

    der.plot(
        resumen["ruido_relativo"], resumen["falsos_por_giro_verdadero"],
        marker="o", color=estilo.MAXIMO, label="Barrido principal",
    )
    if resumen_fino is not None and len(resumen_fino):
        der.plot(
            resumen_fino["ruido_relativo"], resumen_fino["falsos_por_giro_verdadero"],
            marker=".", linestyle=":", color=estilo.GRIS, label="Barrido fino",
        )
        der.legend(loc="upper left", fontsize=9)
    der.set_xlabel("Ruido relativo  (sigma / cambio tipico por vela)")
    der.set_ylabel("Giros falsos por giro verdadero")
    der.set_title("Cuantos giros inventa")

    fig.suptitle(
        "Sensibilidad del etiquetador al ruido — serie construida, no es Litecoin",
        color=estilo.NAVY, fontweight="bold",
    )
    fig.tight_layout()
    return fig


def figura_series_ejemplo(niveles=(0.0, 0.7, 4.0), n: int = 220, w: int = 7, semilla: int = 0):
    """Un tramo de la misma serie a tres niveles de ruido, con los giros verdaderos
    y los detectados superpuestos.

    La tabla dice cuanto se degrada; esta figura dice como se ve la degradacion,
    que es lo que hace entendible el resultado en el documento.

    Los tres niveles no se eligieron mirando el dibujo: son el caso limpio, el
    punto de quiebre que salio del barrido, y el ruido maximo probado. Los
    conteos del titulo son de ESTE tramo y ESTA semilla, no del barrido; para
    citar en el informe valen los promedios de `resumir()`, que van sobre diez
    semillas. Un conteo de una sola serie es una anecdota.
    """
    import matplotlib.pyplot as plt

    from src.visual import estilo

    fig, ejes = plt.subplots(len(niveles), 1, figsize=(9.5, 2.5 * len(niveles)), sharex=True)
    limpia, giros = serie_zigzag(n=n, w=w, semilla=semilla, ruido=0.0)
    verdad = etiquetas_esperadas(n, giros, limpia.to_numpy(), w)
    posiciones_verdad = _posiciones_extremas(verdad)

    for eje, ruido in zip(ejes, niveles, strict=True):
        serie, _ = serie_zigzag(n=n, w=w, semilla=semilla, ruido=ruido)
        deteccion = _posiciones_extremas(etiquetar(serie, w))
        conteos = comparar_giros(posiciones_verdad, deteccion, tolerancia=1)

        eje.plot(range(n), serie.to_numpy(), color=estilo.NAVY, linewidth=1.1)
        eje.scatter(
            list(posiciones_verdad), [serie.iloc[i] for i in posiciones_verdad],
            color=estilo.MINIMO, marker="o", s=46, zorder=3, label="Giro verdadero (lo pusimos)",
        )
        eje.scatter(
            list(deteccion), [serie.iloc[i] for i in deteccion],
            facecolors="none", edgecolors=estilo.MAXIMO, marker="o",
            s=130, linewidths=1.3, zorder=4, label="Giro detectado",
        )
        titulo = (
            f"sigma = {ruido}   ·   "
            f"{conteos['aciertos']}/{conteos['verdaderos']} recuperados   ·   "
            f"{conteos['falsos_positivos']} falsos"
        )
        eje.set_title(titulo, fontsize=10)
        eje.set_ylabel("Precio")

    ejes[0].legend(loc="lower center", bbox_to_anchor=(0.5, 1.30), ncols=2, fontsize=9)
    ejes[-1].set_xlabel("Vela")
    fig.tight_layout()
    return fig


def generar_evidencia(directorio=None) -> dict:
    """Corre el barrido completo y deja tabla, figuras y JSON en docs/evidencias/.

    Punto de entrada reproducible:  uv run python -m src.sintetico.sensibilidad
    """
    from datetime import UTC, datetime

    from src.visual import estilo

    estilo.aplicar()
    destino = directorio or estilo.DIRECTORIO_EVIDENCIAS
    destino.mkdir(parents=True, exist_ok=True)

    crudo = medir_sensibilidad()
    resumen = resumir(crudo)
    crudo_fino = medir_sensibilidad(niveles_ruido=NIVELES_FINOS)
    resumen_fino = resumir(crudo_fino)

    resumen.to_csv(destino / "m2-ruido-etiquetado.csv", index=False)
    resumen_fino.to_csv(destino / "m2-ruido-etiquetado-fino.csv", index=False)

    estilo.guardar(figura_curvas(resumen, resumen_fino), "m2-ruido-curvas", destino)
    estilo.guardar(figura_series_ejemplo(), "m2-ruido-series", destino)

    quiebre = punto_de_quiebre(resumen)
    quiebre_fino = punto_de_quiebre(resumen_fino)

    evidencia = {
        "parametros": {
            "n": 800,
            "w": 7,
            "amplitud": 12.0,
            "semillas": list(SEMILLAS_POR_DEFECTO),
            "tolerancia_velas": 1,
            "niveles_ruido": list(NIVELES_RUIDO_POR_DEFECTO),
            "niveles_ruido_finos": list(NIVELES_FINOS),
        },
        "resumen": resumen.to_dict(orient="records"),
        "resumen_fino": resumen_fino.to_dict(orient="records"),
        "punto_de_quiebre": quiebre,
        "punto_de_quiebre_fino": quiebre_fino,
        "_meta": {
            "generado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "issue": "S1-M2-01",
            "advertencia": (
                "Serie lineal a tramos con ruido gaussiano, construida por nosotros. "
                "No es Litecoin. Estos numeros caracterizan al etiquetador, no al mercado."
            ),
        },
    }

    import json

    (destino / "m2-ruido-etiquetado.json").write_text(
        json.dumps(evidencia, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    return evidencia


if __name__ == "__main__":
    resultado = generar_evidencia()
    print(pd.DataFrame(resultado["resumen"]).to_string(index=False))
    print()
    print(resultado["punto_de_quiebre"])
