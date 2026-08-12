"""Genera docs/03-backlog.md a partir de los issues de GitHub.

El backlog se genera y no se escribe a mano por una razon concreta: un documento
de tareas mantenido en paralelo con el tablero se desincroniza en dias, y despues
nadie sabe cual de los dos manda. Aqui manda GitHub; este documento es una foto
con fecha, util para leer de corrido o para adjuntar a una entrega.

Uso:
    uv run python scripts/generar_backlog.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DESTINO = RAIZ / "docs" / "03-backlog.md"
REPO = "NeoFao/caso1-ltc-inflexion"

PERSONAS = {
    "M0-infra": (
        "Fabrizio Espinoza", "NeoFao", "Infraestructura, contratos, evaluacion e integracion"
    ),
    "M1-datos-app": ("Jose Pablo Monestel", "JpMonestelC", "Datos, diagnostico y aplicacion web"),
    "M2-features": ("Alejandro Zamora", "HumanoidCat", "Etiquetado, sinteticos y caracteristicas"),
    "M3-modelos": ("Isaac Morun", "PipeDevGit", "Modelo fundacional y modelo avanzado"),
}


def gh(*argumentos: str) -> str:
    resultado = subprocess.run(
        ["gh", *argumentos], capture_output=True, text=True, encoding="utf-8"
    )
    if resultado.returncode != 0:
        sys.exit(f"fallo `gh {' '.join(argumentos)}`: {resultado.stderr.strip()}")
    return resultado.stdout


def main() -> None:
    issues = json.loads(
        gh("issue", "list", "-R", REPO, "-L", "200", "--state", "all",
           "--json", "number,title,state,milestone,labels,assignees,url")
    )
    hitos = json.loads(gh("api", f"repos/{REPO}/milestones?state=all&per_page=100"))
    vencimiento = {h["title"]: (h["due_on"] or "")[:10] for h in hitos}

    por_sprint: dict[str, list[dict]] = {}
    for issue in issues:
        titulo_hito = (issue["milestone"] or {}).get("title", "Sin sprint")
        por_sprint.setdefault(titulo_hito, []).append(issue)

    lineas = [
        "# Backlog",
        "",
        "**Quien hace que, en que orden y contra que criterio se da por terminado.**",
        "",
        f"Generado el {datetime.now(UTC).strftime('%d/%m/%Y')} desde los issues del repositorio "
        f"con `uv run python scripts/generar_backlog.py`.",
        "",
        "Este documento es una **foto**. La fuente de verdad es el tablero: si algo difiere, "
        f"manda [GitHub](https://github.com/{REPO}/issues). Cada issue trae la guia paso a paso "
        "con los comandos y el codigo a correr; aca solo esta el indice.",
        "",
        "---",
        "",
        "## Quien es quien",
        "",
        "| Modulo | Persona | Usuario | De que responde |",
        "|---|---|---|---|",
    ]
    for etiqueta, (nombre, usuario, area) in PERSONAS.items():
        codigo = etiqueta.split("-")[0]
        lineas.append(f"| **{codigo}** | {nombre} | `{usuario}` | {area} |")

    lineas += [
        "",
        "**Nadie comparte tarea con nadie.** Cada persona tiene sus carpetas y nadie edita "
        "archivos ajenos sin avisar por escrito.",
        "",
        "---",
        "",
        "## Como leer el nombre de una tarea",
        "",
        "```",
        "S1-M2-03 · Indicadores tecnicos sin fuga de informacion",
        "│  │  │",
        "│  │  └── orden sugerido dentro del modulo: mediciones primero, redaccion al final",
        "│  └───── modulo, o sea la persona",
        "└──────── sprint",
        "```",
        "",
        "Ordenados alfabeticamente quedan agrupados por sprint, dentro por persona, y dentro "
        "en el orden en que conviene hacerlos.",
        "",
        "---",
        "",
    ]

    for titulo_hito in sorted(por_sprint, key=lambda t: vencimiento.get(t, "9")):
        lista = por_sprint[titulo_hito]
        vence = vencimiento.get(titulo_hito, "sin fecha")
        abiertos = sum(1 for i in lista if i["state"] == "OPEN")
        lineas += [
            f"## {titulo_hito}",
            "",
            f"**Entrega: {vence}** · {abiertos} abiertos de {len(lista)}",
            "",
        ]
        for etiqueta, (nombre, _, _) in PERSONAS.items():
            suyos = sorted(
                (i for i in lista if any(e["name"] == etiqueta for e in i["labels"])),
                key=lambda i: i["title"],
            )
            if not suyos:
                continue
            lineas += [f"### {nombre}", ""]
            for issue in suyos:
                marca = "x" if issue["state"] == "CLOSED" else " "
                etiquetas = {e["name"] for e in issue["labels"]}
                senales = []
                if "bloquea" in etiquetas:
                    senales.append("**bloquea a otros**")
                if "contrato" in etiquetas:
                    senales.append("toca `contracts/`")
                if "entregable" in etiquetas:
                    senales.append("entra al documento")
                sufijo = f" — {', '.join(senales)}" if senales else ""
                lineas.append(f"- [{marca}] [{issue['title']}]({issue['url']}){sufijo}")
            lineas.append("")

        sin_modulo = [i for i in lista if not any(e["name"] in PERSONAS for e in i["labels"])]
        if sin_modulo:
            lineas += ["### Todo el equipo", ""]
            for issue in sorted(sin_modulo, key=lambda i: i["title"]):
                marca = "x" if issue["state"] == "CLOSED" else " "
                lineas.append(f"- [{marca}] [{issue['title']}]({issue['url']})")
            lineas.append("")
        lineas.append("---")
        lineas.append("")

    lineas += [
        "## Cuando una tarea esta terminada",
        "",
        "- [ ] Codigo en la rama, con sus pruebas pasando",
        "- [ ] Un numero obtenido ejecutando, no estimando",
        "- [ ] La seccion del documento, con figuras numeradas y referenciadas",
        "- [ ] Slide con lo esencial — **solo desde la Semana 3**",
        "",
        "En las semanas 1 y 2 el profesor pidio documento, no presentacion.",
        "",
        "## Como filtrar lo tuyo",
        "",
        "```bash",
        "gh issue list --assignee @me --state open",
        "```",
        "",
    ]

    DESTINO.write_text("\n".join(lineas), encoding="utf-8")
    print(f"escrito: {DESTINO.relative_to(RAIZ)}  ({len(issues)} issues, {len(lineas)} lineas)")


if __name__ == "__main__":
    main()
