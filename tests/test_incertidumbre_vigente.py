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
