"""Escalado de caracteristicas (RF-F3). Modulo de Alejandro (M2), issue S2-M2-01.

Una sola regla gobierna este archivo:

    **Los estadisticos del escalador se calculan SOLO con el bloque de
    entrenamiento.**

Ajustarlo sobre el panel completo es fuga de informacion, y de la peor clase: no
lanza ningun error, no rompe ninguna prueba obvia, y produce metricas mejores que
las reales. El modelo habria visto —a traves de la media y la desviacion— datos de
validacion y de prueba.

Es tan facil de escribir mal que conviene tener el contraejemplo a la vista:

    escalador.fit(X)                      # MAL: ve prueba
    escalador.fit(X[particion.entrenamiento])   # BIEN

Por eso `ajustar()` exige la mascara de entrenamiento como argumento obligatorio.
No hay forma de llamarlo "sin querer" sobre todo el panel.

El escalado NO se hace dentro de `construir()`. Depende de la particion, y la
particion depende de quien entrena; meterlo ahi obligaria a que el modulo de
caracteristicas conozca el split y volveria facil el error que este archivo trata
de impedir.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

METODOS = ("robusto", "estandar")


class Escalador:
    """Estandariza columnas con estadisticos aprendidos solo del entrenamiento.

    Dos metodos:

    - `robusto` (por defecto): resta la mediana y divide entre el rango
      intercuartil. Es el que corresponde aqui. Los retornos de criptomonedas
      tienen colas pesadas, y con media y desviacion un puñado de velas extremas
      —el desplome de 2022, por ejemplo— fija la escala de toda la serie y aplasta
      el resto de los datos contra el cero.
    - `estandar`: media y desviacion. Se deja implementado para poder mostrar la
      diferencia medida en vez de afirmarla.

    Las columnas con dispersion nula en entrenamiento se dejan sin escalar y se
    registran en `columnas_constantes`. Dividir entre cero produciria infinitos que
    despues aparecen como NaN cincuenta pasos mas adelante, sin rastro de donde
    salieron.
    """

    def __init__(self, metodo: str = "robusto") -> None:
        if metodo not in METODOS:
            raise ValueError(f"metodo desconocido: {metodo!r}. Esperado uno de {METODOS}")
        self.metodo = metodo
        self.centro_: pd.Series | None = None
        self.escala_: pd.Series | None = None
        self.columnas_: list[str] | None = None
        self.columnas_constantes_: list[str] = []
        self.n_filas_ajuste_: int = 0

    def ajustar(self, X: pd.DataFrame, mascara_entrenamiento: np.ndarray) -> Escalador:
        """Aprende centro y escala usando UNICAMENTE las filas de entrenamiento.

        La mascara es obligatoria a proposito: sin ella, la forma mas corta de
        llamar a esta funcion seria la incorrecta.
        """
        if not isinstance(X, pd.DataFrame):
            raise TypeError(f"X debe ser DataFrame, es {type(X).__name__}")
        mascara = np.asarray(mascara_entrenamiento, dtype=bool)
        if len(mascara) != len(X):
            raise ValueError(
                f"la mascara tiene {len(mascara)} elementos y X tiene {len(X)} filas"
            )
        if not mascara.any():
            raise ValueError("la mascara de entrenamiento no selecciona ninguna fila")

        entrenamiento = X.loc[mascara]
        self.columnas_ = list(X.columns)
        self.n_filas_ajuste_ = int(mascara.sum())

        if self.metodo == "robusto":
            centro = entrenamiento.median()
            escala = entrenamiento.quantile(0.75) - entrenamiento.quantile(0.25)
        else:
            centro = entrenamiento.mean()
            escala = entrenamiento.std()

        constantes = escala.isna() | np.isclose(escala.to_numpy(dtype=float), 0.0)
        self.columnas_constantes_ = list(escala.index[constantes])
        escala = escala.mask(constantes, 1.0)

        self.centro_ = centro
        self.escala_ = escala
        return self

    def transformar(self, X: pd.DataFrame) -> pd.DataFrame:
        """Aplica la transformacion aprendida. Se usa sobre TODO el panel.

        Que aqui entren tambien validacion y prueba no es fuga: se les aplica una
        transformacion fijada de antemano, no se las mira para calcularla. La fuga
        seria lo contrario.
        """
        if self.centro_ is None or self.escala_ is None:
            raise RuntimeError("hay que llamar a ajustar() antes de transformar()")
        faltantes = [c for c in self.columnas_ if c not in X.columns]
        if faltantes:
            raise ValueError(f"faltan columnas que si estaban al ajustar: {faltantes[:8]}")
        return (X[self.columnas_] - self.centro_) / self.escala_

    def ajustar_y_transformar(
        self, X: pd.DataFrame, mascara_entrenamiento: np.ndarray
    ) -> pd.DataFrame:
        return self.ajustar(X, mascara_entrenamiento).transformar(X)

    def parametros(self) -> pd.DataFrame:
        """Centro y escala por columna. Es lo que se documenta en el informe:
        RF-F3 pide que la escala este documentada, no solo aplicada."""
        if self.centro_ is None:
            raise RuntimeError("el escalador no esta ajustado")
        return pd.DataFrame(
            {"centro": self.centro_, "escala": self.escala_}
        ).assign(constante=lambda d: d.index.isin(self.columnas_constantes_))


def diagnostico_desplazamiento(
    X_escalado: pd.DataFrame,
    mascara_entrenamiento: np.ndarray,
    mascara_prueba: np.ndarray,
    umbral: float = 5.0,
) -> pd.DataFrame:
    """Cuanto se sale del rango de entrenamiento cada columna en el bloque de prueba.

    Escalar no vuelve estacionaria a una columna que no lo es. Si el precio de LTC
    en prueba esta fuera del rango que tuvo en entrenamiento, su version escalada
    tambien lo estara, y el modelo recibe valores en una zona donde nunca aprendio
    nada. Esta funcion pone numero a ese problema en vez de dejarlo como advertencia.

    Devuelve, por columna, la fraccion de filas de prueba cuyo valor escalado supera
    `umbral` en valor absoluto, y el maximo alcanzado.
    """
    entrenamiento = np.asarray(mascara_entrenamiento, dtype=bool)
    prueba = np.asarray(mascara_prueba, dtype=bool)

    filas = []
    for columna in X_escalado.columns:
        en_prueba = X_escalado.loc[prueba, columna].dropna()
        en_entrenamiento = X_escalado.loc[entrenamiento, columna].dropna()
        if en_prueba.empty:
            continue
        filas.append(
            {
                "columna": columna,
                "fuera_de_rango_pct": round(
                    100 * float((en_prueba.abs() > umbral).mean()), 3
                ),
                "abs_max_prueba": round(float(en_prueba.abs().max()), 3),
                "abs_max_entrenamiento": round(float(en_entrenamiento.abs().max()), 3),
            }
        )
    tabla = pd.DataFrame(filas)
    tabla["familia"] = tabla["columna"].map(familia_de)
    return tabla.sort_values("fuera_de_rango_pct", ascending=False).reset_index(drop=True)


def familia_de(columna: str) -> str:
    """Agrupa cada columna en la familia de RF-F1 a la que pertenece.

    Sirve para dos cosas: leer el diagnostico por familia en vez de por columna, y
    para las ablaciones, donde lo que se quita o se deja es una familia entera.
    """
    if "rezago" in columna:
        return "rezagos"
    if columna.startswith("corr_"):
        return "correlacion_cruzada"
    if "volatilidad" in columna:
        return "volatilidad"
    if "retorno" in columna:
        return "retornos"
    if any(t in columna for t in ("sma", "ema", "rsi", "macd", "bollinger")):
        return "indicadores_tecnicos"
    if any(t in columna for t in ("rango", "posicion", "asimetria", "curtosis")):
        return "ventana_deslizante"
    return "otras"


# ---------------------------------------------------------------------------
# Evidencia. Punto de entrada:  uv run python -m src.features.escalado
# ---------------------------------------------------------------------------


def _resumen_por_familia(diagnostico: pd.DataFrame) -> pd.DataFrame:
    return (
        diagnostico.groupby("familia")
        .agg(
            columnas=("columna", "size"),
            fuera_de_rango_pct_medio=("fuera_de_rango_pct", "mean"),
            peor_columna_pct=("fuera_de_rango_pct", "max"),
            abs_max_prueba=("abs_max_prueba", "max"),
        )
        .round(3)
        .sort_values("fuera_de_rango_pct_medio", ascending=False)
        .reset_index()
    )


def figura_desplazamiento(nivel: pd.DataFrame, relativo: pd.DataFrame):
    """Cuanto se sale del rango de entrenamiento cada familia, con rezagos en nivel
    contra rezagos relativos."""
    import matplotlib.pyplot as plt

    from src.visual import estilo

    familias = list(
        dict.fromkeys(list(nivel["familia"]) + list(relativo["familia"]))
    )
    def valor(tabla, familia):
        fila = tabla[tabla["familia"] == familia]
        return float(fila["fuera_de_rango_pct_medio"].iloc[0]) if len(fila) else 0.0

    x = np.arange(len(familias))
    ancho = 0.38
    fig, eje = plt.subplots(figsize=(10, 4.4))
    eje.bar(
        x - ancho / 2, [valor(nivel, f) for f in familias], ancho,
        color=estilo.MAXIMO, edgecolor="black", linewidth=0.6, hatch="//",
        label="Rezagos en nivel de precio",
    )
    eje.bar(
        x + ancho / 2, [valor(relativo, f) for f in familias], ancho,
        color=estilo.MINIMO, edgecolor="black", linewidth=0.6, hatch="\\\\",
        label="Rezagos relativos al precio actual",
    )
    eje.set_xticks(x, [f.replace("_", " ") for f in familias], fontsize=9)
    eje.set_ylabel("% de filas de prueba fuera del rango\nde entrenamiento (|z| > 5)")
    eje.set_title("Escalar no vuelve estacionaria una columna que no lo es")
    eje.legend(fontsize=9)
    fig.autofmt_xdate(rotation=18, ha="right")
    fig.tight_layout()
    return fig


def generar_evidencia(directorio=None, w: int = 7, h: int = 5) -> dict:
    """Mide el desplazamiento con las dos formas de los rezagos y con los dos metodos.

    Se usa el panel de 4 horas con w = 7 y h = 5, que es lo que recomienda la
    medicion de scripts/spike_datos.py. `contracts/config.py` sigue PROVISIONAL.
    """
    import json
    from datetime import UTC, datetime

    from contracts.splits import particionar
    from src.features.base import construir
    from src.visual import estilo

    estilo.aplicar()
    destino = directorio or estilo.DIRECTORIO_EVIDENCIAS
    destino.mkdir(parents=True, exist_ok=True)

    panel = pd.read_parquet("data/processed/panel_4h_v1.parquet")
    particion = particionar(len(panel), w, h)

    resultados = {}
    resumenes = {}
    for etiqueta, relativo in (("nivel", False), ("relativo", True)):
        X = construir(panel, rezagos_relativos=relativo)
        for metodo in METODOS:
            escalador = Escalador(metodo)
            escalado = escalador.ajustar_y_transformar(X, particion.entrenamiento)
            diagnostico = diagnostico_desplazamiento(
                escalado, particion.entrenamiento, particion.prueba
            )
            resumen = _resumen_por_familia(diagnostico)
            clave = f"rezagos_{etiqueta}__metodo_{metodo}"
            resumenes[clave] = resumen
            resultados[clave] = {
                "n_columnas": int(X.shape[1]),
                "n_filas_ajuste": escalador.n_filas_ajuste_,
                "columnas_constantes": escalador.columnas_constantes_,
                "por_familia": resumen.to_dict(orient="records"),
                "peores_columnas": diagnostico.head(10).to_dict(orient="records"),
            }
            if etiqueta == "nivel" and metodo == "robusto":
                escalador.parametros().round(6).to_csv(
                    destino / "m2-escalado-parametros.csv"
                )

    estilo.guardar(
        figura_desplazamiento(
            resumenes["rezagos_nivel__metodo_robusto"],
            resumenes["rezagos_relativo__metodo_robusto"],
        ),
        "m2-escalado-desplazamiento",
        destino,
    )

    evidencia = {
        "parametros": {"panel": "4h", "w": w, "h": h, "umbral_fuera_de_rango": 5.0},
        "resultados": resultados,
        "_meta": {
            "generado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "issue": "S2-M2-01",
            "nota": (
                "El escalador se ajusta solo con el bloque de entrenamiento. "
                "El diagnostico mide algo distinto del escalado: cuanto se sale del "
                "rango aprendido cada familia, que es un problema de estacionariedad "
                "y no de escala."
            ),
        },
    }
    (destino / "m2-escalado.json").write_text(
        json.dumps(evidencia, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    return evidencia


if __name__ == "__main__":
    salida = generar_evidencia()
    for clave, bloque in salida["resultados"].items():
        print(f"===== {clave}  ({bloque['n_columnas']} columnas) =====")
        print(pd.DataFrame(bloque["por_familia"]).to_string(index=False))
        print()
