# Cómo producir la versión de ~45 páginas

**Estado: pendiente de ejecutar.** Este documento es autosuficiente: quien lo tome
no necesita haber estado en la conversación donde se decidió.

---

## 1. Qué existe hoy

| Versión | Carpeta | Palabras (Word) | Páginas |
|---|---|---|---|
| Extensa | `docs/entregas/semana-1/` | 13 710 | **62** |
| Concisa | `docs/entregas/semana-1-concisa/` | 10 832 | **54** |
| Objetivo de este documento | `docs/entregas/semana-1-breve/` | ~7 600 | **~45** |

La concisa ya es el resultado de una primera pasada de densificación que redujo un
25 % sin quitar ninguna figura, ninguna referencia ni ningún argumento.

## 2. La aritmética, medida

No hay que estimarla: se midió construyendo el documento y abriéndolo en Word.

> **24 páginas son fijas + 1 página por cada ~360 palabras de prosa.**

Las 24 páginas fijas se midieron construyendo una versión que conserva las 15
figuras, las 4 tablas, todos los pies, encabezados, portada, índice y las 30
referencias, **y borra toda la prosa**: dio 24 páginas con 1 970 palabras.

Achicar las figuras un 40 % (de 600 a 380 px de ancho) baja ese piso de 24 a **23**.
Una sola página. **Las figuras no son lo que ocupa**; lo son el índice, los pies a
doble espacio y sobre todo las 30 referencias con sangría francesa.

**Consecuencia:** 45 páginas = 24 fijas + 21 de prosa ≈ **7 600 palabras**. Desde las
10 832 actuales, hay que quitar unas 3 200.

**Por qué no se baja de ahí.** 35 páginas exigirían ~4 000 palabras para los 17
puntos del enunciado, es decir 235 por punto: alcanza para una definición, el número
medido y una frase de consecuencia, y no para el análisis. El análisis es el criterio
que más pesa en la rúbrica.

## 3. Qué NO se puede tocar

Estas son las restricciones. Romper cualquiera invalida el trabajo.

1. **Las 15 figuras se quedan todas.** Seis son series construidas por nosotros, y el
   profesor pidió expresamente en sesión que construyéramos series sintéticas con
   volatilidad y correlación fijadas de antemano.
2. **La sección 8.4, sensibilidad al ruido, se queda entera.** Es donde esa sugerencia
   del profesor produjo un resultado propio, y además la sección 4 de métricas depende
   de sus dos números (96,0 % y 72,9 %).
3. **Ningún valor numérico se borra** salvo que el mismo valor siga apareciendo en
   otro punto del documento. Se comprueba mecánicamente, ver el paso 6.
4. **Las 30 referencias y todas las citas en el texto se quedan.**
5. **Los 17 puntos del enunciado conservan su encabezado propio.**
6. **Nadie edita `docs/entregas/semana-1/` ni `docs/entregas/semana-1-concisa/`.** La
   versión nueva va en carpeta aparte.

## 4. Qué sí se recorta, y cómo

Lo que funcionó en la primera pasada, por orden de rendimiento:

**a) Prosa que repite el bloque «Medido».** Cada sección abre con los valores medidos
y después el párrafo los vuelve a decir. La regla: la cabecera **da** el número, la
prosa lo **interpreta**. Si el párrafo repite la cifra, se reescribe para que explique
qué implica, no para que la enuncie otra vez.

**b) Aposiciones largas entre rayas.** Había 52 en el documento original. Casi todas
caben como frase corta aparte o se eliminan.

**c) Oraciones que anuncian lo que se va a decir.** «Lo que sigue es…», «conviene
separar en dos partes», «la lectura de la figura tiene dos partes». Se borran y se
entra directo.

**d) Muletillas de enlace.** «de modo que», «por lo tanto», «en consecuencia», «es
decir». Había 23. La mitad sobra.

**e) Oraciones de más de 40 palabras.** Había 70. Partirlas suele acortarlas.

**f) Argumentos contados dos veces en secciones distintas.** El de nivel contra
retornos aparecía seis veces. La segunda mención debe remitir a la primera en una
frase, no reconstruir el argumento.

**Lo que no es recortar:** quitar una advertencia metodológica, un «esto no permite
afirmar que», una limitación declarada o una cita. Eso es contenido y es lo que
distingue el trabajo.

## 5. Procedimiento

```bash
cp -r docs/entregas/semana-1-concisa docs/entregas/semana-1-breve
```

Borrar de la copia el `.docx` heredado antes de empezar, para no confundirlo con el
que se va a generar.

Reescribir los cinco `.md` aplicando el punto 4. Medir el avance con:

```bash
python -c "import glob;print(sum(len(open(f,encoding='utf-8').read().split()) for f in glob.glob('docs/entregas/semana-1-breve/*.md')))"
```

**Objetivo: ~7 800 palabras de markdown**, que en Word dan unas 7 600 y unas 45
páginas. El markdown cuenta un poco más porque incluye encabezados y tablas.

Ensamblar:

```bash
CARPETA_ENTREGA=semana-1-breve npm run ensamblar --prefix scripts
```

El ensamblador acepta la carpeta por variable de entorno, que es lo que permite
construir variantes sin sobrescribir la versión vigente. Renombrar la salida a
`Marco teorico - Semana 1 (breve).docx`.

## 6. Verificación obligatoria

Los cuatro chequeos, todos antes de dar la versión por buena.

**Que ningún número quedó sin respaldo:**

```bash
uv run python scripts/verificar_numeros.py
```

**Que ningún número desapareció del documento** respecto de la concisa. Cualquier
valor que aparezca en la lista tiene que estar justificado por escrito:

```bash
python -c "import re,glob;a=set(re.findall(r'\d+,\d+',''.join(open(f,encoding='utf-8').read() for f in glob.glob('docs/entregas/semana-1-concisa/*.md'))));b=set(re.findall(r'\d+,\d+',''.join(open(f,encoding='utf-8').read() for f in glob.glob('docs/entregas/semana-1-breve/*.md'))));print(sorted(a-b) or 'ninguno')"
```

**Que el documento generado está completo.** El ensamblador tiene que decir
`sin bloques pendientes`, 15 figuras y 4 tablas renumeradas de corrido, y 30
referencias fundidas.

**Que las referencias siguen vigentes:**

```bash
uv run python scripts/verificar_referencias.py docs/entregas/semana-1-breve/*.md
```

## 7. El paso manual que no se puede automatizar

El índice se escribe como campo de Word sin resultado calculado, así que **abre en
blanco**. Antes de entregar hay que abrir el `.docx`, seleccionar el índice y pulsar
F9. El propio comando de ensamblado lo recuerda al terminar.

## 8. Después de generarla

La guía de defensa y el guion de exposición viven en `docs/defensa/`. Hay un par por
cada versión del documento.

- **El guion no cambia.** Se comprobó que las ocho figuras que proyecta llevan el
  mismo número y el mismo pie en todas las versiones, y que ningún dato dicho en voz
  alta desaparece al condensar.
- **La guía de defensa sí.** Hay que actualizar el recuento de páginas y palabras, y
  revisar si algún número que la guía da por impreso en el documento dejó de estarlo.
  Si eso ocurre, ese número pasa a memoria obligatoria y hay que decirlo en la guía,
  como ya se hizo con el piso de 300, los 149 y los 420 en la versión concisa.

## 9. Pendiente sin resolver

Al cerrar la sesión que produjo este documento quedaron en `docs/entregas/` dos
carpetas, `_tmp-concisa-sf` y `_tmp-extensa-sf`, con los dos documentos **sin ninguna
imagen** y sin índice. No las creó el proceso descrito aquí y no se sabe su propósito.
Además el `.docx` de la versión concisa figura como borrado en git y hay uno
renombrado sin versionar.

**Hay que resolver eso antes de seguir**, porque mientras tanto no está claro cuál es
el archivo vigente de la versión concisa.
