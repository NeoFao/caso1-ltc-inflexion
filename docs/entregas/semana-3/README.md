# Semana 3 — Modelo fundacional y pruebas de detección

Avance por separado, como pidió el profesor ([D26](../../DECISIONES.md#d26)). El mismo material
está también en el informe único; lo que cambia es el alcance, no las cifras.

## Qué contiene

| Capítulo | Archivo | Autor |
|---|---|---|
| Introducción | `m0-introduccion.md` | Fabrizio (M0) |
| Diseño | `m0-diseno.md` | Fabrizio (M0) |
| El modelo fundacional | `m3-fundacional.md` | Isaac (M3) |
| Pruebas de detección | `m0-pruebas-deteccion.md` | Fabrizio (M0) |
| Conclusión | `m0-conclusion.md` | Fabrizio (M0) |

## Cómo se regenera el Word

```bash
CARPETA_ENTREGA=semana-3 npm run ensamblar --prefix scripts
```

Después, abrir en Word, seleccionar el índice y pulsar F9: el campo del índice no trae los números
de página hasta que Word los calcula.

## Por qué los capítulos son copias y no texto nuevo

**Ninguna cifra vive aquí.** Los capítulos técnicos son los mismos archivos del informe final, para
que una cifra exista en un solo lugar y los dos documentos no se puedan desincronizar. Lo único
propio de esta entrega son la introducción y la conclusión.

La única diferencia con el original es la numeración de los pies de tabla: el ensamblador semanal
espera `**Tabla N.**` y renumera de corrido entre archivos, mientras que el informe final numera por
sección (`**Tabla 2.1.**`) porque se lee como un documento con secciones numeradas.
