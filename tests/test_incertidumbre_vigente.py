"""Pruebas del bootstrap remedido con la representacion vigente."""

from __future__ import annotations

import numpy as np
import pytest

from contracts.labeling import Clase
from src.features import incertidumbre_vigente as vigente


def _predicciones_falsas(valores: dict) -> dict:
    return {nombre: np.asarray(v, dtype=int) for nombre, v in valores.items()}


def test_los_controles_pueden_fallar():
    """Si el control no pudiera fallar, no avalaria ningun intervalo."""
    y = np.array([int(Clase.CONTINUIDAD)] * 10)
    predicciones = _predicciones_falsas(
        {
            "bosque_aleatorio_rezagos_en_nivel": [int(Clase.MAXIMO)] * 10,
            "bosque_aleatorio_rezagos_relativos": [int(Clase.MAXIMO)] * 10,
        }
    )
    with pytest.raises(AssertionError, match="No se publica nada"):
        vigente.verificar_controles(predicciones, y)


def test_el_mensaje_de_fallo_nombra_los_dos_modelos():
    y = np.array([int(Clase.CONTINUIDAD)] * 10)
    predicciones = _predicciones_falsas(
        {
            "bosque_aleatorio_rezagos_en_nivel": [int(Clase.MAXIMO)] * 10,
            "bosque_aleatorio_rezagos_relativos": [int(Clase.MAXIMO)] * 10,
        }
    )
    with pytest.raises(AssertionError) as error:
        vigente.verificar_controles(predicciones, y)
    assert "bosque_aleatorio_rezagos_en_nivel" in str(error.value)
    assert "bosque_aleatorio_rezagos_relativos" in str(error.value)


def test_los_controles_son_los_dos_numeros_ya_publicados():
    """Uno es de M3 y el otro lo obtuvieron M3 y M2 por separado."""
    assert vigente.CONTROLES["bosque_aleatorio_rezagos_en_nivel"] == 0.3443065490077563
    assert vigente.CONTROLES["bosque_aleatorio_rezagos_relativos"] == 0.390497720487045


def test_este_modulo_no_escribe_sobre_la_evidencia_entregada():
    """La D13: remedir produce evidencia nueva, no reescribe la entregada."""
    fuente = open(vigente.__file__, encoding="utf-8").read()
    assert '"m2-incertidumbre.json"' not in fuente
    assert "m2-incertidumbre-vigente-" in fuente


def test_las_dos_representaciones_comparten_las_filas_de_validacion():
    """Es lo que hace legitimo el remuestreo pareado entre las dos matrices."""
    matrices, y_entrena, y_valida, _ = vigente._matrices()
    _, relativo_valida = matrices["relativo"]
    _, nivel_valida = matrices["nivel"]
    assert relativo_valida.index.equals(nivel_valida.index)
    assert len(relativo_valida) == len(y_valida)


def test_las_dos_representaciones_no_son_la_misma_matriz():
    """Si lo fueran, la comparacion entre ambas no mediria nada."""
    matrices, _, _, _ = vigente._matrices()
    _, relativo_valida = matrices["relativo"]
    _, nivel_valida = matrices["nivel"]
    en_nivel = [c for c in nivel_valida.columns if "_rezago_" in c and "_rezago_rel_" not in c]
    assert en_nivel, "la matriz 'nivel' tendria que traer rezagos en nivel de precio"
    assert not [
        c for c in relativo_valida.columns if "_rezago_" in c and "_rezago_rel_" not in c
    ], "la matriz 'relativo' no puede traer ningun rezago en nivel"


def test_los_nombres_son_los_mismos_que_los_de_m3():
    """Un modelo, un nombre, en todo el repositorio.

    Se comprueba contra la evidencia de M3 y no contra una lista escrita aqui: una
    lista propia volveria a permitir que los dos lados se separen, que es el defecto
    que se esta arreglando.
    """
    import json
    from pathlib import Path

    esperados = set()
    for ruta in Path("docs/evidencias").glob("modelo-clasico-*-rezagos-*.json"):
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        esperados |= {r["modelo"] for r in datos["resultados"]}

    assert esperados, "no se encontro evidencia de M3 contra la cual comparar"
    for nombre in vigente.CONTROLES:
        assert nombre in esperados, (
            f"{nombre!r} no es un nombre que M3 use. Un mismo modelo con dos nombres "
            "hace incomparables los JSON entre si."
        )


def test_ningun_modulo_de_m2_inventa_un_nombre_de_modelo():
    """Los dos modulos de bootstrap tienen que usar la nomenclatura de M3.

    Recorre los literales `bosque_*` de ambos archivos y exige que cada uno exista en
    la evidencia de M3. Es la version general del arreglo: no basta con renombrar hoy,
    hace falta que inventar un nombre nuevo manana falle.
    """
    import json
    import re
    from pathlib import Path

    esperados = set()
    for ruta in Path("docs/evidencias").glob("modelo-clasico-*-rezagos-*.json"):
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        esperados |= {r["modelo"] for r in datos["resultados"]}
    assert esperados

    for modulo in ("incertidumbre.py", "incertidumbre_vigente.py"):
        fuente = Path("src/features") / modulo
        texto = fuente.read_text(encoding="utf-8")
        # Solo literales entre comillas: los nombres que terminan en el JSON.
        usados = set(re.findall(r'"(bosque_[a-z0-9_]+)"', texto))
        desconocidos = usados - esperados
        assert not desconocidos, (
            f"{modulo} usa nombres de modelo que M3 no usa: {sorted(desconocidos)}. "
            "Un mismo modelo con dos nombres hace incomparables los JSON entre si."
        )


def test_el_barrido_registra_las_seis_metricas_que_muestra_el_panel():
    """La fase 2 del #92 no se puede cerrar si el barrido mide menos de lo que se publica.

    El panel de la aplicacion muestra seis columnas y hasta el 01/09 el barrido de
    semillas guardaba solo el F1 macro. Publicar medias en las seis exigia medir las
    seis, asi que esto vigila que el conjunto no se encoja: si alguien quita una
    metrica del barrido, la media de esa columna deja de existir en silencio y el
    panel vuelve a publicar una corrida suelta sin que nada avise.

    Se compara contra el panel y no contra una lista escrita aqui, por la misma razon
    que `test_los_nombres_son_los_mismos_que_los_de_m3`: una lista propia se
    desincroniza sola.
    """
    import json
    from pathlib import Path

    panel = Path("app/public/datos/comparacion-modelos.json")
    evidencia = Path("docs/evidencias/m2-incertidumbre-vigente-4h-w7-h1.json")
    if not (panel.exists() and evidencia.exists()):
        pytest.skip("falta el panel de la aplicacion o la evidencia del barrido")

    fila = json.loads(panel.read_text(encoding="utf-8"))["modelos"][0]
    descriptivas = {"clave", "etiqueta", "papel", "corrida_individual", "rango_entre_semillas"}
    del_panel = {
        k
        for k, v in fila.items()
        if k not in descriptivas and isinstance(v, (int, float))
    }

    medidas = json.loads(evidencia.read_text(encoding="utf-8"))
    por_modelo = medidas["sensibilidad_a_la_semilla"]["metricas_por_modelo"]
    for modelo, metricas in por_modelo.items():
        faltan = del_panel - set(metricas)
        assert not faltan, (
            f"el barrido de semillas no mide {sorted(faltan)} para {modelo}, y el panel "
            "las publica. Sin la media de esas columnas, la fase 2 del #92 no se puede "
            "cerrar: el panel seguiria mostrando una corrida suelta en ellas."
        )
