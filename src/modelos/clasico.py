"""Modelo clasico de referencia. Modulo de Isaac (M3), tarea S1-M3-01.

No esta aqui para ganar. Esta para demostrar que el circuito completo funciona
-- panel, caracteristicas, particion, entrenamiento, arnes, evidencia -- con algo
que sabemos que anda, y para dejar el numero contra el que se compara todo lo
demas. Si el primer modelo que se intenta es un transformer, cuando falle no se
sabe si el problema es el modelo, las caracteristicas, la particion o la interfaz.

Los hiperparametros estan fijados antes de mirar ningun resultado y su razon esta
en la tabla de HIPERPARAMETROS, mas abajo. Ajustarlos mirando validacion es la
tarea S4-M3-02, no esta.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

from src.modelos.base import Modelo

# Se declara aqui, y no solo en el llamado, para que el guion de evidencia lo
# escriba tal cual en el JSON. Asi "lo elegimos antes de medir" es auditable y no
# una afirmacion nuestra.
HIPERPARAMETROS = {
    "n_estimators": 300,
    "min_samples_leaf": 5,
    "max_depth": None,
    "class_weight": "balanced",
    "random_state": 0,
}

CRITERIO_PREREGISTRADO = {
    "class_weight": (
        "balanced. Gini sobre la distribucion empirica (~91 % Continuidad) optimiza un "
        "criterio que no es el que reportamos, asi que se decidio de antemano reponderar "
        "las clases para alinear el entrenamiento con el F1 macro."
    ),
    "class_weight_correccion": (
        "CAMBIO DECLARADO. La primera corrida uso balanced_subsample, elegido a priori "
        "por coherencia con el bootstrap. Medido: colapsa a la mayoritaria en validacion "
        "y empata exactamente con BaselineTrivial (F1 macro 0.316120), aunque si produce "
        "predicciones minoritarias en entrenamiento. balanced, que implementa la misma "
        "intencion declarada, si produce minoritarias fuera de muestra. El cambio se hizo "
        "DESPUES de ver ese resultado y por eso queda escrito aqui: es una correccion de "
        "la variante, no una busqueda de hiperparametros, que es la tarea S4-M3-02."
    ),
    "n_estimators": (
        "300. El F1 macro sobre una clase con pocos cientos de ejemplos es ruidoso "
        "con 100 arboles, y 300 sigue siendo barato a esta escala."
    ),
    "min_samples_leaf": (
        "5. Con cientos de ejemplos minoritarios y decenas de variables, las hojas "
        "unitarias memorizan ruido."
    ),
    "max_depth": (
        "None, deliberadamente sin ajustar. Buscar hiperparametros ahora gastaria el "
        "conjunto de validacion antes de que exista el modelo fundacional. Eso es la "
        "tarea S4-M3-02."
    ),
    "metrica_que_decide": "F1 macro, no exactitud (RF-V1 y seccion 3.3 del PRD).",
    "conjunto_de_prueba": (
        "No se toca. Se mide sobre validacion; prueba se gasta una sola vez, al final."
    ),
}


class BosqueAleatorio(Modelo):
    """RandomForest de scikit-learn detras de la interfaz Modelo.

    La imputacion va adentro del modelo a proposito. El arnes filtra las filas por
    y.notna() pero no toca los nulos de X, y las caracteristicas de M2 arrancan con
    ~30 filas nulas por las ventanas moviles. Las dos salidas eran imputar o
    descartar filas antes de particionar; se imputa porque descartar corre las
    fronteras de los bloques, y entonces la validacion cubre fechas distintas a las
    que midio el spike y los numeros dejan de ser comparables entre personas.

    Ademas predecir() no puede descartar filas nunca: contracts.metrics._limpiar
    exige que las longitudes coincidan. Una sola politica, los dos caminos.
    """

    nombre = "bosque_aleatorio"

    def __init__(
        self,
        n_arboles: int = HIPERPARAMETROS["n_estimators"],
        min_hojas: int = HIPERPARAMETROS["min_samples_leaf"],
        profundidad_maxima: int | None = HIPERPARAMETROS["max_depth"],
        peso_clases: str | None = HIPERPARAMETROS["class_weight"],
        semilla: int = HIPERPARAMETROS["random_state"],
        n_procesos: int = -1,
        excluir: tuple[str, ...] = (),
        excluir_exactas: tuple[str, ...] = (),
        nombre: str | None = None,
    ) -> None:
        # Dos formas de excluir, y conviene saber cual usar.
        #
        # `excluir` recibe FRAGMENTOS de nombre. Es comodo, pero compara por
        # subcadena: excluir "LTC_cierre_rezago_1" tambien se llevaria por delante a
        # "LTC_cierre_rezago_10" el dia que M2 anada ese orden. Y un fragmento puede
        # cambiar de significado sin cambiar de forma, que es justo lo que paso con
        # "_rezago_" cuando los rezagos pasaron a ser relativos.
        #
        # `excluir_exactas` recibe NOMBRES COMPLETOS y compara por igualdad. Es la
        # que hay que usar cuando la lista de columnas se calcula con un ayudante de
        # M2 -- columnas_en_nivel_de_precio(), por ejemplo -- en vez de adivinarla
        # desde este modulo.
        self.n_arboles = n_arboles
        self.min_hojas = min_hojas
        self.profundidad_maxima = profundidad_maxima
        self.peso_clases = peso_clases
        self.semilla = semilla
        self.n_procesos = n_procesos
        self.excluir = excluir
        self.excluir_exactas = excluir_exactas
        if nombre is not None:
            self.nombre = nombre
        self._tuberia: Pipeline | None = None
        self._columnas: list[str] | None = None

    def _seleccionar(self, columnas: pd.Index) -> list[str]:
        exactas = set(self.excluir_exactas)
        return [
            c
            for c in columnas
            if c not in exactas and not any(p in c for p in self.excluir)
        ]

    @staticmethod
    def _preparar(X: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
        """Recorta a las columnas usadas y convierte los infinitos en nulos.

        El imputador trata los nulos pero no los +-inf: check_array de sklearn
        aborta con "Input contains infinity". Un solo pct_change sobre un precio
        cero bastaria. Es mas barato neutralizarlo aqui, en el camino compartido
        por entrenar y predecir, que depurarlo el dia que la aplicacion en vivo
        mande una fila rara.
        """
        return X.loc[:, columnas].astype("float64").replace([np.inf, -np.inf], np.nan)

    def entrenar(self, X: pd.DataFrame, y: pd.Series) -> BosqueAleatorio:
        if len(X) != len(y):
            raise ValueError(f"X e y tienen largos distintos: {len(X)} vs {len(y)}")
        if X.columns.has_duplicates:
            # Con nombres repetidos, X.loc[:, columnas] devuelve mas columnas de las
            # pedidas y la importancia por variable deja de ser interpretable. M2
            # todavia tiene que agregar familias de caracteristicas, asi que la
            # colision es posible; que falle nombrando a la culpable.
            repetidas = X.columns[X.columns.duplicated()].unique().tolist()
            raise ValueError(f"X tiene columnas repetidas: {repetidas[:5]}")

        columnas = self._seleccionar(X.columns)
        if not columnas:
            raise ValueError(f"excluir={self.excluir} no dejo ninguna columna")

        # y llega como Int64 nullable. np.asarray sobre un array enmascarado de
        # pandas devuelve dtype object, y con eso classes_ y predict() salen como
        # object. La conversion explicita ademas falla ruidosamente si quedo algun
        # nulo, que es lo que queremos: el arnes ya filtro por y.notna().
        objetivo = pd.Series(y).astype("int64").to_numpy()

        tuberia = Pipeline(
            [
                # La mediana se calcula solo con las filas de entrenamiento que
                # entrega el arnes, asi que no hay fuga. keep_empty_features=True es
                # obligatorio: sin el, una columna enteramente nula desaparece en
                # silencio y feature_importances_ deja de alinearse con _columnas.
                ("imputador", SimpleImputer(strategy="median", keep_empty_features=True)),
                (
                    "bosque",
                    RandomForestClassifier(
                        n_estimators=self.n_arboles,
                        min_samples_leaf=self.min_hojas,
                        max_depth=self.profundidad_maxima,
                        class_weight=self.peso_clases,
                        random_state=self.semilla,
                        n_jobs=self.n_procesos,
                    ),
                ),
            ]
        )
        tuberia.fit(self._preparar(X, columnas), objetivo)

        # Se asignan despues del fit: si el ajuste falla, el modelo queda sin
        # entrenar y predecir() avisa, en vez de responder con una tuberia a medias.
        self._tuberia = tuberia
        self._columnas = columnas
        return self

    def predecir(self, X: pd.DataFrame) -> np.ndarray:
        if self._tuberia is None or self._columnas is None:
            raise RuntimeError("hay que llamar a entrenar() antes de predecir()")
        faltantes = [c for c in self._columnas if c not in X.columns]
        if faltantes:
            raise ValueError(
                f"faltan {len(faltantes)} columnas que si estaban al entrenar: "
                f"{faltantes[:5]}. El modelo no puede predecir con otras variables "
                f"que las que vio."
            )
        return self._tuberia.predict(self._preparar(X, self._columnas)).astype(int)

    def importancias(self) -> pd.Series:
        """Importancia por variable, ordenada de mayor a menor.

        Es el diagnostico honesto de si el bosque se apoya en precios en nivel, que
        no son estacionarios: si los rezagos de cierre encabezan la lista, el modelo
        aprendio el rango de precios del periodo de entrenamiento y eso hay que
        decirlo en el informe.
        """
        if self._tuberia is None or self._columnas is None:
            raise RuntimeError("hay que llamar a entrenar() antes de pedir importancias()")
        bosque = self._tuberia.named_steps["bosque"]
        return pd.Series(
            bosque.feature_importances_, index=self._columnas, name="importancia"
        ).sort_values(ascending=False)
