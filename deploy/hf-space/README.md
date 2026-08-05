---
title: Puntos de inflexion LTC - backend
emoji: 📈
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Backend — Pronóstico de puntos de inflexión en LTC

API de solo lectura que sirve las series, las etiquetas y las métricas del Caso N.º 1.

No calcula nada por su cuenta: expone como JSON las funciones de `contracts/` del repositorio del proyecto, que es la única fuente de las definiciones de punto de inflexión y de las métricas.

- **Código:** https://github.com/NeoFao/caso1-ltc-inflexion
- **Interfaz web:** https://neofao.github.io/caso1-ltc-inflexion/

## Endpoints

| Ruta | Qué devuelve |
|---|---|
| `GET /api/config` | Parámetros vigentes: `w`, `h`, granularidad, latencia efectiva |
| `GET /api/sintetico` | Serie sintética con giros conocidos por construcción |
| `GET /api/historico?activo=LTC` | Precios reales con etiquetas verdaderas y predichas |
| `GET /docs` | Documentación interactiva generada por FastAPI |

## Aviso

Este Space no da recomendaciones de inversión. Es un trabajo académico de clasificación de series temporales.
