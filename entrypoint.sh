#!/bin/bash

python /opt/carniceriavv/manage.py migrate

python /opt/carniceriavv/manage.py collectstatic

python /opt/carniceriavv/manage.py runserver 0.0.0.0:8000