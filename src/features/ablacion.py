"""Ablaciones de familias de caracteristicas. Modulo de Alejandro (M2).

Responde una sola pregunta, y con numero: **si saco esta familia de caracteristicas,
cuanto empeora el F1 macro.** Es la infraestructura que necesitan el issue S2-M2-02
(¿aporta una representacion posterior a 2025?) y S4-M2-01 (¿aporta realmente el
enfoque multivariante?).

Tres decisiones que conviene tener claras antes de leer cualquier numero de aqui:

**1. Se mide sobre VALIDACION, nunca sobre prueba.** Elegir caracteristicas mirando
el bloque de prueba lo contamina: despues, el resultado final del proyecto estaria
reportado sobre datos que ya se usaron para decidir. El bloque de prueba se toca una
vez, al final, y para nada mas.

**2. El modelo de referencia NO es el modelo del proyecto.** Es una regresion
logistica regularizada, fija y documentada, que existe solo para que las familias se
comparen entre si en igualdad de condiciones. Un numero de este archivo dice "esta
familia aporta", no "el sistema rinde asi". El rendimiento del sistema sale del
modelo de M3 a traves del arnes de M0.

Se eligio un modelo lineal a proposito: es determinista, entrena en segundos, y no
tiene la varianza entre corridas que tendria un bosque, que en una ablacion se
confunde facil con el efecto que se quiere medir.

**3. El escalador se ajusta dentro de cada corrida, solo con entrenamiento.** Si se
ajustara una vez sobre el panel completo y se reutilizara, cada ablacion heredaria
fuga. Es el error que RF-F3 trata de impedir, y en una ablacion es especialmente
facil de cometer.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd

from contracts.labeling import etiquetar, objetivo
from contracts.metrics import evaluar
from contracts.schema import cierre
from contracts.splits import particionar
from src.features.escalado import Escalador, familia_de

# Semilla fija: una ablacion cuyo resultado cambia entre corridas no permite
# distinguir el efecto de la familia del ruido del ajuste.
SEMILLA = 0


def _modelo_referencia():
    from sklearn.linear_model import LogisticRegression

    return LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        random_state=SEMILLA,
    )


def _matriz_limpia(X: pd.DataFrame, y: pd.Series, mascara: np.ndarray):
    """Filas del bloque pedido donde estan presentes todas las columnas y la etiqueta.

    Se descartan filas incompletas en vez de imputarlas: imputar aqui meteria una
    decision de modelado dentro de una herramienta de medicion, y el efecto de esa
    decision se confundiria con el de la familia que se esta quitando.
    """
    completas = X.notna().all(axis=1).to_numpy() & y.notna().to_numpy()
    seleccion = np.asarray(mascara, dtype=bool) & completas
    return X.loc[seleccion], y.loc[seleccion].astype(int).to_numpy()


def evaluar_conjunto(
    X: pd.DataFrame,
    y: pd.Series,
    particion,
    nombre: str = "conjunto",
) -> dict:
    """Entrena el modelo de referencia con un conjunto de columnas y mide en validacion."""
    if X.shape[1] == 0:
        raise ValueError(f"el conjunto {nombre!r} no tiene ninguna columna")

    escalador = Escalador("robusto").ajustar(X, particion.entrenamiento)
    X_escalado = escalador.transformar(X)

    X_entrena, y_entrena = _matriz_limpia(X_escalado, y, particion.entrenamiento)
    X_valida, y_valida = _matriz_limpia(X_escalado, y, particion.validacion)

    modelo = _modelo_referencia().fit(X_entrena, y_entrena)
    predicciones = modelo.predict(X_valida)

    resultado = {"conjunto": nombre, "n_columnas": int(X.shape[1])}
    resultado.update(evaluar(y_valida, predicciones))
    resultado["n_entrenamiento"] = int(len(y_entrena))
    return resultado


def columnas_por_familia(X: pd.DataFrame) -> dict[str, list[str]]:
    agrupadas: dict[str, list[str]] = {}
    for columna in X.columns:
        agrupadas.setdefault(familia_de(columna), []).append(columna)
    return agrupadas


def es_de_activo_de_apoyo(columna: str) -> bool:
    """Columna que existe solo porque el problema es multivariante.

    Incluye la correlacion cruzada, que nombra a los dos activos, y las columnas de
    los cinco activos de apoyo. Excluye todo lo que se calcula solo con LTC.
    """
    from contracts.config import ACTIVOS_APOYO

    if columna.startswith("corr_"):
        return True
    return any(columna.startswith(f"{activo}_") for activo in ACTIVOS_APOYO)


def conjuntos_estandar(X: pd.DataFrame) -> dict[str, list[str]]:
    """Los conjuntos que responden las preguntas abiertas del proyecto.

    `solo_LTC` es el que importa para S4-M2-01: si su F1 macro empata con el del
    conjunto completo, el enfoque multivariante que pide el enunciado no esta
    aportando nada, y eso hay que reportarlo aunque incomode.
    """
    familias = columnas_por_familia(X)
    todas = list(X.columns)
    conjuntos = {"completo": todas}

    for familia, columnas in familias.items():
        restantes = [c for c in todas if c not in columnas]
        if restantes:
            conjuntos[f"sin_{familia}"] = restantes

    conjuntos["solo_LTC"] = [c for c in todas if not es_de_activo_de_apoyo(c)]
    conjuntos["sin_rezagos_de_apoyo"] = [
        c for c in todas if not (es_de_activo_de_apoyo(c) and "rezago" in c)
    ]
    return {k: v for k, v in conjuntos.items() if v}


def ablacionar(
    panel: pd.DataFrame,
    w: int,
    h: int,
    constructor: Callable[[pd.DataFrame], pd.DataFrame] | None = None,
    conjuntos: dict[str, list[str]] | None = None,
) -> pd.DataFrame:
    """Corre todos los conjuntos y devuelve la tabla con el delta contra el completo."""
    from src.features.base import construir

    constructor = constructor or construir
    X = constructor(panel)
    y = objetivo(etiquetar(cierre(panel, "LTC"), w), h)
    particion = particionar(len(panel), w, h)
    conjuntos = conjuntos or conjuntos_estandar(X)

    filas = [
        evaluar_conjunto(X[columnas], y, particion, nombre)
        for nombre, columnas in conjuntos.items()
    ]
    tabla = pd.DataFrame(filas)

    referencia = tabla.loc[tabla["conjunto"] == "completo", "f1_macro"]
    if len(referencia):
        tabla["delta_f1_macro"] = (tabla["f1_macro"] - float(referencia.iloc[0])).round(4)
    return tabla.sort_values("f1_macro", ascending=False).reset_index(drop=True)


def con_baselines(tabla: pd.DataFrame, panel: pd.DataFrame, w: int, h: int) -> pd.DataFrame:
    """Agrega los tres baselines obligatorios a la tabla, medidos en validacion.

    Sin ellos, un F1 macro de 0,35 no se puede leer: hay que saber si el piso esta en
    0,31 o en 0,30.
    """
    from src.modelos.base import BaselineAleatorio, BaselineMayoritario, BaselineTrivial

    X = pd.DataFrame(index=panel.index, data={"_": 0.0})
    y = objetivo(etiquetar(cierre(panel, "LTC"), w), h)
    particion = particionar(len(panel), w, h)

    X_entrena, y_entrena = _matriz_limpia(X, y, particion.entrenamiento)
    X_valida, y_valida = _matriz_limpia(X, y, particion.validacion)

    filas = []
    for modelo in (BaselineTrivial(), BaselineMayoritario(), BaselineAleatorio(semilla=SEMILLA)):
        modelo.entrenar(X_entrena, pd.Series(y_entrena))
        fila = {"conjunto": modelo.nombre, "n_columnas": 0}
        fila.update(evaluar(y_valida, modelo.predecir(X_valida)))
        filas.append(fila)

    return pd.concat([tabla, pd.DataFrame(filas)], ignore_index=True)


def comparar_modelos_de_referencia(panel: pd.DataFrame, w: int, h: int) -> pd.DataFrame:
    """Cuatro modelos de referencia sobre el conjunto completo, medidos en validacion.

    Existe por un motivo concreto: la primera corrida de las ablaciones dio que
    NINGUN conjunto de caracteristicas supera al baseline trivial. Antes de reportar
    eso hay que separar dos explicaciones muy distintas:

    - que las caracteristicas no informen, o
    - que el modelo de referencia lineal no sea capaz de usarlas.

    Se comparan lineal y de arboles, cada uno con y sin compensacion de clases. Si
    todos colapsan a Continuidad, la conclusion no es sobre el modelo lineal: es
    sobre lo dificil que es el problema con las caracteristicas actuales, y es un
    dato que M3 necesita antes de elegir el modelo fundacional.
    """
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression

    from src.features.base import construir

    X = construir(panel)
    y = objetivo(etiquetar(cierre(panel, "LTC"), w), h)
    particion = particionar(len(panel), w, h)

    escalado = Escalador("robusto").ajustar_y_transformar(X, particion.entrenamiento)
    X_entrena, y_entrena = _matriz_limpia(escalado, y, particion.entrenamiento)
    X_valida, y_valida = _matriz_limpia(escalado, y, particion.validacion)

    candidatos = {
        "logistica_balanceada": LogisticRegression(
            max_iter=2000, class_weight="balanced", random_state=SEMILLA
        ),
        "logistica_sin_balancear": LogisticRegression(max_iter=2000, random_state=SEMILLA),
        "arboles_balanceado": HistGradientBoostingClassifier(
            max_iter=300, class_weight="balanced", random_state=SEMILLA
        ),
        "arboles_sin_balancear": HistGradientBoostingClassifier(
            max_iter=300, random_state=SEMILLA
        ),
    }

    filas = []
    for nombre, modelo in candidatos.items():
        modelo.fit(X_entrena, y_entrena)
        fila = {"modelo": nombre}
        fila.update(evaluar(y_valida, modelo.predict(X_valida)))
        filas.append(fila)
    return pd.DataFrame(filas)


def generar_evidencia(directorio=None, w: int = 7, h: int = 5) -> dict:
    """Punto de entrada:  uv run python -m src.features.ablacion"""
    import json
    from datetime import UTC, datetime

    from src.visual import estilo

    estilo.aplicar()
    destino = directorio or estilo.DIRECTORIO_EVIDENCIAS
    destino.mkdir(parents=True, exist_ok=True)

    panel = pd.read_parquet("data/processed/panel_4h_v1.parquet")
    tabla = ablacionar(panel, w=w, h=h)
    completa = con_baselines(tabla, panel, w=w, h=h)
    completa.round(4).to_csv(destino / "m2-ablacion-familias.csv", index=False)

    modelos = comparar_modelos_de_referencia(panel, w=w, h=h)
    modelos.round(4).to_csv(destino / "m2-modelos-referencia.csv", index=False)

    evidencia = {
        "modelos_de_referencia": modelos.round(6).to_dict(orient="records"),
        "parametros": {
            "panel": "4h", "w": w, "h": h,
            "conjunto_de_medicion": "validacion",
            "modelo_de_referencia": "LogisticRegression(class_weight='balanced'), semilla 0",
        },
        "resultados": completa.round(6).to_dict(orient="records"),
        "_meta": {
            "generado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "issues": ["S2-M2-02", "S4-M2-01"],
            "advertencia": (
                "Estos numeros comparan FAMILIAS DE CARACTERISTICAS entre si con un "
                "modelo de referencia fijo. No son el rendimiento del sistema: ese sale "
                "del modelo de M3 por el arnes de M0, y sobre el bloque de prueba, que "
                "aqui no se toca."
            ),
        },
    }
    (destino / "m2-ablacion.json").write_text(
        json.dumps(evidencia, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    return evidencia


if __name__ == "__main__":
    salida = generar_evidencia()
    tabla = pd.DataFrame(salida["resultados"])
    columnas = [
        "conjunto", "n_columnas", "n", "f1_macro", "delta_f1_macro",
        "precision_direccional", "f1_maximo", "f1_minimo", "exactitud",
    ]
    print("===== ablacion por familia (validacion) =====")
    print(tabla[[c for c in columnas if c in tabla.columns]].round(4).to_string(index=False))
    print()
    print("===== modelos de referencia sobre el conjunto completo (validacion) =====")
    modelos = pd.DataFrame(salida["modelos_de_referencia"])
    print(
        modelos[
            ["modelo", "f1_macro", "precision_direccional", "exactitud",
             "f1_maximo", "f1_minimo", "f1_continuidad"]
        ].round(4).to_string(index=False)
    )
