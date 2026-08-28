# pull the official base image
FROM python:3.9-bullseye

# Seteamos directorio de trabajo dentro de la nueva imagen
WORKDIR /opt/carniceriavv

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq-dev \
        python-dev-is-python3 \
        wkhtmltopdf \
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
