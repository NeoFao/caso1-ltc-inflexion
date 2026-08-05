# Guías del equipo

Una por persona. Buscá la tuya y seguila de arriba abajo.

| Persona | Módulo | Guía |
|---|---|---|
| Fabrizio Espinoza | M0 · Infraestructura, contratos, evaluación, integración | [fabrizio.md](fabrizio.md) |
| Jose Pablo Monestel | M1 · Datos, diagnóstico y aplicación web | [monestel.md](monestel.md) |
| Alejandro Zamora | M2 · Etiquetado, sintéticos y características | [alejandro.md](alejandro.md) |
| Isaac Morun | M3 · Modelo fundacional y modelo avanzado | [isaac.md](isaac.md) |

---

## Lo que vale para los cuatro

### Antes de tocar nada

```bash
pip install uv
```

```bash
uv sync --group dev
```

```bash
uv run pytest -q
```

Si las 44 pruebas pasan, tu entorno está bien. Si no, escribilo en el grupo antes de seguir: no es tu culpa y no lo arregles a mano, porque un entorno distinto al de los demás produce resultados distintos.

**Un error conocido en Windows.** Si `uv sync` falla con `Missing expected target directory for Python minor version link`, borrá el enlace y volvé a intentar:

```bash
rm -rf "$APPDATA/uv/python/cpython-3.14-windows-x86_64-none" && uv sync --group dev
```

Es un fallo de `uv`, no tuyo. Pasó en la máquina donde se montó el proyecto y la segunda corrida funcionó.

### Cómo se trabaja

1. **Nunca trabajás en `main`.** Tu rama se llama `feat/<tu-modulo>-<lo-que-hacés>`, por ejemplo `feat/m1-adf-estacionariedad`.
2. **Subís todos los días**, aunque esté a medias. Un día sin subir nada es una señal de alarma, no un problema de disciplina.
3. **Solo editás tus carpetas.** Si necesitás algo de otro módulo, se pide por escrito. No hay excepciones "porque era rapidito".
4. **Antes de abrir un PR:** `uv run pytest -q` y `uv run ruff check .` tienen que pasar.
5. **`contracts/` no se toca.** Si creés que un contrato está mal, lo decís; no lo cambiás.

### Cuándo terminaste una tarea

Las cuatro cosas, no la primera:

- [ ] Código en tu rama, con sus pruebas pasando
- [ ] Un número que salió de ejecutar algo, no de estimarlo
- [ ] Tu sección del documento, con las figuras numeradas y referenciadas en el texto
- [ ] Un slide con lo esencial

### Si te trabás

Más de un día trabado, lo decís. En un proyecto de cinco semanas un día perdido es el 3 % del tiempo. Nadie va a pensar menos de vos por preguntar; sí por callarte tres días.

### Lo que nunca se hace

- Reportar un número que no obtuviste ejecutando. Si no lo corriste: **"no lo he medido"**.
- Concluir a partir de una salida que se cortó.
- Presentar algo que construiste vos como si fuera lo que pasa en los datos reales.
- Decir "funciona" cuando lo que probaste es que "corre".
