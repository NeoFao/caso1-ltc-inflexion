"""Las tres tablas de la seccion de metricas, medidas con el contrato vigente.

La seccion `docs/entregas/semana-1/m2-metricas.md` trae tres tablas —balance de
clases, baseline trivial sobre la serie completa, y los tres baselines sobre el
bloque de prueba— medidas con `1d`, `w = 5` y `h = 3`, que era el contrato cuando
se redacto. El contrato quedo congelado despues en `4h`, `w = 7` y `h = 1`.

Este modulo vuelve a medir las mismas tres tablas con cualquier terna de
parametros. NO reescribe la evidencia de la Semana 1: la D11 dice que la evidencia
de una entrega hecha es historia, no una vista del contrato vigente. Lo que produce
es un archivo nuevo, y en que documento se citan esas cifras es una decision que no
toma este modulo.

El control es la parte importante
---------------------------------
La regla 2 del proyecto dice que todo numero nuevo tiene que reproducir uno
conocido antes de publicarse. Aqui eso es literal: antes de medir nada nuevo,
`verificar_control()` corre el mismo procedimiento con `1d`, `w = 5`, `h = 3` y
comprueba que reproduce, cifra por cifra, lo que ya esta publicado en
`marco-teorico.json` y `m2-baselines.json`.

Si el control falla, `generar_evidencia()` se detiene y no escribe nada. Un
procedimiento que no reproduce lo conocido no tiene por que acertar en lo nuevo, y
la unica forma de enterarse es comprobarlo. Los cinco errores de la Semana 2 los
atrapo un control, ninguno una relectura.

Punto de entrada:  uv run python -m src.features.tablas_metricas
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from contracts.config import ACTIVO_OBJETIVO
from contracts.labeling import Clase, cota_superior_extremos, etiquetar, objetivo
from contracts.metrics import evaluar, matriz_confusion
from contracts.schema import cierre
from contracts.splits import particionar
from src.modelos.base import BaselineAleatorio, BaselineMayoritario, BaselineTrivial

EVIDENCIAS = Path("docs/evidencias")

#: Valores publicados en la Semana 1. El control tiene que reproducirlos exactos.
#: Estan escritos aqui a proposito y no leidos de los JSON: si se leyeran, un JSON
#: corrupto haria pasar el control comparandose consigo mismo.
CONTROL_SEMANA_1 = {
    "parametros": {"intervalo": "1d", "w": 5, "h": 3},
    "balance": {"Maximo": 143, "Minimo": 141, "Continuidad": 1891},
    "porcentajes": {"Maximo": 6.575, "Minimo": 6.483, "Continuidad": 86.943},
    "trivial_serie_completa": {"n": 2175, "f1_macro": 0.3101, "exactitud": 0.8694},
    "prueba": {
        "n": 320,
        "baseline_trivial": {"f1_macro": 0.3075, "exactitud": 0.8563},
        "baseline_mayoritario": {"f1_macro": 0.3075, "exactitud": 0.8563},
        "baseline_aleatorio": {"f1_macro": 0.3202, "exactitud": 0.7156},
    },
}


def _panel(intervalo: str) -> pd.DataFrame:
    return pd.read_parquet(f"data/processed/panel_{intervalo}_v1.parquet")


def tabla_balance(panel: pd.DataFrame, w: int) -> pd.DataFrame:
    """Tabla 1: cuantas velas de cada clase hay en toda la serie.

    Se mide sobre las etiquetas sin desplazar por `h`: la tabla describe la serie,
    no el problema de pronostico. Las `w` velas de cada extremo no tienen etiqueta
    porque les falta vecindario, y quedan fuera del total.
    """
    etiquetas = etiquetar(cierre(panel, ACTIVO_OBJETIVO), w)
    validas = etiquetas.dropna().astype(int)
    filas = [
        {
            "clase": clase.name.capitalize(),
            "codigo": int(clase),
            "n": int((validas == int(clase)).sum()),
            "porcentaje": round(100 * float((validas == int(clase)).mean()), 3),
        }
        for clase in Clase
    ]
    tabla = pd.DataFrame(filas)
    tabla.attrs["n_etiquetadas"] = int(len(validas))
    tabla.attrs["n_serie"] = int(len(panel))
    tabla.attrs["cota_superior_extremos_pct"] = round(100 * cota_superior_extremos(w), 3)
    return tabla


def medir_trivial_serie_completa(panel: pd.DataFrame, w: int) -> dict:
    """Tabla 2: el baseline trivial sobre la serie completa.

    Es el numero que sostiene el argumento entero de la seccion: un modelo que no
    detecta ni un solo punto de inflexion obtiene una exactitud alta. No hace falta
    particion porque el trivial no aprende nada; medirlo sobre la serie entera es
    lo que hace la cifra comparable con la Tabla 1.
    """
    etiquetas = etiquetar(cierre(panel, ACTIVO_OBJETIVO), w)
    validas = etiquetas.notna()
    reales = etiquetas[validas].astype(int)
    predicciones = np.full(len(reales), int(Clase.CONTINUIDAD), dtype=int)
    resultado = evaluar(reales, predicciones)
    resultado["n"] = int(len(reales))
    return resultado


def medir_baselines_en_prueba(panel: pd.DataFrame, w: int, h: int) -> dict:
    """Tabla 3: los tres baselines sobre el bloque de prueba.

    Aqui si hace falta la particion, porque el mayoritario y el aleatorio aprenden
    del entrenamiento —cual es la clase dominante y en que proporcion aparece cada
    una— y medirlos donde aprendieron no diria nada.

    Medir baselines sobre prueba no gasta el bloque: ninguno de los tres se elige
    ni se ajusta mirando el resultado, que es lo que contaminaria la reserva. Los
    modelos que si se eligen se comparan sobre validacion.
    """
    serie = cierre(panel, ACTIVO_OBJETIVO)
    etiquetas = etiquetar(serie, w)
    y = objetivo(etiquetas, h)
    X = pd.DataFrame(index=panel.index)  # los baselines no miran caracteristicas

    particion = particionar(len(panel), w, h)
    con_etiqueta = y.notna().to_numpy()
    entrenables = particion.entrenamiento & con_etiqueta
    evaluables = particion.prueba & con_etiqueta

    resultados = []
    matrices = {}
    for modelo in (BaselineTrivial(), BaselineMayoritario(), BaselineAleatorio()):
        modelo.entrenar(X[entrenables], y[entrenables])
        predicciones = modelo.predecir(X[evaluables])
        reales = y[evaluables].astype(int)
        fila = evaluar(reales, predicciones)
        fila["modelo"] = modelo.nombre
        fila["n"] = int(evaluables.sum())
        resultados.append(fila)
        matrices[modelo.nombre] = matriz_confusion(reales, predicciones).to_dict()

    balance_prueba = [
        {
            "clase": clase.name.capitalize(),
            "codigo": int(clase),
            "n": int((y[evaluables] == int(clase)).sum()),
            "porcentaje": round(100 * float((y[evaluables] == int(clase)).mean()), 3),
        }
        for clase in Clase
    ]

    return {
        "n_prueba_con_etiqueta": int(evaluables.sum()),
        "n_prueba_bruto": int(particion.prueba.sum()),
        "balance_bloque_prueba": balance_prueba,
        "baselines": resultados,
        "matrices_confusion": matrices,
        "particion": [
            {
                "conjunto": nombre,
                "n": int(mascara.sum()),
                "desde": str(panel.index[mascara][0]),
                "hasta": str(panel.index[mascara][-1]),
            }
            for nombre, mascara in (
                ("entrenamiento", particion.entrenamiento),
                ("validacion", particion.validacion),
                ("prueba", particion.prueba),
            )
        ],
    }


def medir(intervalo: str, w: int, h: int) -> dict:
    """Las tres tablas para una terna de parametros."""
    panel = _panel(intervalo)
    balance = tabla_balance(panel, w)
    return {
        "parametros": {"intervalo": intervalo, "w": w, "h": h},
        "serie": {
            "n": int(len(panel)),
            "n_etiquetadas": balance.attrs["n_etiquetadas"],
            "desde": str(panel.index[0]),
            "hasta": str(panel.index[-1]),
        },
        "tabla_1_balance": {
            "filas": balance.to_dict(orient="records"),
            "cota_superior_extremos_pct": balance.attrs["cota_superior_extremos_pct"],
        },
        "tabla_2_trivial_serie_completa": medir_trivial_serie_completa(panel, w),
        "tabla_3_baselines_en_prueba": medir_baselines_en_prueba(panel, w, h),
    }


def verificar_control(tolerancia: float = 5e-4) -> dict:
    """Reproduce las cifras publicadas de la Semana 1. Levanta si no coinciden.

    No compara contra los JSON del repositorio sino contra los valores copiados a
    mano de las tablas del documento entregado: lo que interesa es que este codigo
    reproduzca lo que se entrego, y un JSON que se hubiera regenerado por accidente
    haria pasar el control comparandose consigo mismo.
    """
    esperado = CONTROL_SEMANA_1
    obtenido = medir(**esperado["parametros"])
    diferencias = []

    def comparar(ruta: str, valor, referencia, tol=tolerancia):
        if abs(float(valor) - float(referencia)) > tol:
            diferencias.append(f"{ruta}: obtenido {valor}, publicado {referencia}")

    for fila in obtenido["tabla_1_balance"]["filas"]:
        comparar(f"balance/{fila['clase']}/n", fila["n"], esperado["balance"][fila["clase"]], 0)
        comparar(
            f"balance/{fila['clase']}/pct",
            fila["porcentaje"],
            esperado["porcentajes"][fila["clase"]],
            1e-3,
        )

    trivial = obtenido["tabla_2_trivial_serie_completa"]
    for clave, referencia in esperado["trivial_serie_completa"].items():
        tol = 0 if clave == "n" else tolerancia
        comparar(f"trivial_serie_completa/{clave}", trivial[clave], referencia, tol)

    prueba = obtenido["tabla_3_baselines_en_prueba"]
    comparar("prueba/n", prueba["n_prueba_con_etiqueta"], esperado["prueba"]["n"], 0)
    for fila in prueba["baselines"]:
        referencia = esperado["prueba"][fila["modelo"]]
        for clave, valor in referencia.items():
            comparar(f"prueba/{fila['modelo']}/{clave}", fila[clave], valor)

    if diferencias:
        raise AssertionError(
            "El control no reproduce las cifras publicadas de la Semana 1. No se "
            "publica nada hasta entenderlo:\n  - " + "\n  - ".join(diferencias)
        )
    return obtenido


def generar_evidencia(directorio: Path | None = None) -> dict:
    """Corre el control y, solo si pasa, mide con el contrato vigente."""
    from contracts.config import GRANULARIDAD, HORIZONTE_H, VENTANA_W

    destino = directorio or EVIDENCIAS
    destino.mkdir(parents=True, exist_ok=True)

    control = verificar_control()
    vigente = medir(GRANULARIDAD, VENTANA_W, HORIZONTE_H)

    evidencia = {
        "vigente": vigente,
        "control_semana_1": {
            "proposito": (
                "Reproduce con este mismo codigo las cifras publicadas en la Semana 1 "
                "(1d, w = 5, h = 3). Si no coincidieran, generar_evidencia() se detiene "
                "antes de escribir nada."
            ),
            "reproduce_lo_publicado": True,
            "tabla_1_balance": control["tabla_1_balance"],
            "tabla_2_trivial_serie_completa": control["tabla_2_trivial_serie_completa"],
            "tabla_3_baselines_en_prueba": {
                "n_prueba_con_etiqueta": control["tabla_3_baselines_en_prueba"][
                    "n_prueba_con_etiqueta"
                ],
                "baselines": control["tabla_3_baselines_en_prueba"]["baselines"],
            },
        },
        "_meta": {
            "generado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "advertencia": (
                "Estas cifras NO reemplazan las de docs/entregas/semana-1/. La D11 dice "
                "que la evidencia de una entrega hecha es historia. Donde se citan estos "
                "numeros es una decision del equipo, no de este modulo."
            ),
        },
    }

    ruta = destino / f"m2-tablas-metricas-{GRANULARIDAD}-w{VENTANA_W}-h{HORIZONTE_H}.json"
    ruta.write_text(json.dumps(evidencia, indent=1, ensure_ascii=False), encoding="utf-8")
    return evidencia


def _imprimir(bloque: dict) -> None:
    parametros = bloque["parametros"]
    print(f"\n===== {parametros['intervalo']}, w = {parametros['w']}, h = {parametros['h']} =====")
    print("\nTabla 1 — balance de clases")
    print(pd.DataFrame(bloque["tabla_1_balance"]["filas"]).to_string(index=False))
    cota = bloque["tabla_1_balance"]["cota_superior_extremos_pct"]
    print(f"cota superior por clase extrema: {cota} %")

    trivial = bloque["tabla_2_trivial_serie_completa"]
    print("\nTabla 2 — baseline trivial sobre la serie completa")
    print(
        f"n = {trivial['n']}   exactitud = {trivial['exactitud']:.4f}   "
        f"F1 macro = {trivial['f1_macro']:.4f}   PD = {trivial['precision_direccional']:.4f}"
    )

    prueba = bloque["tabla_3_baselines_en_prueba"]
    print(f"\nTabla 3 — los tres baselines sobre prueba (n = {prueba['n_prueba_con_etiqueta']})")
    columnas = ["modelo", "n", "exactitud", "f1_macro", "precision_direccional"]
    print(pd.DataFrame(prueba["baselines"])[columnas].round(4).to_string(index=False))


if __name__ == "__main__":
    salida = generar_evidencia()
    print("Control contra la Semana 1 (1d, w = 5, h = 3): reproduce lo publicado.")
    _imprimir(salida["vigente"])
