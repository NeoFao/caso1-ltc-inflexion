"""Modelo fundacional: Chronos-Bolt detras de la interfaz Modelo (tarea S3-M3-01).

El modelo elegido en la D12. Es un modelo de pronostico, no un clasificador: dada
una serie devuelve la trayectoria futura, y nosotros necesitamos Maximo, Minimo o
Continuidad. El puente entre las dos cosas es lo que implementa este archivo.

Como cruza el puente, y por que asi. Se pronostica la trayectoria y se le aplica
`etiquetar()` del contrato, que es la misma funcion con la que se etiquetan los
datos reales. La alternativa era usar el modelo congelado como extractor de
representaciones y entrenar una cabeza de clasificacion encima. Se eligio esta
porque reutiliza el contrato en vez de agregar una pieza entrenable nueva, y
porque su costo resulto ser despreciable: la D12 lo dejo medido en unos 12
segundos sobre todo el bloque de validacion. Cuando la opcion simple cuesta eso,
la compleja tiene que justificar su costo, no al reves.

De donde sale el precio. La interfaz recibe X, la matriz de caracteristicas, y
desde el PR #58 ninguna de sus columnas esta en unidades de precio: los rezagos
son relativos. Un modelo de pronostico necesita la serie en nivel, asi que se le
entrega al construirlo y se usa `X.index` para saber en que instante hay que
pararse. La interfaz no cambia; lo que cambia es de donde sale el dato.

Por que no hay fuga, que es el riesgo real de este archivo. Para etiquetar el
instante t+h hacen falta las w velas anteriores y las w posteriores a t+h. Puesto
en t: las anteriores van de t+h-w a t, y esas ya ocurrieron; las posteriores van
de t+1 a t+h+w, y esas se pronostican. El contexto que se le da al modelo termina
en t. En ningun punto se lee un cierre posterior a t, y hay una prueba que lo
comprueba perturbando el futuro y exigiendo que la prediccion no se mueva.

Uso:
    uv sync --group dev --group modelos
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from contracts.config import HORIZONTE_H, VENTANA_W
from contracts.labeling import Clase, etiquetar
from src.modelos.base import Modelo

REPO_POR_DEFECTO = "amazon/chronos-bolt-small"
# 512 velas de 4 horas son ~85 dias. Es el contexto con el que se midio el
# inventario de la D12, y entra en el contexto nativo del modelo.
CONTEXTO_POR_DEFECTO = 512
TAMANO_LOTE = 64
# Los 9 cuantiles que devuelve Chronos-Bolt van de 0,1 a 0,9; el 4 es la mediana.
INDICE_MEDIANA = 4


class ChronosBolt(Modelo):
    """Chronos-Bolt de Amazon, en modo zero-shot, cumpliendo la interfaz Modelo.

    No se entrena: `entrenar()` solo carga los pesos. Eso es deliberado y es la
    razon por la que se eligio un modelo fundacional -- con 420 ejemplos de la
    clase minoritaria no hay de donde entrenar una arquitectura grande desde cero.
    """

    nombre = "chronos_bolt"

    def __init__(
        self,
        cierre: pd.Series,
        w: int = VENTANA_W,
        h: int = HORIZONTE_H,
        contexto: int = CONTEXTO_POR_DEFECTO,
        repo: str = REPO_POR_DEFECTO,
        lote: int = TAMANO_LOTE,
        nombre: str | None = None,
    ) -> None:
        if not isinstance(cierre, pd.Series):
            raise TypeError(f"cierre debe ser pd.Series, es {type(cierre).__name__}")
        if w < 1 or h < 0:
            raise ValueError(f"w debe ser >= 1 y h >= 0; se recibio w={w}, h={h}")

        self._valores = cierre.to_numpy(dtype=float)
        self._indice = cierre.index
        self.w = w
        self.h = h
        self.contexto = contexto
        self.repo = repo
        self.lote = lote
        if nombre is not None:
            self.nombre = nombre
        self._tuberia = None
        # Cuantas filas no tuvieron historia suficiente para armar la ventana. Se
        # expone para que el guion de evidencia lo reporte en vez de que quede
        # escondido detras de un valor por omision.
        self.sin_historia = 0

    # ------------------------------------------------------------------ interna

    def _cargar(self):
        """Carga perezosa: chronos vive en el grupo `modelos`, que CI no instala.

        Importar arriba haria fallar la recoleccion de pruebas en CI, que corre con
        --group dev. Aqui el import solo ocurre cuando alguien de verdad va a
        pronosticar.
        """
        if self._tuberia is None:
            import torch
            from chronos import BaseChronosPipeline

            torch.manual_seed(0)
            self._tuberia = BaseChronosPipeline.from_pretrained(
                self.repo, device_map="cpu", dtype=torch.float32
            )
        return self._tuberia

    def _posiciones(self, X: pd.DataFrame) -> np.ndarray:
        posiciones = self._indice.get_indexer(X.index)
        if (posiciones < 0).any():
            faltan = X.index[posiciones < 0][:3].tolist()
            raise ValueError(
                f"{int((posiciones < 0).sum())} instantes de X no estan en la serie de "
                f"cierre que recibio el modelo, por ejemplo {faltan}. Las dos tienen "
                f"que venir del mismo panel."
            )
        return posiciones

    def _etiqueta_de(self, i: int, pronostico: np.ndarray) -> int:
        """Arma la ventana centrada en t+h y le aplica el etiquetado del contrato.

        La ventana mide 2w+1 y su centro es exactamente t+h, asi que `etiquetar()`
        deja un solo valor no nulo, el del centro. Se lee ese.
        """
        inicio_pasado = i + self.h - self.w
        if inicio_pasado < 0:
            # Menos de w-h velas de historia. Solo pasa al principio de la serie,
            # dentro del bloque de entrenamiento.
            self.sin_historia += 1
            return int(Clase.CONTINUIDAD)

        pasado = self._valores[inicio_pasado : i + 1]
        ventana = np.concatenate([pasado, pronostico])
        if len(ventana) != 2 * self.w + 1:
            raise RuntimeError(
                f"la ventana quedo de {len(ventana)} y tenia que medir {2 * self.w + 1}. "
                f"Es un error de indices, no de datos."
            )

        etiquetas = etiquetar(pd.Series(ventana), self.w)
        etiqueta = etiquetas.iloc[self.w]
        if pd.isna(etiqueta):
            return int(Clase.CONTINUIDAD)
        return int(etiqueta)

    # ------------------------------------------------------------------ interfaz

    def entrenar(self, X: pd.DataFrame, y: pd.Series) -> ChronosBolt:
        """Zero-shot: no ajusta nada, solo deja los pesos cargados.

        Se respeta la interfaz igual, para que el arnes y la aplicacion no tengan
        que saber que este modelo no se entrena.
        """
        self._cargar()
        return self

    def predecir(self, X: pd.DataFrame) -> np.ndarray:
        if self._tuberia is None:
            raise RuntimeError("hay que llamar a entrenar() antes de predecir()")

        # Validar antes de importar: si X no casa con la serie, conviene decirlo con
        # el mensaje de arriba y no con un ModuleNotFoundError de torch, que manda a
        # revisar la instalacion cuando el problema son los datos.
        posiciones = self._posiciones(X)

        import torch

        horizonte = self.h + self.w
        etiquetas = np.empty(len(posiciones), dtype=int)

        for arranque in range(0, len(posiciones), self.lote):
            bloque = posiciones[arranque : arranque + self.lote]
            contextos = [
                torch.tensor(
                    self._valores[max(0, int(i) - self.contexto + 1) : int(i) + 1],
                    dtype=torch.float32,
                )
                for i in bloque
            ]
            # (lote, 9 cuantiles, horizonte). Se usa la mediana como trayectoria
            # puntual; los otros ocho cuantiles quedan disponibles para una version
            # que module la decision por incertidumbre, que no es esta.
            salida = self._cargar().predict(contextos, prediction_length=horizonte)
            medianas = np.asarray(salida[:, INDICE_MEDIANA, :], dtype=float)

            for desplazamiento, i in enumerate(bloque):
                etiquetas[arranque + desplazamiento] = self._etiqueta_de(
                    int(i), medianas[desplazamiento]
                )

        return etiquetas
