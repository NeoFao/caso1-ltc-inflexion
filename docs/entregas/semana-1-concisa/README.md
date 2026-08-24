# Semana 1 — Marco teórico, versión concisa

**Esta carpeta contiene dos `.docx` y no son intercambiables.**

| Archivo | Qué es |
|---|---|
| `Marco teorico - Semana 1 (entregada18.8.26).docx` | **Lo que se entregó** el 18 de agosto de 2026. No se toca. |
| `Marco teorico - Semana 1 (concisa).docx` | La versión vigente, con la verificación sobre el panel de 4 horas añadida después. |

## Por qué hay dos

El 19 de agosto se añadió a esta versión la sección *Verificación sobre el panel de
trabajo*, que repite los diagnósticos de la Semana 1 sobre velas de 4 horas y reporta
que dos de los seis activos cambian de veredicto de estacionariedad al aumentar el
tamaño de muestra. Es una mejora real y por eso está.

Lo que estuvo mal fue **cómo** se hizo: al regenerar el `.docx` se borró el archivo que
llevaba la marca de entregado, de modo que durante cinco días el repositorio no
contenía el documento que el profesor recibió, sino uno parecido. La marca la había
pedido el PM justamente para que eso no pasara.

El archivo entregado se restauró desde el historial, byte a byte
(`md5 1e6339d28117138042f55784d6e1b0c0`, commit `92508e9`).

## La regla que salió de esto

Esto ocurrió el 19 de agosto a las 22:27. La [D11](../../DECISIONES.md) —*la evidencia
de una entrega hecha no se regenera*— se escribió el 20 a las 21:45, y la
[D13](../../DECISIONES.md) —*remedir produce evidencia nueva, nunca reescribe la
entregada*— el 21.

Las dos describen exactamente este caso. **Regenerar un entregable no es actualizarlo:
es perderlo**, porque nadie compara un `.docx` contra su recuerdo.

Para cambiar algo de una entrega hecha: se crea el archivo nuevo, se deja el entregado
como está, y se dice cuál es cuál. Que es lo que hace la tabla de arriba.
