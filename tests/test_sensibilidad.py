"""Pruebas de la medicion de sensibilidad al ruido (S1-M2-01).

Lo que se prueba no es "que corra": es que el emparejamiento entre giros
verdaderos y detectados cuente lo que decimos que cuenta. Si esa contabilidad
estuviera mal, el numero que se lleva al informe seria falso y las pruebas no se
enterarian, porque el barrido correria igual de bien.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from contracts.labeling import Clase, etiquetar
from src.sintetico.generador import serie_zigzag
from src.sintetico.sensibilidad import (
    comparar_giros,
    medir_sensibilidad,
    punto_de_quiebre,
    resumir,
)

MAXIMO = int(Clase.MAXIMO)
MINIMO = int(Clase.MINIMO)


def test_sin_ruido_el_etiquetador_encuentra_todos_los_vertices():
    """Es la propiedad que hace valida toda la medicion. Si fallara, el punto de
    quiebre que reportemos no seria del ruido: seria del etiquetador."""
    tabla = medir_sensibilidad(niveles_ruido=[0.0], semillas=range(5), n=400)
    assert (tabla["recall_exacto"] == 1.0).all()
    assert (tabla["falsos_positivos"] == 0).all()


def test_deteccion_perfecta_se_cuenta_como_perfecta():
    verdaderos = {10: MAXIMO, 30: MINIMO, 50: MAXIMO}
    resultado = comparar_giros(verdaderos, dict(verdaderos), tolerancia=0)
    assert resultado["aciertos"] == 3
    assert resultado["falsos_positivos"] == 0
    assert resultado["no_detectados"] == 0


def test_un_giro_corrido_una_vela_falla_en_exacto_y_acierta_con_tolerancia():
    """La distincion entera del analisis: perder un giro no es lo mismo que
    correrlo una vela, y una sola metrica no puede separar las dos cosas."""
    verdaderos = {10: MAXIMO}
    detectados = {11: MAXIMO}

    exacto = comparar_giros(verdaderos, detectados, tolerancia=0)
    assert exacto["aciertos"] == 0
    assert exacto["no_detectados"] == 1
    assert exacto["falsos_positivos"] == 1

    tolerante = comparar_giros(verdaderos, detectados, tolerancia=1)
    assert tolerante["aciertos"] == 1
    assert tolerante["falsos_positivos"] == 0


def test_confundir_maximo_con_minimo_no_cuenta_como_acierto():
    """Es el peor error del problema: el sistema anunciaria lo contrario de lo que
    pasa. Contarlo como deteccion parcial seria maquillar el resultado."""
    resultado = comparar_giros({10: MAXIMO}, {10: MINIMO}, tolerancia=1)
    assert resultado["aciertos"] == 0
    assert resultado["invertidos"] == 1
    assert resultado["falsos_positivos"] == 0


def test_un_solo_detectado_no_puede_justificar_dos_verdaderos():
    """Sin emparejamiento uno a uno, con tolerancia alta un acierto taparia varios
    fallos y el recall quedaria inflado."""
    resultado = comparar_giros({10: MAXIMO, 11: MAXIMO}, {10: MAXIMO}, tolerancia=1)
    assert resultado["aciertos"] == 1
    assert resultado["no_detectados"] == 1


def test_giro_detectado_donde_no_habia_ninguno_es_falso_positivo():
    resultado = comparar_giros({10: MAXIMO}, {10: MAXIMO, 200: MINIMO}, tolerancia=1)
    assert resultado["aciertos"] == 1
    assert resultado["falsos_positivos"] == 1


def test_la_serie_limpia_y_la_ruidosa_comparten_los_mismos_vertices():
    """De esto depende que la verdad de referencia se pueda tomar de la limpia y la
    deteccion de la ruidosa. Si el ruido moviera los vertices, la comparacion
    estaria midiendo dos series distintas."""
    limpia, giros_limpia = serie_zigzag(n=500, w=7, semilla=3, ruido=0.0)
    ruidosa, giros_ruidosa = serie_zigzag(n=500, w=7, semilla=3, ruido=2.0)
    assert np.array_equal(giros_limpia, giros_ruidosa)
    assert not np.allclose(limpia.to_numpy(), ruidosa.to_numpy())


def test_mas_ruido_nunca_mejora_la_deteccion():
    """Monotonia. No es una obviedad: si saliera al reves, habria un error en el
    emparejamiento y el resultado del informe seria justo el contrario."""
    resumen = resumir(medir_sensibilidad(niveles_ruido=[0.0, 1.0, 4.0], semillas=range(6), n=500))
    recalls = resumen.sort_values("ruido")["recall_exacto"].to_numpy()
    assert np.all(np.diff(recalls) <= 1e-9)
    falsos = resumen.sort_values("ruido")["falsos_positivos"].to_numpy()
    assert falsos[0] == 0
    assert falsos[-1] > 0


def test_el_punto_de_quiebre_no_inventa_valores_fuera_del_barrido():
    """Si el barrido nunca degrada, el punto de quiebre tiene que ser NaN y no el
    ultimo nivel probado. Reportar un numero que no se midio es exactamente lo que
    las reglas del proyecto prohiben."""
    resumen = resumir(medir_sensibilidad(niveles_ruido=[0.0, 0.1], semillas=range(3), n=400))
    quiebre = punto_de_quiebre(resumen)
    assert np.isnan(quiebre["ruido_donde_cae_el_recall"])
    assert np.isnan(quiebre["ruido_del_primer_falso_positivo"])
    assert quiebre["ruido_maximo_probado"] == 0.1


def test_el_etiquetador_no_marca_giros_en_los_bordes():
    """Los primeros y ultimos w instantes no tienen ventana completa. Si el
    etiquetador los marcara, el barrido contaria falsos positivos que en realidad
    son etiquetas indefinidas."""
    serie, _ = serie_zigzag(n=300, w=7, semilla=1, ruido=1.0)
    etiquetas = etiquetar(serie, 7)
    assert etiquetas.iloc[:7].isna().all()
    assert etiquetas.iloc[-7:].isna().all()


def test_el_resumen_conserva_los_totales_del_barrido():
    """El resumen agrega; si perdiera o duplicara giros, la tabla del documento no
    cuadraria con los datos crudos y nadie lo notaria."""
    crudo = medir_sensibilidad(niveles_ruido=[0.0, 1.0], semillas=range(4), n=400)
    resumen = resumir(crudo)
    esperado = crudo.groupby("ruido")["verdaderos"].sum().reset_index()
    assert pd.Series(resumen["giros_verdaderos"].to_numpy()).equals(
        pd.Series(esperado["verdaderos"].to_numpy())
    )
