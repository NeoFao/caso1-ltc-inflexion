"""Pruebas del backend (M0).

`src/api/` no tenia ninguna, y por eso paso inadvertido durante semanas que la
serializacion truncaba la marca de tiempo a la fecha. Con velas de 4 horas hay seis
por dia, asi que las seis salian con la misma etiqueta; el grafico, que necesita
tiempos estrictamente ascendentes, descartaba cinco de cada seis y con ellas sus
marcadores. Medido sobre LTC cuando se encontro: 1 027 de los 1 217 giros no
llegaban a dibujarse.

Lo que se fija aqui es la propiedad, no ese numero: que la serializacion no pierda
observaciones ni las vuelva indistinguibles entre si. El conteo concreto depende del
panel y cambiaria con otro; la propiedad no.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from contracts.labeling import etiquetar
from src.api.main import _serializar


def _serie_de_4h(n: int = 48) -> pd.Series:
    """Una serie con la granularidad real del proyecto: seis velas por dia."""
    indice = pd.date_range("2026-01-01", periods=n, freq="4h", tz="UTC")
    valores = 100 + np.sin(np.arange(n) / 3.0) * 5
    return pd.Series(valores, index=indice, name="LTC_cierre")


@pytest.fixture
def serializada() -> list[dict]:
    serie = _serie_de_4h()
    etiquetas = etiquetar(serie, w=2)
    predichas = pd.Series(3, index=serie.index)
    return _serializar(serie, etiquetas, predichas)


def test_cada_vela_tiene_una_marca_de_tiempo_distinta(serializada):
    """La que fallaba.

    Si dos velas comparten `fecha`, cualquier consumidor que ordene por tiempo o
    exija tiempos crecientes tiene que descartar una de las dos, y lo hara en
    silencio. Con velas de 4 horas eso son cinco de cada seis.
    """
    fechas = [v["fecha"] for v in serializada]
    repetidas = len(fechas) - len(set(fechas))
    assert repetidas == 0, (
        f"{repetidas} velas comparten marca de tiempo con otra. Ejemplo: "
        f"{sorted(f for f in fechas if fechas.count(f) > 1)[:4]}"
    )


def test_no_se_pierde_ninguna_observacion(serializada):
    """Serializar no es filtrar: salen tantas velas como entraron."""
    assert len(serializada) == len(_serie_de_4h())


def test_las_marcas_de_tiempo_son_estrictamente_crecientes(serializada):
    """Es lo que exige la libreria de graficos, y lo que hace innecesario
    deduplicar del lado del frontend."""
    tiempos = [pd.Timestamp(v["fecha"]) for v in serializada]
    # strict=False a proposito: los dos tramos tienen largos distintos por
    # construccion, es un recorrido por pares consecutivos.
    assert all(b > a for a, b in zip(tiempos, tiempos[1:], strict=False))


def test_la_marca_conserva_la_hora_y_no_solo_el_dia(serializada):
    """Con granularidad intradiaria, la hora es parte del dato y no un adorno."""
    horas = {pd.Timestamp(v["fecha"]).hour for v in serializada}
    assert len(horas) > 1, (
        "todas las velas caen a la misma hora: la marca de tiempo se esta truncando"
    )


def test_los_giros_sobreviven_a_la_serializacion():
    """Ningun extremo etiquetado desaparece al serializar.

    Es la consecuencia que importaba: el proposito de la aplicacion es mostrar
    puntos de inflexion, asi que perderlos en el transporte vacia la vista aunque
    las metricas sigan bien.
    """
    serie = _serie_de_4h()
    etiquetas = etiquetar(serie, w=2)
    predichas = pd.Series(3, index=serie.index)
    esperados = int(etiquetas.isin([1, 2]).sum())
    assert esperados > 0, "la serie de prueba no produce giros; revisar el generador"

    salida = _serializar(serie, etiquetas, predichas)
    obtenidos = sum(1 for v in salida if v["etiqueta"] in (1, 2))
    assert obtenidos == esperados
