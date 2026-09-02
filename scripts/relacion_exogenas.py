"""Mide si alguna variable de apoyo guarda con LTC una relacion inversa.

Por que existe
--------------
El profesor senalo el 1 de septiembre que, al usar variables exogenas, lo que hay
que buscar es que sean **proporcionales o inversamente proporcionales** a la
objetivo. Una variable que se mueve igual que LTC aporta poco; una que se mueve al
reves aporta informacion que LTC no tiene.

Este guion contesta si tenemos alguna de las dos, y la respuesta explica un
resultado que hasta ahora solo teniamos medido sin entender: por que los cinco
activos de apoyo no aportan de forma distinguible (S4-M2-01).

Lo que se mide
--------------
1. La correlacion de retornos de LTC con cada uno de los cinco.
2. Si existe algun par inversamente proporcional entre los seis.
3. Si se puede CONSTRUIR una variable decorrelacionada a partir de los mismos seis
   --cocientes de fuerza relativa y exceso sobre la media del resto-- o si eso
   tampoco alcanza.

Punto de entrada:  uv run python -m scripts.relacion_exogenas
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

from contracts.config import ACTIVO_OBJETIVO, ACTIVOS, GRANULARIDAD  # noqa: E402
from contracts.schema import cierre  # noqa: E402

RUTA = RAIZ / "docs" / "evidencias" / "relacion-exogenas.json"

#: Por debajo de esta correlacion absoluta consideramos que una variable aporta
#: informacion que la objetivo no tiene. Es una convencion del equipo, no un
#: contraste, y se fija aqui antes de mirar ningun resultado.
UMBRAL_DECORRELACION = 0.3


def medir() -> dict:
    panel = pd.read_parquet(RAIZ / "data" / "processed" / f"panel_{GRANULARIDAD}_v1.parquet")
    retornos = pd.DataFrame({a: cierre(panel, a).pct_change() for a in ACTIVOS}).dropna()
    objetivo = retornos[ACTIVO_OBJETIVO]
    matriz = retornos.corr()

    apoyo = [a for a in ACTIVOS if a != ACTIVO_OBJETIVO]
    con_objetivo = {a: float(matriz.loc[ACTIVO_OBJETIVO, a]) for a in apoyo}

    pares = [
        {"par": f"{i}-{j}", "correlacion": float(matriz.loc[i, j])}
        for k, i in enumerate(ACTIVOS)
        for j in ACTIVOS[k + 1 :]
    ]
    inversos = [p for p in pares if p["correlacion"] < 0]

    # Se intenta CONSTRUIR una variable decorrelacionada con lo que ya tenemos, antes
    # de concluir que hace falta traer un activo de fuera.
    resto = [a for a in apoyo]
    construidas = {
        f"fuerza_relativa_{ACTIVO_OBJETIVO}_{a}": (
            cierre(panel, ACTIVO_OBJETIVO) / cierre(panel, a)
        ).pct_change()
        for a in apoyo
    }
    construidas["exceso_sobre_la_media_del_resto"] = objetivo - retornos[resto].mean(axis=1)

    intentos = []
    for nombre, serie in construidas.items():
        alineada = serie.reindex(objetivo.index)
        correlacion = float(alineada.corr(objetivo))
        intentos.append(
            {
                "variable": nombre,
                "correlacion_con_el_objetivo": round(correlacion, 6),
                "decorrelaciona": bool(abs(correlacion) < UMBRAL_DECORRELACION),
            }
        )

    valores = np.array([p["correlacion"] for p in pares])
    return {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "pregunta": (
            "Hay entre los seis activos alguna relacion inversamente proporcional, o "
            "se puede construir una variable decorrelacionada con los mismos datos?"
        ),
        "criterio_preregistrado": (
            f"Se considera decorrelacionada una variable con |correlacion| < "
            f"{UMBRAL_DECORRELACION}. Es una convencion del equipo, fijada antes de mirar."
        ),
        "parametros": {"intervalo": GRANULARIDAD, "objetivo": ACTIVO_OBJETIVO},
        "correlacion_del_objetivo_con_cada_apoyo": con_objetivo,
        "todos_los_pares": pares,
        "rango_entre_pares": {"minimo": float(valores.min()), "maximo": float(valores.max())},
        "pares_inversamente_proporcionales": inversos,
        "hay_alguna_relacion_inversa": bool(inversos),
        "variables_construidas": intentos,
        "alguna_construida_decorrelaciona": any(i["decorrelaciona"] for i in intentos),
        "_meta": {
            "para_que_sirve": (
                "Explica el resultado de S4-M2-01. Los cinco activos de apoyo no aportan "
                "de forma distinguible porque son fuertemente proporcionales a LTC: no "
                "traen informacion que LTC no tenga ya. Una variable inversamente "
                "proporcional si la traeria, y entre los seis del enunciado no existe."
            ),
        },
    }


def probar_las_decorrelacionadas(intentos: list[dict]) -> dict:
    """Si las variables que SI decorrelacionan mejoran el modelo, medido.

    Encontrar una variable decorrelacionada no es encontrar una util: puede traer
    informacion distinta y que esa informacion no sirva para esta etiqueta. Se
    separa a proposito, porque confundir las dos cosas es la forma facil de
    justificar una caracteristica por su estadistica en vez de por su efecto.

    Se mide con cinco semillas y se lee con las tres condiciones de la D16.
    """
    from contracts.config import HORIZONTE_H, VENTANA_W
    from contracts.labeling import etiquetar, objetivo
    from contracts.metrics import evaluar
    from contracts.splits import particionar
    from src.features.base import construir
    from src.modelos.clasico import BosqueAleatorio

    utiles = [i["variable"] for i in intentos if i["decorrelaciona"]]
    if not utiles:
        return {"se_probaron": [], "por_que": "ninguna variable construida decorrelaciona"}

    panel = pd.read_parquet(RAIZ / "data" / "processed" / f"panel_{GRANULARIDAD}_v1.parquet")
    X = construir(panel)
    y = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), VENTANA_W), HORIZONTE_H)
    particion = particionar(n=len(y), w=VENTANA_W, h=HORIZONTE_H)
    entrenables = particion.entrenamiento & y.notna().to_numpy()
    evaluables = particion.validacion & y.notna().to_numpy()
    verdad = y[evaluables].astype(int).to_numpy()

    # Los rezagos son los mismos ordenes que usa el resto de las caracteristicas: la
    # comparacion tiene que ser entre tener o no la variable, no entre dos formas de
    # construirla.
    extra = pd.DataFrame(index=X.index)
    for nombre in utiles:
        activo = nombre.rsplit("_", 1)[-1]
        fuerza = (cierre(panel, ACTIVO_OBJETIVO) / cierre(panel, activo)).pct_change()
        for k in (1, 5, 7):
            extra[f"fuerza_rel_{ACTIVO_OBJETIVO}_{activo}_rezago_{k}"] = fuerza.shift(k)

    medidas = {}
    for etiqueta, datos in (("sin", X), ("con", pd.concat([X, extra], axis=1))):
        f1 = []
        for semilla in range(5):
            modelo = BosqueAleatorio(semilla=semilla)
            modelo.entrenar(datos[entrenables], y[entrenables].astype(int).to_numpy())
            predichas = np.asarray(modelo.predecir(datos[evaluables]), dtype=int)
            f1.append(evaluar(verdad, predichas)["f1_macro"])
        medidas[etiqueta] = f1

    diferencias = [b - a for a, b in zip(medidas["sin"], medidas["con"], strict=True)]
    cambia = not (all(d > 0 for d in diferencias) or all(d < 0 for d in diferencias))
    return {
        "se_probaron": utiles,
        "columnas_anadidas": list(extra.columns),
        "f1_sin_por_semilla": [round(v, 6) for v in medidas["sin"]],
        "f1_con_por_semilla": [round(v, 6) for v in medidas["con"]],
        "diferencia_media": round(float(np.mean(diferencias)), 6),
        "cambia_de_signo": cambia,
        "se_puede_afirmar_que_aporta": bool(np.mean(diferencias) > 0 and not cambia),
        "lectura": (
            "Con las tres condiciones de la D16: si la media es negativa o el signo "
            "cambia entre semillas, no se puede afirmar que aporte. Decorrelacionar no "
            "es lo mismo que informar."
        ),
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    medido = medir()
    RUTA.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Correlacion de retornos con {ACTIVO_OBJETIVO}:")
    for activo, valor in medido["correlacion_del_objetivo_con_cada_apoyo"].items():
        print(f"  {activo}: {valor:+.4f}")
    rango = medido["rango_entre_pares"]
    print(f"\nRango entre los quince pares: {rango['minimo']:+.4f} a {rango['maximo']:+.4f}")
    print(f"Pares inversamente proporcionales: "
          f"{len(medido['pares_inversamente_proporcionales'])}")

    print("\nVariables construidas con los mismos datos:")
    for intento in medido["variables_construidas"]:
        print(f"  {intento['variable']:38} {intento['correlacion_con_el_objetivo']:+.4f}  "
              f"decorrelaciona: {intento['decorrelaciona']}")

    prueba = probar_las_decorrelacionadas(medido["variables_construidas"])
    medido["prueba_sobre_el_modelo"] = prueba
    RUTA.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")

    if prueba["se_probaron"]:
        print(f"\nProbadas sobre el modelo: {', '.join(prueba['se_probaron'])}")
        print(f"  diferencia media: {prueba['diferencia_media']:+.6f}   "
              f"cambia de signo: {prueba['cambia_de_signo']}")
        print(f"  se puede afirmar que aporta: {prueba['se_puede_afirmar_que_aporta']}")

    print(f"\nEvidencia: {RUTA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
