lSISTEMA PARA CARNICERIAS
==================


### Descripción

El Sistema para Carniceias es un sistema WEB responsive para la Tradición Carnicerías
permite realizar de manera online las diferentes gestiones que actualmente se realizan.


## Instalación

1. Creación de un entorno virtual.
2. Instalacion de dependencias: `pip install -r requirements/development.txt`
3. Creacion de una base de datos. (Preferentemente PostgreSQL)
4. Configuracion del proyecto desde el archivo `.env`: `cp env.example .env`
5. Correr migraciones. `python manage.py migrate`