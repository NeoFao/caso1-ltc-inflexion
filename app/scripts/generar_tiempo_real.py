"""El panel de Tiempo real, con las predicciones REALES del bosque y su confianza.

Por que existe
--------------
Hasta hoy el modo "Tiempo real" de la aplicacion servia `historico-LTC.json`, que lo
produce `scripts/exportar_estatico.py` con el **baseline trivial**. Ese baseline
responde siempre Continuidad, asi que sobre sus 1 200 velas la columna `predicha` vale
`3` en las 1 200. **La vista no dibujaba ni una sola flecha, nunca.**

Y al mismo tiempo la pantalla decia *"el modelo anuncia cada vela en el momento"*. Las
dos cosas no pueden ser ciertas a la vez: era el mismo defecto del #149 --la app
afirmando algo que no es-- pero en el contenido y no en la fecha, y por eso no se veia
mirando el chip de antiguedad.

Que produce
-----------
`app/public/datos/tiempo-real-LTC.json`, con el bosque aleatorio --el modelo clasico
del proyecto, el mismo de la evidencia-- prediciendo sobre las ultimas velas del panel,
y con **la confianza de cada aviso**.

La confianza es lo que hace posible el #150: hoy una prediccion con 12 % de
probabilidad se dibuja igual que una con 45 %, y no son lo mismo. Con la probabilidad
en el dato, la vista puede callarse por debajo de un umbral sin calcular nada.

Lo que este guion NO hace
-------------------------
**No reentrena.** Es el mismo bosque, con el mismo bloque de entrenamiento y la misma
semilla. Solo se le piden las probabilidades ademas de la clase.

**No calcula metricas por su cuenta.** Salen de `contracts.metrics.evaluar`, como en
todos los demas paneles.

**No elige el umbral.** Publica la probabilidad por vela; el umbral lo mueve quien mira,
y la curva medida vive en `punto-de-operacion.json`.

**No escribe nada si el control falla.** Antes de exportar, el bosque tiene que
reproducir sobre validacion el F1 macro `0.390497720487045` que M3 y M2 midieron por
separado. Si no lo reproduce, algo cambio en el camino y ningun numero de este archivo
describiria lo que dice describir.

Uso:  uv run python app/scripts/generar_tiempo_real.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from contracts.config import (  # noqa: E402
    ACTIVO_OBJETIVO,
    GRANULARIDAD,
    HORIZONTE_H,
    VENTANA_W,
)
from contracts.labeling import Clase, etiquetar, objetivo  # noqa: E402
from contracts.metrics import evaluar, f1_macro  # noqa: E402
from contracts.schema import cierre as serie_cierre  # noqa: E402
from contracts.splits import particionar  # noqa: E402
from src.features.base import construir  # noqa: E402
from src.modelos.clasico import BosqueAleatorio  # noqa: E402

DESTINO = RAIZ / "app" / "public" / "datos" / "tiempo-real-LTC.json"
EVIDENCIA_OPERACION = RAIZ / "docs" / "evidencias" / "m0-aviso-con-abstencion-4h-w7-h1.json"
DESTINO_OPERACION = RAIZ / "app" / "public" / "datos" / "punto-de-operacion.json"

#: Las mismas que exporta el resto de la aplicacion, para que las vistas se comparen.
VELAS_EXPORTADAS = 1200

#: El numero que el bosque tiene que reproducir antes de que esto publique nada.
#: Lo obtuvieron por separado M3 en el #63 y M2 en el #62, con codigo distinto.
CONTROL_VALIDACION = 0.390497720487045

#: Las dos clases que son un aviso. Continuidad no es un aviso: es el silencio.
RARAS = (int(Clase.MAXIMO), int(Clase.MINIMO))


def _confianza(probabilidades: np.ndarray, clases: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Para cada vela: la clase rara mas probable y con cuanta probabilidad.

    Se mira solo entre las dos clases raras a proposito. La confianza que le importa a
    quien usa la vista no es "que tan seguro esta de que NO pasa nada" --que es casi
    siempre altisima-- sino que tan seguro esta del aviso que da.
    """
    columnas = [int(np.where(clases == r)[0][0]) for r in RARAS]
    p_raras = probabilidades[:, columnas]
    mejor = p_raras.argmax(axis=1)
    return np.array(RARAS)[mejor], p_raras.max(axis=1)


def main() -> None:
    panel = pd.read_parquet(RAIZ / f"data/processed/panel_{GRANULARIDAD}_v1.parquet")
    X = construir(panel)
    etiquetas = etiquetar(serie_cierre(panel, ACTIVO_OBJETIVO), VENTANA_W)
    y = objetivo(etiquetas, HORIZONTE_H)
    particion = particionar(len(panel), VENTANA_W, HORIZONTE_H)

    entrenables = particion.entrenamiento & y.notna().to_numpy()
    bosque = BosqueAleatorio(semilla=0, nombre="bosque_aleatorio_rezagos_relativos")
    bosque.entrenar(X[entrenables], y[entrenables])

    # El control, antes de exportar nada.
    validables = particion.validacion & y.notna().to_numpy()
    obtenido = float(
        f1_macro(y[validables].astype(int).to_numpy(), bosque.predecir(X[validables]))
    )
    if abs(obtenido - CONTROL_VALIDACION) > 1e-9:
        raise AssertionError(
            f"el bosque no reproduce su cifra publicada: obtenido {obtenido!r}, "
            f"publicado {CONTROL_VALIDACION!r}. No se exporta nada hasta entenderlo."
        )

    ultimas = X.index[-VELAS_EXPORTADAS:]
    predichas = bosque.predecir(X.loc[ultimas])
    tuberia = bosque._tuberia
    probabilidades = tuberia.predict_proba(
        bosque._preparar(X.loc[ultimas], bosque._columnas)
    )
    clase_rara, confianza = _confianza(probabilidades, tuberia.classes_)

    cierres = serie_cierre(panel, ACTIVO_OBJETIVO).loc[ultimas]
    y_ultimas = y.loc[ultimas]

    serie = [
        {
            "fecha": pd.Timestamp(fecha).isoformat().replace("+00:00", "Z"),
            "cierre": round(float(cierres.loc[fecha]), 4),
            "etiqueta": None if pd.isna(y_ultimas.loc[fecha]) else int(y_ultimas.loc[fecha]),
            "predicha": int(predichas[i]),
            # La clase rara mas probable y su probabilidad. Van siempre, tambien
            # cuando `predicha` es Continuidad: es justo lo que permite bajar el
            # umbral y ver avisos que hoy la clase mas probable esconde.
            "aviso": int(clase_rara[i]),
            "confianza": round(float(confianza[i]), 6),
        }
        for i, fecha in enumerate(ultimas)
    ]

    evaluables = y_ultimas.notna().to_numpy()
    metricas = evaluar(
        y_ultimas[evaluables].astype(int).to_numpy(), predichas[evaluables]
    )

    salida = {
        "fuente": "app/scripts/generar_tiempo_real.py",
        "activo": ACTIVO_OBJETIVO,
        "modelo": "bosque_aleatorio_rezagos_relativos",
        "generado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "ultima_vela": serie[-1]["fecha"],
        "control": {
            "descripcion": (
                "El bosque reproduce sobre validacion la cifra publicada antes de "
                "exportar. Si no la reproduce, este archivo no se escribe."
            ),
            "esperado": CONTROL_VALIDACION,
            "obtenido": obtenido,
            "reproduce": True,
        },
        "serie": serie,
        "metricas": metricas,
        # Lo usa la leyenda de la app (#151.4): sin el porcentaje de Continuidad, la
        # pantalla explica los colores pero no por que el problema es dificil.
        "balance": [
            {
                "clase": clase.name.capitalize(),
                "codigo": int(clase),
                "n": int((y_ultimas == int(clase)).sum()),
                "porcentaje": round(
                    100 * float((y_ultimas == int(clase)).sum()) / int(evaluables.sum()), 3
                ),
            }
            for clase in (Clase.MAXIMO, Clase.MINIMO, Clase.CONTINUIDAD)
        ],
    }
    DESTINO.write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")

    # La curva del punto de operacion se COPIA de la evidencia medida, no se recalcula:
    # si la app la recalculara, tarde o temprano daria distinto que el informe.
    medido = json.loads(EVIDENCIA_OPERACION.read_text(encoding="utf-8"))
    operacion = {
        "fuente": "docs/evidencias/m0-aviso-con-abstencion-4h-w7-h1.json",
        "generado_utc": salida["generado_utc"],
        "que_mide": medido["que_mide"],
        "n_observaciones": medido["n_observaciones"],
        "frecuencia_base_de_giros": medido["frecuencia_base_de_giros"],
        "tramos": medido["parametros"]["n_tramos"],
        "umbrales": [
            {
                "umbral": float(u),
                "cobertura": b["cobertura"],
                "precision": b["precision"],
                "precision_azar": b["precision_azar_misma_cobertura"],
                "tramos_a_favor": b["tramos_a_favor"],
                "tramos_medidos": b["tramos_medidos"],
            }
            for u, b in sorted(medido["agregado"].items(), key=lambda kv: float(kv[0]))
        ],
    }
    DESTINO_OPERACION.write_text(
        json.dumps(operacion, indent=1, ensure_ascii=False), encoding="utf-8"
    )

    print(f"control: obtenido {obtenido!r} == publicado {CONTROL_VALIDACION!r}")
    print(f"{DESTINO.relative_to(RAIZ)}: {len(serie)} velas, ultima {salida['ultima_vela']}")
    avisa = sum(1 for p in serie if p["predicha"] in RARAS)
    print(f"  avisos con la clase mas probable: {avisa} de {len(serie)}")
    print(f"  F1 macro sobre las exportadas: {metricas['f1_macro']:.6f}")
    print(f"{DESTINO_OPERACION.relative_to(RAIZ)}: {len(operacion['umbrales'])} umbrales")


if __name__ == "__main__":
    main()
