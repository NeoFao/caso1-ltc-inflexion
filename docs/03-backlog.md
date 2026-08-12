# Backlog

**Quien hace que, en que orden y contra que criterio se da por terminado.**

Generado el 12/08/2026 desde los issues del repositorio con `uv run python scripts/generar_backlog.py`.

Este documento es una **foto**. La fuente de verdad es el tablero: si algo difiere, manda [GitHub](https://github.com/NeoFao/caso1-ltc-inflexion/issues). Cada issue trae la guia paso a paso con los comandos y el codigo a correr; aca solo esta el indice.

---

## Quien es quien

| Modulo | Persona | Usuario | De que responde |
|---|---|---|---|
| **M0** | Fabrizio Espinoza | `NeoFao` | Infraestructura, contratos, evaluacion e integracion |
| **M1** | Jose Pablo Monestel | `JpMonestelC` | Datos, diagnostico y aplicacion web |
| **M2** | Alejandro Zamora | `HumanoidCat` | Etiquetado, sinteticos y caracteristicas |
| **M3** | Isaac Morun | `PipeDevGit` | Modelo fundacional y modelo avanzado |

**Nadie comparte tarea con nadie.** Cada persona tiene sus carpetas y nadie edita archivos ajenos sin avisar por escrito.

---

## Como leer el nombre de una tarea

```
S1-M2-03 · Indicadores tecnicos sin fuga de informacion
│  │  │
│  │  └── orden sugerido dentro del modulo: mediciones primero, redaccion al final
│  └───── modulo, o sea la persona
└──────── sprint
```

Ordenados alfabeticamente quedan agrupados por sprint, dentro por persona, y dentro en el orden en que conviene hacerlos.

---

## Sprint 1 — Marco teorico y datos

**Entrega: 2026-08-18** · 20 abiertos de 20

### Fabrizio Espinoza

- [ ] [S1-M0-01 · Enviar la consulta al profesor](https://github.com/NeoFao/caso1-ltc-inflexion/issues/1)
- [ ] [S1-M0-02 · Recolectar las especificaciones de maquina de cada integrante](https://github.com/NeoFao/caso1-ltc-inflexion/issues/2)
- [ ] [S1-M0-03 · Congelar w, h y granularidad en contracts/config.py](https://github.com/NeoFao/caso1-ltc-inflexion/issues/3) — toca `contracts/`
- [ ] [S1-M0-04 · Publicar el backend en Hugging Face Spaces](https://github.com/NeoFao/caso1-ltc-inflexion/issues/4)
- [ ] [S1-M0-05 · Ensamblar y entregar la Semana 1](https://github.com/NeoFao/caso1-ltc-inflexion/issues/39) — entra al documento

### Jose Pablo Monestel

- [ ] [S1-M1-01 · Tabla de estacionariedad ADF, en nivel y en retornos](https://github.com/NeoFao/caso1-ltc-inflexion/issues/5) — entra al documento
- [ ] [S1-M1-02 · Autocorrelacion de LTC](https://github.com/NeoFao/caso1-ltc-inflexion/issues/6) — entra al documento
- [ ] [S1-M1-03 · Matriz de correlacion cruzada entre las seis criptomonedas](https://github.com/NeoFao/caso1-ltc-inflexion/issues/7) — entra al documento
- [ ] [S1-M1-04 · Volatilidad movil y evidencia de heterocedasticidad](https://github.com/NeoFao/caso1-ltc-inflexion/issues/8) — entra al documento
- [ ] [S1-M1-05 · Series sinteticas con volatilidad y correlacion controladas para el marco teorico](https://github.com/NeoFao/caso1-ltc-inflexion/issues/38) — entra al documento
- [ ] [S1-M1-06 · Seccion teorica: series temporales](https://github.com/NeoFao/caso1-ltc-inflexion/issues/9) — entra al documento

### Alejandro Zamora

- [ ] [S1-M2-01 · Spike: sensibilidad del etiquetador al ruido](https://github.com/NeoFao/caso1-ltc-inflexion/issues/10) — entra al documento
- [ ] [S1-M2-02 · Indicadores tecnicos sin fuga de informacion](https://github.com/NeoFao/caso1-ltc-inflexion/issues/11)
- [ ] [S1-M2-03 · Caracteristicas de ventana deslizante](https://github.com/NeoFao/caso1-ltc-inflexion/issues/12)
- [ ] [S1-M2-04 · Elegir los ordenes de rezago con medicion](https://github.com/NeoFao/caso1-ltc-inflexion/issues/34)
- [ ] [S1-M2-05 · Seccion teorica: criptoactivos y punto de inflexion](https://github.com/NeoFao/caso1-ltc-inflexion/issues/13) — entra al documento
- [ ] [S1-M2-06 · Seccion teorica: metricas de evaluacion para puntos de inflexion](https://github.com/NeoFao/caso1-ltc-inflexion/issues/33) — entra al documento

### Isaac Morun

- [ ] [S1-M3-01 · Modelo clasico de referencia, de punta a punta](https://github.com/NeoFao/caso1-ltc-inflexion/issues/14)
- [ ] [S1-M3-02 · Spike: es viable CryptoMamba sin CUDA?](https://github.com/NeoFao/caso1-ltc-inflexion/issues/15)
- [ ] [S1-M3-03 · Spike: inventario de modelos fundacionales que corran en CPU](https://github.com/NeoFao/caso1-ltc-inflexion/issues/16)

---

## Sprint 2 — Modelos y pipeline

**Entrega: 2026-08-25** · 9 abiertos de 9

### Fabrizio Espinoza

- [ ] [S2-M0-01 · Ensamblador del documento semanal](https://github.com/NeoFao/caso1-ltc-inflexion/issues/18)
- [ ] [S2-M0-02 · Seccion del pipeline en el documento](https://github.com/NeoFao/caso1-ltc-inflexion/issues/22) — entra al documento
- [ ] [S2-M0-03 · Ensamblar y entregar la Semana 2](https://github.com/NeoFao/caso1-ltc-inflexion/issues/40) — entra al documento

### Jose Pablo Monestel

- [ ] [S2-M1-01 · Esqueleto de la aplicacion contra datos falsos](https://github.com/NeoFao/caso1-ltc-inflexion/issues/19)

### Alejandro Zamora

- [ ] [S2-M2-01 · Escalado ajustado solo con datos de entrenamiento](https://github.com/NeoFao/caso1-ltc-inflexion/issues/20)
- [ ] [S2-M2-02 · Feature engineering con herramientas posteriores a 2025](https://github.com/NeoFao/caso1-ltc-inflexion/issues/35) — entra al documento

### Isaac Morun

- [ ] [S2-M3-01 · Decidir y justificar el modelo fundacional](https://github.com/NeoFao/caso1-ltc-inflexion/issues/21)
- [ ] [S2-M3-02 · Seccion teorica: TSFMs, VTA, FinLSPM y CryptoMamba](https://github.com/NeoFao/caso1-ltc-inflexion/issues/17) — entra al documento
- [ ] [S2-M3-03 · Seccion teorica: modelos estadisticos clasicos y de machine learning](https://github.com/NeoFao/caso1-ltc-inflexion/issues/36) — entra al documento

---

## Sprint 3 — Modelo fundacional

**Entrega: 2026-09-01** · 5 abiertos de 5

### Fabrizio Espinoza

- [ ] [S3-M0-01 · Pruebas de deteccion: sintetico, entrenamiento y tiempo real](https://github.com/NeoFao/caso1-ltc-inflexion/issues/26) — entra al documento
- [ ] [S3-M0-02 · Ensamblar y entregar la Semana 3](https://github.com/NeoFao/caso1-ltc-inflexion/issues/41) — entra al documento

### Jose Pablo Monestel

- [ ] [S3-M1-01 · Modos sintetico e historico conectados al modelo real](https://github.com/NeoFao/caso1-ltc-inflexion/issues/24)

### Alejandro Zamora

- [ ] [S3-M2-01 · Medicion de importancia de caracteristicas](https://github.com/NeoFao/caso1-ltc-inflexion/issues/25) — entra al documento

### Isaac Morun

- [ ] [S3-M3-01 · Modelo fundacional funcionando y evaluado](https://github.com/NeoFao/caso1-ltc-inflexion/issues/23) — entra al documento

---

## Sprint 4 — Modelo avanzado

**Entrega: 2026-09-08** · 6 abiertos de 6

### Fabrizio Espinoza

- [ ] [S4-M0-01 · Comparacion fundacional contra avanzado y decision final](https://github.com/NeoFao/caso1-ltc-inflexion/issues/30) — entra al documento
- [ ] [S4-M0-02 · Ensamblar y entregar la Semana 4](https://github.com/NeoFao/caso1-ltc-inflexion/issues/42) — entra al documento

### Jose Pablo Monestel

- [ ] [S4-M1-01 · Modo tiempo real en la aplicacion](https://github.com/NeoFao/caso1-ltc-inflexion/issues/28)

### Alejandro Zamora

- [ ] [S4-M2-01 · Ablaciones: aporta realmente el enfoque multivariante?](https://github.com/NeoFao/caso1-ltc-inflexion/issues/29) — entra al documento

### Isaac Morun

- [ ] [S4-M3-01 · Modelo avanzado funcionando y evaluado](https://github.com/NeoFao/caso1-ltc-inflexion/issues/27) — entra al documento
- [ ] [S4-M3-02 · Optimizacion de hiperparametros de ambos modelos](https://github.com/NeoFao/caso1-ltc-inflexion/issues/37) — entra al documento

---

## Sprint 5 — Reporte final

**Entrega: 2026-09-15** · 3 abiertos de 3

### Fabrizio Espinoza

- [ ] [S5-M0-01 · Ensamblar y entregar la Semana 5](https://github.com/NeoFao/caso1-ltc-inflexion/issues/43) — entra al documento

### Todo el equipo

- [ ] [S5-MX-01 · Reporte final ensamblado](https://github.com/NeoFao/caso1-ltc-inflexion/issues/31)
- [ ] [S5-MX-02 · Ensayo con exposicion cruzada](https://github.com/NeoFao/caso1-ltc-inflexion/issues/32)

---

## Cuando una tarea esta terminada

- [ ] Codigo en la rama, con sus pruebas pasando
- [ ] Un numero obtenido ejecutando, no estimando
- [ ] La seccion del documento, con figuras numeradas y referenciadas
- [ ] Slide con lo esencial — **solo desde la Semana 3**

En las semanas 1 y 2 el profesor pidio documento, no presentacion.

## Como filtrar lo tuyo

```bash
gh issue list --assignee @me --state open
```
