"""Circuito completo del modelo clasico de referencia (tarea S1-M3-01).

Carga el panel congelado, construye las caracteristicas de M2, etiqueta con el
contrato, parte cronologicamente con embargo, evalua los tres baselines y el
bosque con el mismo arnes y la misma particion, y deja la evidencia.

Los valores por omision (4h, w=7, h=1) salen del contrato congelado en
contracts/config.py el 18 de agosto de 2026, justificado en
docs/04-decision-w-h-granularidad.md. PROVISIONAL es False: estos numeros ya
entran al informe como definitivos.

Los rezagos salen en la forma que decida M2 en `construir()`. Desde D6 esa forma es
relativa al precio actual; `--rezagos-en-nivel` reproduce las mediciones anteriores.
El nombre de cada modelo lleva la forma de los rezagos con la que se midio, porque
dos filas del CSV con el mismo nombre tienen que significar lo mismo.

Salidas:
    docs/evidencias/resultados.csv                          una fila por modelo, se anade
    docs/evidencias/modelo-clasico-<intervalo>-w<w>-h<h>-rezagos-<forma>.json

Uso:
    uv run python -m src.modelos.experimento
    uv run python -m src.modelos.experimento --intervalo 1d --w 5 --h 3
    uv run python -m src.modelos.experimento --sin-variantes
    uv run python -m src.modelos.experimento --rezagos-en-nivel   # reproduce pre-D6
"""

from __future__ import annotations

import argparse
import math
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from contracts.config import ACTIVO_OBJETIVO, PROVISIONAL
from contracts.labeling import etiquetar, latencia_real, objetivo, resumen_clases
from contracts.schema import cierre, validar_panel
from contracts.splits import particionar
from src.evaluacion.arnes import comparar, evaluar_modelo, guardar_json, guardar_resultado
from src.features.base import construir
from src.modelos.base import BaselineAleatorio, BaselineMayoritario, BaselineTrivial
from src.modelos.clasico import CRITERIO_PREREGISTRADO, HIPERPARAMETROS, BosqueAleatorio

RAIZ = Path(__file__).resolve().parents[2]
EVIDENCIAS = RAIZ / "docs" / "evidencias"
RUTA_RESULTADOS = EVIDENCIAS / "resultados.csv"

try:
    from src.features.base import columnas_en_nivel_de_precio
except ImportError:  # pragma: no cover - solo hasta que entre el PR #58 de M2
    # Respaldo temporal con la MISMA regla que el ayudante de M2, para que este
    # cambio pueda entrar a main antes que el #58 sin romper el CI. En cuanto el
    # #58 este fusionado, el import de arriba gana y este bloque deja de usarse.
    def columnas_en_nivel_de_precio(X: pd.DataFrame) -> list[str]:
        return [c for c in X.columns if "_rezago_" in c and "_rezago_rel_" not in c]


def columnas_de_rezago(X: pd.DataFrame) -> list[str]:
    """Todas las columnas de rezago, esten en nivel o en forma relativa.

    Es la pregunta que sostiene la variante `bosque_aleatorio_sin_rezagos`: si el
    bosque necesita los rezagos, en cualquiera de sus dos formas. Se responde igual
    antes y despues del cambio de M2, y por eso esa variante no cambia de
    significado cuando el valor por defecto pasa a relativo.
    """
    return [c for c in X.columns if "_rezago_" in c]


def _verificar_encabezado(ruta: Path, resultado: dict) -> None:
    """guardar_resultado anade con header=False: el primero que escribe fija el
    orden de columnas. Si un resultado trae otras claves, o las mismas en otro
    orden, los valores se escriben debajo del encabezado equivocado y el CSV queda
    bien formado y con todos los numeros mal. Es silencioso, asi que se comprueba.
    """
    if not ruta.exists():
        return
    encabezado = pd.read_csv(ruta, nrows=0).columns.tolist()
    if encabezado != list(resultado):
        raise SystemExit(
            f"el encabezado de {ruta.name} es {encabezado} y este resultado trae "
            f"{list(resultado)}. Anadir asi desalinearia las columnas en silencio."
        )


def detecta_mejor_que_azar(resultado_modelo: dict, resultado_aleatorio: dict) -> bool:
    """Si el modelo detecta las dos clases extremas, o solo les acierta por casualidad.

    "> 0" no alcanza como piso: con un solo acierto de 94 casos ya da True, y el
    aviso para el que existe este chequeo nunca llegaria a imprimirse (issue #51).
    El piso correcto es el F1 por clase del baseline_aleatorio de la MISMA corrida:
    si el bosque no le gana ni al azar en una clase extrema, no la esta detectando.
    """
    return bool(
        resultado_modelo["f1_maximo"] > resultado_aleatorio["f1_maximo"]
        and resultado_modelo["f1_minimo"] > resultado_aleatorio["f1_minimo"]
    )


def _finito(valor):
    """Convierte los flotantes no finitos en None.

    precision_direccional devuelve NaN, no 0.0, cuando el bloque no tiene ningun
    extremo real. guardar_json lo serializaria como NaN, que Python lee pero no es
    JSON valido: el JSON.parse de la aplicacion de M1 reventaria.
    """
    if isinstance(valor, float) and not math.isfinite(valor):
        return None
    return valor


def _limpiar_json(datos):
    if isinstance(datos, dict):
        return {clave: _limpiar_json(valor) for clave, valor in datos.items()}
    if isinstance(datos, list):
        return [_limpiar_json(valor) for valor in datos]
    return _finito(datos)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intervalo", default="4h", help="4h o 1d")
    parser.add_argument("--w", type=int, default=7, help="ventana del etiquetado")
    # h=1 y no 5: docs/04-decision-w-h-granularidad.md midio la informacion mutua
    # entre las caracteristicas en t y la etiqueta en t+h, y cae 4,2 veces de h=1 a
    # h=3 para despues aplanarse. Lo observable informa sobre la vela siguiente y
    # casi nada mas alla.
    parser.add_argument("--h", type=int, default=1, help="horizonte del pronostico")
    parser.add_argument("--conjunto", default="validacion", choices=["validacion", "prueba"])
    parser.add_argument(
        "--gastar-prueba",
        action="store_true",
        help="requerido para evaluar sobre prueba; el bloque se gasta una sola vez",
    )
    parser.add_argument("--sin-variantes", action="store_true", help="solo los cuatro modelos")
    parser.add_argument(
        "--rezagos-en-nivel",
        action="store_true",
        help=(
            "construye los rezagos en nivel de precio en vez de relativos. Existe para "
            "reproducir las mediciones anteriores a D6, no para el pipeline."
        ),
    )
    parser.add_argument("--semilla", type=int, default=HIPERPARAMETROS["random_state"])
    parser.add_argument("--n-arboles", type=int, default=HIPERPARAMETROS["n_estimators"])
    argumentos = parser.parse_args()

    if argumentos.conjunto == "prueba" and not argumentos.gastar_prueba:
        raise SystemExit(
            "evaluar sobre prueba gasta el unico conjunto no visto que tenemos, y la "
            "tarea S1-M3-01 pide validacion. Si de verdad es lo que queres, agrega "
            "--gastar-prueba y dejalo escrito en el informe."
        )

    w, h = argumentos.w, argumentos.h

    print(f"Modelo clasico de referencia -- intervalo {argumentos.intervalo}, w={w}, h={h}")
    if PROVISIONAL:
        print(
            "  contracts/config.py sigue marcado PROVISIONAL: estos numeros no entran\n"
            "  al informe como definitivos. Parametros tomados de la medicion del spike."
        )

    # ------------------------------------------------------------------ [1/6]
    ruta_panel = RAIZ / "data" / "processed" / f"panel_{argumentos.intervalo}_v1.parquet"
    if not ruta_panel.exists():
        raise SystemExit(f"no existe {ruta_panel.relative_to(RAIZ)}")
    panel = pd.read_parquet(ruta_panel)
    validar_panel(panel)
    print(
        f"\n[1/6] Panel        {len(panel)} filas x {len(panel.columns)} columnas, "
        f"{panel.index.min():%Y-%m-%d} a {panel.index.max():%Y-%m-%d}"
    )

    # ------------------------------------------------------------------ [2/6]
    X = construir(panel, rezagos_relativos=not argumentos.rezagos_en_nivel)
    # Se le pregunta a M2 cuales columnas estan en unidades de precio en vez de
    # deducirlo de un fragmento de nombre desde aqui: la nomenclatura es suya y
    # puede cambiar, la pregunta no.
    columnas_en_nivel = columnas_en_nivel_de_precio(X)
    columnas_rezago = columnas_de_rezago(X)
    filas_con_nulos = int(X.isna().any(axis=1).sum())

    # El nombre lleva SIEMPRE la forma de los rezagos, incluso en el caso por
    # defecto. Un bosque entrenado con niveles y uno entrenado con relativos no son
    # el mismo modelo, y resultados.csv se anade sin sobrescribir: si los dos se
    # llamaran `bosque_aleatorio`, dos filas con el mismo nombre significarian cosas
    # distintas y solo la fecha las distinguiria. Nombrar solo la variante rara y
    # dejar el caso por defecto sin sufijo mueve el problema, no lo resuelve.
    if columnas_en_nivel:
        forma_rezagos = "en nivel de precio"
        sufijo = "_rezagos_en_nivel"
    elif columnas_rezago:
        forma_rezagos = "relativos al precio actual"
        sufijo = "_rezagos_relativos"
    else:
        forma_rezagos = "no hay columnas de rezago"
        sufijo = "_sin_rezagos_disponibles"

    print(
        f"[2/6] Caracteristicas  {len(X.columns)} columnas, "
        f"{filas_con_nulos} filas con algun nulo"
    )
    print(
        f"      rezagos: {forma_rezagos} "
        f"({len(columnas_rezago)} columnas, {len(columnas_en_nivel)} de ellas en nivel)"
    )

    # ------------------------------------------------------------------ [3/6]
    y = objetivo(etiquetar(cierre(panel, ACTIVO_OBJETIVO), w), h)
    if not (len(X) == len(y) == len(panel)):
        raise SystemExit(
            f"desalineacion: panel={len(panel)}, X={len(X)}, y={len(y)}. El arnes "
            f"compara por posicion, asi que los tres tienen que medir lo mismo."
        )
    print(
        f"[3/6] Etiquetas    {int(y.notna().sum())} etiquetadas, "
        f"latencia real {latencia_real(w, h)} velas"
    )

    # ------------------------------------------------------------------ [4/6]
    particion = particionar(n=len(y), w=w, h=h)
    entrenables = int((particion.entrenamiento & y.notna().to_numpy()).sum())
    print("[4/6] Particion")
    print(particion.resumen(panel.index).to_string(index=False))
    print(f"      filas que llegan a entrenar(): {entrenables}")

    balance = resumen_clases(y[particion.entrenamiento & y.notna().to_numpy()])
    print(balance.to_string(index=False))

    # ------------------------------------------------------------------ [5/6]
    nombre_principal = f"bosque_aleatorio{sufijo}"
    modelos = [
        BaselineTrivial(),
        BaselineMayoritario(),
        BaselineAleatorio(semilla=argumentos.semilla),
        BosqueAleatorio(
            n_arboles=argumentos.n_arboles,
            semilla=argumentos.semilla,
            nombre=nombre_principal,
        ),
    ]
    if not argumentos.sin_variantes:
        # Las variantes se distinguen por su nombre y NO por una columna extra:
        # agregar claves al dict de resultado desalinearia el CSV (ver
        # _verificar_encabezado). Las dos existen para dejar medido, y no argumentado,
        # lo que el informe va a tener que explicar.
        #
        # `sin_rezagos` reemplaza al antiguo `sin_niveles`. El nombre viejo describia
        # bien lo que media solo mientras TODOS los rezagos estuvieran en nivel:
        # excluia el fragmento "_rezago_", que entonces eran los 24 niveles y nada
        # mas. Con los rezagos relativos ese mismo filtro se lleva tambien los
        # relativos, asi que la variante seguiria midiendo "sin ningun rezago" bajo
        # un nombre que dice "sin niveles". Se renombra a lo que de verdad hace, que
        # ademas es una pregunta que sigue teniendo sentido en las dos formas: si el
        # bosque necesita los rezagos.
        if columnas_rezago:
            modelos.append(
                BosqueAleatorio(
                    n_arboles=argumentos.n_arboles,
                    semilla=argumentos.semilla,
                    excluir_exactas=tuple(columnas_rezago),
                    nombre="bosque_aleatorio_sin_rezagos",
                )
            )
        modelos.append(
            BosqueAleatorio(
                n_arboles=argumentos.n_arboles,
                semilla=argumentos.semilla,
                peso_clases=None,
                nombre=f"bosque_aleatorio_sin_pesos{sufijo}",
            )
        )

    print(f"\n[5/6] Evaluacion sobre {argumentos.conjunto}")
    resultados = []
    for numero, modelo in enumerate(modelos, start=1):
        resultados.append(evaluar_modelo(modelo, X, y, particion, conjunto=argumentos.conjunto))
        print(f"      [{numero}/{len(modelos)}] {modelo.nombre}")

    print()
    print(comparar(resultados).to_string(index=False))

    # ------------------------------------------------------------------ [6/6]
    for resultado in resultados:
        _verificar_encabezado(RUTA_RESULTADOS, resultado)
        guardar_resultado(resultado, ruta=RUTA_RESULTADOS)

    por_nombre = {r["modelo"]: r for r in resultados}
    bosque_r = por_nombre[nombre_principal]
    delta = bosque_r["f1_macro"] - por_nombre["baseline_trivial"]["f1_macro"]
    supera = bool(delta > 0)

    # Superar al trivial por decimales no significa que el modelo sirva: se puede
    # ganar F1 macro sin detectar de verdad un extremo. Ver detecta_mejor_que_azar.
    aleatorio_r = por_nombre["baseline_aleatorio"]
    detecta = detecta_mejor_que_azar(bosque_r, aleatorio_r)

    bosque = next(m for m in modelos if m.nombre == nombre_principal)
    importancias = bosque.importancias()

    medido = {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "intervalo": argumentos.intervalo,
        "w": w,
        "h": h,
        "latencia_real": latencia_real(w, h),
        "conjunto": argumentos.conjunto,
        "config_provisional": PROVISIONAL,
        "origen_parametros": f"docs/evidencias/spike-datos-{argumentos.intervalo}.json",
        "panel": {
            "filas": int(len(panel)),
            "columnas": int(len(panel.columns)),
            "desde": panel.index.min(),
            "hasta": panel.index.max(),
        },
        "caracteristicas": {
            "n_columnas": int(len(X.columns)),
            "n_columnas_en_nivel": int(len(columnas_en_nivel)),
            "n_columnas_rezago": int(len(columnas_rezago)),
            "forma_rezagos": forma_rezagos,
            "filas_con_algun_nulo": filas_con_nulos,
            "origen_columnas_en_nivel": (
                "src.features.base.columnas_en_nivel_de_precio(), el ayudante de M2, "
                "en vez de un fragmento de nombre deducido desde M3"
            ),
        },
        "modelo_principal": nombre_principal,
        "particion": {
            "n_entrenamiento": int(particion.entrenamiento.sum()),
            "n_validacion": int(particion.validacion.sum()),
            "n_prueba": int(particion.prueba.sum()),
            "n_embargo": int(particion.embargo.sum()),
            "filas_entrenables": entrenables,
        },
        "balance_entrenamiento": balance.to_dict(orient="records"),
        "hiperparametros": HIPERPARAMETROS,
        "criterio_preregistrado": CRITERIO_PREREGISTRADO,
        "resultados": resultados,
        "veredicto": {
            "supera_al_trivial": supera,
            "delta_f1_macro": delta,
            "detecta_ambos_extremos": detecta,
            "criterio_deteccion": (
                "F1 por clase extrema estrictamente mayor que el del "
                "baseline_aleatorio de la misma corrida, no simplemente > 0"
            ),
            "f1_maximo": bosque_r["f1_maximo"],
            "f1_minimo": bosque_r["f1_minimo"],
            "f1_maximo_aleatorio": aleatorio_r["f1_maximo"],
            "f1_minimo_aleatorio": aleatorio_r["f1_minimo"],
            "precision_direccional": bosque_r["precision_direccional"],
        },
        "importancias_top10": importancias.head(10).round(6).to_dict(),
    }
    # w, h y la forma de los rezagos van en el nombre: si no, dos configuraciones
    # distintas se sobrescriben y el informe termina citando numeros de una corrida
    # que ya no es la vigente.
    marca_rezagos = sufijo.replace("_", "-")
    ruta_json = (
        EVIDENCIAS / f"modelo-clasico-{argumentos.intervalo}-w{w}-h{h}{marca_rezagos}.json"
    )
    guardar_json(_limpiar_json(medido), ruta_json)

    print("\n[6/6] Evidencia")
    print(f"      {RUTA_RESULTADOS.relative_to(RAIZ)}  (+{len(resultados)} filas)")
    print(f"      {ruta_json.relative_to(RAIZ)}")
    print("\n      importancias mas altas:")
    for variable, peso in importancias.head(5).items():
        print(f"        {peso:.4f}  {variable}")

    # La evidencia se escribe ANTES de fallar: el rastro de un fallo tiene que
    # sobrevivir al fallo.
    if not supera:
        raise SystemExit(
            f"\nel bosque no supera al BaselineTrivial en F1 macro (delta {delta:+.4f}). "
            f"Segun el criterio de aceptacion de S1-M3-01, hay que averiguar por que "
            f"antes de seguir."
        )
    print(f"\n      el bosque supera al trivial por {delta:+.4f} de F1 macro.")
    if not detecta:
        print(
            "      PERO no detecta las dos clases extremas mejor que el azar: "
            f"F1 Maximo={bosque_r['f1_maximo']:.4f} (azar {aleatorio_r['f1_maximo']:.4f}), "
            f"F1 Minimo={bosque_r['f1_minimo']:.4f} (azar {aleatorio_r['f1_minimo']:.4f}).\n"
            "      El criterio de aceptacion se cumple por un margen que no es deteccion.\n"
            "      Esto va al informe tal cual: 'corre' y 'funciona' no son lo mismo."
        )
    else:
        print(
            "      Y detecta ambos extremos mejor que el azar: "
            f"F1 Maximo={bosque_r['f1_maximo']:.4f} (azar {aleatorio_r['f1_maximo']:.4f}), "
            f"F1 Minimo={bosque_r['f1_minimo']:.4f} (azar {aleatorio_r['f1_minimo']:.4f})."
        )


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
