import json

from django.conf import settings
from django.core.management.base import BaseCommand

from caja.models import TipoMovimiento

cache = {
    'ingreso', 'egreso'}


def importador():
    for dato in cache:
        entidad, creada = TipoMovimiento.objects.get_or_create(
            tipo=dato
        )

        if creada:
            print(f'se creo: {entidad}')


class Command(BaseCommand):
    help = "Crear tipo movimiento"

    def handle(self, *args, **options):
        print('Iniciamos la creacion ...')
        importador()
