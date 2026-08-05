# Despliegue

Dos piezas, en dos sitios distintos, por una razón: **la página nunca puede verse rota**.

| Pieza | Dónde | Estado |
|---|---|---|
| Frontend | GitHub Pages — https://neofao.github.io/caso1-ltc-inflexion/ | Automático en cada push a `main` |
| Backend | Hugging Face Space (Docker) | Pendiente de crear |

## Cómo se comporta la página

Al cargar, intenta el backend con un límite de 1,5 segundos. Si no responde, cae al snapshot congelado en `app/public/datos/` y lo declara en la cabecera: *«datos congelados · hoy · backend no disponible»*.

Eso significa tres cosas:

1. La página funciona aunque el Space esté dormido, caído o sin crear.
2. El día de la exposición no dependemos del wifi del aula.
3. Nunca se presentan datos viejos como si fueran frescos — la antigüedad va escrita.

---

## Crear el backend en Hugging Face

**Por qué Hugging Face y no Render, Fly o Railway.** El nivel gratuito da 2 vCPU y 16 GB de RAM sin tarjeta. Render gratis da 512 MB, que no alcanza para servir inferencia de un modelo fundacional. Y hay una razón que pesa más que las especificaciones: el enunciado obliga a usar un modelo fundacional de Hugging Face, así que en la semana 3 los pesos van a estar del mismo lado que el servidor.

**Lo que se pierde:** el Space se duerme tras unas 48 horas sin visitas y tarda en despertar. Deja de importar porque la página cae al snapshot mientras tanto.

### Pasos

**1.** Crear el Space en https://huggingface.co/new-space

- Nombre: `caso1-ltc-backend`
- SDK: **Docker** → plantilla *Blank*
- Hardware: CPU basic (gratis)
- Visibilidad: público

**2.** Subir los dos archivos de `deploy/hf-space/` a la raíz del Space:

```bash
git clone https://huggingface.co/spaces/<tu-usuario>/caso1-ltc-backend
```

```bash
cp deploy/hf-space/Dockerfile deploy/hf-space/README.md caso1-ltc-backend/
```

Después, dentro de esa carpeta: `git add . && git commit -m "Backend inicial" && git push`.

El Space tarda unos minutos en construir. Cuando termine, comprobalo:

```bash
curl https://<tu-usuario>-caso1-ltc-backend.hf.space/api/config
```

**3.** Conectar el frontend. En el repositorio de GitHub, `Settings → Secrets and variables → Actions → Variables → New repository variable`:

- Nombre: `API_BASE`
- Valor: `https://<tu-usuario>-caso1-ltc-backend.hf.space`

O por línea de comandos:

```bash
gh variable set API_BASE --body "https://<tu-usuario>-caso1-ltc-backend.hf.space"
```

El siguiente despliegue de Pages toma la variable y la cabecera pasa a decir *«backend en vivo»*.

### Cómo está armado el Dockerfile

El Space **clona este repositorio** en vez de duplicar el código. Una sola fuente de verdad: si alguien corrige `contracts/metrics.py`, el siguiente rebuild lo toma. Duplicar el backend garantizaría que en tres semanas el servidor calcule distinto que el informe.

No instala `torch` ni `transformers`. Son varios GB y alargarían cada rebuild sin dar nada a cambio mientras no haya modelo. Cuando Isaac tenga uno, se agregan al `pip install` del Dockerfile.

---

## Regenerar el snapshot

Cada vez que cambien los datos, los parámetros congelados o el modelo:

```bash
uv run python scripts/exportar_estatico.py
```

Escribe `app/public/datos/*.json` con su marca de generación. **Va commiteado a propósito**: así el despliegue no depende de descargar precios desde el runner, y si Binance estuviera caído la página se publica igual con los últimos datos conocidos.

---

## Verificar el frontend antes de publicar

```bash
npm run build --prefix app && npx vite preview --prefix app --port 4173
```

Con el backend apagado tiene que mostrar los datos del snapshot y el aviso de datos congelados. Si aparece la página en blanco o un error, algo se rompió en el respaldo.
