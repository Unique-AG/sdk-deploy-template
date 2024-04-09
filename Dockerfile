FROM python:3.11-slim-bookworm

ARG MODULE
ARG APP_NAME=app
ARG ENCRYPTED_ENV_FILE=.env.enc
ARG POETRY_VERSION=1.7.1
ARG SOPS_VERSION=3.8.1
ARG PORT=8080

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  # Poetry's configuration:
  POETRY_NO_INTERACTION=1 \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  POETRY_HOME='/usr/local' \
  PORT=${PORT} \
  MODULE=${MODULE} \
  APP_NAME=${APP_NAME} \
  ENCRYPTED_ENV_FILE=${ENCRYPTED_ENV_FILE}


# System deps:
RUN useradd -m app && \
    mkdir -p /opt/pipx && \
    apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes pipx curl && \
    PIPX_HOME=/opt/pipx PIPX_BIN_DIR=/usr/local/bin pipx install poetry==${POETRY_VERSION} && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:${PATH}"

# Copy only requirements to cache them in docker layer
WORKDIR /code
COPY poetry.lock pyproject.toml /code/

# Project initialization:
RUN poetry install --only=main --no-interaction --no-ansi

# SOPS installation
RUN curl -LO https://github.com/getsops/sops/releases/download/v${SOPS_VERSION}/sops-v${SOPS_VERSION}.linux.amd64 && \
    mv sops-v${SOPS_VERSION}.linux.amd64 /usr/local/bin/sops && \
    chmod +x /usr/local/bin/sops

# Creating folders, and files for a project:
COPY . /code

RUN <<EOF cat >> entrypoint.sh
#!/bin/sh
set -e

# decrypt the secrets file
sops --decrypt --input-type=dotenv --output-type=dotenv /code/${ENCRYPTED_ENV_FILE} > /code/.env

# use gunicorn as the entrypoint from CMD
exec poetry run gunicorn \
  --workers=2 \
  --threads=4 \
  --worker-class=gthread \
  --worker-tmp-dir /dev/shm \
  --bind "0.0.0.0:${PORT}" \
  "${MODULE}:${APP_NAME}"
EOF

# Create a non-root user and change ownership
RUN chown -R app:app /code && \
    chmod +x /code/entrypoint.sh

USER app

ENTRYPOINT ["/code/entrypoint.sh"]
