"""S4-M2-01: aportan los cinco activos de apoyo informacion sobre LTC?

El enunciado entero descansa en que BTC, ETH, SOL, XRP y ADA dicen algo sobre LTC.
Este modulo lo mide en vez de asumirlo, y esta escrito para poder responder que no.

Por que no alcanza con la ablacion que ya existe
------------------------------------------------
`src/features/ablacion.py` ya compara `completo` contra `solo_LTC`, pero lo hace con
un modelo de referencia lineal elegido para que las familias se comparen entre si en
igualdad de condiciones. Ese modelo, con caracteristicas estacionarias, **queda por
debajo de los tres baselines**: F1 macro 0,2550 contra 0,3161 del trivial. Una
diferencia medida sobre un modelo que no le gana al azar no dice si la informacion
esta ahi; dice que ese modelo no la usa.

Asi que la pregunta se vuelve a medir sobre el modelo que si funciona —el bosque de
M3, importado tal cual— y con el intervalo de la diferencia, no comparando dos
intervalos por separado.

Las dos representaciones, a proposito
-------------------------------------
Se mide dos veces: con los rezagos en nivel de precio y con los rezagos relativos.

No es redundante. Con rezagos en nivel, la ablacion lineal atribuia a los activos de
apoyo una caida de 0,1008 en F1 macro al quitarlos; con rezagos relativos la misma
medicion da 0,0082. La diferencia entre esas dos cifras no es informacion sobre el
mercado: los precios en nivel son no estacionarios y le sirven al modelo como
indicador de en que parte de la serie esta cada fila, no de que hace el precio.

Publicar solo la primera cifra seria publicar un artefacto. Publicar solo la segunda
seria esconder por que la primera existia. Van las dos.

Punto de entrada:  uv run python -m src.features.multivariante
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from contracts.config import (
    ACTIVO_OBJETIVO,
    ACTIVOS_APOYO,
    DELTA_F1_DECISIVO,
    GRANULARIDAD,
    HORIZONTE_H,
    VENTANA_W,
)
from contracts.labeling import etiquetar, objetivo
from contracts.metrics import evaluar, f1_macro
from contracts.schema import cierre
from contracts.splits import particionar
from src.features.ablacion import es_de_activo_de_apoyo
from src.features.base import construir
from src.features.incertidumbre import intervalo_diferencia, intervalo_metrica
from src.modelos.base import BaselineAleatorio, BaselineTrivial
from src.modelos.clasico import BosqueAleatorio

EVIDENCIAS = Path("docs/evidencias")

#: Fragmentos que identifican una columna que existe solo porque el problema es
#: multivariante. `BosqueAleatorio.excluir` trabaja por subcadena, asi que hay que
#: expresarlo asi; `_verificar_equivalencia_del_filtro` comprueba en cada corrida
#: que esta lista selecciona exactamente lo mismo que `es_de_activo_de_apoyo()`,
#: para que las dos definiciones no puedan separarse en silencio.
FRAGMENTOS_DE_APOYO: tuple[str, ...] = ("corr_", *(f"{activo}_" for activo in ACTIVOS_APOYO))

#: F1 macro del bosque de M3 sobre validacion, con rezagos en nivel, publicado en
#: docs/evidencias/modelo-clasico-4h-w7-h1.json. El control tiene que reproducirlo.
CONTROL_BOSQUE_M3 = 0.3443065490077563


def _verificar_equivalencia_del_filtro(columnas: pd.Index) -> None:
    por_fragmento = {c for c in columnas if any(f in c for f in FRAGMENTOS_DE_APOYO)}
    por_funcion = {c for c in columnas if es_de_activo_de_apoyo(c)}
    if por_fragmento != por_funcion:
        diferencia = por_fragmento.symmetric_difference(por_funcion)
        raise AssertionError(
            "FRAGMENTOS_DE_APOYO y es_de_activo_de_apoyo() ya no seleccionan lo mismo. "
            f"Difieren en: {sorted(diferencia)}. Arreglar antes de medir nada: si no, "
            "'solo_LTC' deja de significar lo que dice su nombre."
        )


def _datos(relativo: bool):
    panel = pd.read_parquet(f"data/processed/panel_{GRANULARIDAD}_v1.parquet")
    y = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), VENTANA_W), HORIZONTE_H)
    particion = particionar(len(panel), VENTANA_W, HORIZONTE_H)
    X = construir(panel, rezagos_relativos=relativo)
    _verificar_equivalencia_del_filtro(X.columns)

    # Mismo filtrado que el arnes de M0 y que el experimento de M3: solo se exige que
    # la etiqueta exista. Los nulos de X los resuelve el imputador del pipeline. Si
    # se filtrara tambien por X.notna(), las cifras dejarian de ser comparables con
    # las de M3 aunque el modelo fuera el mismo.
    entrenables = particion.entrenamiento & y.notna().to_numpy()
    validables = particion.validacion & y.notna().to_numpy()
    return (
        X[entrenables],
        y[entrenables],
        X[validables],
        y[validables].astype(int).to_numpy(),
        int(X.shape[1]),
    )


def medir(relativo: bool) -> dict:
    """Bosque con todo contra bosque solo con LTC, sobre validacion.

    Se mide sobre validacion y no sobre prueba: esta comparacion es una decision de
    representacion, y decidir mirando el bloque de prueba lo gastaria.
    """
    X_entrena, y_entrena, X_valida, y_valida, n_columnas = _datos(relativo)

    modelos = {
        "completo": BosqueAleatorio(),
        "solo_LTC": BosqueAleatorio(excluir=FRAGMENTOS_DE_APOYO, nombre="solo_LTC"),
        "baseline_trivial": BaselineTrivial(),
        "baseline_aleatorio": BaselineAleatorio(semilla=0),
    }

    predicciones: dict[str, np.ndarray] = {}
    metricas = {}
    for nombre, modelo in modelos.items():
        modelo.entrenar(X_entrena, y_entrena)
        predicciones[nombre] = np.asarray(modelo.predecir(X_valida), dtype=int)
        metricas[nombre] = evaluar(y_valida, predicciones[nombre])

    n_solo_ltc = sum(1 for c in X_entrena.columns if not es_de_activo_de_apoyo(c))

    diferencias = {
        "completo_vs_solo_LTC": intervalo_diferencia(
            y_valida, predicciones["completo"], predicciones["solo_LTC"]
        ),
        "completo_vs_baseline_aleatorio": intervalo_diferencia(
            y_valida, predicciones["completo"], predicciones["baseline_aleatorio"]
        ),
        "solo_LTC_vs_baseline_aleatorio": intervalo_diferencia(
            y_valida, predicciones["solo_LTC"], predicciones["baseline_aleatorio"]
        ),
    }

    return {
        "representacion": "rezagos relativos" if relativo else "rezagos en nivel de precio",
        "rezagos_relativos": relativo,
        "n_columnas": {"completo": n_columnas, "solo_LTC": n_solo_ltc},
        "n_validacion": int(len(y_valida)),
        "metricas": metricas,
        "intervalos_f1_macro": {
            nombre: intervalo_metrica(y_valida, pred, f1_macro)
            for nombre, pred in predicciones.items()
        },
        "diferencias": diferencias,
    }


def sensibilidad_a_la_semilla(relativo: bool, semillas=(0, 1, 2, 3, 4)) -> dict:
    """Cuanto se mueve la diferencia solo por cambiar la semilla del bosque.

    El intervalo por bootstrap acota la variabilidad del CONJUNTO DE EVALUACION:
    responde "si me hubieran tocado otras velas, cuanto cambiaria". No dice nada
    sobre la otra fuente de ruido, que es el ajuste del propio bosque: 300 arboles
    con otra semilla dan otro modelo.

    Si la diferencia entre `completo` y `solo_LTC` se mueve entre semillas tanto
    como su propio valor, entonces no hay efecto que reportar por mas estrecho que
    salga el intervalo. Es la comprobacion que separa un hallazgo de un accidente
    del generador de numeros aleatorios.
    """
    X_entrena, y_entrena, X_valida, y_valida, _ = _datos(relativo)

    filas = []
    for semilla in semillas:
        completo = BosqueAleatorio(semilla=semilla)
        solo_ltc = BosqueAleatorio(
            semilla=semilla, excluir=FRAGMENTOS_DE_APOYO, nombre="solo_LTC"
        )
        completo.entrenar(X_entrena, y_entrena)
        solo_ltc.entrenar(X_entrena, y_entrena)
        f1_completo = f1_macro(y_valida, completo.predecir(X_valida))
        f1_solo = f1_macro(y_valida, solo_ltc.predecir(X_valida))
        filas.append(
            {
                "semilla": int(semilla),
                "f1_completo": float(f1_completo),
                "f1_solo_LTC": float(f1_solo),
                "diferencia": float(f1_completo - f1_solo),
            }
        )

    diferencias = np.array([f["diferencia"] for f in filas])
    return {
        "por_semilla": filas,
        "diferencia_media": float(diferencias.mean()),
        "diferencia_minima": float(diferencias.min()),
        "diferencia_maxima": float(diferencias.max()),
        "desviacion": float(diferencias.std(ddof=1)),
        "cambia_de_signo": bool(diferencias.min() < 0 < diferencias.max()),
    }


def verificar_control(medicion_en_nivel: dict, tolerancia: float = 1e-9) -> None:
    """El bosque completo con rezagos en nivel tiene que dar el numero de M3.

    Es el mismo modelo, la misma particion y las mismas caracteristicas que corrio
    M3, asi que tiene que salir identico. Si no sale, algo cambio en el camino —el
    filtrado de filas, el orden de las columnas, la semilla— y ninguna otra cifra de
    este archivo es confiable.
    """
    obtenido = medicion_en_nivel["metricas"]["completo"]["f1_macro"]
    if abs(obtenido - CONTROL_BOSQUE_M3) > tolerancia:
        raise AssertionError(
            f"El bosque completo da F1 macro {obtenido!r} y M3 publico "
            f"{CONTROL_BOSQUE_M3!r} en modelo-clasico-{GRANULARIDAD}-w{VENTANA_W}-"
            f"h{HORIZONTE_H}.json. No se publica nada hasta entender la diferencia."
        )


def _veredicto(medicion: dict) -> dict:
    """Lo que se puede afirmar, y lo que no, a partir de una medicion."""
    diferencia = medicion["diferencias"]["completo_vs_solo_LTC"]
    completo_le_gana_al_azar = medicion["diferencias"]["completo_vs_baseline_aleatorio"][
        "excluye_el_cero"
    ]
    return {
        "aporte_medido": diferencia["diferencia"],
        "ic_95": [diferencia["ic_inferior"], diferencia["ic_superior"]],
        "excluye_el_cero": diferencia["excluye_el_cero"],
        "fraccion_a_favor": diferencia["fraccion_a_favor"],
        "supera_el_umbral_del_equipo": abs(diferencia["diferencia"]) >= DELTA_F1_DECISIVO,
        "el_modelo_completo_le_gana_al_azar": completo_le_gana_al_azar,
        "se_puede_afirmar_que_aporta": bool(
            diferencia["excluye_el_cero"] and diferencia["diferencia"] > 0
        ),
    }


def figura_aporte(evidencia: dict):
    """Las diferencias con su intervalo, y la misma diferencia por semilla.

    Las dos mitades responden preguntas distintas y por eso van juntas: la de arriba
    dice cuanto se movería el resultado con otras velas de evaluacion; la de abajo,
    cuanto se mueve solo por reentrenar el mismo bosque. Un efecto que no sobrevive
    a la segunda no existe, por estrecho que salga el intervalo de la primera.
    """
    import matplotlib.pyplot as plt

    from src.visual import estilo

    fig, (arriba, abajo) = plt.subplots(
        2, 1, figsize=(9.5, 5.8), height_ratios=[0.8, 1]
    )

    etiquetas, valores, inferiores, superiores, colores = [], [], [], [], []
    for clave, titulo in (
        ("con_rezagos_relativos", "rezagos relativos"),
        ("con_rezagos_en_nivel", "rezagos en nivel"),
    ):
        d = evidencia[clave]["diferencias"]["completo_vs_solo_LTC"]
        etiquetas.append(f"completo − solo LTC\n({titulo})")
        valores.append(d["diferencia"])
        inferiores.append(d["diferencia"] - d["ic_inferior"])
        superiores.append(d["ic_superior"] - d["diferencia"])
        colores.append(estilo.NAVY if d["excluye_el_cero"] else estilo.GRIS)

    y = np.arange(len(etiquetas))
    arriba.errorbar(
        valores, y, xerr=[inferiores, superiores], fmt="o", capsize=5,
        color=estilo.NAVY, ecolor=estilo.ACENTO, markersize=7, linewidth=1.6,
    )
    for i, color in enumerate(colores):
        arriba.plot(valores[i], y[i], "o", color=color, markersize=7)
    arriba.axvline(0, color=estilo.MAXIMO, linestyle="--", linewidth=1.2, label="sin aporte")
    arriba.axvline(
        DELTA_F1_DECISIVO, color=estilo.GRIS, linestyle=":", linewidth=1.1,
        label=f"umbral del equipo ({DELTA_F1_DECISIVO})",
    )
    arriba.set_yticks(y, etiquetas, fontsize=9)
    arriba.set_xlabel("Diferencia en F1 macro (IC 95 %, remuestreo pareado)")
    arriba.set_title("Aportan los cinco activos de apoyo? — bosque de M3, sobre validacion")
    arriba.legend(fontsize=8, loc="center right", framealpha=0.9)
    arriba.set_ylim(len(etiquetas) - 0.55, -0.55)

    sensibilidad = evidencia["sensibilidad_a_la_semilla"]["con_rezagos_relativos"]
    filas = pd.DataFrame(sensibilidad["por_semilla"])
    abajo.bar(
        filas["semilla"], filas["diferencia"],
        color=[estilo.MINIMO if v > 0 else estilo.MAXIMO for v in filas["diferencia"]],
        edgecolor="black", linewidth=0.6, width=0.55,
    )
    abajo.axhline(0, color="black", linewidth=1.0)
    abajo.axhline(
        sensibilidad["diferencia_media"], color=estilo.GRIS, linestyle="--", linewidth=1.1,
        label=f"media ({sensibilidad['diferencia_media']:+.4f})",
    )
    abajo.set_xticks(filas["semilla"])
    abajo.set_xlabel("Semilla del bosque (todo lo demas identico)")
    abajo.set_ylabel("Diferencia en F1 macro")
    abajo.set_title("La misma diferencia cambia de signo al reentrenar")
    abajo.legend(fontsize=8)

    fig.tight_layout()
    return fig


def generar_evidencia(directorio: Path | None = None) -> dict:
    en_nivel = medir(relativo=False)
    verificar_control(en_nivel)
    relativo = medir(relativo=True)

    destino = directorio or EVIDENCIAS
    destino.mkdir(parents=True, exist_ok=True)

    evidencia = {
        "pregunta": (
            "Aportan los cinco activos de apoyo informacion sobre LTC, medido sobre el "
            "modelo del proyecto y no sobre un modelo de referencia?"
        ),
        "parametros": {
            "panel": GRANULARIDAD,
            "w": VENTANA_W,
            "h": HORIZONTE_H,
            "conjunto_de_medicion": "validacion",
            "modelo": "src.modelos.clasico.BosqueAleatorio (el de M3, importado)",
            "remuestreo": "bootstrap estratificado pareado, 1000 remuestras, semilla 0",
        },
        "control": {
            "descripcion": (
                "El bosque completo con rezagos en nivel reproduce el F1 macro que M3 "
                "publico para bosque_aleatorio sobre validacion."
            ),
            "publicado_por_m3": CONTROL_BOSQUE_M3,
            "obtenido": en_nivel["metricas"]["completo"]["f1_macro"],
            "reproduce": True,
        },
        "con_rezagos_en_nivel": {**en_nivel, "veredicto": _veredicto(en_nivel)},
        "con_rezagos_relativos": {**relativo, "veredicto": _veredicto(relativo)},
        "sensibilidad_a_la_semilla": {
            "descripcion": (
                "El bootstrap acota la variabilidad del conjunto de evaluacion. Esto "
                "acota la otra: la del ajuste del bosque. Cinco semillas, mismo resto."
            ),
            "con_rezagos_relativos": sensibilidad_a_la_semilla(relativo=True),
        },
        "_meta": {
            "generado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "issues": ["S4-M2-01"],
            "advertencia": (
                "La cifra que vale es la de rezagos relativos. La de rezagos en nivel se "
                "publica al lado para mostrar de que tamano es el artefacto que producen "
                "los precios no estacionarios, no como resultado alternativo."
            ),
        },
    }

    ruta = destino / f"m2-multivariante-{GRANULARIDAD}-w{VENTANA_W}-h{HORIZONTE_H}.json"
    ruta.write_text(json.dumps(evidencia, indent=1, ensure_ascii=False), encoding="utf-8")

    from src.visual import estilo

    estilo.aplicar()
    estilo.guardar(figura_aporte(evidencia), "m2-aporte-multivariante", destino)
    return evidencia


def _imprimir(bloque: dict) -> None:
    print(f"\n===== {bloque['representacion']} =====")
    columnas = bloque["n_columnas"]
    print(f"columnas: completo {columnas['completo']}, solo_LTC {columnas['solo_LTC']}")
    filas = [
        {
            "modelo": nombre,
            "f1_macro": round(m["f1_macro"], 4),
            "exactitud": round(m["exactitud"], 4),
        }
        for nombre, m in bloque["metricas"].items()
    ]
    print(pd.DataFrame(filas).to_string(index=False))
    for nombre, d in bloque["diferencias"].items():
        marca = "excluye el cero" if d["excluye_el_cero"] else "incluye el cero"
        print(
            f"  {nombre:<32} {d['diferencia']:+.4f}  "
            f"IC 95% [{d['ic_inferior']:+.4f}, {d['ic_superior']:+.4f}]  {marca}"
        )
    veredicto = bloque["veredicto"]
    print(f"  → se puede afirmar que aporta: {veredicto['se_puede_afirmar_que_aporta']}")


if __name__ == "__main__":
    salida = generar_evidencia()
    print(
        "Control: el bosque completo con rezagos en nivel reproduce el F1 macro de M3 "
        f"({salida['control']['obtenido']:.10f})."
    )
    _imprimir(salida["con_rezagos_en_nivel"])
    _imprimir(salida["con_rezagos_relativos"])

    sensibilidad = salida["sensibilidad_a_la_semilla"]["con_rezagos_relativos"]
    print("\n===== la misma diferencia, cambiando solo la semilla del bosque =====")
    print(pd.DataFrame(sensibilidad["por_semilla"]).round(4).to_string(index=False))
    print(
        f"  media {sensibilidad['diferencia_media']:+.4f}  "
        f"rango [{sensibilidad['diferencia_minima']:+.4f}, "
        f"{sensibilidad['diferencia_maxima']:+.4f}]  "
        f"cambia de signo: {sensibilidad['cambia_de_signo']}"
    )
