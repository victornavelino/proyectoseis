from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from caja.models import Caja
from empleado.models import Sucursal

Usuario = get_user_model()


@pytest.fixture
def sucursal():
    return Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')


@pytest.fixture
def usuario(sucursal):
    return Usuario.objects.create_user(username='vendedor', password='password', sucursal=sucursal)


@pytest.mark.django_db
def test_sin_permisos_no_puede_abrir_caja(usuario):
    # Reproduce el bug reportado en sentido inverso: un usuario sólo con permiso para cargar
    # ventas (grupo "vendedores") no debería poder además operar la caja.
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = client.post('/api/v1/caja/abrir/')

    assert response.status_code == 403


@pytest.mark.django_db
def test_sin_permisos_no_puede_cobrar_venta(usuario):
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = client.post('/api/v1/caja/cobrar-venta/', {'venta': 1}, format='json')

    assert response.status_code == 403


@pytest.mark.django_db
def test_sin_permisos_no_puede_cerrar_caja(usuario, sucursal):
    caja = Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=Decimal('0'))
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = client.post(f'/api/v1/caja/{caja.id}/cerrar/', {'arqueo': '0'})

    assert response.status_code == 403
