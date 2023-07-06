#!/bin/bash

set -e

echo "${0}: running migrations."
python manage.py makemigrations 
python manage.py migrate

echo "${0}: collecting statics."

python manage.py collectstatic