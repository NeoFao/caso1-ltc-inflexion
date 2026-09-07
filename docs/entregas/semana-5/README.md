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

**Completo.** El ensamblador ya no marca bloques pendientes: la subsección 5.4 se rellenó con la
cifra de la corrida única del 07/09/2026, que se hizo una sola vez y quedó registrada en el pestillo
con `n_corridas: 1`.

El resultado, en una línea: **dos de las tres condiciones que el protocolo exige**. La diferencia
contra el azar es positiva y estable en signo, y su intervalo incluye el cero — así que el informe
reporta que **no se puede afirmar que el sistema detecte mejor que el azar sobre datos no vistos**.

Es la segunda de las tres lecturas que estaban escritas antes de conocer la cifra.
