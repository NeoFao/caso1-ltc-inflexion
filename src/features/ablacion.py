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


def comparar_modelos_de_referencia(
    panel: pd.DataFrame, w: int, h: int, *, rezagos_relativos: bool
) -> pd.DataFrame:
    """Cuatro modelos de referencia sobre el conjunto completo, medidos en validacion.

    `rezagos_relativos` es obligatorio y no tiene valor por omision, a proposito.
    Antes lo heredaba del default de `construir()`, y cuando el PR #58 cambio ese
    default esta funcion paso a medir la representacion relativa mientras el bloque
    `resultados` del mismo archivo seguia midiendo la de nivel: dos representaciones
    distintas dentro del mismo JSON, sin que nada lo dijera y sin que ninguna linea
    de codigo cambiara. Misma forma que `Escalador.ajustar()`, y por la misma razon:
    si equivocarse es silencioso, el parametro se pide.

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

    X = construir(panel, rezagos_relativos=rezagos_relativos)
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


def generar_evidencia(directorio=None, w: int | None = None, h: int | None = None) -> dict:
    """Punto de entrada:  uv run python -m src.features.ablacion

    Granularidad, w y h salen de `contracts/config.py` y no de un valor por defecto
    propio, para que no existan dos fuentes de verdad de los tres numeros que
    definen el problema.
    """
    import json
    from datetime import UTC, datetime

    from contracts.config import GRANULARIDAD, HORIZONTE_H, VENTANA_W
    from src.visual import estilo

    w = VENTANA_W if w is None else w
    h = HORIZONTE_H if h is None else h

    estilo.aplicar()
    destino = directorio or estilo.DIRECTORIO_EVIDENCIAS
    destino.mkdir(parents=True, exist_ok=True)

    panel = pd.read_parquet(f"data/processed/panel_{GRANULARIDAD}_v1.parquet")

    # Se corre la ablacion DOS veces, con los rezagos en nivel y relativos. No es
    # por completitud: la primera version daba que quitar los rezagos de los activos
    # de apoyo costaba 0,10 de F1 macro, y eso se leia como evidencia a favor del
    # enfoque multivariante. Con los rezagos relativos —que contienen la misma
    # informacion dado que en t conocemos p(t)— el mismo efecto cae a 0,003. O sea
    # que lo que el modelo estaba usando era el NIVEL de precio, que funciona como
    # un indicador de en que tramo de la muestra estamos, y no la relacion entre
    # activos. Correr una sola de las dos habria producido una conclusion falsa.
    from src.features.base import construir

    variantes = {}
    for etiqueta, relativo in (("rezagos_en_nivel", False), ("rezagos_relativos", True)):
        tabla = ablacionar(
            panel, w=w, h=h,
            constructor=lambda p, r=relativo: construir(p, rezagos_relativos=r),
        )
        variantes[etiqueta] = con_baselines(tabla, panel, w=w, h=h)

    completa = variantes["rezagos_en_nivel"]
    for etiqueta, tabla in variantes.items():
        nombre = f"m2-ablacion-{etiqueta.replace('_', '-')}.csv"
        tabla.round(4).to_csv(destino / nombre, index=False)

    modelos = {
        etiqueta: comparar_modelos_de_referencia(
            panel, w=w, h=h, rezagos_relativos=relativo
        )
        for etiqueta, relativo in (("rezagos_en_nivel", False), ("rezagos_relativos", True))
    }
    for etiqueta, tabla in modelos.items():
        nombre = f"m2-modelos-referencia-{etiqueta.replace('_', '-')}.csv"
        tabla.round(4).to_csv(destino / nombre, index=False)

    # El invariante que habria cazado la desincronizacion del #58 el mismo dia:
    # `logistica_balanceada` en el bloque de modelos de referencia y `completo` en la
    # ablacion son literalmente el mismo modelo sobre las mismas columnas. Si no dan
    # lo mismo, las dos mitades del archivo estan midiendo representaciones distintas
    # y ninguna cifra de aqui significa lo que dice su etiqueta.
    for etiqueta, tabla in modelos.items():
        del_modelo = float(
            tabla.loc[tabla["modelo"] == "logistica_balanceada", "f1_macro"].iloc[0]
        )
        ablacion = variantes[etiqueta]
        del_completo = float(
            ablacion.loc[ablacion["conjunto"] == "completo", "f1_macro"].iloc[0]
        )
        if abs(del_modelo - del_completo) > 1e-9:
            raise AssertionError(
                f"En {etiqueta}, logistica_balanceada da {del_modelo!r} y el conjunto "
                f"'completo' de la ablacion da {del_completo!r}. Es el mismo modelo "
                "sobre las mismas columnas: si difieren, los dos bloques no estan "
                "midiendo la misma representacion."
            )

    evidencia = {
        "representacion_vigente": "rezagos_relativos",
        "modelos_de_referencia_rezagos_en_nivel": modelos["rezagos_en_nivel"]
        .round(6)
        .to_dict(orient="records"),
        "modelos_de_referencia_rezagos_relativos": modelos["rezagos_relativos"]
        .round(6)
        .to_dict(orient="records"),
        "parametros": {
            "panel": GRANULARIDAD, "w": w, "h": h,
            "conjunto_de_medicion": "validacion",
            "modelo_de_referencia": "LogisticRegression(class_weight='balanced'), semilla 0",
            "nota": (
                "Cada bloque dice en su nombre con que representacion se midio. Antes "
                "habia un unico bloque 'modelos_de_referencia' que heredaba el default "
                "de construir(), y al cambiar ese default en el #58 quedo midiendo una "
                "representacion distinta de la del bloque 'resultados' del mismo archivo."
            ),
        },
        "resultados_rezagos_en_nivel": completa.round(6).to_dict(orient="records"),
        "resultados_rezagos_relativos": variantes["rezagos_relativos"]
        .round(6)
        .to_dict(orient="records"),
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
    tabla = pd.DataFrame(salida["resultados_rezagos_en_nivel"])
    columnas = [
        "conjunto", "n_columnas", "n", "f1_macro", "delta_f1_macro",
        "precision_direccional", "f1_maximo", "f1_minimo", "exactitud",
    ]
    print("===== ablacion por familia, rezagos EN NIVEL (validacion) =====")
    print(tabla[[c for c in columnas if c in tabla.columns]].round(4).to_string(index=False))
    print()
    print("===== la misma ablacion con rezagos RELATIVOS =====")
    relativos = pd.DataFrame(salida["resultados_rezagos_relativos"])
    presentes = [c for c in columnas if c in relativos.columns]
    print(relativos[presentes].round(4).to_string(index=False))
    print()
    print("===== modelos de referencia, rezagos RELATIVOS (la representacion vigente) =====")
    modelos = pd.DataFrame(salida["modelos_de_referencia_rezagos_relativos"])
    print(
        modelos[
            ["modelo", "f1_macro", "precision_direccional", "exactitud",
             "f1_maximo", "f1_minimo", "f1_continuidad"]
        ].round(4).to_string(index=False)
    )
