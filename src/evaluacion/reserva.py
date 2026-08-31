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
from datetime import UTC, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RUTA_PESTILLO = RAIZ / "docs" / "evidencias" / "prueba-consumida.json"


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
) -> dict:
    """Registra una evaluacion sobre el bloque de prueba, o falla si ya hubo una.

    `motivo` es obligatorio a partir de la segunda vez, y se guarda junto al registro
    anterior en vez de reemplazarlo: el valor de este archivo esta en que acumule el
    historial completo, no en que muestre la ultima corrida.
    """
    previo = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else None

    if previo is not None and not motivo:
        cuando = previo["corridas"][0]["cuando_utc"]
        raise ReservaYaConsumida(
            f"El bloque de prueba ya se midio el {cuando} "
            f"(commit {previo['corridas'][0]['commit'][:8]}, "
            f"modelos: {', '.join(previo['corridas'][0]['modelos'])}).\n"
            "\n"
            "La D18 dice que se toca una sola vez y que el informe reporta la primera "
            "cifra que salga. Si de verdad hace falta repetirla, pasa motivo='...' "
            "explicando por que, y queda registrado junto a la anterior.\n"
            "\n"
            f"El registro esta en {_mostrar(ruta)}."
        )

    corrida = {
        "cuando_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "modelos": sorted(modelos),
        "commit": _commit_actual(),
        "arbol_limpio": _arbol_limpio(),
        "motivo": motivo,
    }

    registro = previo or {
        "que_es": (
            "Constancia de cada evaluacion sobre el bloque de prueba. La D18 dice que "
            "se toca una sola vez; este archivo hace que repetirlo deje rastro."
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
