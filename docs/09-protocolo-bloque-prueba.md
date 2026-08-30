# Protocolo para tocar el bloque de prueba, escrito antes de tocarlo

**Autor:** Alejandro Zamora (M2) · **Estado: PROPUESTA.** No es una decisión hasta que el equipo
la acepte y quede como fila en `DECISIONES.md`.

> **Lo que este documento intenta impedir.** Que el resultado final del proyecto se decida después
> de verlo.

---

## 1. Por qué esto hace falta ahora

**El bloque de prueba no se ha tocado nunca, y eso está bien.** Lo verifiqué:
`docs/evidencias/resultados.csv` tiene 40 evaluaciones y **las 40 son sobre validación**. Ni el
bosque, ni Chronos-Bolt, ni iTransformer han visto la reserva.

Lo que no existe es **cómo se va a tocar**. `DECISIONES.md` tiene diecisiete decisiones y ninguna
habla del bloque de prueba. El informe final lo necesita, y hasta hoy el procedimiento vive en la
cabeza de cada uno.

Es el mismo hueco que la D16 llenó para las semillas y la D13 para la evidencia remedida: la
práctica era correcta, pero no estaba escrita, así que dependía de que nadie se olvidara.

**Escribirlo antes de mirar es lo único que hace que el resultado signifique algo.** Después de
ver el número, cualquier criterio que elijamos estará contaminado por conocerlo — y no por mala fe,
sino porque es imposible desconocerlo.

## 2. Lo que ya sabemos del bloque, y por qué saberlo no lo contamina

Estos datos salen de contar filas y etiquetas, sin evaluar ningún modelo. Conocer el tamaño y el
balance no gasta la reserva; lo que la gasta es medir un modelo sobre ella.

**Partición** (`4h`, `w = 7`, `h = 1`, con embargo de `w + h`):

| Conjunto | n | Desde | Hasta |
|---|---|---|---|
| Entrenamiento | 9 171 | 2020-08-11 | 2024-10-17 |
| Validación | 1 959 | 2024-10-19 | 2025-09-10 |
| **Prueba** | **1 968** | **2025-09-11** | **2026-08-05** |

**Balance del bloque de prueba** (1 960 filas con etiqueta):

| Clase | n | % |
|---|---|---|
| Máximo | 86 | 4,39 |
| Mínimo | 86 | 4,39 |
| Continuidad | 1 788 | 91,22 |

**Los tres baselines ya están medidos sobre prueba**, y eso tampoco la gasta: ninguno se elige ni
se ajusta mirando el resultado.

| Baseline | F1 macro | Exactitud | PD |
|---|---|---|---|
| Trivial | 0,3180 | 0,9122 | 0,0000 |
| Mayoritario | 0,3180 | 0,9122 | 0,0000 |
| **Aleatorio** | **0,3435** | 0,8306 | 0,0640 |

El aleatorio vuelve a ser el piso exigente, igual que en validación (D7).

**Un dato que conviene tener presente antes de mirar nada:** el bloque de prueba está **más
desbalanceado** que validación —91,22 % de Continuidad contra 90,15 %— y tiene 86 ejemplos por
clase extrema. Con esa cantidad, unos pocos aciertos mueven el F1 macro de forma apreciable. El
intervalo va a ser ancho, y eso es una propiedad del conjunto, no del modelo.

## 3. Qué se evalúa: se fija ahora, no después

Se evalúa **una configuración por familia de modelo**, elegida sobre validación y **congelada
antes de correr nada**. La lista va aquí para que quede en el repositorio con fecha anterior al
resultado:

| Familia | Configuración | F1 macro en validación |
|---|---|---|
| Clásico | `bosque_aleatorio_rezagos_relativos` | 0,3905 |
| Fundacional | `chronos_bolt` | *(la que M3 declare)* |
| Avanzado | `itransformer` | *(la que M3 declare)* |

Más los tres baselines, que ya están.

**No se evalúan variantes.** Nada de `sin_rezagos`, `solo_LTC`, `sin_pesos` ni configuraciones
alternativas de hiperparámetros. Cada variante adicional es otra oportunidad de que alguna quede
bien por azar, y elegir después la que quedó mejor es exactamente lo que la reserva existe para
impedir.

M3 completa las dos celdas vacías **antes** de la corrida, no después.

## 4. Qué se reporta

La misma maquinaria que se usó en validación, para que las cifras sean comparables:

- **F1 macro y Precisión Direccional**, con intervalo del 95 % por bootstrap estratificado.
- **Diferencia contra cada baseline con remuestreo pareado** — no dos intervalos por separado,
  por lo que ya está escrito en `incertidumbre.py`.
- **Cinco semillas** (D16), reportando media y rango.
- **Matriz de confusión** de cada modelo.

Y una comparación explícita **validación contra prueba** para cada modelo, porque la caída entre
las dos es información sobre cuánto nos apoyamos en validación al elegir.

## 5. La regla de decisión, fijada de antemano

El proyecto declara que **detecta puntos de inflexión** si, sobre el bloque de prueba, el mejor
modelo cumple **las tres**:

1. supera al `baseline_aleatorio` en F1 macro,
2. el intervalo del 95 % de esa diferencia **excluye el cero**, y
3. el signo **no cambia** entre las cinco semillas.

Son las mismas tres condiciones que la D16 exige para cualquier diferencia. No se inventa un
criterio nuevo para el resultado final.

**El umbral de 0,02 (D5) no se aplica aquí.** Ese umbral se fijó para decidir *entre modelos
nuestros*; contra un baseline, lo que importa es si la diferencia se distingue del azar.

## 6. Lo que el informe dice en cada caso, escrito antes de saber cuál toca

Esta es la parte que más incomoda escribir y la que más sirve.

**Si se cumplen las tres condiciones:** el sistema detecta puntos de inflexión mejor que el azar
sobre datos que no vio nunca, con esta definición de punto de inflexión y esta granularidad. Se
reporta la cifra con su intervalo y la caída respecto de validación.

**Si la diferencia es positiva pero el intervalo incluye el cero:** no podemos afirmar que detecte
mejor que el azar sobre prueba. Se reporta así, junto con el resultado de validación, y se dice que
la diferencia entre ambos conjuntos es la que cabe esperar cuando se elige mirando uno de ellos.

**Si la diferencia es negativa:** se reporta que el modelo no supera al azar sobre datos nuevos.
**No se busca una configuración que sí lo haga.** El proyecto sigue siendo válido —el método, los
controles y los resultados negativos bien medidos son la contribución— y esa sería la conclusión
honesta.

En los tres casos el informe reporta **la misma cifra**: la primera y única que salga.

## 7. Lo que queda prohibido después de la corrida

- Cambiar el modelo elegido.
- Ajustar hiperparámetros, umbrales, `w`, `h` o granularidad.
- Correr más semillas y quedarse con un subconjunto.
- Volver a correrlo "para confirmar".
- Agregar o quitar características.

Si algo de esto hiciera falta por un error real —un fallo de código, no un resultado
decepcionante—, se declara en `DECISIONES.md` **qué se corrigió y por qué**, y el informe dice que
la reserva se tocó dos veces. Un bloque de prueba usado dos veces con eso declarado sigue siendo
interpretable; usado dos veces en silencio, no.

## 8. Cómo hacer que "una sola vez" sea comprobable

Una regla que depende de que nadie se olvide no es una regla; es una intención. Propongo un
pestillo en `src/evaluacion/`:

- La primera corrida sobre prueba escribe `docs/evidencias/prueba-consumida.json` con la fecha, el
  commit, los modelos evaluados y el hash de sus predicciones.
- Cualquier corrida posterior sobre prueba **falla** si ese archivo existe, salvo que se le pase
  explícitamente algo como `--segunda-vez-declarada`, que además exige un motivo escrito y lo
  agrega al archivo.

Así, "la reserva se tocó una sola vez" deja de ser una afirmación del informe y pasa a ser algo que
cualquiera puede verificar mirando un archivo versionado.

`src/evaluacion/` no es mi carpeta, así que lo propongo en vez de escribirlo. Si M0 quiere, lo
implemento yo.

## 9. Qué pido concretamente

1. Que M3 complete las dos celdas de la sección 3 **antes** de cualquier corrida.
2. Que esto se acepte —o se corrija— y quede como fila en `DECISIONES.md`. Mientras sea solo este
   documento, es la opinión de quien lo escribió, y la regla 3 dice exactamente eso.
3. Que quien corra la evaluación final sea **una sola persona, una sola vez**, con el protocolo ya
   aceptado.

---

> **Nota.** Nada de este documento afirma un resultado. Todas las cifras que trae son de
> validación, del conteo de filas del bloque de prueba, o de los tres baselines, que no lo gastan.
