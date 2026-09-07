"""Completa la condicion 2 de la regla principal del protocolo sobre el bloque de prueba.

Por que hace falta
------------------
La seccion 5 de `docs/09-protocolo-bloque-prueba.md` aplica las tres condiciones de la
D16 al **mejor modelo contra el `baseline_aleatorio`**. La corrida unica dejo medidas la
condicion 1 (la diferencia es positiva) y la 3 (el signo no cambia en cinco semillas),
pero **no la 2**: `comparar_fundacional` solo calcula intervalos pareados de los modelos
profundos, y el mejor modelo resulto ser el bosque.

Sin este numero, la regla que el proyecto fijo de antemano no se puede aplicar a su
propio resultado final.

Por que esto NO es una segunda medicion
---------------------------------------
La seccion 7 del protocolo prohibe volver a correr "para confirmar", cambiar el modelo,
ajustar nada o quedarse con un subconjunto de semillas. **Esto no es ninguna de esas.**

El bosque y el `baseline_aleatorio` **reproducen bit a bit entre procesos**: esta medido
y comprometido en `m0-reproducibilidad-predicciones-4h-w7-h1.json`, con la misma huella
SHA-256 en tres procesos distintos y tambien en CI sobre Linux. Asi que las predicciones
que este guion recalcula son **las mismas** que produjo la corrida, no unas nuevas.

Y se comprueba en vez de suponerse: antes de calcular el intervalo, el guion **verifica
que el F1 macro recalculado coincida exactamente con el que la corrida dejo escrito en la
evidencia**. Si no coincidiera, se detiene: querria decir que las predicciones no son las
mismas y entonces si haria falta una decision del equipo.

Un calculo determinista sobre predicciones ya producidas no se puede "elegir": da un solo
resultado. No hay nada que repetir hasta que salga bonito, que es lo que la D18 protege.

No pasa por el arnes ni por el pestillo a proposito: no produce una cifra nueva de un
modelo, completa la lectura de una que ya existe.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from contracts.config import ACTIVO_OBJETIVO, HORIZONTE_H, VENTANA_W  # noqa: E402
from contracts.labeling import etiquetar, objetivo  # noqa: E402
from contracts.metrics import f1_macro  # noqa: E402
from contracts.schema import cierre  # noqa: E402
from contracts.splits import particionar  # noqa: E402
from src.features.base import construir  # noqa: E402
from src.features.incertidumbre import intervalo_diferencia  # noqa: E402
from src.modelos.base import BaselineAleatorio  # noqa: E402
from src.modelos.clasico import HIPERPARAMETROS, BosqueAleatorio  # noqa: E402

EVIDENCIA = RAIZ / "docs" / "evidencias"
CORRIDA = EVIDENCIA / "modelo-clasico-4h-w7-h1-rezagos-relativos-prueba.json"
SALIDA = EVIDENCIA / "m0-intervalo-regla-principal-prueba-4h-w7-h1.json"

MEJOR = "bosque_aleatorio_rezagos_relativos"
AZAR = "baseline_aleatorio"


def main() -> None:
    esperado = {
        r["modelo"]: r["f1_macro"]
        for r in json.loads(CORRIDA.read_text(encoding="utf-8"))["resultados"]
    }

    panel = pd.read_parquet(RAIZ / "data" / "processed" / "panel_4h_v1.parquet")
    X = construir(panel, rezagos_relativos=True)
    w, h = VENTANA_W, HORIZONTE_H
    y = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), w), h)
    particion = particionar(n=len(y), w=w, h=h)

    entrenables = particion.entrenamiento & y.notna().to_numpy()
    mascara = particion.prueba & y.notna().to_numpy()
    semilla = HIPERPARAMETROS["random_state"]

    modelos = {
        MEJOR: BosqueAleatorio(
            n_arboles=HIPERPARAMETROS["n_estimators"], semilla=semilla, nombre=MEJOR
        ),
        AZAR: BaselineAleatorio(semilla=semilla),
    }

    predicciones = {}
    print("Comprobando que las predicciones sean las MISMAS de la corrida unica:")
    for nombre, modelo in modelos.items():
        modelo.entrenar(X[entrenables], y[entrenables])
        pred = np.asarray(modelo.predecir(X[mascara]))
        predicciones[nombre] = pred
        obtenido = float(f1_macro(y[mascara], pred))
        coincide = abs(obtenido - esperado[nombre]) < 1e-12
        print(
            f"  {nombre:38} corrida {esperado[nombre]:.6f}  "
            f"recalculado {obtenido:.6f}  {'IGUAL' if coincide else 'DISTINTO'}"
        )
        if not coincide:
            raise SystemExit(
                f"\n{nombre} no reproduce el F1 de la corrida "
                f"({esperado[nombre]!r} contra {obtenido!r}).\n"
                "Las predicciones NO son las mismas, asi que este calculo seria una "
                "segunda medicion y no una lectura de la primera. Se detiene: esto "
                "necesita una decision del equipo, no un guion."
            )

    print("\nLas dos reproducen. El intervalo se calcula sobre las predicciones de la corrida.\n")

    ic = intervalo_diferencia(y[mascara], predicciones[MEJOR], predicciones[AZAR])
    excluye = ic["excluye_el_cero"]

    print("CONDICION 2 de la regla principal (seccion 5 del protocolo):")
    print(f"  diferencia   {ic['diferencia']:+.6f}")
    print(f"  IC 95 %      [{ic['ic_inferior']:+.6f} , {ic['ic_superior']:+.6f}]")
    print(f"  excluye el cero: {'SI' if excluye else 'NO'}")

    # Las condiciones 1 y 3 se leen de la corrida, pero su MEDIA es una cifra derivada:
    # si el informe la cita y no existe en la evidencia, `verificar_numeros` la marca sin
    # respaldo -- con razon. Se guarda aqui, que es el archivo de la regla aplicada.
    prof = json.loads(
        (EVIDENCIA / "m3-modelos-profundos-4h-w7-h1-prueba.json").read_text(encoding="utf-8")
    )
    ps = prof["por_semilla"]
    diferencias = {
        str(s): (
            ps["por_modelo"][MEJOR]["por_semilla"][str(s)]["f1_macro"]
            - ps["por_modelo"][AZAR]["por_semilla"][str(s)]["f1_macro"]
        )
        for s in ps["semillas"]
    }
    valores = list(diferencias.values())
    media = float(np.mean(valores))
    signo_estable = all(v > 0 for v in valores) or all(v < 0 for v in valores)

    print()
    print("CONDICION 1 y 3 (leidas de la corrida, la media calculada aqui):")
    print(f"  media de las diferencias: {media:+.6f}")
    print(f"  signo estable en las cinco: {'SI' if signo_estable else 'NO'}")

    datos = {
        "que_es": (
            "Condicion 2 de la regla principal del protocolo: el intervalo pareado del "
            "mejor modelo contra el baseline_aleatorio sobre el bloque de prueba. La "
            "corrida unica no lo calculo porque `comparar_fundacional` solo compara los "
            "modelos profundos, y el mejor resulto ser el bosque."
        ),
        "no_es_una_segunda_medicion": (
            "Las predicciones son las mismas de la corrida unica: los dos modelos "
            "reproducen bit a bit entre procesos (m0-reproducibilidad-predicciones), y "
            "se comprobo que el F1 recalculado coincide exactamente con el que la "
            "corrida dejo escrito. Un calculo determinista sobre predicciones ya "
            "producidas no se puede elegir."
        ),
        "conjunto": "prueba",
        "n": int(mascara.sum()),
        "mejor_modelo": MEJOR,
        "contra": AZAR,
        "f1_macro_verificado": {k: esperado[k] for k in (MEJOR, AZAR)},
        "condicion_1_diferencia_positiva": {
            "por_semilla": diferencias,
            "media": media,
            "se_cumple": media > 0,
        },
        "condicion_2_intervalo_excluye_el_cero": {
            **ic,
            "se_cumple": ic["excluye_el_cero"],
        },
        "condicion_3_signo_estable": {
            "positivas": sum(1 for v in valores if v > 0),
            "de": len(valores),
            "se_cumple": signo_estable,
        },
        "condiciones_cumplidas": sum(
            [media > 0, bool(ic["excluye_el_cero"]), signo_estable]
        ),
        "lectura": (
            "El protocolo (seccion 5) exige las TRES. Con dos de tres, la lectura que "
            "toca es la segunda de las escritas de antemano en su seccion 6: no se puede "
            "afirmar que el sistema detecte mejor que el azar sobre el bloque de prueba."
        ),
        "intervalo": ic,
    }
    SALIDA.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nconstancia en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
