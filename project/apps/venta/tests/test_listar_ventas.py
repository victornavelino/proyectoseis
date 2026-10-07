from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from cliente.models import Cliente
from empleado.models import Empleado, Sucursal
from persona.models import Persona
from venta.models import Venta

Usuario = get_user_model()


def _crear_venta(*, sucursal, usuario, empleado, apellido, documento, numero_ticket=None):
    persona_cliente = Persona.objects.create(nombre='Cliente', apellido=apellido, documento_identidad=documento)
    cliente = Cliente.objects.create(persona=persona_cliente, condicion_iva=Cliente.CONSUMIDOR_FINAL)
    return Venta.objects.create(
        empleado=empleado,
        fecha=timezone.now(),
        monto=Decimal('1000.00'),
        descuento=Decimal('0.00'),
        sucursal=sucursal,
        cliente=cliente,
        usuario=usuario,
    )


@pytest.fixture
def ventas():
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    persona_empleado = Persona.objects.create(nombre='Ana', apellido='Vendedora', documento_identidad='11111111')
    empleado = Empleado.objects.create(persona=persona_empleado, cuil='20111111112')
    usuario = Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)

    venta_perez = _crear_venta(
        sucursal=sucursal, usuario=usuario, empleado=empleado, apellido='Perez', documento='30111222',
    )
    venta_gomez = _crear_venta(
        sucursal=sucursal, usuario=usuario, empleado=empleado, apellido='Gomez', documento='30333444',
    )
    return usuario, venta_perez, venta_gomez


@pytest.mark.django_db
def test_listar_ventas_busca_por_apellido(ventas):
    usuario, venta_perez, _venta_gomez = ventas
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = client.get('/api/v1/venta/', {'search': 'perez'})

    assert response.status_code == 200
    tickets = [v['numero_ticket'] for v in response.json()['results']]
    assert tickets == [venta_perez.numero_ticket]


@pytest.mark.django_db
def test_listar_ventas_busca_por_documento(ventas):
    usuario, _venta_perez, venta_gomez = ventas
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = client.get('/api/v1/venta/', {'search': '30333444'})

    assert response.status_code == 200
    tickets = [v['numero_ticket'] for v in response.json()['results']]
    assert tickets == [venta_gomez.numero_ticket]


@pytest.mark.django_db
def test_listar_ventas_busca_por_numero_de_ticket(ventas):
    usuario, venta_perez, _venta_gomez = ventas
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = client.get('/api/v1/venta/', {'search': f'#{venta_perez.numero_ticket}'})

    assert response.status_code == 200
    tickets = [v['numero_ticket'] for v in response.json()['results']]
    assert tickets == [venta_perez.numero_ticket]


@pytest.mark.django_db
def test_listar_ventas_sin_resultados(ventas):
    usuario, _venta_perez, _venta_gomez = ventas
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = client.get('/api/v1/venta/', {'search': 'inexistente'})

    assert response.status_code == 200
    assert response.json()['results'] == []
