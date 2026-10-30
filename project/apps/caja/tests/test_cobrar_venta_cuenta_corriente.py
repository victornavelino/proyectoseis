from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
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
    # cobrar-venta ahora exige el permiso caja.add_cobroventa (ver util.permissions.
    # TienePermiso) — ver comentario equivalente en caja/tests/test_caja_abierta.py.
    usuario = Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)
    usuario.groups.add(Group.objects.get(name='Acceso operativo (ventas y caja)'))
    persona_empleado = Persona.objects.create(nombre='Ana', apellido='Vendedora', documento_identidad='11111111')
    empleado = Empleado.objects.create(persona=persona_empleado, cuil='20111111112')
    persona_cliente = Persona.objects.create(nombre='Cliente', apellido='Perez', documento_identidad='30111222')
    cliente = Cliente.objects.create(persona=persona_cliente, condicion_iva=Cliente.CONSUMIDOR_FINAL)
    # Explícito (no el default $0 de una cuenta nueva): estos tests ejercitan el límite del
    # tope en sí, no el valor por defecto -eso lo cubre cuentacorriente/tests aparte-.
    cuenta = CuentaCorriente.objects.create(cliente=cliente, tope=Decimal('100000.00'))
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
    con ese monto a favor (saldo negativo, ver cuentacorriente.utils.calcular_saldo_cc). Crea el
    movimiento directo (no vía el service) para no generar de paso un Ingreso de caja acá."""
    MovimientoCuentaCorriente.objects.create(
        cuenta=contexto['cuenta'], importe=importe, tipo=CREDITO, usuario=contexto['usuario'],
    )


@pytest.mark.django_db
def test_pago_cuenta_corriente_puede_superar_el_saldo_a_favor_hasta_el_tope(contexto):
    """La cuenta corriente es una línea de crédito hasta `tope` (default $100.000), no sólo una
    billetera prepaga: un pago puede dejar al cliente debiendo, siempre que no supere el tope."""
    _dar_saldo_a_favor(contexto=contexto, importe=Decimal('50000.00'))
    # saldo a favor $50.000 + tope $100.000 -> disponible $150.000.
    venta = _crear_venta(contexto=contexto, monto=Decimal('150000.00'))

    response = contexto['client'].post('/api/v1/caja/cobrar-venta/', {
        'venta': venta.numero_ticket,
        'pagos_cuenta_corriente': [{'importe': '150000.00'}],
    }, format='json')

    assert response.status_code == 200, response.data
    venta.refresh_from_db()
    assert venta.cobrada is True
    assert MovimientoCuentaCorriente.objects.filter(venta=venta).count() == 1


@pytest.mark.django_db
def test_pago_cuenta_corriente_que_supera_el_tope_se_rechaza(contexto):
    _dar_saldo_a_favor(contexto=contexto, importe=Decimal('50000.00'))
    # disponible $150.000 (ver test de arriba) -> $150.000,01 debería rechazarse.
    venta = _crear_venta(contexto=contexto, monto=Decimal('150000.01'))

    response = contexto['client'].post('/api/v1/caja/cobrar-venta/', {
        'venta': venta.numero_ticket,
        'pagos_cuenta_corriente': [{'importe': '150000.01'}],
    }, format='json')

    assert response.status_code == 400
    assert 'pagos' in response.data
    venta.refresh_from_db()
    assert venta.cobrada is False
    assert not MovimientoCuentaCorriente.objects.filter(venta=venta).exists()


@pytest.mark.django_db
def test_pago_cuenta_corriente_sin_saldo_a_favor_se_acepta_hasta_el_tope(contexto):
    """Un cliente sin nada a favor (saldo en 0) puede igual "fiar" hasta el tope configurado
    ($100.000 por defecto) -ya no hace falta que haya depositado plata antes-."""
    venta = _crear_venta(contexto=contexto, monto=Decimal('50000.00'))

    response = contexto['client'].post('/api/v1/caja/cobrar-venta/', {
        'venta': venta.numero_ticket,
        'pagos_cuenta_corriente': [{'importe': '50000.00'}],
    }, format='json')

    assert response.status_code == 200, response.data
    venta.refresh_from_db()
    assert venta.cobrada is True


@pytest.mark.django_db
def test_pago_cuenta_corriente_que_supera_el_tope_sin_saldo_a_favor_se_rechaza(contexto):
    venta = _crear_venta(contexto=contexto, monto=Decimal('100000.01'))

    response = contexto['client'].post('/api/v1/caja/cobrar-venta/', {
        'venta': venta.numero_ticket,
        'pagos_cuenta_corriente': [{'importe': '100000.01'}],
    }, format='json')

    assert response.status_code == 400
    assert 'pagos' in response.data
