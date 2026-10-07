from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from rest_framework.test import APIClient

from caja.models import Banco, Caja, PagoQr
from cliente.models import Cliente
from empleado.models import Empleado, Sucursal
from persona.models import Persona
from venta.models import Venta

Usuario = get_user_model()


@pytest.fixture
def contexto():
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    usuario = Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)
    usuario.groups.add(Group.objects.get(name='Acceso operativo (ventas y caja)'))
    persona_empleado = Persona.objects.create(nombre='Ana', apellido='Vendedora', documento_identidad='11111111')
    empleado = Empleado.objects.create(persona=persona_empleado, cuil='20111111112')
    persona_cliente = Persona.objects.create(nombre='Cliente', apellido='Perez', documento_identidad='30111222')
    cliente = Cliente.objects.create(persona=persona_cliente, condicion_iva=Cliente.CONSUMIDOR_FINAL)
    Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=Decimal('0'))

    client = APIClient()
    client.force_authenticate(user=usuario)
    return {'sucursal': sucursal, 'usuario': usuario, 'empleado': empleado, 'cliente': cliente, 'client': client}


def _crear_venta(*, contexto, monto):
    return Venta.objects.create(
        empleado=contexto['empleado'], fecha=timezone.now(), monto=monto, descuento=Decimal('0.00'),
        sucursal=contexto['sucursal'], cliente=contexto['cliente'], usuario=contexto['usuario'],
    )


@pytest.mark.django_db
def test_pago_con_qr_se_acepta_y_queda_registrado(contexto):
    banco = Banco.objects.create(nombre='Banco Nación')
    venta = _crear_venta(contexto=contexto, monto=Decimal('1000.00'))

    response = contexto['client'].post('/api/v1/caja/cobrar-venta/', {
        'venta': venta.numero_ticket,
        'pagos_qr': [{
            'importe': '1000.00', 'documento_identidad': '30111222', 'nombre': 'Cliente',
            'apellido': 'Perez', 'banco': banco.id,
        }],
    }, format='json')

    assert response.status_code == 200, response.data
    venta.refresh_from_db()
    assert venta.cobrada is True
    pago = PagoQr.objects.get(venta=venta)
    assert pago.importe == Decimal('1000.00')
    assert pago.banco_id == banco.id
    assert response.data['medios_pago'] == ['qr']


@pytest.mark.django_db
def test_pago_con_qr_sin_banco_tambien_se_acepta(contexto):
    venta = _crear_venta(contexto=contexto, monto=Decimal('500.00'))

    response = contexto['client'].post('/api/v1/caja/cobrar-venta/', {
        'venta': venta.numero_ticket,
        'pagos_qr': [{'importe': '500.00', 'documento_identidad': '30111222'}],
    }, format='json')

    assert response.status_code == 200, response.data
    pago = PagoQr.objects.get(venta=venta)
    assert pago.banco_id is None


@pytest.mark.django_db
def test_pago_con_qr_combinado_con_efectivo(contexto):
    venta = _crear_venta(contexto=contexto, monto=Decimal('1000.00'))

    response = contexto['client'].post('/api/v1/caja/cobrar-venta/', {
        'venta': venta.numero_ticket,
        'pagos_efectivo': [{'importe': '400.00'}],
        'pagos_qr': [{'importe': '600.00', 'documento_identidad': '30111222'}],
    }, format='json')

    assert response.status_code == 200, response.data
    assert sorted(response.data['medios_pago']) == ['efectivo', 'qr']
