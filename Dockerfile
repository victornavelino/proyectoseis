# pull the official base image
FROM python:3.9-slim
#Seteamos directorio de trabajo dentro de la nueva imagen
WORKDIR /opt/carniceriavv
# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get install libpq-dev python-dev-is-python3 wkhtmltopdf -y --no-install-recommends
COPY . .
RUN pip install -r requirements/base.txt
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT "/entrypoint.sh"
EXPOSE 8000

