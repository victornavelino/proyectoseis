# pull the official base image
FROM python:3.9
#Seteamos directorio de trabajo dentro de la nueva imagen
WORKDIR /opt/carniceriavv
# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get install libpq-dev python-dev-is-python3 -y --no-install-recommends
COPY . .
RUN pip install -r requirements/base.txt
# copy entrypoint.sh
COPY ./entrypoint.sh /opt/carniceriavv/entrypoint.sh
RUN chmod -R 755 /opt/carniceriavv/entrypoint.sh 
CMD ["/bin/sh","-c","/opt/carniceriavv/entrypoint.sh"]

#ENTRYPOINT ["/opt/carniceriavv/entrypoint.sh"]
#ENTRYPOINT [ "entrypoint.sh" ]
EXPOSE 8000
#CMD ["python", "manage.py", "migrate"]
