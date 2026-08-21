"""Pruebas del modelo fundacional (S3-M3-01).

Se parten en dos grupos a proposito.

Las de la primera mitad no necesitan chronos y corren siempre, incluido CI, que
instala solo --group dev. Cubren la aritmetica de indices del puente entre
pronostico y etiqueta, que es donde un error de uno se traduce en etiquetas
sistematicamente corridas sin que nada falle.

Las de la segunda mitad necesitan los pesos y se saltan solas cuando no estan. La
que importa de verdad es la de fuga: comprueba que perturbar el futuro no mueve la
prediccion del presente.
"""

from __future__ import annotations

import importlib.util

import numpy as np
import pandas as pd
import pytest

from contracts.labeling import Clase
from src.modelos.base import Modelo
from src.modelos.fundacional import ChronosBolt

W = 7
H = 1

# Marca por prueba y NO importorskip a nivel de modulo. Con importorskip, la
# ausencia de chronos se lleva por delante el archivo entero, incluidas las pruebas
# de aritmetica de indices que no lo necesitan -- que son justo las que conviene que
# corran en CI, porque un error de uno ahi no rompe nada y corre todas las etiquetas.
necesita_chronos = pytest.mark.skipif(
    importlib.util.find_spec("chronos") is None,
    reason="chronos vive en el grupo `modelos`, que CI no instala",
)


def _serie(n: int = 600, semilla: int = 0) -> pd.Series:
    generador = np.random.default_rng(semilla)
    valores = 100 + np.cumsum(generador.normal(0, 1, size=n))
    indice = pd.date_range("2020-08-11", periods=n, freq="4h", tz="UTC", name="fecha")
    return pd.Series(valores, index=indice, name="cierre")


def _modelo(serie: pd.Series | None = None, **kwargs) -> ChronosBolt:
    return ChronosBolt(serie if serie is not None else _serie(), w=W, h=H, **kwargs)


# --------------------------------------------------------------- sin chronos


def test_cumple_la_interfaz_sin_haber_cargado_pesos():
    """Construirlo no debe descargar nada: la carga es perezosa y ocurre en
    entrenar(). Si esto se rompe, CI empieza a bajar 182 MB por prueba."""
    modelo = _modelo()
    assert isinstance(modelo, Modelo)
    assert modelo.nombre == "chronos_bolt"
    assert modelo._tuberia is None


def test_predecir_antes_de_entrenar_falla_con_mensaje_claro():
    """Mismo mensaje que el resto de los modelos del proyecto."""
    modelo = _modelo()
    X = pd.DataFrame(index=modelo._indice[:10])
    with pytest.raises(RuntimeError, match="entrenar"):
        modelo.predecir(X)


def test_rechaza_instantes_que_no_estan_en_la_serie():
    """X y la serie de cierre tienen que venir del mismo panel. Si no, el modelo
    estaria pronosticando para un instante que no sabe ubicar."""
    modelo = _modelo()
    ajeno = pd.DataFrame(index=pd.date_range("1999-01-01", periods=3, freq="4h", tz="UTC"))
    modelo._tuberia = object()  # saltarse la carga: lo que se prueba es el mapeo
    with pytest.raises(ValueError, match="no estan en la serie"):
        modelo.predecir(ajeno)


def test_la_ventana_mide_2w_mas_1_y_su_centro_es_t_mas_h():
    """El corazon del puente, y donde un error de uno no se nota.

    Se fabrica un pronostico que hace de t+h un maximo estricto: el centro por
    encima de todo lo demas. Si los indices estuvieran corridos, el centro caeria
    en otro punto y la etiqueta no seria Maximo.
    """
    serie = pd.Series(
        np.full(600, 100.0),
        index=pd.date_range("2020-08-11", periods=600, freq="4h", tz="UTC", name="fecha"),
    )
    modelo = ChronosBolt(serie, w=W, h=H)

    i = 300
    # El pronostico cubre t+1..t+h+w. El centro de la ventana es t+h = t+1, que es
    # su primer valor: se lo pone por encima y el resto por debajo.
    pronostico = np.array([120.0] + [90.0] * (H + W - 1))
    assert modelo._etiqueta_de(i, pronostico) == int(Clase.MAXIMO)

    pronostico_min = np.array([80.0] + [110.0] * (H + W - 1))
    assert modelo._etiqueta_de(i, pronostico_min) == int(Clase.MINIMO)


def test_una_trayectoria_plana_es_continuidad():
    """Sin extremo estricto no hay giro, y el etiquetado del contrato lo resuelve
    igual que con datos reales."""
    serie = pd.Series(
        np.full(600, 100.0),
        index=pd.date_range("2020-08-11", periods=600, freq="4h", tz="UTC", name="fecha"),
    )
    modelo = ChronosBolt(serie, w=W, h=H)
    assert modelo._etiqueta_de(300, np.full(H + W, 100.0)) == int(Clase.CONTINUIDAD)


@pytest.mark.parametrize(("w", "h"), [(3, 1), (7, 1), (7, 5), (10, 2)])
def test_la_ventana_mide_lo_que_debe_para_varios_w_y_h(w, h):
    """La aritmetica tiene que cerrar para cualquier par, no solo para el del
    contrato de hoy: (w-h+1) del pasado mas (h+w) del pronostico son 2w+1."""
    serie = _serie()
    modelo = ChronosBolt(serie, w=w, h=h)
    # No lanza si la ventana mide 2w+1; lanza RuntimeError si no.
    modelo._etiqueta_de(300, np.zeros(h + w))


def test_sin_historia_suficiente_cuenta_y_responde_continuidad():
    """Las primeras w-h velas no tienen ventana completa. Se responde Continuidad y
    se lleva la cuenta, para que el guion de evidencia la reporte en vez de que el
    valor por omision quede escondido."""
    modelo = _modelo()
    assert modelo.sin_historia == 0
    assert modelo._etiqueta_de(0, np.zeros(H + W)) == int(Clase.CONTINUIDAD)
    assert modelo.sin_historia == 1


def test_rechaza_una_serie_que_no_es_serie():
    with pytest.raises(TypeError, match="pd.Series"):
        ChronosBolt([1, 2, 3])


# --------------------------------------------------------------- con chronos

@necesita_chronos
def test_no_hay_fuga_perturbar_el_futuro_no_mueve_el_presente():
    """La prueba que justifica este archivo.

    Para etiquetar t+h el modelo usa cierres hasta t y pronostica el resto. Si por
    un error de indices leyera un cierre posterior a t, las metricas saldrian
    excelentes y falsas, que es el fallo mas caro de este tipo de proyecto y el que
    el propio issue avisa.

    Se comprueba como se comprueban las caracteristicas de M2: se perturba todo lo
    que viene despues del corte y se exige que lo anterior no se mueva.
    """
    serie = _serie(n=600)
    corte = 500
    instantes = serie.index[corte - 20 : corte + 1]
    X = pd.DataFrame(index=instantes)

    limpia = ChronosBolt(serie, w=W, h=H).entrenar(X, pd.Series(dtype="Int64"))
    esperado = limpia.predecir(X)

    perturbada = serie.copy()
    perturbada.iloc[corte + 1 :] = perturbada.iloc[corte + 1 :] * 3.7 + 1000.0
    sucia = ChronosBolt(perturbada, w=W, h=H).entrenar(X, pd.Series(dtype="Int64"))

    assert np.array_equal(esperado, sucia.predecir(X)), (
        "perturbar los cierres posteriores al corte cambio la prediccion de instantes "
        "anteriores: hay fuga de informacion futura."
    )


@necesita_chronos
def test_devuelve_un_codigo_de_clase_por_fila():
    serie = _serie(n=560)
    X = pd.DataFrame(index=serie.index[520:540])
    modelo = ChronosBolt(serie, w=W, h=H).entrenar(X, pd.Series(dtype="Int64"))

    predicciones = modelo.predecir(X)
    assert len(predicciones) == len(X)
    assert predicciones.dtype.kind in "iu"
    assert set(np.unique(predicciones)) <= {int(c) for c in Clase}


@necesita_chronos
def test_es_reproducible():
    """RF-M4. Chronos-Bolt es determinista --predice los nueve cuantiles de una
    pasada, sin muestreo--, asi que dos corridas tienen que coincidir exactamente."""
    serie = _serie(n=560)
    X = pd.DataFrame(index=serie.index[520:535])

    primero = ChronosBolt(serie, w=W, h=H).entrenar(X, pd.Series(dtype="Int64"))
    segundo = ChronosBolt(serie, w=W, h=H).entrenar(X, pd.Series(dtype="Int64"))

    assert np.array_equal(primero.predecir(X), segundo.predecir(X))


@necesita_chronos
def test_el_tamano_de_lote_no_cambia_el_resultado():
    """Agrupar de a 64 o de a 7 es una decision de rendimiento. Si cambiara las
    etiquetas, seria que algo depende del vecino de lote y no del instante."""
    serie = _serie(n=560)
    X = pd.DataFrame(index=serie.index[520:540])

    grande = ChronosBolt(serie, w=W, h=H, lote=64).entrenar(X, pd.Series(dtype="Int64"))
    chico = ChronosBolt(serie, w=W, h=H, lote=7).entrenar(X, pd.Series(dtype="Int64"))

    assert np.array_equal(grande.predecir(X), chico.predecir(X))


def test_el_cuantil_por_defecto_es_la_mediana():
    """La mediana es lo neutral. Si el defecto cambiara sin querer, todas las
    trayectorias se inclinarian y con ellas las etiquetas."""
    modelo = _modelo()
    assert modelo.cuantil == 0.5
    assert modelo._indice_cuantil == 4


@pytest.mark.parametrize("cuantil", [0.1, 0.4, 0.5, 0.9])
def test_los_cuantiles_validos_mapean_a_su_indice(cuantil):
    """El modelo devuelve nueve cuantiles de 0,1 a 0,9; el indice tiene que
    corresponder o se estaria leyendo otro."""
    modelo = _modelo(cuantil=cuantil)
    assert modelo._indice_cuantil == round(cuantil * 10) - 1


def test_un_cuantil_que_el_modelo_no_devuelve_se_rechaza():
    """Pedir 0,95 devolveria en silencio el cuantil de al lado si no se comprueba, y
    la busqueda de hiperparametros creeria estar midiendo algo que no midio."""
    with pytest.raises(ValueError, match="cuantil debe ser uno de"):
        _modelo(cuantil=0.95)
