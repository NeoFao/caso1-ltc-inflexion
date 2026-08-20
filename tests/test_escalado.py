"""Pruebas del escalado (S2-M2-01) y de la maquina de ablaciones.

La prueba que sostiene todo este archivo es una sola: que el escalador no vea datos
de validacion ni de prueba. No se comprueba leyendo el codigo —eso es buena fe—
sino perturbando esos bloques y exigiendo que los parametros aprendidos no se
muevan ni un decimal.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from contracts.config import ACTIVO_OBJETIVO
from contracts.schema import cierre, columna
from contracts.splits import particionar
from src.evaluacion.fuga import verificar_sin_fuga
from src.features.ablacion import conjuntos_estandar, es_de_activo_de_apoyo
from src.features.base import REZAGOS_MEDIDOS, construir, rezagos
from src.features.escalado import Escalador, diagnostico_desplazamiento, familia_de
from src.sintetico.generador import panel_correlacionado


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return panel_correlacionado(n=800, semilla=11)


@pytest.fixture(scope="module")
def caracteristicas(panel) -> pd.DataFrame:
    return construir(panel)


@pytest.fixture(scope="module")
def particion(panel):
    return particionar(len(panel), w=7, h=5)


# ---------------------------------------------------------------------------
# Lo que RF-F3 exige de verdad
# ---------------------------------------------------------------------------


def test_el_escalador_no_usa_datos_fuera_de_entrenamiento(caracteristicas, particion):
    """Es la prueba central del issue. Se perturban validacion y prueba de forma
    brutal; si el escalador los mirara, sus parametros cambiarian."""
    original = Escalador("robusto").ajustar(caracteristicas, particion.entrenamiento)

    contaminado = caracteristicas.copy()
    fuera = ~particion.entrenamiento
    contaminado.loc[fuera, :] = contaminado.loc[fuera, :] * 1000.0 + 5e4
    perturbado = Escalador("robusto").ajustar(contaminado, particion.entrenamiento)

    pd.testing.assert_series_equal(original.centro_, perturbado.centro_)
    pd.testing.assert_series_equal(original.escala_, perturbado.escala_)


def test_ajustar_exige_la_mascara_y_no_acepta_una_de_largo_distinto(caracteristicas):
    with pytest.raises(TypeError):
        Escalador().ajustar(caracteristicas)  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="elementos"):
        Escalador().ajustar(caracteristicas, np.ones(3, dtype=bool))


def test_transformar_antes_de_ajustar_es_un_error(caracteristicas):
    """Devolver los datos sin escalar en silencio seria peor: el modelo entrenaria
    con escalas mezcladas y nadie lo notaria."""
    with pytest.raises(RuntimeError, match="ajustar"):
        Escalador().transformar(caracteristicas)


def test_una_mascara_vacia_no_pasa_desapercibida(caracteristicas):
    with pytest.raises(ValueError, match="ninguna fila"):
        Escalador().ajustar(caracteristicas, np.zeros(len(caracteristicas), dtype=bool))


def test_el_escalado_centra_el_entrenamiento_y_no_el_resto(caracteristicas, particion):
    """La mediana de entrenamiento tiene que quedar en cero. La de prueba no: si
    tambien quedara centrada, el escalador la habria mirado."""
    escalado = Escalador("robusto").ajustar_y_transformar(
        caracteristicas, particion.entrenamiento
    )
    medianas_entrenamiento = escalado.loc[particion.entrenamiento].median()
    assert np.allclose(medianas_entrenamiento.dropna().to_numpy(), 0.0, atol=1e-9)


def test_una_columna_constante_no_produce_infinitos(particion):
    """Dividir entre una dispersion cero daria infinitos que reaparecen como NaN
    veinte pasos despues, sin rastro de donde salieron."""
    X = pd.DataFrame({"constante": np.ones(len(particion.entrenamiento)), "variable": np.arange(
        len(particion.entrenamiento), dtype=float
    )})
    escalador = Escalador("robusto").ajustar(X, particion.entrenamiento)
    assert "constante" in escalador.columnas_constantes_
    assert np.isfinite(escalador.transformar(X)["constante"].to_numpy()).all()


def test_los_parametros_quedan_documentados(caracteristicas, particion):
    """RF-F3 pide que la escala este documentada, no solo aplicada."""
    parametros = Escalador("robusto").ajustar(
        caracteristicas, particion.entrenamiento
    ).parametros()
    assert set(parametros.columns) == {"centro", "escala", "constante"}
    assert len(parametros) == caracteristicas.shape[1]


def test_metodo_desconocido_falla_al_construir():
    with pytest.raises(ValueError, match="metodo desconocido"):
        Escalador("minmax")


# ---------------------------------------------------------------------------
# Rezagos relativos
# ---------------------------------------------------------------------------


def test_el_rezago_relativo_es_el_rezago_dividido_entre_el_precio_actual(panel):
    tabla = rezagos(panel, ACTIVO_OBJETIVO, relativo=True)
    serie = cierre(panel, ACTIVO_OBJETIVO)
    for k in REZAGOS_MEDIDOS:
        esperado = serie.shift(k) / serie - 1
        obtenido = tabla[f"{ACTIVO_OBJETIVO}_cierre_rezago_rel_{k}"]
        assert np.allclose(obtenido.to_numpy(), esperado.to_numpy(), equal_nan=True)


def test_el_rezago_relativo_no_depende_del_nivel_de_precio(panel):
    """Duplicar todos los precios no puede cambiarlo. Es justo lo que le falta a la
    version en nivel y la razon por la que existe esta opcion."""
    doble = panel.copy()
    doble[columna(ACTIVO_OBJETIVO, "cierre")] = doble[columna(ACTIVO_OBJETIVO, "cierre")] * 2
    assert np.allclose(
        rezagos(panel, ACTIVO_OBJETIVO, relativo=True).to_numpy(),
        rezagos(doble, ACTIVO_OBJETIVO, relativo=True).to_numpy(),
        equal_nan=True,
    )


def test_construir_con_rezagos_relativos_tampoco_mira_al_futuro(panel):
    verificar_sin_fuga(lambda p: construir(p, rezagos_relativos=True), panel)


def test_las_dos_formas_producen_el_mismo_numero_de_columnas(panel):
    assert construir(panel).shape[1] == construir(panel, rezagos_relativos=True).shape[1]


def test_los_rezagos_en_nivel_se_salen_del_rango_y_los_relativos_no(panel, particion):
    """El resultado que justifica la opcion, como prueba y no como afirmacion.

    Se le mete una tendencia explicita a la serie porque esa es exactamente la
    condicion de la que habla la propiedad: si el precio de prueba se queda dentro
    del rango de entrenamiento, no hay nada que demostrar. El panel sintetico por
    defecto es un camino aleatorio sin deriva y no la cumple, asi que probar sobre
    el daria cero contra cero y pasaria sin medir nada.
    """
    from contracts.config import ACTIVOS

    tendencia = np.exp(np.linspace(0.0, 2.5, len(panel)))
    con_tendencia = panel.copy()
    for activo in ACTIVOS:
        con_tendencia[columna(activo, "cierre")] = (
            panel[columna(activo, "cierre")].to_numpy() * tendencia
        )

    def fuera_de_rango(relativo: bool) -> float:
        X = construir(con_tendencia, rezagos_relativos=relativo)
        escalado = Escalador("robusto").ajustar_y_transformar(X, particion.entrenamiento)
        tabla = diagnostico_desplazamiento(escalado, particion.entrenamiento, particion.prueba)
        return float(tabla.loc[tabla["familia"] == "rezagos", "fuera_de_rango_pct"].mean())

    en_nivel = fuera_de_rango(relativo=False)
    relativos = fuera_de_rango(relativo=True)

    assert en_nivel > 50.0, "la serie de prueba no tiene suficiente deriva para probar nada"
    assert relativos < 1.0
    assert relativos < en_nivel


# ---------------------------------------------------------------------------
# Ablaciones
# ---------------------------------------------------------------------------


def test_toda_columna_cae_en_una_familia_conocida(caracteristicas):
    """Una columna que caiga en 'otras' quedaria fuera de toda ablacion y su aporte
    nunca se mediria."""
    sin_clasificar = [c for c in caracteristicas.columns if familia_de(c) == "otras"]
    assert sin_clasificar == []


def test_solo_LTC_deja_fuera_las_columnas_de_los_activos_de_apoyo(caracteristicas):
    conjuntos = conjuntos_estandar(caracteristicas)
    assert all(not es_de_activo_de_apoyo(c) for c in conjuntos["solo_LTC"])
    assert len(conjuntos["solo_LTC"]) < len(conjuntos["completo"])


def test_la_correlacion_cruzada_cuenta_como_columna_multivariante():
    """Nombra a dos activos: sin los de apoyo no existiria. Clasificarla como propia
    de LTC haria que la ablacion de S4-M2-01 midiera de menos."""
    assert es_de_activo_de_apoyo("corr_LTC_BTC_30")
    assert es_de_activo_de_apoyo("BTC_cierre_rezago_1")
    assert not es_de_activo_de_apoyo("LTC_rsi_14")
    assert not es_de_activo_de_apoyo("LTC_cierre_rezago_1")


def test_cada_ablacion_quita_columnas_de_verdad(caracteristicas):
    conjuntos = conjuntos_estandar(caracteristicas)
    completo = len(conjuntos["completo"])
    for nombre, columnas in conjuntos.items():
        if nombre == "completo":
            continue
        assert len(columnas) < completo, f"el conjunto {nombre!r} no quita nada"
