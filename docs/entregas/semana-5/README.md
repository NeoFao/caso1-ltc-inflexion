# Semana 5 — Informe final

Avance por separado, como pidió el profesor ([D26](../../DECISIONES.md#d26)). En esta semana el
avance **y** el informe único son el mismo documento: el enunciado pide para la Semana 5 la
presentación del reporte, así que separarlos produciría dos copias de lo mismo.

## Qué contiene

Los ocho archivos de `docs/entregas/informe-final/`, ensamblados en un Word con índice, tablas
renumeradas de corrido y referencias fundidas.

## Cómo se regenera el Word

```bash
CARPETA_ENTREGA=semana-5 npm run ensamblar --prefix scripts
```

## Estado

El ensamblador avisa de **un bloque sin redactar**, y está bien que avise: es la subsección 5.4, la
celda de la corrida única sobre el bloque de prueba. Es lo único que falta del informe, y se rellena
con la cifra de esa medición.

Las tres lecturas posibles de esa cifra están escritas de antemano en `05-rendimiento.md`, para que
rellenarla sea poner un número y no redactar un capítulo con el resultado delante.
