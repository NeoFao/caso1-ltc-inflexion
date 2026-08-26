"""Pruebas de deteccion sobre datos donde la respuesta correcta la fijamos nosotros.

Por que existen
---------------
Todo lo que medimos hasta ahora responde "cuanto acierta el modelo sobre Litecoin".
Ninguna de esas mediciones responde la pregunta previa: **si el circuito completo es
capaz de detectar un giro cuando el giro esta ahi y no hay ambiguedad**.

Son cosas distintas. Un F1 macro de 0,39 sobre datos reales puede convivir con un
canal roto en algun punto -- una caracteristica mal alineada, un desplazamiento de
un indice, una etiqueta que llega corrida -- y el numero no lo delataria, porque
sobre datos reales no sabemos cual era la respuesta correcta.

Aqui si la sabemos, porque la construimos.

Las tres pruebas que pide el enunciado
--------------------------------------
1. **Sintetico.** Serie en zigzag con vertices que ponemos nosotros. El piso
   absoluto: si el circuito no encuentra estos giros, cualquier cifra sobre datos
   reales es ruido con formato.

2. **Entrenamiento.** El modelo sobre el bloque que ya vio. No mide generalizacion
   --para eso esta validacion-- sino que el modelo aprendio algo: si no detecta
   sobre datos que memorizo, no hay nada que generalizar.

3. **Tiempo real.** BLOQUEADA. Depende de que definamos que significa "tiempo real"
   con una etiqueta que no se conoce hasta w velas despues, y eso esta en la
   consulta 3 al profesor, sin responder. Se declara como pendiente en vez de
   inventar una definicion.

El criterio se fija antes de medir
----------------------------------
Cada prueba declara que resultado la da por superada ANTES de correrla, y el guion
lo compara solo. Si el criterio se decidiera despues, la prueba no probaria nada.

Punto de entrada:  uv run python -m scripts.pruebas_deteccion
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from contracts.config import GRANULARIDAD, HORIZONTE_H, VENTANA_W  # noqa: E402
from contracts.labeling import Clase, etiquetar, objetivo  # noqa: E402
from contracts.metrics import evaluar  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from contracts.splits import particionar  # noqa: E402
from src.features.base import construir  # noqa: E402
from src.modelos.base import BaselineAleatorio  # noqa: E402
from src.modelos.clasico import BosqueAleatorio  # noqa: E402
from src.modelos.experimento import detecta_mejor_que_azar  # noqa: E402
from src.sintetico.generador import etiquetas_esperadas, serie_zigzag  # noqa: E402

RUTA = RAIZ / "docs" / "evidencias" / "pruebas-deteccion.json"

#: Cuantos giros de los plantados tiene que recuperar el etiquetador para dar por
#: bueno el canal. Se exige TODOS: la serie se construye sin ruido y con los
#: vertices separados mas de w+1, asi que cada uno es un extremo estricto de su
#: ventana. Fallar uno solo significa que algo esta corrido, no que sea dificil.
RECUPERACION_EXIGIDA = 1.0


def prueba_sintetica(n: int = 3000, semilla: int = 0) -> dict:
    """El piso: recuperar giros que pusimos nosotros, sin ruido.

    Se prueba en dos escalones y conviene no mezclarlos, porque fallan por motivos
    distintos:

    - El **etiquetador** tiene que marcar como giro cada vertice que plantamos. Si
      esto falla, el problema esta en `etiquetar()` o en los indices, y ningun
      modelo lo puede arreglar.
    - El **modelo** tiene que detectar esos giros mejor que el azar. Si el primer
      escalon pasa y este no, el problema esta en las caracteristicas o en el
      aprendizaje, no en el canal.
    """
    serie, giros = serie_zigzag(n=n, w=VENTANA_W, semilla=semilla, ruido=0.0)
    valores = serie.to_numpy()

    esperadas = etiquetas_esperadas(n, giros, valores, VENTANA_W)
    obtenidas = etiquetar(serie, VENTANA_W)

    # Se compara POR POSICION y no por indice: la verdad construida sale de los
    # vertices y lleva un indice propio, mientras que la del etiquetador hereda el de
    # la serie. Alinear por indice aqui compararia dos cosas por su etiqueta en vez de
    # por su lugar, que es lo que importa.
    esperadas_v = esperadas.to_numpy()
    obtenidas_v = obtenidas.to_numpy()
    es_giro_esperado = np.isin(esperadas_v, [int(Clase.MAXIMO), int(Clase.MINIMO)])
    n_plantados = int(es_giro_esperado.sum())
    coinciden = int((obtenidas_v[es_giro_esperado] == esperadas_v[es_giro_esperado]).sum())
    recuperacion = coinciden / n_plantados if n_plantados else 0.0

    return {
        "que_prueba": (
            "Que el etiquetador recupera los vertices que plantamos, sin ruido y con "
            "separacion mayor que w+1, de modo que cada uno es un extremo estricto."
        ),
        "criterio_preregistrado": (
            f"Recuperacion de {RECUPERACION_EXIGIDA:.0%}. Con la serie construida asi, "
            "fallar uno solo significa que algo esta corrido."
        ),
        "n_observaciones": n,
        "giros_plantados": n_plantados,
        "giros_recuperados": coinciden,
        "recuperacion": round(recuperacion, 6),
        "supera": bool(recuperacion >= RECUPERACION_EXIGIDA),
    }


def _panel_desde_serie(serie: pd.Series) -> pd.DataFrame:
    """Envuelve una serie en la forma de panel que espera `construir()`.

    Los cinco activos de apoyo se rellenan con la misma serie desplazada: no
    interesa su contenido, interesa que el panel cumpla el contrato para poder
    pasar la serie sintetica por EL MISMO canal que los datos reales. Usar un canal
    distinto para la prueba de deteccion probaria el canal de la prueba.
    """
    columnas = {}
    for i, activo in enumerate(("LTC", "BTC", "ETH", "SOL", "XRP", "ADA")):
        desplazada = serie.shift(i).bfill()
        campos = (("apertura", 0.999), ("maximo", 1.002), ("minimo", 0.998), ("cierre", 1.0))
        for campo, factor in campos:
            columnas[f"{activo}_{campo}"] = desplazada * factor
        columnas[f"{activo}_volumen"] = pd.Series(1_000.0, index=serie.index)
    return pd.DataFrame(columnas, index=serie.index)


def prueba_modelo_sobre_sintetico(n: int = 3000, semilla: int = 0) -> dict:
    """El modelo completo sobre la serie construida, por el canal de siempre."""
    indice = pd.date_range("2020-01-01", periods=n, freq=GRANULARIDAD, tz="UTC", name="fecha")
    serie, _ = serie_zigzag(n=n, w=VENTANA_W, semilla=semilla, ruido=0.0)
    serie.index = indice

    panel = _panel_desde_serie(serie)
    X = construir(panel)
    y = objetivo(etiquetar(cierre(panel, "LTC"), VENTANA_W), HORIZONTE_H)
    particion = particionar(n=len(y), w=VENTANA_W, h=HORIZONTE_H)

    entrenables = particion.entrenamiento & y.notna().to_numpy()
    evaluables = particion.validacion & y.notna().to_numpy()

    bosque = BosqueAleatorio(semilla=semilla)
    bosque.entrenar(X[entrenables], y[entrenables].astype(int).to_numpy())
    azar = BaselineAleatorio(semilla=semilla)
    azar.entrenar(X[entrenables], y[entrenables].astype(int).to_numpy())

    verdad = y[evaluables].astype(int).to_numpy()
    r_bosque = evaluar(verdad, np.asarray(bosque.predecir(X[evaluables]), dtype=int))
    r_azar = evaluar(verdad, np.asarray(azar.predecir(X[evaluables]), dtype=int))

    detecta = detecta_mejor_que_azar(r_bosque, r_azar)
    return {
        "que_prueba": (
            "Que el circuito completo -- caracteristicas, particion, modelo -- detecta "
            "los giros de una serie construida, pasando por el mismo canal que los "
            "datos reales."
        ),
        "criterio_preregistrado": (
            "El bosque supera al baseline aleatorio en el F1 de LAS DOS clases "
            "extremas, con el guardarrail del issue #51: no basta con que sea > 0."
        ),
        "f1_macro_bosque": round(r_bosque["f1_macro"], 6),
        "f1_macro_azar": round(r_azar["f1_macro"], 6),
        "f1_maximo_bosque": round(r_bosque["f1_maximo"], 6),
        "f1_maximo_azar": round(r_azar["f1_maximo"], 6),
        "f1_minimo_bosque": round(r_bosque["f1_minimo"], 6),
        "f1_minimo_azar": round(r_azar["f1_minimo"], 6),
        "supera": bool(detecta),
    }


def prueba_sobre_entrenamiento() -> dict:
    """El modelo sobre el bloque que ya vio, con datos reales.

    No mide generalizacion. Mide que el modelo aprendio algo: un modelo que no
    detecta sobre datos que memorizo no tiene de donde generalizar, y el problema
    estaria antes del sobreajuste.
    """
    panel = pd.read_parquet(RAIZ / "data" / "processed" / f"panel_{GRANULARIDAD}_v1.parquet")
    X = construir(panel)
    y = objetivo(etiquetar(cierre(panel, "LTC"), VENTANA_W), HORIZONTE_H)
    particion = particionar(n=len(y), w=VENTANA_W, h=HORIZONTE_H)
    entrenables = particion.entrenamiento & y.notna().to_numpy()

    verdad = y[entrenables].astype(int).to_numpy()
    bosque = BosqueAleatorio(semilla=0)
    bosque.entrenar(X[entrenables], verdad)
    azar = BaselineAleatorio(semilla=0)
    azar.entrenar(X[entrenables], verdad)

    r_bosque = evaluar(verdad, np.asarray(bosque.predecir(X[entrenables]), dtype=int))
    r_azar = evaluar(verdad, np.asarray(azar.predecir(X[entrenables]), dtype=int))

    return {
        "que_prueba": "Que el modelo detecta sobre el bloque de entrenamiento, con datos reales.",
        "criterio_preregistrado": (
            "El bosque supera al baseline aleatorio en las dos clases extremas. Es un "
            "piso, no un logro: aqui el modelo ya vio las respuestas."
        ),
        "conjunto": "entrenamiento",
        "n": int(entrenables.sum()),
        "f1_macro_bosque": round(r_bosque["f1_macro"], 6),
        "f1_macro_azar": round(r_azar["f1_macro"], 6),
        "f1_maximo_bosque": round(r_bosque["f1_maximo"], 6),
        "f1_minimo_bosque": round(r_bosque["f1_minimo"], 6),
        "supera": bool(detecta_mejor_que_azar(r_bosque, r_azar)),
        "advertencia": (
            "Un resultado alto aqui NO es evidencia de que el modelo sirva: es lo "
            "esperable de un modelo que vio estas etiquetas. Lo informativo seria un "
            "resultado bajo, que indicaria que el problema esta antes del ajuste."
        ),
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    sintetica = prueba_sintetica()
    modelo_sintetico = prueba_modelo_sobre_sintetico()
    entrenamiento = prueba_sobre_entrenamiento()

    medido = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "parametros": {"intervalo": GRANULARIDAD, "w": VENTANA_W, "h": HORIZONTE_H},
        "1_sintetico_etiquetador": sintetica,
        "2_sintetico_modelo_completo": modelo_sintetico,
        "3_entrenamiento": entrenamiento,
        "4_tiempo_real": {
            "estado": "BLOQUEADA",
            "por_que": (
                "La etiqueta de un instante no se conoce hasta w velas despues, asi que "
                "'tiempo real' admite dos lecturas -- confirmacion tardia pero "
                "verificable, o anuncio en el momento -- y son dos productos distintos. "
                "Esta en la consulta 3 al profesor, sin responder."
            ),
            "que_falta": "La respuesta del profesor. No se inventa una definicion.",
        },
        "veredicto": {
            "las_tres_ejecutables_superan": bool(
                sintetica["supera"] and modelo_sintetico["supera"] and entrenamiento["supera"]
            ),
            "nota": (
                "Superar estas pruebas no dice que el modelo sirva sobre datos reales. "
                "Dice que si no sirviera, no seria porque el canal esta roto."
            ),
        },
    }

    RUTA.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")

    print("PRUEBAS DE DETECCION\n")
    print(f"1. Sintetico, etiquetador: {sintetica['giros_recuperados']}/"
          f"{sintetica['giros_plantados']} giros recuperados -> {sintetica['supera']}")
    print(f"2. Sintetico, modelo completo: F1 macro {modelo_sintetico['f1_macro_bosque']} "
          f"contra {modelo_sintetico['f1_macro_azar']} del azar -> {modelo_sintetico['supera']}")
    print(f"3. Entrenamiento: F1 macro {entrenamiento['f1_macro_bosque']} "
          f"contra {entrenamiento['f1_macro_azar']} del azar -> {entrenamiento['supera']}")
    print("4. Tiempo real: BLOQUEADA por la consulta 3 al profesor")
    print(f"\nEvidencia: {RUTA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
