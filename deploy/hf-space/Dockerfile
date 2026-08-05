# Backend del proyecto, para un Space de Hugging Face con SDK docker.
#
# El Space clona el repositorio publico en vez de duplicar el codigo. Asi hay
# una sola fuente de verdad: si alguien corrige contracts/metrics.py, el
# siguiente rebuild del Space lo toma. Duplicar el codigo aqui garantizaria que
# en tres semanas el backend desplegado calcule distinto que el informe.

FROM python:3.14-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face corre el contenedor como usuario 1000, no como root.
RUN useradd -m -u 1000 usuario
USER usuario
ENV PATH="/home/usuario/.local/bin:$PATH"
WORKDIR /home/usuario/app

ARG REPO=https://github.com/NeoFao/caso1-ltc-inflexion.git
ARG REVISION=main
RUN git clone --depth 1 --branch "$REVISION" "$REPO" .

# Solo las dependencias del backend. torch y transformers viven en el grupo
# "modelos" y no se instalan hasta que haya un modelo real que servir: son
# varios GB y alargarian cada rebuild del Space sin dar nada a cambio.
RUN pip install --no-cache-dir --user \
        "pandas>=2.2" "numpy>=1.26" "pyarrow>=16.0" "requests>=2.32" \
        "scikit-learn>=1.5" "fastapi>=0.115" "uvicorn[standard]>=0.32"

# Origenes permitidos para CORS. La pagina de Pages vive en otro dominio.
ENV ORIGENES_PERMITIDOS="https://neofao.github.io,http://localhost:5173,http://localhost:4173"

# 7860 es el puerto que Hugging Face expone por convencion.
EXPOSE 7860
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
