"""Congela la comparacion de modelos para el panel de la aplicacion (S2-M1-01).

No mide nada nuevo (RF-U6): lee las metricas que M3 ya calculo y publico en
docs/evidencias/m3-modelos-profundos-4h-w7-h1.json -- los cinco modelos evaluados
sobre la MISMA particion de validacion, que es lo que hace valida la comparacion
lado a lado -- y las copia a app/public/datos/ con los nombres que la interfaz
necesita. Si M3 remide y el JSON de origen cambia, correr este script de nuevo
actualiza el panel sin que nadie edite un numero a mano.

Fase 1 del issue #92 (HumanoidCat encontro, Fabrizio decidio el alcance). El
panel publicaba el f1_macro de clasico y avanzado como si fuera "el" rendimiento
del modelo, cuando en realidad es UNA corrida entre cinco semillas, y la corrida
publicada resulto ser la mas alta de las cinco en los dos casos -- exageraba la
ventaja del clasico sobre el avanzado en un 20 %. La D18 declara las medias.

La correccion completa (que el panel publique la media, no la corrida) exige
volver a correr los barridos de sensibilidad registrando las seis metricas por
semilla -- hoy esos barridos solo registran f1_macro -- y eso es de M2 y M3, no
de este script. Lo que si se puede hacer sin ejecutar nada (fase 1, decidida por
Fabrizio en el issue): declarar cuales filas son una corrida individual y mostrar
el rango medido entre semillas al lado, leido de la evidencia de sensibilidad que
M2 y M3 ya midieron. No cambia ninguna cifra publicada; revela lo que ya habia.

Uso:
    uv run python app/scripts/generar_comparacion.py
"""

from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
EVIDENCIAS = RAIZ / "docs" / "evidencias"
ORIGEN = EVIDENCIAS / "m3-modelos-profundos-4h-w7-h1.json"
DESTINO = RAIZ / "app" / "public" / "datos" / "comparacion-modelos.json"

# Que modelo del JSON de origen entra al panel, con que rotulo y que papel juega
# segun las decisiones ya tomadas por el equipo: D7 (los tres baselines son el
# piso obligatorio -- se muestra el mas exigente, el aleatorio), D14 (avanzado:
# iTransformer con las seis series), D12 (fundacional: Chronos-Bolt), y el bosque
# aleatorio de referencia de S1-M3-01 como "clasico".
MODELOS = [
    ("baseline_aleatorio", "Baseline aleatorio", "piso obligatorio (D7)"),
    ("bosque_aleatorio_rezagos_relativos", "Clasico (bosque aleatorio)", "referencia (S1-M3-01)"),
    ("chronos_bolt", "Fundacional (Chronos-Bolt)", "D12"),
    ("itransformer", "Avanzado (iTransformer)", "D14"),
]

CAMPOS = (
    "f1_macro",
    "precision_direccional",
    "exactitud",
    "f1_maximo",
    "f1_minimo",
    "f1_continuidad",
)

# Issue #92: los unicos dos modelos que se entrenan con una semilla aleatoria.
# Baseline aleatorio usa semilla fija por diseno (D7) y Chronos-Bolt es zero-shot
# determinista, asi que ninguno de los dos necesita esta etiqueta. Cada entrada
# apunta al archivo de evidencia donde M2 o M3 ya midieron la sensibilidad, y a
# como llegar al bloque resumen (media, minimo, maximo, rango, desviacion) desde
# ahi -- ese bloque es el que da fe de que la fase 1 no inventa un numero nuevo.
SENSIBILIDAD_SEMILLA = {
    "bosque_aleatorio_rezagos_relativos": (
        "m2-incertidumbre-vigente-4h-w7-h1.json",
        lambda d: d["sensibilidad_a_la_semilla"]["f1_por_modelo"][
            "bosque_aleatorio_rezagos_relativos"
        ],
    ),
    "itransformer": (
        "m3-sensibilidad-avanzado-4h-w7-h1.json",
        lambda d: d["resumen_f1_completo"],
    ),
}


def _sensibilidad(clave: str) -> dict | None:
    if clave not in SENSIBILIDAD_SEMILLA:
        return None
    nombre_archivo, extraer = SENSIBILIDAD_SEMILLA[clave]
    ruta = EVIDENCIAS / nombre_archivo
    if not ruta.exists():
        raise SystemExit(
            f"falta {ruta.relative_to(RAIZ)}, evidencia de sensibilidad para {clave!r}"
        )
    bloque = extraer(json.loads(ruta.read_text(encoding="utf-8")))
    return {
        "corrida_individual": True,
        "media_multisemilla": round(bloque["media"], 4),
        "rango_semillas": round(bloque["rango"], 4),
        "fuente_sensibilidad": nombre_archivo,
    }


def main() -> None:
    if not ORIGEN.exists():
        raise SystemExit(
            f"falta {ORIGEN.relative_to(RAIZ)}. Es evidencia de M3, no se regenera aca."
        )

    fuente = json.loads(ORIGEN.read_text(encoding="utf-8"))
    metricas = fuente["metricas"]

    modelos = []
    for clave, etiqueta, papel in MODELOS:
        if clave not in metricas:
            raise SystemExit(f"{clave!r} no esta en {ORIGEN.name}; revisar MODELOS")
        m = metricas[clave]
        modelos.append(
            {
                "clave": clave,
                "etiqueta": etiqueta,
                "papel": papel,
                **{campo: m[campo] for campo in CAMPOS},
                **(_sensibilidad(clave) or {"corrida_individual": False}),
            }
        )

    salida = {
        "fuente": str(ORIGEN.relative_to(RAIZ)).replace("\\", "/"),
        "ejecutado_utc": fuente["ejecutado_utc"],
        "particion": fuente["parametros"],
        "n": metricas[MODELOS[0][0]]["n"],
        "modelos": modelos,
    }

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"escrito {DESTINO.relative_to(RAIZ)} con {len(modelos)} modelos")


if __name__ == "__main__":
    main()
