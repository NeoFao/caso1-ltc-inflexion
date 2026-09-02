"""Pruebas de los modelos y del arnes que los evalua.

Todo corre sin red y sin tocar data/: los paneles y las series salen de
src/sintetico/generador.py. Un fallo aqui significa siempre "alguien rompio algo"
y nunca "no habia datos".

Los bosques se instancian con pocos arboles a proposito: estas pruebas verifican
el cableado y los contratos, no la calidad del modelo.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from contracts.labeling import Clase, etiquetar, objetivo
from contracts.metrics import f1_macro
from contracts.splits import particionar
from src.evaluacion.arnes import evaluar_modelo, guardar_resultado
from src.features.base import construir
from src.modelos.base import (
    BaselineAleatorio,
    BaselineMayoritario,
    BaselineTrivial,
    Modelo,
)
from src.modelos.clasico import BosqueAleatorio
from src.modelos.experimento import (
    columnas_de_rezago,
    columnas_en_nivel_de_precio,
    detecta_mejor_que_azar,
)
from src.sintetico.generador import panel_correlacionado, serie_zigzag

ARBOLES_DE_PRUEBA = 20


def _caso_separable(n: int = 400, w: int = 5, h: int = 3):
    """Un problema donde la respuesta esta en una columna, mas una de ruido.

    Separable por construccion, asi que una prueba sobre el no puede ser
    intermitente: si falla, lo que esta roto es el cableado del modelo.
    """
    serie, _ = serie_zigzag(n=n, w=w)
    y = objetivo(etiquetar(serie, w), h)
    pista = y.fillna(Clase.CONTINUIDAD).astype("int64").to_numpy()
    generador = np.random.default_rng(0)
    X = pd.DataFrame(
        {"pista": pista.astype(float), "ruido": generador.normal(size=n)},
        index=serie.index,
    )
    return X, y


def _panel_de_prueba(n: int = 600):
    panel = panel_correlacionado(n=n, semilla=0)
    return panel, construir(panel)


def test_cumple_la_interfaz_modelo():
    """La interfaz es lo que permite que el arnes y la aplicacion de M1 no sepan que
    modelo tienen enfrente (RF-M3). Si entrenar() no devuelve self, se rompe el
    encadenamiento que documenta guias/isaac.md."""
    X, y = _caso_separable()
    modelo = BosqueAleatorio(n_arboles=ARBOLES_DE_PRUEBA)

    assert isinstance(modelo, Modelo)
    assert isinstance(modelo.nombre, str) and modelo.nombre
    assert modelo.entrenar(X, y.fillna(Clase.CONTINUIDAD)) is modelo


@pytest.mark.parametrize(
    "constructor",
    [BaselineMayoritario, BaselineAleatorio, BosqueAleatorio],
)
def test_predecir_antes_de_entrenar_falla_con_mensaje_claro(constructor):
    """Un modelo sin ajustar no debe responder. El mensaje es el mismo en los tres
    para que quien lo lea no tenga que averiguar de cual vino."""
    X, _ = _caso_separable(n=50)
    with pytest.raises(RuntimeError, match="entrenar"):
        constructor().predecir(X)


def test_tolera_nulos_en_las_caracteristicas():
    """La trampa mas cara de este modulo.

    evaluar_modelo filtra las filas por y.notna() pero no toca los nulos de X, y
    construir() arranca con ~30 filas nulas por las ventanas moviles. Un
    RandomForestClassifier pelado revienta ahi. La imputacion vive dentro del
    modelo justamente por esto, y esta prueba lo deja fijado.
    """
    X, y = _caso_separable()
    X = X.copy()
    X.iloc[:30, :] = np.nan

    modelo = BosqueAleatorio(n_arboles=ARBOLES_DE_PRUEBA)
    modelo.entrenar(X, y.fillna(Clase.CONTINUIDAD))

    predicciones = modelo.predecir(X)
    assert len(predicciones) == len(X)


def test_los_infinitos_no_tumban_el_ajuste():
    """SimpleImputer trata los nulos pero ignora los +-inf, y check_array aborta
    con "Input contains infinity". Un pct_change sobre un precio cero los produce."""
    X, y = _caso_separable()
    X = X.copy()
    X.iloc[5, 0] = np.inf
    X.iloc[6, 0] = -np.inf

    modelo = BosqueAleatorio(n_arboles=ARBOLES_DE_PRUEBA).entrenar(
        X, y.fillna(Clase.CONTINUIDAD)
    )
    assert len(modelo.predecir(X)) == len(X)


def test_predice_un_codigo_de_clase_valido_por_fila():
    """contracts.metrics._limpiar lanza si las longitudes difieren y castea a int.
    Un array de flotantes, de objetos, o con una fila de menos, corrompe todas las
    metricas aguas abajo."""
    X, y = _caso_separable()
    modelo = BosqueAleatorio(n_arboles=ARBOLES_DE_PRUEBA).entrenar(
        X, y.fillna(Clase.CONTINUIDAD)
    )

    predicciones = modelo.predecir(X)
    assert len(predicciones) == len(X)
    assert predicciones.dtype.kind in "iu"
    assert set(np.unique(predicciones)) <= {int(c) for c in Clase}


def test_aprende_una_senal_separable():
    """No mide calidad: mide que entrenar() y predecir() esten de verdad conectados.
    La respuesta esta en una columna, asi que un F1 bajo significa que algo del
    cableado -- dtypes, orden de clases, la tuberia -- esta mal."""
    X, y = _caso_separable()
    etiquetas = y.fillna(Clase.CONTINUIDAD)

    modelo = BosqueAleatorio(n_arboles=ARBOLES_DE_PRUEBA).entrenar(X, etiquetas)
    assert f1_macro(etiquetas, modelo.predecir(X)) > 0.9


def test_es_reproducible_con_la_misma_semilla():
    """RF-M4 y RNF-2: cualquier numero del informe se regenera con un comando.
    Se afirma solo la igualdad; que otra semilla difiera no es algo que debamos
    garantizar."""
    X, y = _caso_separable()
    etiquetas = y.fillna(Clase.CONTINUIDAD)

    primero = BosqueAleatorio(n_arboles=ARBOLES_DE_PRUEBA, semilla=7).entrenar(X, etiquetas)
    segundo = BosqueAleatorio(n_arboles=ARBOLES_DE_PRUEBA, semilla=7).entrenar(X, etiquetas)

    assert np.array_equal(primero.predecir(X), segundo.predecir(X))


def test_excluir_se_aplica_igual_al_entrenar_y_al_predecir():
    """Si el filtro de columnas se aplicara solo al ajustar, predecir recibiria otras
    variables y sklearn fallaria o, peor, reordenaria en silencio. La variante sin
    precios en nivel depende de que esto sea cierto."""
    X, y = _caso_separable()
    etiquetas = y.fillna(Clase.CONTINUIDAD)

    modelo = BosqueAleatorio(n_arboles=ARBOLES_DE_PRUEBA, excluir=("ruido",)).entrenar(
        X, etiquetas
    )
    assert list(modelo.importancias().index) == ["pista"]

    ensuciado = X.copy()
    ensuciado["ruido"] = 1e6
    assert np.array_equal(modelo.predecir(X), modelo.predecir(ensuciado))


def test_el_ayudante_distingue_niveles_de_relativos_en_las_dos_direcciones():
    """La razon por la que M3 dejo de filtrar por el fragmento "_rezago_".

    El fragmento era correcto mientras los rezagos salieran en nivel. Con la forma
    relativa sigue coincidiendo -- "_rezago_rel_1" lo contiene -- pero ya no
    significa lo mismo. Se fija en las dos direcciones porque una heuristica que
    solo se prueba en un sentido es la que no falla nunca y siempre miente.
    """
    X = pd.DataFrame(
        columns=[
            "LTC_cierre_rezago_1",
            "BTC_cierre_rezago_5",
            "LTC_cierre_rezago_rel_1",
            "BTC_cierre_rezago_rel_5",
            "LTC_retorno_3",
        ]
    )

    assert columnas_en_nivel_de_precio(X) == ["LTC_cierre_rezago_1", "BTC_cierre_rezago_5"]
    assert columnas_de_rezago(X) == [
        "LTC_cierre_rezago_1",
        "BTC_cierre_rezago_5",
        "LTC_cierre_rezago_rel_1",
        "BTC_cierre_rezago_rel_5",
    ]


def test_sin_rezagos_relativos_no_quedan_columnas_en_nivel():
    """Despues del PR #58 esta es la situacion normal, y es la que hacia que la
    variante `sin_niveles` pasara a no excluir nada bajo un nombre que decia que
    excluia algo."""
    X = pd.DataFrame(columns=["LTC_cierre_rezago_rel_1", "LTC_retorno_3"])

    assert columnas_en_nivel_de_precio(X) == []
    assert columnas_de_rezago(X) == ["LTC_cierre_rezago_rel_1"]


def test_excluir_exactas_no_se_lleva_columnas_con_el_mismo_prefijo():
    """El motivo por el que existe excluir_exactas.

    `excluir` compara por subcadena, asi que excluir "x_rezago_1" tambien se
    llevaria "x_rezago_10". Hoy los ordenes medidos son (1,2,3,5) y no se nota, pero
    el dia que M2 anada el orden 10 la variante mediria otra cosa sin fallar.
    """
    generador = np.random.default_rng(0)
    X = pd.DataFrame(
        {
            "x_rezago_1": generador.normal(size=60),
            "x_rezago_10": generador.normal(size=60),
            "senal": generador.normal(size=60),
        }
    )
    y = pd.Series([int(Clase.CONTINUIDAD)] * 30 + [int(Clase.MAXIMO)] * 30)

    exacto = BosqueAleatorio(
        n_arboles=ARBOLES_DE_PRUEBA, excluir_exactas=("x_rezago_1",)
    ).entrenar(X, y)
    assert set(exacto.importancias().index) == {"x_rezago_10", "senal"}

    # La forma por fragmento se lleva las dos: es el fallo que esto evita.
    fragmento = BosqueAleatorio(
        n_arboles=ARBOLES_DE_PRUEBA, excluir=("x_rezago_1",)
    ).entrenar(X, y)
    assert set(fragmento.importancias().index) == {"senal"}


def test_excluir_exactas_ignora_nombres_que_no_estan():
    """El ayudante de M2 devuelve lista vacia cuando no hay columnas en nivel, y
    despues del PR #58 ese es el caso normal. Excluir nada tiene que dejar el
    modelo igual que no excluir, no fallar."""
    X, y = _caso_separable()
    etiquetas = y.fillna(Clase.CONTINUIDAD)

    con = BosqueAleatorio(
        n_arboles=ARBOLES_DE_PRUEBA, excluir_exactas=("columna_que_no_existe",)
    ).entrenar(X, etiquetas)
    sin = BosqueAleatorio(n_arboles=ARBOLES_DE_PRUEBA).entrenar(X, etiquetas)

    assert np.array_equal(con.predecir(X), sin.predecir(X))


def test_predecir_sin_las_columnas_del_ajuste_falla_nombrandolas():
    """src/api/main.py llama predecir(serie.to_frame()) con una sola columna, algo
    que funciona con BaselineTrivial porque ignora X. El dia que M1 enchufe el
    bosque, conviene que el mensaje diga que falta y no un traceback de sklearn."""
    X, y = _caso_separable()
    modelo = BosqueAleatorio(n_arboles=ARBOLES_DE_PRUEBA).entrenar(
        X, y.fillna(Clase.CONTINUIDAD)
    )

    with pytest.raises(ValueError, match="faltan"):
        modelo.predecir(X[["ruido"]])


def test_las_columnas_repetidas_se_rechazan():
    """construir() arma con pd.concat(axis=1) y M2 todavia tiene que agregar
    familias. Con nombres repetidos, la seleccion devuelve mas columnas de las
    pedidas y las importancias dejan de significar algo."""
    X, y = _caso_separable()
    repetido = pd.concat([X, X[["pista"]]], axis=1)

    with pytest.raises(ValueError, match="repetidas"):
        BosqueAleatorio(n_arboles=ARBOLES_DE_PRUEBA).entrenar(
            repetido, y.fillna(Clase.CONTINUIDAD)
        )


def test_el_arnes_evalua_el_bosque_de_punta_a_punta():
    """El circuito exacto que corre src/modelos/experimento.py, sobre datos
    sinteticos. src/evaluacion/arnes.py no tenia ninguna prueba, y es el unico lugar
    donde se producen numeros comparables.

    No se afirma nada sobre precision_direccional: devuelve NaN cuando el bloque no
    tiene extremos reales, que es plausible en una validacion sintetica corta.
    """
    w, h = 5, 3
    panel, X = _panel_de_prueba()
    y = objetivo(etiquetar(panel["LTC_cierre"], w), h)
    particion = particionar(n=len(y), w=w, h=h)

    resultado = evaluar_modelo(
        BosqueAleatorio(n_arboles=ARBOLES_DE_PRUEBA), X, y, particion, conjunto="validacion"
    )

    assert resultado["n"] > 0
    assert 0.0 <= resultado["f1_macro"] <= 1.0
    assert resultado["modelo"] == "bosque_aleatorio"
    assert resultado["conjunto"] == "validacion"


def test_todos_los_modelos_producen_las_mismas_claves_en_el_mismo_orden():
    """guardar_resultado anade con header=False. Si un modelo devolviera otras
    claves, o las mismas en otro orden, sus valores se escribirian debajo del
    encabezado equivocado y el CSV quedaria bien formado y con los numeros mal."""
    w, h = 5, 3
    panel, X = _panel_de_prueba()
    y = objetivo(etiquetar(panel["LTC_cierre"], w), h)
    particion = particionar(n=len(y), w=w, h=h)

    claves = [
        list(evaluar_modelo(modelo, X, y, particion, conjunto="validacion"))
        for modelo in (BaselineTrivial(), BosqueAleatorio(n_arboles=ARBOLES_DE_PRUEBA))
    ]
    assert claves[0] == claves[1]


def test_guardar_resultado_no_desalinea_las_columnas(tmp_path):
    """Ejercita el camino de anadido: tres filas escritas una por una tienen que
    releerse como tres filas con sus nombres en la columna correcta."""
    ruta = tmp_path / "resultados.csv"
    for nombre in ("baseline_trivial", "baseline_mayoritario", "bosque_aleatorio"):
        guardar_resultado(
            {"n": 10, "f1_macro": 0.5, "modelo": nombre, "conjunto": "validacion"}, ruta=ruta
        )

    tabla = pd.read_csv(ruta)
    assert len(tabla) == 3
    assert tabla["modelo"].tolist() == [
        "baseline_trivial",
        "baseline_mayoritario",
        "bosque_aleatorio",
    ]


def test_no_detecta_si_solo_acierta_un_puñado_por_azar():
    """El caso exacto del issue #51: el bosque acierta 1 minimo de 94 y 5 maximos
    de 99, con F1 mayor que cero en las dos clases, pero el baseline aleatorio de
    esa misma corrida las acierta mejor. Con el umbral viejo (`> 0`) esto daba
    detectado; con el correcto, no."""
    bosque = {"f1_maximo": 0.0746, "f1_minimo": 0.0194}
    aleatorio = {"f1_maximo": 0.0518, "f1_minimo": 0.0538}
    assert detecta_mejor_que_azar(bosque, aleatorio) is False


def test_detecta_si_supera_al_azar_en_las_dos_clases_extremas():
    bosque = {"f1_maximo": 0.10, "f1_minimo": 0.10}
    aleatorio = {"f1_maximo": 0.05, "f1_minimo": 0.05}
    assert detecta_mejor_que_azar(bosque, aleatorio) is True


@pytest.mark.parametrize(
    ("bosque", "aleatorio"),
    [
        ({"f1_maximo": 0.10, "f1_minimo": 0.01}, {"f1_maximo": 0.05, "f1_minimo": 0.05}),
        ({"f1_maximo": 0.01, "f1_minimo": 0.10}, {"f1_maximo": 0.05, "f1_minimo": 0.05}),
    ],
)
def test_no_detecta_si_solo_supera_al_azar_en_una_clase(bosque, aleatorio):
    """Detectar 'ambos extremos' exige ganarle al azar en las dos, no en una."""
    assert detecta_mejor_que_azar(bosque, aleatorio) is False


def test_empatar_con_el_azar_no_cuenta_como_deteccion():
    """La desigualdad es estricta: empatar con el azar no es ganarle."""
    bosque = {"f1_maximo": 0.05, "f1_minimo": 0.05}
    aleatorio = {"f1_maximo": 0.05, "f1_minimo": 0.05}
    assert detecta_mejor_que_azar(bosque, aleatorio) is False


# ------------------------------------------- que --sin-variantes haga lo que dice


def _argumentos(**cambios):
    """Las banderas de experimento.py, con los defectos por omision."""
    from argparse import Namespace

    base = dict(
        semilla=0,
        n_arboles=300,
        sin_variantes=False,
        con_fundacional=False,
        con_avanzado=False,
    )
    base.update(cambios)
    return Namespace(**base)


def test_sin_variantes_deja_una_configuracion_por_familia():
    """La seccion 3 del protocolo dice que sobre la reserva no se evaluan variantes.

    Se comprueba con el avanzado incluido a proposito: la bandera se respetaba en el
    bosque y NO en el avanzado, asi que una prueba que solo mirara el bosque habria
    pasado mientras el defecto seguia ahi. `--con-avanzado` anadia
    `itransformer_solo_ltc` igual, y la corrida del sabado habria medido sobre el
    bloque de prueba una variante que el protocolo excluye -- gastandolo.
    """
    from src.modelos.experimento import armar_modelos

    panel = panel_correlacionado(n=300, semilla=0)
    argumentos = _argumentos(sin_variantes=True, con_avanzado=True)
    nombres = [
        m.nombre for m in armar_modelos(argumentos, panel, ["x_rezago_1"], "_r", 7, 1)
    ]

    prohibidas = [n for n in nombres if "solo_ltc" in n or "sin_pesos" in n or "sin_rezagos" in n]
    assert not prohibidas, (
        f"--sin-variantes dejo pasar {prohibidas}. Sobre el bloque de prueba eso es "
        "medir una variante que el protocolo excluye, y la reserva se gasta igual."
    )


def test_sin_la_bandera_las_variantes_siguen_estando():
    """El arreglo de arriba no puede llevarse por delante las variantes de validacion:
    son las que respondieron el #62 y las que el informe tiene que explicar."""
    from src.modelos.experimento import armar_modelos

    panel = panel_correlacionado(n=300, semilla=0)
    argumentos = _argumentos(con_avanzado=True)
    nombres = [
        m.nombre for m in armar_modelos(argumentos, panel, ["x_rezago_1"], "_r", 7, 1)
    ]

    assert nombres == [
        "baseline_trivial",
        "baseline_mayoritario",
        "baseline_aleatorio",
        "bosque_aleatorio_r",
        "bosque_aleatorio_sin_rezagos",
        "bosque_aleatorio_sin_pesos_r",
        "itransformer",
        "itransformer_solo_ltc",
    ], (
        "cambio la composicion o el ORDEN de la corrida. El orden importa dos veces: "
        "resultados.csv se anade sin sobrescribir, y sobre `prueba` el primer modelo "
        "de la lista es el que deja la constancia en el pestillo de la reserva."
    )


def test_la_evidencia_de_prueba_no_pisa_la_de_validacion():
    """La corrida del sabado no puede escribir encima de la evidencia entregada.

    El nombre del JSON llevaba intervalo, w, h y la forma de los rezagos --por la
    razon que el propio codigo explica: dos configuraciones con el mismo nombre se
    sobrescriben-- y el CONJUNTO se habia quedado afuera de esa lista. Es la unica
    de las cinco que no se puede volver a medir: pasa despues de gastar la reserva.
    """
    from src.modelos.experimento import ruta_evidencia

    base = "modelo-clasico-4h-w7-h1-rezagos-relativos"
    validacion = ruta_evidencia(base, "validacion")
    prueba = ruta_evidencia(base, "prueba")

    assert validacion != prueba, (
        "la corrida sobre prueba escribiria encima de la evidencia de validacion. "
        "El archivo conserva nombre y forma y le cambian todos los numeros, asi que "
        "la entrega quedaria citando cifras del bloque de prueba sin que nada falle."
    )


def test_validacion_conserva_el_nombre_que_citan_los_entregables():
    """La otra mitad: arreglar lo de arriba no puede renombrar lo ya citado.

    Estos dos archivos los citan `docs/06`, `docs/07` y dos documentos de la Semana 2
    ya entregada. Anadirles una marca romperia esas citas -- que es exactamente el
    error que la D13 existe para impedir, y uno que ya cometi una vez renombrando
    una evidencia sin buscar quien la citaba.
    """
    from src.modelos.experimento import ruta_evidencia

    assert (
        ruta_evidencia("modelo-clasico-4h-w7-h1-rezagos-relativos", "validacion").name
        == "modelo-clasico-4h-w7-h1-rezagos-relativos.json"
    )
    assert (
        ruta_evidencia("m3-modelos-profundos-4h-w7-h1", "validacion").name
        == "m3-modelos-profundos-4h-w7-h1.json"
    )
