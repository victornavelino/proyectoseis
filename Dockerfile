# Stage 1: build del frontend React (DEC-009: se sirve desde el mismo dominio que Django,
# ver docs/modernizacion/DECISIONES.md y project/urls.py § frontend_index).
FROM node:22-slim AS frontend-build
WORKDIR /frontend

# Vite las hornea en el JS al momento del build (no son variables de entorno del contenedor en
# runtime) — hay que pasarlas como build args. La app en Dokploy está configurada en modo
# "Dockerfile" (build directo de este archivo, sin pasar por docker-compose.yml pese a que el
# repo tenga uno), así que hay que cargarlas en la sección "Build Args" de Dokploy — NO en
# "Environment Variables" (esa es runtime/.env, no llega a `docker build --build-arg`).
ARG VITE_API_BASE_URL=""
ARG VITE_BUSINESS_NAME
ARG VITE_OAUTH_CLIENT_ID
ARG VITE_OAUTH_REDIRECT_URI
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_BUSINESS_NAME=$VITE_BUSINESS_NAME \
    VITE_OAUTH_CLIENT_ID=$VITE_OAUTH_CLIENT_ID \
    VITE_OAUTH_REDIRECT_URI=$VITE_OAUTH_REDIRECT_URI

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: backend Django + build del frontend servido como estático
# pull the official base image
FROM python:3.13-slim-trixie

# Seteamos directorio de trabajo dentro de la nueva imagen
WORKDIR /opt/carniceriavv

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/opt/carniceriavv

# libpango/libcairo/libgdk-pixbuf/libharfbuzz: requeridos en runtime por WeasyPrint
# (reemplaza a wkhtmltopdf, dado de baja y ya no disponible como paquete apt).
# fonts-dejavu-core: fuente por defecto para que los PDF rendericen tildes/símbolos correctamente.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libharfbuzz-subset0 \
        libgdk-pixbuf-2.0-0 \
        libcairo2 \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Instalamos dependencias primero para aprovechar la cache de capas de Docker
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

COPY . .

# Build del frontend (stage 1) servido por WhiteNoise bajo /static/frontend/ — ver
# STATICFILES_DIRS (settings/base.py), `base` en frontend/vite.config.ts y
# project/urls.py § frontend_index. entrypoint.sh corre collectstatic al arrancar.
COPY --from=frontend-build /frontend/dist project/assets/frontend

RUN chmod +x entrypoint.sh \
    && addgroup --system app \
    && adduser --system --ingroup app app \
    && chown -R app:app /opt/carniceriavv

USER app

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
