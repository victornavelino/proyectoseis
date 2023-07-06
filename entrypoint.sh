#!/bin/sh

set -e

echo "${0}: running migrations."
python /opt/carniceriavv/manage.py makemigrations 
python /opt/carniceriavv/manage.py migrate

echo "${0}: collecting statics."

python /opt/carniceriavv/manage.py collectstatic

python /opt/carniceriavv/manage.py runserver 0.0.0.0:8000