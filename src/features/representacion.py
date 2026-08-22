"""S2-M2-02: arnes para medir si una representacion posterior a 2025 aporta.

El enunciado exige "herramientas State of the Art, mayores a 2025". Todo lo que
produce `construir()` es clasico: rezagos, retornos, volatilidad, correlacion movil,
indicadores tecnicos. La via coherente con el resto del proyecto es usar un modelo
fundacional congelado como **extractor de representaciones** y medir si sus columnas
aportan algo sobre las clasicas.

Ojo con no confundir esto con lo que ya hace M3. En la D12, Chronos-Bolt se usa como
**pronosticador**: predice la trayectoria y se le aplica `etiquetar()`. Aqui se
pregunta otra cosa —si sus representaciones internas, como columnas adicionales,
mejoran al bosque— y la D12 declara explicitamente que esa via no se tomo. Son
complementarias, no la misma medicion con otro nombre.

Por que el arnes existe antes que el extractor
-----------------------------------------------
La extraccion real depende de M3. Si este archivo esperara a que llegue, el issue se
quedaria sin seccion; y un arnes a medias esperando una pieza ajena no es entregable,
mientras que **un arnes completo con la extraccion declarada como pendiente si lo es**:
dice que se probo, como se probo, y que falta enchufar.

La regla 2 aplicada a la infraestructura
----------------------------------------
El relleno **no es ruido aleatorio**. Con ruido, el arnes "funcionaria" dando una
caida y no habria forma de distinguir un arnes correcto de uno que mide cualquier
cosa.

El relleno es la identidad: `ExtractorNulo` no agrega ninguna columna, asi que el
bosque tiene que dar **exactamente** el F1 macro ya publicado, `0.390497720487045`.
Si el arnes no reproduce esa cifra, esta mal montado, y eso se sabe antes de que
exista ninguna representacion que medir.

`ExtractorEco` es el segundo control, y responde una pregunta distinta: cuanto se
mueve el resultado por el solo hecho de **agregar columnas**, sin agregar informacion.
Reemite columnas que ya estan, con otro nombre. Si el arnes se moviera mucho ahi, no
tendria resolucion para detectar el efecto de una representacion de verdad, y habria
que saberlo antes y no despues.

Punto de entrada:  uv run python -m src.features.representacion
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from contracts.config import (
    ACTIVO_OBJETIVO,
    DELTA_F1_DECISIVO,
    GRANULARIDAD,
    HORIZONTE_H,
    VENTANA_W,
)
from contracts.labeling import etiquetar, objetivo
from contracts.metrics import f1_macro
from contracts.schema import cierre
from contracts.splits import particionar
from src.evaluacion.fuga import verificar_sin_fuga
from src.features.base import construir
from src.features.incertidumbre import intervalo_diferencia
from src.modelos.clasico import BosqueAleatorio

EVIDENCIAS = Path("docs/evidencias")

#: F1 macro del bosque sobre validacion con las caracteristicas clasicas y la
#: representacion vigente. Lo obtuvieron por separado M3 (#63) y M2 (#62).
CONTROL_SIN_REPRESENTACION = 0.390497720487045


class Extractor(ABC):
    """Contrato que cumple cualquier extractor de representaciones.

    Tres exigencias, y las tres existen por un riesgo concreto:

    **1. `ajustar` recibe la mascara de entrenamiento y es obligatoria.** Misma forma
    que `Escalador.ajustar()`. Un extractor que se ajuste sobre el panel completo
    mete fuga aunque su transformacion parezca inocente, y la fuga no se manifiesta
    como error sino como metricas excelentes.

    **2. `transformar` devuelve solo columnas NUEVAS**, indexadas como el panel. No
    devuelve las clasicas: el arnes concatena. Asi el arnes puede medir el aporte
    marginal sin depender de que el extractor recuerde incluirlas.

    **3. Los nombres de columna llevan el prefijo del extractor.** Sin eso, dos
    extractores distintos producirian columnas homonimas y ya sabemos como termina
    eso en este proyecto.
    """

    nombre: str = "extractor"

    @abstractmethod
    def ajustar(self, panel: pd.DataFrame, mascara_entrenamiento: np.ndarray) -> Extractor:
        """Ajusta lo que haya que ajustar usando SOLO las filas de entrenamiento."""

    @abstractmethod
    def transformar(self, panel: pd.DataFrame) -> pd.DataFrame:
        """Columnas nuevas para todo el panel. Puede venir vacio."""

    def __repr__(self) -> str:
        return f"<{type(self).__name__} nombre={self.nombre!r}>"


class ExtractorNulo(Extractor):
    """No agrega nada. Es el control que valida el arnes.

    Con este extractor el arnes tiene que reproducir exactamente el F1 macro ya
    publicado. Es la unica forma de saber que un resultado posterior mide la
    representacion y no un defecto del montaje.
    """

    nombre = "sin_representacion"

    def ajustar(self, panel: pd.DataFrame, mascara_entrenamiento: np.ndarray) -> ExtractorNulo:
        return self

    def transformar(self, panel: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame(index=panel.index)


class ExtractorEco(Extractor):
    """Reemite columnas que ya existen, con otro nombre. Informacion nueva: cero.

    No es ruido a proposito. Lo que mide es la sensibilidad del arnes al **numero de
    columnas**: si agregar `n` columnas redundantes moviera el resultado tanto como
    el efecto que se busca, el arnes no tendria resolucion para el trabajo y eso hay
    que saberlo antes de enchufar nada.

    Se toman las primeras columnas por orden alfabetico y no las mas importantes: la
    idea es no agregar informacion, y elegirlas por importancia seria elegirlas
    mirando el resultado.
    """

    nombre = "eco_de_clasicas"

    def __init__(self, n_columnas: int = 8) -> None:
        self.n_columnas = n_columnas
        self._columnas: list[str] | None = None

    def ajustar(self, panel: pd.DataFrame, mascara_entrenamiento: np.ndarray) -> ExtractorEco:
        clasicas = construir(panel)
        self._columnas = sorted(clasicas.columns)[: self.n_columnas]
        return self

    def transformar(self, panel: pd.DataFrame) -> pd.DataFrame:
        if self._columnas is None:
            raise RuntimeError("hay que llamar a ajustar() antes de transformar()")
        clasicas = construir(panel)
        return pd.DataFrame(
            {f"{self.nombre}_{c}": clasicas[c] for c in self._columnas}, index=panel.index
        )


#: Registro de extractores disponibles. M3 enchufa el suyo agregando una linea:
#: la clase tiene que heredar de `Extractor` y nada mas del arnes cambia.
EXTRACTORES: dict[str, type[Extractor]] = {
    ExtractorNulo.nombre: ExtractorNulo,
    ExtractorEco.nombre: ExtractorEco,
}


def _datos():
    panel = pd.read_parquet(f"data/processed/panel_{GRANULARIDAD}_v1.parquet")
    y = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), VENTANA_W), HORIZONTE_H)
    particion = particionar(len(panel), VENTANA_W, HORIZONTE_H)
    return panel, y, particion


def matriz_con(extractor: Extractor, panel: pd.DataFrame, entrenamiento: np.ndarray):
    """Clasicas + las del extractor, ajustando el extractor solo con entrenamiento."""
    clasicas = construir(panel)
    extractor.ajustar(panel, entrenamiento)
    nuevas = extractor.transformar(panel)

    if not nuevas.index.equals(panel.index):
        raise ValueError(
            f"{extractor.nombre}: transformar() devolvio un indice distinto al del panel"
        )
    chocan = set(nuevas.columns) & set(clasicas.columns)
    if chocan:
        raise ValueError(
            f"{extractor.nombre}: sus columnas chocan con las clasicas: {sorted(chocan)}"
        )
    return pd.concat([clasicas, nuevas], axis=1), list(nuevas.columns)


def verificar_extractor_sin_fuga(extractor: Extractor, panel: pd.DataFrame, filas: int = 400):
    """Un extractor que mire el futuro invalida todo lo que venga despues.

    Es especialmente pertinente aqui: un modelo de pronostico congelado recibe una
    serie entera, y darle mas contexto del debido es facil y silencioso.
    """
    recorte = panel.iloc[:filas]
    entrenamiento = np.zeros(len(recorte), dtype=bool)
    entrenamiento[: len(recorte) // 2] = True

    def constructor(datos: pd.DataFrame) -> pd.DataFrame:
        copia = type(extractor)() if not isinstance(extractor, ExtractorEco) else ExtractorEco()
        copia.ajustar(datos, np.ones(len(datos), dtype=bool))
        salida = copia.transformar(datos)
        # `verificar_sin_fuga` necesita al menos una columna para poder comparar.
        return salida if salida.shape[1] else pd.DataFrame({"_": 0.0}, index=datos.index)

    verificar_sin_fuga(constructor, recorte)


def evaluar_extractor(extractor_clase: type[Extractor], semillas=(0, 1, 2, 3, 4)) -> dict:
    """Bosque con y sin las columnas del extractor, sobre validacion.

    Se mide sobre validacion, no sobre prueba: elegir una representacion mirando el
    bloque de prueba lo gasta.

    Se usan varias semillas porque el efecto que se busca es del tamano del ruido de
    reentrenamiento. Ya nos paso una vez con el aporte multivariante: un intervalo
    estrecho no dice nada si la diferencia cambia de signo al reentrenar.
    """
    panel, y, particion = _datos()
    entrenables = particion.entrenamiento & y.notna().to_numpy()
    validables = particion.validacion & y.notna().to_numpy()
    y_entrena = y[entrenables]
    y_valida = y[validables].astype(int).to_numpy()

    X_con, columnas_nuevas = matriz_con(extractor_clase(), panel, entrenables)
    X_sin = construir(panel)

    filas = []
    predicciones_semilla_0 = {}
    for semilla in semillas:
        sin = BosqueAleatorio(semilla=semilla).entrenar(X_sin[entrenables], y_entrena)
        con = BosqueAleatorio(semilla=semilla, nombre="con_representacion").entrenar(
            X_con[entrenables], y_entrena
        )
        pred_sin = np.asarray(sin.predecir(X_sin[validables]), dtype=int)
        pred_con = np.asarray(con.predecir(X_con[validables]), dtype=int)
        if semilla == semillas[0]:
            predicciones_semilla_0 = {"sin": pred_sin, "con": pred_con}
        f1_sin = float(f1_macro(y_valida, pred_sin))
        f1_con = float(f1_macro(y_valida, pred_con))
        filas.append(
            {
                "semilla": int(semilla),
                "f1_sin_representacion": f1_sin,
                "f1_con_representacion": f1_con,
                "diferencia": f1_con - f1_sin,
            }
        )

    diferencias = np.array([f["diferencia"] for f in filas])
    intervalo = intervalo_diferencia(
        y_valida, predicciones_semilla_0["con"], predicciones_semilla_0["sin"], f1_macro
    )

    return {
        "extractor": extractor_clase.nombre,
        "n_columnas_nuevas": len(columnas_nuevas),
        "columnas_nuevas": columnas_nuevas,
        "n_validacion": int(len(y_valida)),
        "f1_sin_representacion": filas[0]["f1_sin_representacion"],
        "f1_con_representacion": filas[0]["f1_con_representacion"],
        "intervalo_de_la_diferencia": intervalo,
        "por_semilla": filas,
        "diferencia_media": float(diferencias.mean()),
        "diferencia_minima": float(diferencias.min()),
        "diferencia_maxima": float(diferencias.max()),
        "cambia_de_signo": bool(diferencias.min() < 0 < diferencias.max()),
        "supera_el_umbral_en_todas": bool((diferencias >= DELTA_F1_DECISIVO).all()),
        "se_puede_afirmar_que_aporta": bool(
            intervalo["excluye_el_cero"]
            and intervalo["diferencia"] > 0
            and not (diferencias.min() < 0 < diferencias.max())
        ),
    }


def verificar_arnes(resultado_nulo: dict, tolerancia: float = 1e-12) -> None:
    """Con el extractor nulo, el arnes tiene que dar la cifra ya publicada.

    Las dos ramas —con y sin representacion— tienen que coincidir entre si Y con el
    valor publicado. Lo primero comprueba que la concatenacion de cero columnas no
    altera nada; lo segundo, que la rama de referencia es la del proyecto y no un
    pipeline parecido.
    """
    con = resultado_nulo["f1_con_representacion"]
    sin = resultado_nulo["f1_sin_representacion"]
    fallos = []
    if abs(con - sin) > tolerancia:
        fallos.append(f"las dos ramas difieren: con={con!r}, sin={sin!r}")
    if abs(sin - CONTROL_SIN_REPRESENTACION) > tolerancia:
        fallos.append(
            f"la rama sin representacion da {sin!r} y lo publicado es "
            f"{CONTROL_SIN_REPRESENTACION!r}"
        )
    if fallos:
        raise AssertionError(
            "El arnes no reproduce lo conocido con el extractor nulo, asi que ninguna "
            "medicion suya sobre una representacion real seria confiable:\n  - "
            + "\n  - ".join(fallos)
        )


def generar_evidencia(directorio: Path | None = None) -> dict:
    panel, _, _ = _datos()

    nulo = evaluar_extractor(ExtractorNulo)
    verificar_arnes(nulo)
    verificar_extractor_sin_fuga(ExtractorEco(), panel)
    eco = evaluar_extractor(ExtractorEco)

    destino = directorio or EVIDENCIAS
    destino.mkdir(parents=True, exist_ok=True)

    evidencia = {
        "pregunta": (
            "Aporta una representacion posterior a 2025 sobre las caracteristicas "
            "clasicas, medido y no supuesto?"
        ),
        "estado": (
            "ARNES LISTO, EXTRACCION PENDIENTE. La extraccion real depende de M3. El "
            "arnes esta completo y validado con dos controles; enchufar un extractor "
            "es agregar una clase que herede de Extractor y una linea en EXTRACTORES."
        ),
        "parametros": {
            "panel": GRANULARIDAD,
            "w": VENTANA_W,
            "h": HORIZONTE_H,
            "conjunto_de_medicion": "validacion",
            "modelo": "src.modelos.clasico.BosqueAleatorio (el de M3, importado)",
            "semillas": [0, 1, 2, 3, 4],
            "delta_f1_decisivo": DELTA_F1_DECISIVO,
        },
        "control_del_arnes": {
            "descripcion": (
                "Con el extractor nulo las dos ramas tienen que coincidir entre si y "
                "con el F1 macro ya publicado. Si no, generar_evidencia() se detiene."
            ),
            "publicado": CONTROL_SIN_REPRESENTACION,
            "obtenido": nulo["f1_sin_representacion"],
            "reproduce": True,
        },
        "calibracion_agregar_columnas": eco,
        "extractores_registrados": sorted(EXTRACTORES),
        "que_falta": [
            "Un extractor real que herede de Extractor y produzca representaciones de "
            "un modelo fundacional congelado (Chronos-Bolt es el candidato de la D12).",
            "Correr evaluar_extractor() con el, que ya no requiere tocar este arnes.",
        ],
        "_meta": {
            "generado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "issues": ["S2-M2-02"],
            "advertencia": (
                "Que el arnes este validado no dice nada sobre si una representacion "
                "aporta. Dice que si no aporta, lo vamos a poder afirmar, y que si "
                "aporta, no va a ser un artefacto del montaje."
            ),
        },
    }

    ruta = destino / f"m2-representacion-{GRANULARIDAD}-w{VENTANA_W}-h{HORIZONTE_H}.json"
    ruta.write_text(json.dumps(evidencia, indent=1, ensure_ascii=False), encoding="utf-8")
    return evidencia


if __name__ == "__main__":
    salida = generar_evidencia()
    control = salida["control_del_arnes"]
    print(
        "Control del arnes (extractor nulo): reproduce "
        f"{control['obtenido']!r} == {control['publicado']!r}"
    )

    eco = salida["calibracion_agregar_columnas"]
    print(
        f"\n=== calibracion: {eco['n_columnas_nuevas']} columnas redundantes "
        f"({eco['extractor']}) ==="
    )
    print(pd.DataFrame(eco["por_semilla"]).round(5).to_string(index=False))
    intervalo = eco["intervalo_de_la_diferencia"]
    print(
        f"  diferencia media {eco['diferencia_media']:+.5f}  "
        f"rango [{eco['diferencia_minima']:+.5f}, {eco['diferencia_maxima']:+.5f}]  "
        f"cambia de signo: {eco['cambia_de_signo']}"
    )
    print(
        f"  IC 95 % de la diferencia (semilla 0): "
        f"[{intervalo['ic_inferior']:+.4f}, {intervalo['ic_superior']:+.4f}]  "
        f"excluye el cero: {intervalo['excluye_el_cero']}"
    )
    print("\nExtractores registrados:", ", ".join(salida["extractores_registrados"]))
    print("Estado:", salida["estado"])
