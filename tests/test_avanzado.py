"""Pruebas del modelo avanzado (S4-M3-01).

Mismo reparto que las del fundacional: lo que se puede comprobar sin los pesos
corre siempre, incluido CI; lo que necesita iTransformer lleva marca propia.

La pieza central vuelve a ser la de fuga. Este modelo ademas se entrena, asi que
hay una segunda que no hacia falta alli: que las ventanas de entrenamiento no
alcancen el bloque de validacion.
"""

from __future__ import annotations

import importlib.util

import numpy as np
import pandas as pd
import pytest

from contracts.config import ACTIVOS
from contracts.labeling import Clase
from contracts.schema import columna
from contracts.splits import particionar
from src.modelos.avanzado import ITransformerAvanzado, cierres_del_panel
from src.modelos.base import Modelo

W = 7
H = 1

necesita_itransformer = pytest.mark.skipif(
    importlib.util.find_spec("iTransformer") is None,
    reason="iTransformer vive en el grupo `modelos`, que CI no instala",
)


def _cierres(n: int = 600, semilla: int = 0) -> pd.DataFrame:
    generador = np.random.default_rng(semilla)
    indice = pd.date_range("2020-08-11", periods=n, freq="4h", tz="UTC", name="fecha")
    datos = {
        columna(a, "cierre"): 100 + (j + 1) * np.cumsum(generador.normal(0, 1, size=n))
        for j, a in enumerate(ACTIVOS)
    }
    return pd.DataFrame(datos, index=indice)


def _modelo(cierres=None, **kwargs) -> ITransformerAvanzado:
    return ITransformerAvanzado(
        cierres if cierres is not None else _cierres(), w=W, h=H, lookback=48, **kwargs
    )


# ------------------------------------------------------------- sin iTransformer


def test_cumple_la_interfaz_sin_construir_la_red():
    """Construirlo no arma la red ni importa torch: eso ocurre al entrenar."""
    modelo = _modelo()
    assert isinstance(modelo, Modelo)
    assert modelo.nombre == "itransformer"
    assert modelo._red is None


def test_predecir_antes_de_entrenar_falla_con_mensaje_claro():
    modelo = _modelo()
    X = pd.DataFrame(index=modelo._indice[:10])
    with pytest.raises(RuntimeError, match="entrenar"):
        modelo.predecir(X)


def test_rechaza_algo_que_no_es_dataframe():
    with pytest.raises(TypeError, match="pd.DataFrame"):
        ITransformerAvanzado(pd.Series([1.0, 2.0]))


def test_solo_objetivo_deja_una_sola_serie():
    """La variante existe para poder medir si las cinco de apoyo aportan, en vez de
    suponerlo. Con la medicion del #62 encima de la mesa, suponerlo seria justo lo
    que no se puede hacer."""
    completo = _modelo()
    uno = _modelo(solo_objetivo=True)
    assert completo._valores.shape[1] == len(ACTIVOS)
    assert uno._valores.shape[1] == 1
    assert uno._columnas == [columna(ACTIVOS[0], "cierre")]


def test_el_objetivo_es_la_primera_columna():
    """_etiqueta_de lee la columna 0 como el activo objetivo. Si el orden cambiara,
    el modelo etiquetaria los giros de otra moneda sin que nada fallara."""
    cierres = cierres_del_panel(_cierres().rename(columns=str))
    assert cierres.columns[0] == columna(ACTIVOS[0], "cierre")
    assert ACTIVOS[0] == "LTC"


def test_la_ventana_mide_2w_mas_1_y_su_centro_es_t_mas_h():
    """Misma aritmetica que el fundacional, y misma razon para fijarla: un error de
    uno aqui corre todas las etiquetas sin romper nada."""
    cierres = pd.DataFrame(
        {columna(a, "cierre"): np.full(600, 100.0) for a in ACTIVOS},
        index=pd.date_range("2020-08-11", periods=600, freq="4h", tz="UTC", name="fecha"),
    )
    modelo = ITransformerAvanzado(cierres, w=W, h=H, lookback=48)

    assert modelo._etiqueta_de(300, np.array([120.0] + [90.0] * (H + W - 1))) == int(
        Clase.MAXIMO
    )
    assert modelo._etiqueta_de(300, np.array([80.0] + [110.0] * (H + W - 1))) == int(
        Clase.MINIMO
    )
    assert modelo._etiqueta_de(300, np.full(H + W, 100.0)) == int(Clase.CONTINUIDAD)


def test_la_normalizacion_por_ventana_no_usa_nada_de_afuera():
    """Cada ventana se estandariza con su propia media y desviacion. Escalar una
    ventana entera no puede cambiar su version normalizada."""
    entradas = np.random.default_rng(0).normal(size=(4, 48, 6)).astype(np.float32)
    normal, _, _ = ITransformerAvanzado._normalizar(entradas)
    escaladas, _, _ = ITransformerAvanzado._normalizar(entradas * 7.0 + 3.0)
    assert np.allclose(normal, escaladas, atol=1e-4)


def test_la_normalizacion_sobrevive_una_ventana_plana():
    """Desviacion cero dividiria por cero y propagaria NaN a toda la red."""
    entradas = np.full((2, 48, 6), 100.0, dtype=np.float32)
    normal, _, _ = ITransformerAvanzado._normalizar(entradas)
    assert np.isfinite(normal).all()


def test_las_ventanas_de_entrenamiento_no_alcanzan_validacion():
    """La razon por la que el embargo mide w+h y no menos.

    Se entrena a pronosticar w+h velas, asi que el objetivo de la ultima ventana de
    entrenamiento llega w+h mas alla. `particionar()` deja exactamente ese hueco, y
    esta prueba comprueba que alcanza: el ultimo objetivo cae antes de la primera
    fila de validacion.
    """
    n = 600
    particion = particionar(n=n, w=W, h=H)
    ultima_entrenamiento = int(np.where(particion.entrenamiento)[0].max())
    primera_validacion = int(np.where(particion.validacion)[0].min())

    ultimo_objetivo = ultima_entrenamiento + W + H
    assert ultimo_objetivo < primera_validacion, (
        f"el objetivo de la ultima ventana de entrenamiento cae en {ultimo_objetivo} y "
        f"validacion empieza en {primera_validacion}: el embargo no alcanza."
    )


# ------------------------------------------------------------- con iTransformer


@necesita_itransformer
def test_no_hay_fuga_perturbar_el_futuro_no_mueve_el_presente():
    """Se entrena una sola vez y se predice sobre dos paneles que solo difieren
    despues del corte. Si algo del futuro entrara en la prediccion, las dos tandas
    diferirian."""
    cierres = _cierres(n=400)
    corte = 330
    X = pd.DataFrame(index=cierres.index[corte - 15 : corte + 1])

    modelo = _modelo(cierres, epocas=1)
    entrena = pd.DataFrame(index=cierres.index[60:250])
    modelo.entrenar(entrena, pd.Series(dtype="Int64"))
    esperado = modelo.predecir(X)

    perturbados = cierres.copy()
    perturbados.iloc[corte + 1 :] = perturbados.iloc[corte + 1 :] * 3.7 + 1000.0
    modelo._valores = perturbados[modelo._columnas].to_numpy(dtype=np.float32)

    assert np.array_equal(esperado, modelo.predecir(X)), (
        "perturbar los cierres posteriores al corte cambio la prediccion de instantes "
        "anteriores: hay fuga de informacion futura."
    )


@necesita_itransformer
def test_devuelve_un_codigo_de_clase_por_fila():
    cierres = _cierres(n=400)
    modelo = _modelo(cierres, epocas=1)
    modelo.entrenar(pd.DataFrame(index=cierres.index[60:250]), pd.Series(dtype="Int64"))

    X = pd.DataFrame(index=cierres.index[300:330])
    predicciones = modelo.predecir(X)
    assert len(predicciones) == len(X)
    assert predicciones.dtype.kind in "iu"
    assert set(np.unique(predicciones)) <= {int(c) for c in Clase}


@necesita_itransformer
def test_es_reproducible_con_la_misma_semilla():
    """RF-M4. Con la misma semilla, dos entrenamientos tienen que dar lo mismo."""
    cierres = _cierres(n=400)
    entrena = pd.DataFrame(index=cierres.index[60:250])
    X = pd.DataFrame(index=cierres.index[300:320])

    salidas = []
    for _ in range(2):
        modelo = _modelo(cierres, epocas=1, semilla=3)
        modelo.entrenar(entrena, pd.Series(dtype="Int64"))
        salidas.append(modelo.predecir(X))

    assert np.array_equal(salidas[0], salidas[1])


@necesita_itransformer
def test_entrenar_deja_medido_el_costo():
    """La RNF-4 fija un presupuesto de dos horas. Para respetarlo hay que medirlo,
    asi que el modelo guarda lo que tardo y cuantos parametros tiene."""
    cierres = _cierres(n=400)
    modelo = _modelo(cierres, epocas=1)
    modelo.entrenar(pd.DataFrame(index=cierres.index[60:250]), pd.Series(dtype="Int64"))

    assert modelo.segundos_entrenamiento is not None
    assert modelo.n_parametros > 0
    assert modelo.perdida_final is not None and np.isfinite(modelo.perdida_final)


def test_la_capacidad_es_configurable_y_su_defecto_no_cambio():
    """dimension y profundidad se parametrizan para poder buscarlas en S4-M3-02. El
    defecto tiene que seguir siendo el que midio S4-M3-01, o las cifras publicadas
    dejarian de corresponder al modelo por omision."""
    modelo = _modelo()
    assert (modelo.dimension, modelo.profundidad) == (64, 2)

    otro = _modelo(dimension=32, profundidad=1)
    assert (otro.dimension, otro.profundidad) == (32, 1)


@necesita_itransformer
def test_una_dimension_menor_da_una_red_mas_chica():
    """Si el parametro no llegara a la red, la rejilla mediria seis veces el mismo
    modelo y creeria estar comparando capacidades."""
    cierres = _cierres(n=400)
    entrena = pd.DataFrame(index=cierres.index[60:250])

    grande = _modelo(cierres, epocas=1, dimension=64).entrenar(
        entrena, pd.Series(dtype="Int64")
    )
    chico = _modelo(cierres, epocas=1, dimension=32).entrenar(
        entrena, pd.Series(dtype="Int64")
    )

    assert chico.n_parametros < grande.n_parametros


def test_el_barrido_mide_las_seis_metricas_que_publica_el_panel():
    """La fase 2 del #92, fijada para que no se deshaga.

    El barrido guardaba solo el F1 macro y el panel publica seis columnas, asi que
    publicar medias en las seis era imposible y terminaba mostrando una corrida
    suelta donde la D18 declara medias de cinco. Si alguien recorta METRICAS, el
    mismo problema vuelve sin que nada falle.
    """
    from src.modelos.sensibilidad_avanzado import METRICAS

    assert set(METRICAS) == {
        "f1_macro",
        "precision_direccional",
        "exactitud",
        "f1_maximo",
        "f1_minimo",
        "f1_continuidad",
    }


def test_las_seis_metricas_existen_en_lo_que_devuelve_el_arnes():
    """De nada sirve nombrarlas si el arnes no las produce con ese nombre: el
    barrido fallaria a mitad de camino, despues de entrenar cinco redes."""
    from contracts.metrics import evaluar
    from src.modelos.sensibilidad_avanzado import METRICAS

    reales = [int(Clase.CONTINUIDAD)] * 8 + [int(Clase.MAXIMO), int(Clase.MINIMO)]
    predichas = [int(Clase.CONTINUIDAD)] * 9 + [int(Clase.MINIMO)]

    resultado = evaluar(reales, predichas)
    faltantes = [m for m in METRICAS if m not in resultado]
    assert not faltantes, f"el arnes no devuelve {faltantes}"
