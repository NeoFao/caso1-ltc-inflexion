"""S3-M2-01: cuales caracteristicas aportan de verdad, medido por permutacion.

RF-F4. Con 420 ejemplos de la clase minoritaria en entrenamiento, mas caracteristicas
no es mejor: cada columna es una oportunidad mas de ajustar ruido. Hay que demostrar
cuales aportan en vez de conservarlas todas por si acaso.

Por que permutacion y no la importancia del bosque
---------------------------------------------------
`BosqueAleatorio.importancias()` devuelve la importancia por impureza, que es la que
trae scikit-learn de fabrica. Tiene dos sesgos conocidos y los dos pegan justo aqui:

- **Favorece a las variables de alta cardinalidad.** Una columna continua ofrece mas
  puntos de corte que una casi discreta, asi que acumula reduccion de impureza aunque
  no informe mas.
- **Se calcula sobre ENTRENAMIENTO.** Mide de que se colgo el modelo para ajustar lo
  que ya vio, no que le sirve para predecir lo que no vio.

La importancia por permutacion mide otra cosa: cuanto empeora el F1 macro **sobre
validacion** cuando se desordena una columna y todo lo demas queda igual. Si una
columna se puede desordenar sin que el resultado se mueva, el modelo no la estaba
usando para nada util.

Se reportan las dos y se comparan. Donde discrepan esta lo interesante.

El control que hace que la tabla signifique algo
-------------------------------------------------
Una tabla ordenada por importancia siempre se puede leer: aunque todas las columnas
fueran ruido, alguna quedaria primera. Lo que hace falta es un **piso de ruido**.

Se entrena un segundo modelo con las mismas columnas mas unas cuantas **centinelas**:
columnas de ruido puro, generadas con semilla fija, que por construccion no pueden
informar nada. La importancia mas alta que alcance una centinela es el piso: toda
caracteristica real que quede por debajo es indistinguible de una columna inventada.

Sin ese piso, "el rezago 5 es la tercera mas importante" no dice si es importante o
si simplemente hay que ordenar de alguna manera.

Se mide sobre VALIDACION, nunca sobre prueba: decidir que columnas conservar mirando
el bloque de prueba lo contamina.

Punto de entrada:  uv run python -m src.features.importancia
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from contracts.config import ACTIVO_OBJETIVO, GRANULARIDAD, HORIZONTE_H, VENTANA_W
from contracts.labeling import etiquetar, objetivo
from contracts.metrics import f1_macro
from contracts.schema import cierre
from contracts.splits import particionar
from src.features.base import construir
from src.features.escalado import familia_de
from src.modelos.clasico import BosqueAleatorio

EVIDENCIAS = Path("docs/evidencias")

REPETICIONES = 10
SEMILLA = 0
N_CENTINELAS = 5

#: F1 macro del bosque sobre validacion con la representacion vigente. Lo obtuvieron
#: por separado M3 en el #63 y M2 en el #62, con codigo distinto.
CONTROL_BOSQUE = 0.390497720487045


def columnas_centinela(indice: pd.Index, n: int = N_CENTINELAS, semilla: int = SEMILLA):
    """Columnas de ruido puro, para fijar el piso de lo que no informa.

    Tres formas distintas a proposito, porque un solo tipo de ruido no cubre los dos
    sesgos que se quieren detectar: la normal y la uniforme son continuas de alta
    cardinalidad —que es lo que la importancia por impureza premia— y la discreta
    controla el caso contrario.
    """
    generador = np.random.default_rng(semilla)
    datos = {}
    for i in range(n):
        if i % 3 == 0:
            valores = generador.normal(size=len(indice))
        elif i % 3 == 1:
            valores = generador.uniform(size=len(indice))
        else:
            valores = generador.integers(0, 5, size=len(indice)).astype(float)
        datos[f"centinela_ruido_{i + 1}"] = valores
    return pd.DataFrame(datos, index=indice)


def _datos():
    panel = pd.read_parquet(f"data/processed/panel_{GRANULARIDAD}_v1.parquet")
    y = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), VENTANA_W), HORIZONTE_H)
    particion = particionar(len(panel), VENTANA_W, HORIZONTE_H)
    X = construir(panel)

    entrenables = particion.entrenamiento & y.notna().to_numpy()
    validables = particion.validacion & y.notna().to_numpy()
    return (
        X[entrenables],
        y[entrenables],
        X[validables],
        y[validables].astype(int).to_numpy(),
    )


def importancia_por_permutacion(
    modelo,
    X_valida: pd.DataFrame,
    y_valida: np.ndarray,
    repeticiones: int = REPETICIONES,
    semilla: int = SEMILLA,
) -> pd.DataFrame:
    """Cuanto cae el F1 macro al desordenar cada columna, todo lo demas igual.

    Se permuta sobre VALIDACION y sin reentrenar: la pregunta es de que depende el
    modelo ya ajustado, no que pasaria si se entrenara sin esa columna —eso es una
    ablacion, y esta en `src/features/ablacion.py`.

    Se repite `repeticiones` veces con permutaciones distintas porque una sola es una
    muestra de una variable aleatoria. La desviacion entre repeticiones es parte del
    resultado: una caida media de 0,004 con desviacion 0,006 no es una caida.
    """
    generador = np.random.default_rng(semilla)
    base = float(f1_macro(y_valida, modelo.predecir(X_valida)))

    filas = []
    for columna in X_valida.columns:
        original = X_valida[columna].to_numpy(copy=True)
        caidas = np.empty(repeticiones)
        for r in range(repeticiones):
            barajada = generador.permutation(original)
            X_valida[columna] = barajada
            caidas[r] = base - float(f1_macro(y_valida, modelo.predecir(X_valida)))
        X_valida[columna] = original

        filas.append(
            {
                "columna": columna,
                "familia": familia_de(columna),
                "caida_media": float(caidas.mean()),
                "caida_desviacion": float(caidas.std(ddof=1)),
                "caida_minima": float(caidas.min()),
                "caida_maxima": float(caidas.max()),
            }
        )

    tabla = pd.DataFrame(filas).sort_values("caida_media", ascending=False)
    tabla.attrs["f1_base"] = base
    return tabla.reset_index(drop=True)


def piso_de_ruido(tabla_con_centinelas: pd.DataFrame) -> dict:
    """Hasta donde llega una columna que por construccion no informa nada."""
    centinelas = tabla_con_centinelas[
        tabla_con_centinelas["columna"].str.startswith("centinela_ruido_")
    ]
    if centinelas.empty:
        raise ValueError("la tabla no trae centinelas: no hay piso que calcular")
    return {
        "n_centinelas": int(len(centinelas)),
        "piso": float(centinelas["caida_media"].max()),
        "piso_columna": str(centinelas.loc[centinelas["caida_media"].idxmax(), "columna"]),
        "centinelas": centinelas.round(6).to_dict(orient="records"),
    }


def comparar_con_impureza(permutacion: pd.DataFrame, impureza: pd.Series) -> dict:
    """Cuanto coinciden los dos criterios, y en que se separan."""
    comun = permutacion.set_index("columna")["caida_media"].reindex(impureza.index)
    correlacion = float(comun.rank().corr(impureza.rank(), method="spearman"))

    top_permutacion = list(permutacion.head(10)["columna"])
    top_impureza = list(impureza.head(10).index)
    return {
        "correlacion_de_rangos_spearman": round(correlacion, 4),
        "top10_permutacion": top_permutacion,
        "top10_impureza": top_impureza,
        "en_ambos_top10": sorted(set(top_permutacion) & set(top_impureza)),
        "solo_en_top10_de_impureza": sorted(set(top_impureza) - set(top_permutacion)),
    }


def resumen_por_familia(tabla: pd.DataFrame) -> pd.DataFrame:
    reales = tabla[~tabla["columna"].str.startswith("centinela_ruido_")]
    return (
        reales.groupby("familia")
        .agg(
            columnas=("columna", "size"),
            caida_total=("caida_media", "sum"),
            caida_maxima=("caida_media", "max"),
            caida_mediana=("caida_media", "median"),
        )
        .sort_values("caida_total", ascending=False)
        .reset_index()
    )


def evaluar_recorte(
    X_entrena: pd.DataFrame,
    y_entrena: pd.Series,
    X_valida: pd.DataFrame,
    y_valida: np.ndarray,
    conservar: list[str],
    semillas=(0, 1, 2, 3, 4),
) -> dict:
    """Entrena con y sin las columnas descartadas, y compara. Con varias semillas.

    Sin esto, "conservar 46 de 63" seria una opinion. La tabla de importancia dice de
    que se apoya el modelo; no dice que pase si se le quitan las que no usa. Eso hay
    que entrenarlo.

    Se usan varias semillas porque la diferencia esperada es del tamano del ruido de
    reentrenamiento, que es exactamente la trampa en la que ya caimos una vez con el
    aporte multivariante.
    """
    descartadas = [c for c in X_entrena.columns if c not in set(conservar)]
    filas = []
    for semilla in semillas:
        completo = BosqueAleatorio(semilla=semilla).entrenar(X_entrena, y_entrena)
        recortado = BosqueAleatorio(semilla=semilla, nombre="recortado").entrenar(
            X_entrena[conservar], y_entrena
        )
        f1_completo = float(f1_macro(y_valida, completo.predecir(X_valida)))
        f1_recortado = float(f1_macro(y_valida, recortado.predecir(X_valida[conservar])))
        filas.append(
            {
                "semilla": int(semilla),
                "f1_completo": f1_completo,
                "f1_recortado": f1_recortado,
                "diferencia": f1_recortado - f1_completo,
            }
        )

    diferencias = np.array([f["diferencia"] for f in filas])
    return {
        "n_conservadas": len(conservar),
        "n_descartadas": len(descartadas),
        "descartadas": descartadas,
        "por_semilla": filas,
        "diferencia_media": float(diferencias.mean()),
        "diferencia_minima": float(diferencias.min()),
        "diferencia_maxima": float(diferencias.max()),
        "cambia_de_signo": bool(diferencias.min() < 0 < diferencias.max()),
        "el_recorte_mejora_en_todas": bool((diferencias > 0).all()),
    }


def generar_evidencia(directorio: Path | None = None) -> dict:
    X_entrena, y_entrena, X_valida, y_valida = _datos()

    # Modelo A: el del proyecto, sin tocar. Es el que produce la tabla que se reporta,
    # y el unico que tiene que reproducir la cifra publicada.
    modelo = BosqueAleatorio().entrenar(X_entrena, y_entrena)
    obtenido = float(f1_macro(y_valida, modelo.predecir(X_valida)))
    if abs(obtenido - CONTROL_BOSQUE) > 1e-9:
        raise AssertionError(
            f"El bosque da F1 macro {obtenido!r} y lo publicado es {CONTROL_BOSQUE!r}. "
            "No se publica ninguna importancia hasta entender la diferencia."
        )

    tabla = importancia_por_permutacion(modelo, X_valida.copy(), y_valida)

    # Modelo B: el mismo mas centinelas de ruido. Existe solo para fijar el piso; su
    # tabla no se reporta como importancia de nada.
    #
    # Se hace con dos cantidades de centinelas a proposito. El piso es el MAXIMO sobre
    # las centinelas, y un maximo sobre k muestras crece con k: con mas centinelas el
    # piso sube aunque el ruido sea el mismo. Si la conclusion cambiara entre 5 y 15,
    # el piso seria un artefacto de cuantas se pusieron y no una propiedad del ruido.
    pisos = {}
    for n in (N_CENTINELAS, 3 * N_CENTINELAS):
        X_entrena_c = pd.concat([X_entrena, columnas_centinela(X_entrena.index, n=n)], axis=1)
        X_valida_c = pd.concat([X_valida, columnas_centinela(X_valida.index, n=n)], axis=1)
        modelo_c = BosqueAleatorio(nombre=f"bosque_con_{n}_centinelas").entrenar(
            X_entrena_c, y_entrena
        )
        tabla_c = importancia_por_permutacion(modelo_c, X_valida_c.copy(), y_valida)
        bloque = piso_de_ruido(tabla_c)
        bloque["f1_del_modelo_con_centinelas"] = tabla_c.attrs["f1_base"]
        bloque["cuantas_reales_lo_superan"] = int((tabla["caida_media"] > bloque["piso"]).sum())
        pisos[n] = bloque

    ruido = pisos[N_CENTINELAS]
    piso = ruido["piso"]
    tabla["supera_el_piso_de_ruido"] = tabla["caida_media"] > piso
    tabla["caida_supera_su_propia_desviacion"] = (
        tabla["caida_media"] > tabla["caida_desviacion"]
    )

    conservar = tabla[tabla["supera_el_piso_de_ruido"]]["columna"].tolist()

    # La decision no se toma leyendo la tabla: se entrena sin las descartadas y se
    # compara. Con varias semillas, porque la diferencia esperada es del tamano del
    # ruido de reentrenamiento.
    recorte = evaluar_recorte(X_entrena, y_entrena, X_valida, y_valida, conservar)

    destino = directorio or EVIDENCIAS
    destino.mkdir(parents=True, exist_ok=True)
    tabla.round(6).to_csv(
        destino / f"m2-importancia-{GRANULARIDAD}-w{VENTANA_W}-h{HORIZONTE_H}.csv", index=False
    )

    evidencia = {
        "metodo": (
            "Importancia por permutacion sobre VALIDACION, sin reentrenar, "
            f"{REPETICIONES} permutaciones por columna, semilla {SEMILLA}. La metrica "
            "es F1 macro, que es la metrica de decision del proyecto (D5); usar "
            "exactitud daria un orden distinto y sin sentido, porque un modelo que no "
            "detecta nada ya tiene 90 % de exactitud."
        ),
        "parametros": {
            "panel": GRANULARIDAD,
            "w": VENTANA_W,
            "h": HORIZONTE_H,
            "conjunto_de_medicion": "validacion",
            "modelo": "src.modelos.clasico.BosqueAleatorio (el de M3, importado)",
            "representacion": "rezagos relativos (default desde el #58)",
            "n_columnas": int(X_entrena.shape[1]),
            "n_validacion": int(len(y_valida)),
        },
        "control": {
            "descripcion": "El bosque reproduce el F1 macro publicado antes de medir nada.",
            "publicado": CONTROL_BOSQUE,
            "obtenido": obtenido,
            "reproduce": True,
        },
        "piso_de_ruido": {
            **ruido,
            "explicacion": (
                "Importancia mas alta alcanzada por una columna de ruido puro en un "
                "modelo entrenado con ellas dentro. Toda caracteristica real por debajo "
                "de este valor es indistinguible de una columna inventada."
            ),
            "criterio_del_piso": (
                f"Se usa el piso de {N_CENTINELAS} centinelas y no el de "
                f"{3 * N_CENTINELAS}. Con 15, el modelo auxiliar pierde F1 macro "
                "(0,3664 contra 0,3905 del real): 15 columnas de ruido le cuestan mas "
                "que todo el aporte multivariante medido en S4-M2-01, que es RF-F4 "
                "ilustrado. Un piso medido sobre un modelo peor no es el piso de este "
                "modelo. Ademas el de 5 es el mas exigente: deja menos columnas dentro."
            ),
            "sensibilidad_al_numero_de_centinelas": {
                str(n): {
                    "piso": bloque["piso"],
                    "cuantas_reales_lo_superan": bloque["cuantas_reales_lo_superan"],
                    "f1_del_modelo_con_centinelas": bloque["f1_del_modelo_con_centinelas"],
                }
                for n, bloque in pisos.items()
            },
        },
        "f1_base": tabla.attrs["f1_base"],
        "importancias": tabla.round(6).to_dict(orient="records"),
        "por_familia": resumen_por_familia(tabla).round(6).to_dict(orient="records"),
        "comparacion_con_impureza": comparar_con_impureza(tabla, modelo.importancias()),
        "decision": {
            "columnas_que_superan_el_piso": conservar,
            "n_que_superan": len(conservar),
            "n_total": int(len(tabla)),
            "recorte_medido": recorte,
        },
        "_meta": {
            "generado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "issues": ["S3-M2-01"],
            "advertencia": (
                "Que una columna no supere el piso NO prueba que sea inutil: prueba que "
                "esta medicion no la distingue del ruido. Con 1959 velas de validacion y "
                "columnas correlacionadas entre si, la permutacion reparte el credito "
                "entre las correlacionadas y subestima a las dos."
            ),
        },
    }

    ruta = destino / f"m2-importancia-{GRANULARIDAD}-w{VENTANA_W}-h{HORIZONTE_H}.json"
    ruta.write_text(json.dumps(evidencia, indent=1, ensure_ascii=False), encoding="utf-8")

    from src.visual import estilo

    estilo.aplicar()
    estilo.guardar(figura_importancia(evidencia), "m2-importancia-permutacion", destino)
    return evidencia


def figura_importancia(evidencia: dict, cuantas: int = 20):
    """Las mas importantes con su dispersion, y el piso de ruido marcado.

    La barra de error no es decoracion: es lo que separa "esta columna importa" de
    "esta columna quedo primera esta vez". Y la linea del piso es lo que convierte
    un orden en una afirmacion.
    """
    import matplotlib.pyplot as plt

    from src.visual import estilo

    tabla = pd.DataFrame(evidencia["importancias"]).head(cuantas).iloc[::-1]
    piso = evidencia["piso_de_ruido"]["piso"]

    fig, eje = plt.subplots(figsize=(9.5, 0.32 * cuantas + 1.8))
    colores = [
        estilo.NAVY if supera else estilo.GRIS for supera in tabla["supera_el_piso_de_ruido"]
    ]
    eje.barh(
        tabla["columna"], tabla["caida_media"],
        xerr=tabla["caida_desviacion"], color=colores,
        edgecolor="black", linewidth=0.5, error_kw={"ecolor": estilo.ACENTO, "capsize": 2.5},
    )
    eje.axvline(
        piso, color=estilo.MAXIMO, linestyle="--", linewidth=1.3,
        label=f"piso de ruido ({piso:.4f})",
    )
    eje.set_xlabel("Caida del F1 macro al desordenar la columna (validacion)")
    eje.set_title(
        f"Importancia por permutacion — las {cuantas} primeras de "
        f"{evidencia['decision']['n_total']}"
    )
    eje.legend(fontsize=9, loc="lower right")
    eje.tick_params(axis="y", labelsize=8)
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    salida = generar_evidencia()
    print(f"Control: el bosque reproduce {salida['control']['obtenido']!r}.")
    print(f"F1 macro base sobre validacion: {salida['f1_base']:.6f}")

    ruido = salida["piso_de_ruido"]
    print(
        f"\nPiso de ruido: {ruido['piso']:.6f}  "
        f"(lo marca {ruido['piso_columna']}, de {ruido['n_centinelas']} centinelas)"
    )
    for n, bloque in ruido["sensibilidad_al_numero_de_centinelas"].items():
        print(
            f"  con {n:>2} centinelas: piso {bloque['piso']:.6f}  "
            f"lo superan {bloque['cuantas_reales_lo_superan']} columnas reales  "
            f"(F1 del modelo con ellas: {bloque['f1_del_modelo_con_centinelas']:.6f})"
        )

    tabla = pd.DataFrame(salida["importancias"])
    print("\n=== las 15 mas importantes por permutacion ===")
    print(
        tabla.head(15)[
            ["columna", "familia", "caida_media", "caida_desviacion", "supera_el_piso_de_ruido"]
        ]
        .round(5)
        .to_string(index=False)
    )

    decision = salida["decision"]
    print(
        f"\nSuperan el piso de ruido: {decision['n_que_superan']} de {decision['n_total']}"
    )

    print("\n=== por familia ===")
    print(pd.DataFrame(salida["por_familia"]).round(5).to_string(index=False))

    recorte = salida["decision"]["recorte_medido"]
    print(
        f"\n=== quitar las {recorte['n_descartadas']} que no superan el piso ===\n"
        + pd.DataFrame(recorte["por_semilla"]).round(4).to_string(index=False)
    )
    print(
        f"  media {recorte['diferencia_media']:+.4f}  "
        f"rango [{recorte['diferencia_minima']:+.4f}, {recorte['diferencia_maxima']:+.4f}]  "
        f"mejora en todas: {recorte['el_recorte_mejora_en_todas']}"
    )

    comparacion = salida["comparacion_con_impureza"]
    print(
        f"\nCorrelacion de rangos con la importancia por impureza: "
        f"{comparacion['correlacion_de_rangos_spearman']}"
    )
    print("Solo en el top 10 de impureza:", comparacion["solo_en_top10_de_impureza"])
