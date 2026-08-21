<!--
Antes de abrir el PR, tres preguntas. No son burocracia: cada una sale de un error
real que nos costó tiempo esta semana.
-->

## Qué hace

<!-- Cierra #N -->

## Los tres controles

- [ ] **Ningún número que no haya obtenido ejecutando.** Si cité una cifra, salió de
      correr algo y está en `docs/evidencias/`.
- [ ] **Todo número nuevo reproduce uno conocido.** Antes de publicar una medición
      nueva, comprobé que mi procedimiento reproduce un valor que ya conocíamos. Los
      cinco errores de la Semana 2 los atrapó ejecutar un control, no releer el diff.
- [ ] **Toda decisión que cito como acordada puede señalar dónde se acordó.** Si escribí
      "decidido por el equipo" o atribuí algo a alguien, hay una fila en
      [`docs/DECISIONES.md`](../docs/DECISIONES.md), un issue o un PR que lo respalda.
      **No un mensaje suelto.**

## Verificación

<!-- Pegá la salida, no la describas. -->

```
uv run pytest -q        →
uv run ruff check .     →
```

## Si toca una decisión vigente

Si el cambio contradice algo de [`docs/DECISIONES.md`](../docs/DECISIONES.md), las
pruebas de `tests/test_decisiones.py` van a fallar, y eso es deliberado.

**No las edites para que pasen.** El orden es: añadir la fila nueva en el documento con
la evidencia que justifica el cambio, marcar la anterior como reemplazada, y recién
entonces actualizar la prueba. Si el documento y la prueba se separan, queda una
restricción en el código sin razón escrita al lado.

## Alcance

- [ ] No toqué carpetas de otro módulo sin avisar por escrito.
- [ ] Si toqué `contracts/`, lo declaro acá y lo revisa quien lo consume.
