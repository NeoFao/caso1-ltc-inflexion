"""Modelo avanzado: iTransformer entrenado por nosotros (tarea S4-M3-01).

El enunciado pide que el segundo modelo sea un Transformer, y nombra iTransformer
e Informer entre las opciones. Cual de los dos se puede usar de verdad en nuestras
maquinas esta medido en `src/modelos/inventario_avanzado.py`.

Que hace iTransformer y por que encaja con la forma de nuestros datos. Un
Transformer clasico sobre series atiende entre INSTANTES de tiempo: cada vela es
un token. iTransformer invierte eso y atiende entre SERIES: cada activo completo
es un token, y la atencion aprende como se relacionan LTC, BTC, ETH, SOL, XRP y
ADA entre si. Encaja con la forma de un panel de seis series.

Ojo con leer eso como una ventaja demostrada. Que la arquitectura corresponda a la
forma del panel no significa que las cinco series de apoyo aporten: eso se midio y
no se puede afirmar (docs/06-aporte-multivariante.md). Por eso el modelo acepta
`solo_objetivo=True`, para poder medir las dos formas en vez de suponer cual gana.

El puente a las tres clases es el MISMO que usa el fundacional: se pronostica la
trayectoria y se le aplica `etiquetar()` del contrato sobre una ventana de 2w+1
centrada en t+h. Eso es deliberado. Si el fundacional y el avanzado cruzaran el
puente de formas distintas, la diferencia entre sus F1 mezclaria dos cosas -- el
modelo y el puente -- y dejaria de ser una comparacion entre modelos.

Normalizacion por ventana, y por que hace falta. Los precios no son estacionarios:
un modelo entrenado con el rango de 2020-2024 y evaluado en 2025 ve valores fuera
de lo que vio nunca. Cada ventana se estandariza con SU PROPIA media y desviacion,
que son datos anteriores a t, y el pronostico se devuelve a la escala original con
esas mismas constantes. No usa nada del futuro.

Uso:
    uv sync --group dev --group modelos
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from contracts.config import ACTIVOS, HORIZONTE_H, VENTANA_W
from contracts.labeling import Clase, etiquetar
from src.modelos.base import Modelo

LOOKBACK_POR_DEFECTO = 96
PROFUNDIDAD = 2
DIMENSION = 64
EPOCAS = 8
TAMANO_LOTE = 64
TASA_APRENDIZAJE = 3e-4


class ITransformerAvanzado(Modelo):
    """iTransformer entrenado sobre nuestro panel, detras de la interfaz Modelo.

    A diferencia del fundacional, este SI se entrena. Es la diferencia que el
    informe tiene que explicar: uno trae su conocimiento de miles de series ajenas,
    el otro solo puede aprender de las nuestras, y las nuestras tienen 420 ejemplos
    de la clase minoritaria.
    """

    nombre = "itransformer"

    def __init__(
        self,
        cierres: pd.DataFrame,
        w: int = VENTANA_W,
        h: int = HORIZONTE_H,
        lookback: int = LOOKBACK_POR_DEFECTO,
        epocas: int = EPOCAS,
        dimension: int = DIMENSION,
        profundidad: int = PROFUNDIDAD,
        lote: int = TAMANO_LOTE,
        semilla: int = 0,
        solo_objetivo: bool = False,
        nombre: str | None = None,
    ) -> None:
        if not isinstance(cierres, pd.DataFrame):
            raise TypeError(f"cierres debe ser pd.DataFrame, es {type(cierres).__name__}")
        if cierres.shape[1] < 1:
            raise ValueError("cierres no tiene columnas")

        self._columnas = [cierres.columns[0]] if solo_objetivo else list(cierres.columns)
        self._valores = cierres[self._columnas].to_numpy(dtype=np.float32)
        self._indice = cierres.index
        self.w = w
        self.h = h
        self.lookback = lookback
        self.epocas = epocas
        self.dimension = dimension
        self.profundidad = profundidad
        self.lote = lote
        self.semilla = semilla
        self.solo_objetivo = solo_objetivo
        if nombre is not None:
            self.nombre = nombre
        self._red = None
        self.sin_historia = 0
        # Se rellenan al entrenar, para que el guion de evidencia los reporte y el
        # presupuesto de la RNF-4 quede medido y no estimado.
        self.segundos_entrenamiento = None
        self.n_parametros = None
        self.perdida_final = None

    # ------------------------------------------------------------------ interna

    @property
    def horizonte(self) -> int:
        return self.h + self.w

    def _ventanas(self, posiciones: np.ndarray, con_objetivo: bool):
        """Arma las ventanas de entrada y, si se piden, las de salida.

        La entrada de la posicion i son los `lookback` cierres que terminan en i.
        La salida son los `w+h` cierres siguientes, que en entrenamiento existen de
        verdad y en prediccion son lo que hay que pronosticar.
        """
        entradas, salidas, validas = [], [], []
        for i in posiciones:
            i = int(i)
            inicio = i - self.lookback + 1
            if inicio < 0:
                continue
            if con_objetivo and i + self.horizonte >= len(self._valores):
                continue
            entradas.append(self._valores[inicio : i + 1])
            if con_objetivo:
                salidas.append(self._valores[i + 1 : i + 1 + self.horizonte])
            validas.append(i)
        if not entradas:
            raise ValueError(
                f"ninguna de las {len(posiciones)} posiciones tiene {self.lookback} velas "
                f"de historia. Con un lookback tan largo no queda nada que usar."
            )
        return (
            np.stack(entradas),
            np.stack(salidas) if con_objetivo else None,
            np.asarray(validas),
        )

    @staticmethod
    def _normalizar(entradas: np.ndarray):
        """Estandariza cada ventana con su propia media y desviacion.

        Las dos constantes salen de la ventana, que es pasado, asi que no hay fuga.
        Sin esto el modelo aprende el rango de precios del entrenamiento y falla
        cuando el precio sale de ese rango, que es el mismo problema que la D6
        encontro en los rezagos en nivel.
        """
        media = entradas.mean(axis=1, keepdims=True)
        desvio = entradas.std(axis=1, keepdims=True)
        desvio = np.where(desvio < 1e-8, 1.0, desvio)
        return (entradas - media) / desvio, media, desvio

    def _construir_red(self, n_variates: int):
        import torch
        from iTransformer import iTransformer

        torch.manual_seed(self.semilla)
        return iTransformer(
            num_variates=n_variates,
            lookback_len=self.lookback,
            depth=self.profundidad,
            dim=self.dimension,
            pred_length=(self.horizonte,),
        )

    def _etiqueta_de(self, i: int, pronostico: np.ndarray) -> int:
        """Identico al del fundacional: ventana de 2w+1 centrada en t+h."""
        inicio_pasado = i + self.h - self.w
        if inicio_pasado < 0:
            self.sin_historia += 1
            return int(Clase.CONTINUIDAD)

        pasado = self._valores[inicio_pasado : i + 1, 0]
        ventana = np.concatenate([pasado, pronostico])
        if len(ventana) != 2 * self.w + 1:
            raise RuntimeError(
                f"la ventana quedo de {len(ventana)} y tenia que medir {2 * self.w + 1}."
            )
        etiquetas = etiquetar(pd.Series(ventana), self.w)
        etiqueta = etiquetas.iloc[self.w]
        return int(Clase.CONTINUIDAD) if pd.isna(etiqueta) else int(etiqueta)

    def _posiciones(self, X: pd.DataFrame) -> np.ndarray:
        posiciones = self._indice.get_indexer(X.index)
        if (posiciones < 0).any():
            raise ValueError(
                f"{int((posiciones < 0).sum())} instantes de X no estan en el panel de "
                f"cierres que recibio el modelo. Las dos cosas tienen que venir del "
                f"mismo panel."
            )
        return posiciones

    # ------------------------------------------------------------------ interfaz

    def entrenar(self, X: pd.DataFrame, y: pd.Series) -> ITransformerAvanzado:
        """Entrena a pronosticar los w+h cierres siguientes.

        Las ventanas se arman solo con las posiciones que el arnes entrega como
        entrenamiento. Sus objetivos alcanzan como mucho w+h velas mas alla de la
        ultima, y eso cae dentro del embargo que `particionar()` deja justamente de
        ese tamano, asi que ningun objetivo toca validacion.
        """
        import time

        import torch

        posiciones = self._posiciones(X)
        entradas, salidas, _ = self._ventanas(posiciones, con_objetivo=True)
        entradas_n, media, desvio = self._normalizar(entradas)
        salidas_n = (salidas - media) / desvio

        red = self._construir_red(entradas.shape[2])
        self.n_parametros = int(sum(p.numel() for p in red.parameters()))
        optimizador = torch.optim.AdamW(red.parameters(), lr=TASA_APRENDIZAJE)
        perdida_fn = torch.nn.MSELoss()

        tensor_entrada = torch.tensor(entradas_n, dtype=torch.float32)
        tensor_salida = torch.tensor(salidas_n, dtype=torch.float32)
        n = len(tensor_entrada)
        generador = np.random.default_rng(self.semilla)

        reloj = time.perf_counter()
        red.train()
        for _ in range(self.epocas):
            orden = generador.permutation(n)
            acumulada, bloques = 0.0, 0
            for arranque in range(0, n, self.lote):
                idx = orden[arranque : arranque + self.lote]
                optimizador.zero_grad()
                prediccion = red(tensor_entrada[idx])
                perdida = perdida_fn(prediccion, tensor_salida[idx])
                perdida.backward()
                optimizador.step()
                acumulada += float(perdida.item())
                bloques += 1
            self.perdida_final = acumulada / max(bloques, 1)
        self.segundos_entrenamiento = round(time.perf_counter() - reloj, 1)

        red.eval()
        self._red = red
        return self

    def predecir(self, X: pd.DataFrame) -> np.ndarray:
        if self._red is None:
            raise RuntimeError("hay que llamar a entrenar() antes de predecir()")

        posiciones = self._posiciones(X)

        import torch

        etiquetas = np.full(len(posiciones), int(Clase.CONTINUIDAD), dtype=int)
        entradas, _, validas = self._ventanas(posiciones, con_objetivo=False)
        entradas_n, media, desvio = self._normalizar(entradas)
        donde = {int(p): k for k, p in enumerate(posiciones)}

        with torch.no_grad():
            for arranque in range(0, len(entradas_n), self.lote):
                bloque = slice(arranque, arranque + self.lote)
                salida = self._red(torch.tensor(entradas_n[bloque], dtype=torch.float32))
                # (lote, horizonte, variates) -> se devuelve a escala y se toma el
                # activo objetivo, que es la primera columna.
                crudo = salida.numpy() * desvio[bloque] + media[bloque]
                for desplazamiento, i in enumerate(validas[bloque]):
                    etiquetas[donde[int(i)]] = self._etiqueta_de(
                        int(i), crudo[desplazamiento, :, 0]
                    )
        return etiquetas


def cierres_del_panel(panel: pd.DataFrame) -> pd.DataFrame:
    """Los seis cierres, con el activo objetivo primero.

    El orden importa: `_etiqueta_de` lee la columna 0 como el objetivo.
    """
    from contracts.schema import columna

    return panel[[columna(a, "cierre") for a in ACTIVOS]]
