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

RUN chmod +x entrypoint.sh \
    && addgroup --system app \
    && adduser --system --ingroup app app \
    && chown -R app:app /opt/carniceriavv

USER app

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
