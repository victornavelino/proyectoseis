from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from caja.models import Caja
from empleado.models import Sucursal

Usuario = get_user_model()


@pytest.fixture
def sucursal():
    return Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')


@pytest.fixture
def usuario(sucursal):
    return Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)


@pytest.mark.django_db
def test_resumen_de_caja_cerrada_trae_el_mismo_desglose_que_cerrar(sucursal, usuario):
    """El historial (CajaPage.tsx) reabre el mismo diálogo "Resumen de cierre" para una caja ya
    cerrada sin tener que volver a cerrarla — este endpoint reutiliza el mismo cálculo que
    `cerrar` (caja/api.py `_serializar_resumen_cierre`)."""
    caja = Caja.objects.create(
        sucursal=sucursal, usuario=usuario, fecha_fin=timezone.now(), caja_inicial=Decimal('0'),
        caja_final=Decimal('500.00'),
    )
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = client.get(f'/api/v1/caja/{caja.id}/resumen/')

    assert response.status_code == 200
    data = response.json()
    assert data['id'] == caja.id
    for campo in ('ingresos', 'total_ingresos', 'egresos', 'total_egresos', 'total_cuenta_corriente'):
        assert campo in data


@pytest.mark.django_db
def test_resumen_de_caja_abierta_rechaza(sucursal, usuario):
    caja = Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=Decimal('0'))
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = client.get(f'/api/v1/caja/{caja.id}/resumen/')

    assert response.status_code == 400


@pytest.mark.django_db
def test_resumen_de_caja_requiere_autenticacion(sucursal, usuario):
    caja = Caja.objects.create(
        sucursal=sucursal, usuario=usuario, fecha_fin=timezone.now(), caja_inicial=Decimal('0'),
        caja_final=Decimal('500.00'),
    )
    client = APIClient()

    response = client.get(f'/api/v1/caja/{caja.id}/resumen/')

    assert response.status_code in (401, 403)
