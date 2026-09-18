from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from caja.models import Caja
from cliente.models import Cliente
from cuentacorriente.constants import CREDITO
from cuentacorriente.models import CuentaCorriente, MovimientoCuentaCorriente
from empleado.models import Empleado, Sucursal
from persona.models import Persona
from venta.models import Venta

Usuario = get_user_model()


@pytest.fixture
def contexto():
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    usuario = Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)
    persona_empleado = Persona.objects.create(nombre='Ana', apellido='Vendedora', documento_identidad='11111111')
    empleado = Empleado.objects.create(persona=persona_empleado, cuil='20111111112')
    persona_cliente = Persona.objects.create(nombre='Cliente', apellido='Perez', documento_identidad='30111222')
    cliente = Cliente.objects.create(persona=persona_cliente, condicion_iva=Cliente.CONSUMIDOR_FINAL)
    cuenta = CuentaCorriente.objects.create(cliente=cliente)
    caja = Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=Decimal('0'))

    client = APIClient()
    client.force_authenticate(user=usuario)
    return {
        'sucursal': sucursal, 'usuario': usuario, 'empleado': empleado, 'cliente': cliente,
        'cuenta': cuenta, 'caja': caja, 'client': client,
    }


def _crear_venta(*, contexto, monto):
    return Venta.objects.create(
        empleado=contexto['empleado'], fecha=timezone.now(), monto=monto, descuento=Decimal('0.00'),
        sucursal=contexto['sucursal'], cliente=contexto['cliente'], usuario=contexto['usuario'],
    )


def _dar_saldo_a_favor(*, contexto, importe):
    """Simula que el cliente ya pagó/depositó `importe` de más en su cuenta corriente, dejándolo
    con ese monto a favor (saldo negativo, ver cuentacorriente.utils.calcular_saldo_cc)."""
    MovimientoCuentaCorriente.objects.create(
        cuenta=contexto['cuenta'], importe=importe, tipo=CREDITO, usuario=contexto['usuario'],
    )


@pytest.mark.django_db
def test_pago_cuenta_corriente_no_puede_superar_el_saldo_a_favor(contexto):
    """La cuenta corriente es un saldo a favor del cliente, no una línea de crédito: un pago que
    lo dejaría debiendo dinero al negocio debe rechazarse, sin importar el `tope` configurado."""
    _dar_saldo_a_favor(contexto=contexto, importe=Decimal('100000.00'))
    venta = _crear_venta(contexto=contexto, monto=Decimal('150000.00'))

    response = contexto['client'].post('/api/v1/caja/cobrar-venta/', {
        'venta': venta.numero_ticket,
        'pagos_cuenta_corriente': [{'importe': '150000.00'}],
    }, format='json')

    assert response.status_code == 400
    assert 'pagos' in response.data
    venta.refresh_from_db()
    assert venta.cobrada is False
    assert not MovimientoCuentaCorriente.objects.filter(venta=venta).exists()


@pytest.mark.django_db
def test_pago_cuenta_corriente_hasta_el_saldo_a_favor_se_acepta(contexto):
    _dar_saldo_a_favor(contexto=contexto, importe=Decimal('100000.00'))
    venta = _crear_venta(contexto=contexto, monto=Decimal('100000.00'))

    response = contexto['client'].post('/api/v1/caja/cobrar-venta/', {
        'venta': venta.numero_ticket,
        'pagos_cuenta_corriente': [{'importe': '100000.00'}],
    }, format='json')

    assert response.status_code == 200, response.data
    venta.refresh_from_db()
    assert venta.cobrada is True
    assert MovimientoCuentaCorriente.objects.filter(venta=venta).count() == 1


@pytest.mark.django_db
def test_pago_cuenta_corriente_sin_saldo_a_favor_se_rechaza(contexto):
    """Un cliente que no tiene nada a favor (saldo en 0) no puede pagar nada con cuenta
    corriente: antes se permitía igual mientras no se superara el tope por defecto ($100.000)."""
    venta = _crear_venta(contexto=contexto, monto=Decimal('50000.00'))

    response = contexto['client'].post('/api/v1/caja/cobrar-venta/', {
        'venta': venta.numero_ticket,
        'pagos_cuenta_corriente': [{'importe': '50000.00'}],
    }, format='json')

    assert response.status_code == 400
    assert 'pagos' in response.data
