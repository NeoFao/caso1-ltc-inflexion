"""Pestillo del bloque de prueba: que "se toco una sola vez" sea comprobable.

Por que existe
--------------
La D18 dice que el bloque de prueba se mide una sola vez, con el protocolo escrito
de antemano. Hasta ahora eso era una afirmacion del informe: nadie podia comprobarla
sin revisar el historial a mano y confiar en que nadie hubiera corrido nada fuera de
el.

Una promesa que solo se puede verificar leyendo commits no se verifica nunca. Este
modulo la convierte en un archivo: la primera evaluacion sobre `prueba` deja
constancia, y las siguientes fallan salvo declaracion explicita con motivo.

Lo que NO hace
--------------
No impide gastar la reserva. Eso seria falso: quien quiera puede borrar el archivo,
o llamar a las metricas directamente sin pasar por el arnes. Lo que hace es que
gastarla dos veces **deje rastro** en vez de pasar inadvertido, y que reutilizarla
exija escribir por que.

El objetivo no es la seguridad, es la trazabilidad. Contra el descuido, no contra la
mala fe.
"""

from __future__ import annotations

import json
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RUTA_PESTILLO = RAIZ / "docs" / "evidencias" / "prueba-consumida.json"

# La unidad del pestillo es la SESION DE MEDICION, no el modelo. Se genera una vez
# al importar el modulo, o sea una por proceso, que es lo que la seccion 8 del
# protocolo llama "una corrida": «la primera corrida sobre prueba escribe [...] los
# modelos evaluados», en plural y en una sola corrida.
#
# Antes la unidad era el modelo, y por eso una corrida sobre seis modelos moria en el
# segundo: el primero dejaba la constancia y el segundo la encontraba puesta. El
# pestillo funcionaba y el arnes funcionaba; lo que estaba mal era que median cosas
# distintas (issue #100).
SESION = uuid.uuid4().hex


class ReservaYaConsumida(RuntimeError):
    """La reserva ya se midio antes y esta corrida no declara por que se repite."""


def _mostrar(ruta: Path) -> Path:
    """La ruta relativa a la raiz si esta dentro, y la absoluta si no.

    `relative_to()` a secas revienta cuando la ruta cae fuera del proyecto, que es lo
    que pasa al inyectar un directorio temporal desde las pruebas. Un mensaje de
    error que falla al construirse esconde el error que iba a reportar.
    """
    return ruta.relative_to(RAIZ) if ruta.is_relative_to(RAIZ) else ruta


def _commit_actual() -> str:
    """El commit desde el que se midio, para que la cifra sea reproducible.

    Si no se puede determinar -- no hay git, o el arbol no es un repositorio -- se
    devuelve una marca explicita en vez de una cadena vacia: un campo vacio se lee
    como "no aplica" y esto es "no se pudo saber", que no es lo mismo.
    """
    try:
        salida = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return "no-determinable"
    return salida.stdout.strip() or "no-determinable"


def _arbol_limpio() -> bool | str:
    """Si habia cambios sin comitear al medir. Importa mas de lo que parece.

    Una cifra del informe medida sobre un arbol sucio no es reproducible: el commit
    que se registra no describe el codigo que la produjo.
    """
    try:
        salida = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return "no-determinable"
    return not salida.stdout.strip()


def consumir(
    modelos: list[str],
    *,
    motivo: str | None = None,
    ruta: Path = RUTA_PESTILLO,
    sesion: str = SESION,
) -> dict:
    """Registra modelos evaluados sobre el bloque de prueba en la sesion en curso.

    La primera llamada de una sesion abre una corrida. Las siguientes de la MISMA
    sesion le anaden sus modelos, sin volver a preguntar nada: evaluar seis modelos
    en una corrida es una sola medicion, no seis.

    Una sesion nueva sobre un registro que ya existe es lo que el pestillo tiene que
    frenar, y ahi `motivo` pasa a ser obligatorio. Se guarda junto al registro
    anterior en vez de reemplazarlo: el valor de este archivo esta en que acumule el
    historial completo, no en que muestre la ultima corrida.

    `sesion` se puede inyectar para que las pruebas simulen un segundo proceso. En
    produccion nadie lo pasa: sale de SESION, que es una por proceso.

    El archivo se reescribe en CADA llamada, y no al final de la sesion, a proposito.
    Una corrida que muera a la mitad si toco la reserva --alguien pudo ver esos
    numeros-- y tiene que dejar constancia de los modelos que alcanzo a medir. Un
    pestillo que solo se cierra cuando todo sale bien no sirve para el unico caso en
    que hace falta.
    """
    previo = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else None
    abierta = previo["corridas"][-1] if previo and previo.get("corridas") else None

    if abierta is not None and abierta.get("sesion") == sesion:
        # Misma corrida: se acumulan los modelos y no se vuelve a exigir motivo.
        abierta["modelos"] = sorted(set(abierta["modelos"]) | set(modelos))
        registro = previo
        corrida = abierta
    else:
        if previo is not None and not motivo:
            primera = previo["corridas"][0]
            raise ReservaYaConsumida(
                f"El bloque de prueba ya se midio el {primera['cuando_utc']} "
                f"(commit {primera['commit'][:8]}, "
                f"modelos: {', '.join(primera['modelos'])}).\n"
                "\n"
                "La D18 dice que se toca una sola vez y que el informe reporta la "
                "primera cifra que salga. Si de verdad hace falta repetirla, pasa "
                "motivo='...' explicando por que, y queda registrado junto a la "
                "anterior.\n"
                "\n"
                f"El registro esta en {_mostrar(ruta)}."
            )

        corrida = {
            "sesion": sesion,
            "cuando_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "modelos": sorted(modelos),
            "commit": _commit_actual(),
            "arbol_limpio": _arbol_limpio(),
            "motivo": motivo,
        }
        registro = previo or {
            "que_es": (
                "Constancia de cada sesion de medicion sobre el bloque de prueba. La "
                "D18 dice que se toca una sola vez; este archivo hace que repetirlo "
                "deje rastro. Una sesion es una corrida del guion, con todos los "
                "modelos que haya evaluado."
            ),
            "corridas": [],
        }
        registro["corridas"].append(corrida)

    registro["n_corridas"] = len(registro["corridas"])

    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(registro, indent=2, ensure_ascii=False), encoding="utf-8")
    return corrida


def esta_consumida(ruta: Path = RUTA_PESTILLO) -> bool:
    """Si la reserva ya se midio alguna vez. Sin efectos."""
    return ruta.exists()
