"""Intervalos de confianza de las metricas por bootstrap. Modulo de Alejandro (M2).

Nace de una pregunta que conviene tener respondida antes de la defensa: el mejor
modelo del proyecto esta en F1 macro 0,3672 contra 0,3368 del baseline aleatorio.
Son 0,0304 de diferencia. **Cual es el intervalo de ese 0,3672?**

Sin esa respuesta, "cruza DELTA_F1_DECISIVO" suena a criterio objetivo y en realidad
es una convencion que fijamos nosotros. Lo cual esta bien —hace falta un umbral y se
fijo antes de medir— pero hay que decirlo asi y acompanarlo de la incertidumbre.

---

**Dos advertencias metodologicas que hay que leer antes de usar cualquier numero de
aqui, porque cambian que significa el resultado.**

**1. Se mide sobre VALIDACION, no sobre prueba.** La forma natural de pedir esto es
"un bootstrap sobre el test", y no corresponde, por dos razones. Primera: las cifras
que preocupan —0,3672 y 0,3368— estan medidas sobre validacion, asi que un intervalo
sobre prueba no seria el intervalo de esas cifras, seria otro numero. Segunda: el
bloque de prueba se toca una vez, al final, y toda decision tomada mirandolo lo
contamina. Un intervalo
de confianza es informacion que usariamos para decidir si el modelo aporta; calcularlo
sobre prueba y despues reportar el resultado final sobre prueba seria reportar sobre
datos que ya se usaron para decidir.

**2. Comparar dos intervalos que se solapan NO es una prueba de la diferencia.** Es
el error mas comun con este metodo: dos intervalos pueden solaparse y aun asi la
diferencia ser sistematicamente distinta de cero, porque los dos modelos aciertan y
fallan sobre las MISMAS velas y sus errores estan correlacionados. Lo que responde la
pregunta es el intervalo de la DIFERENCIA, remuestreando las dos predicciones juntas
sobre las mismas filas. Este modulo calcula las dos cosas y reporta las dos, y si
alguna vez se contradicen, la que manda es la de la diferencia.

El remuestreo es sobre filas con reemplazo, estratificado por clase real para que
ninguna remuestra se quede sin ejemplos de una clase minoritaria: con ~90 velas de
Maximo en validacion, un remuestreo simple produce a veces cero, el F1 de esa clase
queda indefinido y el macro se degrada por un artefacto del metodo y no del modelo.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from contracts.labeling import Clase
from contracts.metrics import f1_macro, precision_direccional

REMUESTRAS = 1000
SEMILLA = 0


def _indices_estratificados(y_real: np.ndarray, generador) -> np.ndarray:
    """Remuestra con reemplazo dentro de cada clase, conservando su tamano.

    Sin estratificar, las remuestras donde no cae ningun Maximo dan F1 cero para esa
    clase por ausencia de casos y no por error del modelo, y el intervalo sale ancho
    hacia abajo por una razon que no tiene que ver con el modelo.
    """
    partes = []
    for clase in np.unique(y_real):
        posiciones = np.flatnonzero(y_real == clase)
        partes.append(generador.choice(posiciones, size=len(posiciones), replace=True))
    return np.concatenate(partes)


def intervalo_metrica(
    y_real, y_pred, metrica=f1_macro, remuestras: int = REMUESTRAS, semilla: int = SEMILLA
) -> dict:
    """Percentiles 2,5 y 97,5 de una metrica por bootstrap estratificado."""
    real = np.asarray(y_real, dtype=int)
    pred = np.asarray(y_pred, dtype=int)
    generador = np.random.default_rng(semilla)

    valores = np.empty(remuestras)
    for i in range(remuestras):
        idx = _indices_estratificados(real, generador)
        valores[i] = metrica(real[idx], pred[idx])

    return {
        "valor": float(metrica(real, pred)),
        "ic_inferior": float(np.percentile(valores, 2.5)),
        "ic_superior": float(np.percentile(valores, 97.5)),
        "desviacion_bootstrap": float(valores.std(ddof=1)),
        "remuestras": remuestras,
    }


def intervalo_diferencia(
    y_real, y_pred_a, y_pred_b, metrica=f1_macro,
    remuestras: int = REMUESTRAS, semilla: int = SEMILLA,
) -> dict:
    """Intervalo de `metrica(A) - metrica(B)` con remuestreo PAREADO.

    Las dos predicciones se remuestrean sobre las mismas filas en cada iteracion.
    Esa es la diferencia entre esta funcion y comparar dos intervalos por separado, y
    es la que responde la pregunta: si A y B aciertan y fallan sobre las mismas velas,
    sus errores estan correlacionados y el intervalo de la diferencia es mas estrecho
    que lo que sugeriria el solape de los intervalos individuales.

    `fraccion_a_favor` es la proporcion de remuestras en que A supera a B. Es la
    lectura mas directa para el informe: "en el X % de las remuestras el modelo supera
    al baseline".
    """
    real = np.asarray(y_real, dtype=int)
    pred_a = np.asarray(y_pred_a, dtype=int)
    pred_b = np.asarray(y_pred_b, dtype=int)
    generador = np.random.default_rng(semilla)

    diferencias = np.empty(remuestras)
    for i in range(remuestras):
        idx = _indices_estratificados(real, generador)
        diferencias[i] = metrica(real[idx], pred_a[idx]) - metrica(real[idx], pred_b[idx])

    inferior = float(np.percentile(diferencias, 2.5))
    superior = float(np.percentile(diferencias, 97.5))
    return {
        "diferencia": float(metrica(real, pred_a) - metrica(real, pred_b)),
        "ic_inferior": inferior,
        "ic_superior": superior,
        "excluye_el_cero": bool(inferior > 0 or superior < 0),
        "fraccion_a_favor": float((diferencias > 0).mean()),
        "remuestras": remuestras,
    }


def resumen_clases(y_real) -> pd.DataFrame:
    """Cuantos casos de cada clase tiene el conjunto.

    Va explicito porque un intervalo sobre 90 casos de la clase minoritaria no
    significa lo mismo que sobre 900, y el numero tiene que estar al lado del
    intervalo para que se pueda leer."""
    real = pd.Series(np.asarray(y_real, dtype=int))
    total = len(real)
    return pd.DataFrame(
        [
            {
                "clase": clase.name.capitalize(),
                "codigo": int(clase),
                "n": int((real == int(clase)).sum()),
                "porcentaje": round(100 * float((real == int(clase)).mean()), 3),
            }
            for clase in Clase
        ]
        + [{"clase": "TOTAL", "codigo": 0, "n": total, "porcentaje": 100.0}]
    )


def generar_evidencia(directorio=None) -> dict:
    """Intervalos de las configuraciones que hoy sostienen las cifras del proyecto.

    Punto de entrada:  uv run python -m src.features.incertidumbre
    """
    import json
    from datetime import UTC, datetime

    from contracts.config import ACTIVO_OBJETIVO, GRANULARIDAD, HORIZONTE_H, VENTANA_W
    from contracts.labeling import etiquetar, objetivo
    from contracts.schema import cierre
    from contracts.splits import particionar
    from src.modelos.base import BaselineAleatorio, BaselineTrivial
    from src.modelos.clasico import BosqueAleatorio
    from src.visual import estilo

    estilo.aplicar()
    destino = directorio or estilo.DIRECTORIO_EVIDENCIAS
    destino.mkdir(parents=True, exist_ok=True)

    panel = pd.read_parquet(f"data/processed/panel_{GRANULARIDAD}_v1.parquet")
    y = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), VENTANA_W), HORIZONTE_H)
    particion = particionar(len(panel), VENTANA_W, HORIZONTE_H)

    # Se reproduce el experimento de M3 tal cual, importando SU modelo y no uno
    # equivalente: misma imputacion por mediana, mismos hiperparametros, sin
    # escalado. Un intervalo calculado sobre una reimplementacion parecida seria el
    # intervalo de otra cosa. La primera version de este archivo usaba mi propio
    # pipeline y daba F1 macro 0,3563 donde el suyo da 0,3672 — una diferencia del
    # mismo tamano que los efectos que estamos discutiendo.
    #
    # Los rezagos van EN NIVEL porque es lo que habia cuando M3 corrio el
    # experimento. Cuando entre el cambio de default hay que repetir esto.
    from src.features.base import construir

    X = construir(panel, rezagos_relativos=False)

    # Mismo filtrado que el arnes de M0: solo se exige que la etiqueta exista. Los
    # nulos de las caracteristicas los resuelve el imputador dentro del pipeline.
    entrenables = particion.entrenamiento & y.notna().to_numpy()
    validables = particion.validacion & y.notna().to_numpy()
    X_entrena, y_entrena = X[entrenables], y[entrenables]
    X_valida = X[validables]
    y_valida = y[validables].astype(int).to_numpy()

    predicciones: dict[str, np.ndarray] = {}
    for nombre, modelo in (
        ("baseline_trivial", BaselineTrivial()),
        ("baseline_aleatorio", BaselineAleatorio(semilla=0)),
        (
            "bosque_aleatorio_rezagos_en_nivel",
            BosqueAleatorio(nombre="bosque_aleatorio_rezagos_en_nivel"),
        ),
        (
            "bosque_aleatorio_sin_rezagos",
            BosqueAleatorio(excluir=("_rezago_",), nombre="bosque_aleatorio_sin_rezagos"),
        ),
    ):
        modelo.entrenar(X_entrena, y_entrena)
        predicciones[nombre] = np.asarray(modelo.predecir(X_valida), dtype=int)

    intervalos = {
        nombre: {
            "f1_macro": intervalo_metrica(y_valida, pred, f1_macro),
            "precision_direccional": intervalo_metrica(y_valida, pred, precision_direccional),
        }
        for nombre, pred in predicciones.items()
    }

    comparaciones = {}
    for a, b in (
        ("bosque_aleatorio_sin_rezagos", "baseline_aleatorio"),
        ("bosque_aleatorio_sin_rezagos", "baseline_trivial"),
        ("bosque_aleatorio_sin_rezagos", "bosque_aleatorio_rezagos_en_nivel"),
        ("bosque_aleatorio_rezagos_en_nivel", "baseline_aleatorio"),
    ):
        comparaciones[f"{a}__vs__{b}"] = intervalo_diferencia(
            y_valida, predicciones[a], predicciones[b], f1_macro
        )

    y_prueba = y[particion.prueba & y.notna().to_numpy()].astype(int).to_numpy()
    evidencia = {
        "parametros": {
            "panel": GRANULARIDAD, "w": VENTANA_W, "h": HORIZONTE_H,
            "conjunto": "validacion",
            "remuestras": REMUESTRAS,
            "remuestreo": "estratificado por clase real, con reemplazo",
            "delta_f1_decisivo": 0.02,
        },
        "tamano_validacion": resumen_clases(y_valida).to_dict(orient="records"),
        "tamano_prueba_sin_tocar": resumen_clases(y_prueba).to_dict(orient="records"),
        "intervalos": intervalos,
        "comparaciones_pareadas": comparaciones,
        "_meta": {
            "generado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "advertencia": (
                "Medido sobre VALIDACION y no sobre prueba: las cifras que se querian "
                "acotar estan medidas ahi, y el bloque de prueba se reserva para el "
                "resultado final. El tamano de prueba se reporta solo como referencia, "
                "sin evaluar ningun modelo sobre el."
            ),
        },
    }
    (destino / "m2-incertidumbre.json").write_text(
        json.dumps(evidencia, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    return evidencia


if __name__ == "__main__":
    salida = generar_evidencia()
    print("=== tamano del conjunto de validacion ===")
    print(pd.DataFrame(salida["tamano_validacion"]).to_string(index=False))
    print("\n=== tamano del bloque de prueba (reservado, no se evalua) ===")
    print(pd.DataFrame(salida["tamano_prueba_sin_tocar"]).to_string(index=False))

    print("\n=== F1 macro con intervalo al 95 % (validacion) ===")
    filas = [
        {
            "modelo": nombre,
            "f1_macro": round(bloque["f1_macro"]["valor"], 4),
            "ic_95": f"[{bloque['f1_macro']['ic_inferior']:.4f}, "
                     f"{bloque['f1_macro']['ic_superior']:.4f}]",
            "prec_direccional": round(bloque["precision_direccional"]["valor"], 4),
            "ic_95_pd": f"[{bloque['precision_direccional']['ic_inferior']:.4f}, "
                        f"{bloque['precision_direccional']['ic_superior']:.4f}]",
        }
        for nombre, bloque in salida["intervalos"].items()
    ]
    print(pd.DataFrame(filas).to_string(index=False))

    print("\n=== diferencias con remuestreo PAREADO (lo que responde la pregunta) ===")
    filas = [
        {
            "comparacion": nombre.replace("__vs__", "  vs  "),
            "diferencia": round(bloque["diferencia"], 4),
            "ic_95": f"[{bloque['ic_inferior']:.4f}, {bloque['ic_superior']:.4f}]",
            "excluye_cero": bloque["excluye_el_cero"],
            "frac_a_favor": round(bloque["fraccion_a_favor"], 3),
        }
        for nombre, bloque in salida["comparaciones_pareadas"].items()
    ]
    print(pd.DataFrame(filas).to_string(index=False))
