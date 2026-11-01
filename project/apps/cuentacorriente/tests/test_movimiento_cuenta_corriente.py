from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from caja.models import Banco, Caja, CuponPagoTarjeta, Ingreso, PagoQr, PagoTransferencia, PlanTarjetaDeCredito, TarjetaDeCredito
from caja.utils import calcular_saldo_caja
from cliente.models import Cliente
from cuentacorriente.constants import CREDITO, DEBITO
from cuentacorriente.models import CuentaCorriente, MovimientoCuentaCorriente
from empleado.models import Sucursal
from persona.models import Persona

Usuario = get_user_model()


@pytest.fixture
def cliente():
    persona = Persona.objects.create(nombre='Juan', apellido='Cliente', documento_identidad='22222222')
    return Cliente.objects.create(persona=persona, condicion_iva=Cliente.CONSUMIDOR_FINAL)


@pytest.fixture
def sucursal():
    return Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')


@pytest.fixture
def usuario(sucursal):
    return Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)


@pytest.fixture
def cuenta(cliente):
    return CuentaCorriente.objects.create(cliente=cliente, tope=Decimal('100000.00'))


@pytest.fixture
def plan_tarjeta():
    tarjeta = TarjetaDeCredito.objects.create(nombre='Visa')
    return PlanTarjetaDeCredito.objects.create(tarjeta=tarjeta, nombre_plan='3 cuotas', interes=Decimal('10.00'))


@pytest.fixture
def client(usuario):
    api_client = APIClient()
    api_client.force_authenticate(user=usuario)
    return api_client


@pytest.mark.django_db
def test_credito_genera_un_ingreso_en_la_caja_abierta(client, cuenta, sucursal, usuario):
    Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=Decimal('0'))

    response = client.post('/api/v1/movimientocuentacorriente/', {
        'cuenta': cuenta.id, 'tipo': CREDITO, 'importe': '5000.00', 'medio_pago': 'efectivo',
        'observaciones': 'Pago en efectivo',
    }, format='json')

    assert response.status_code == 201, response.data
    movimiento = MovimientoCuentaCorriente.objects.get(cuenta=cuenta, tipo=CREDITO, importe=Decimal('5000.00'))
    assert movimiento.medio_pago == 'efectivo'
    ingreso = Ingreso.objects.get(sucursal=sucursal)
    assert ingreso.importe == Decimal('5000.00')
    assert ingreso.tipo_ingreso.descripcion == 'Pago de cuenta corriente'


@pytest.mark.django_db
def test_credito_sin_medio_de_pago_se_rechaza(client, cuenta, sucursal, usuario):
    Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=Decimal('0'))

    response = client.post('/api/v1/movimientocuentacorriente/', {
        'cuenta': cuenta.id, 'tipo': CREDITO, 'importe': '5000.00',
    }, format='json')

    assert response.status_code == 400
    assert 'medio_pago' in response.data
    assert not MovimientoCuentaCorriente.objects.filter(cuenta=cuenta).exists()
    assert not Ingreso.objects.exists()


@pytest.mark.django_db
def test_credito_sin_caja_abierta_se_rechaza(client, cuenta):
    response = client.post('/api/v1/movimientocuentacorriente/', {
        'cuenta': cuenta.id, 'tipo': CREDITO, 'importe': '5000.00', 'medio_pago': 'efectivo',
    }, format='json')

    assert response.status_code == 400
    assert not MovimientoCuentaCorriente.objects.filter(cuenta=cuenta).exists()
    assert not Ingreso.objects.exists()


@pytest.mark.django_db
def test_credito_por_transferencia_no_genera_ingreso_sino_pago_transferencia(client, cuenta, sucursal, usuario):
    """Regresión: antes CUALQUIER crédito -sin importar el medio- generaba un Ingreso genérico,
    inflando el efectivo esperado de caja con plata que en realidad nunca entró en billetes."""
    caja = Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=Decimal('0'))

    response = client.post('/api/v1/movimientocuentacorriente/', {
        'cuenta': cuenta.id, 'tipo': CREDITO, 'importe': '5000.00', 'medio_pago': 'transferencia',
    }, format='json')

    assert response.status_code == 201, response.data
    assert not Ingreso.objects.exists()
    pago = PagoTransferencia.objects.get(documento_identidad=cuenta.cliente.persona.documento_identidad)
    assert pago.importe == Decimal('5000.00')
    assert pago.venta is None
    # No es efectivo -> no tiene que contar para el arqueo de la caja.
    assert calcular_saldo_caja(caja) == Decimal('0')


@pytest.mark.django_db
def test_credito_por_qr_sin_banco_se_rechaza(client, cuenta, sucursal, usuario):
    Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=Decimal('0'))

    response = client.post('/api/v1/movimientocuentacorriente/', {
        'cuenta': cuenta.id, 'tipo': CREDITO, 'importe': '5000.00', 'medio_pago': 'qr',
    }, format='json')

    assert response.status_code == 400
    assert 'banco' in response.data
    assert not MovimientoCuentaCorriente.objects.filter(cuenta=cuenta).exists()


@pytest.mark.django_db
def test_credito_por_qr_no_genera_ingreso_sino_pago_qr(client, cuenta, sucursal, usuario):
    caja = Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=Decimal('0'))
    banco = Banco.objects.create(nombre='Mercado Pago')

    response = client.post('/api/v1/movimientocuentacorriente/', {
        'cuenta': cuenta.id, 'tipo': CREDITO, 'importe': '5000.00', 'medio_pago': 'qr', 'banco': banco.id,
    }, format='json')

    assert response.status_code == 201, response.data
    assert not Ingreso.objects.exists()
    movimiento = MovimientoCuentaCorriente.objects.get(cuenta=cuenta, tipo=CREDITO)
    assert movimiento.banco == banco
    pago = PagoQr.objects.get(documento_identidad=cuenta.cliente.persona.documento_identidad)
    assert pago.importe == Decimal('5000.00')
    assert pago.banco == banco
    assert calcular_saldo_caja(caja) == Decimal('0')


@pytest.mark.django_db
def test_credito_por_transferencia_sin_banco_se_acepta(client, cuenta, sucursal, usuario):
    # A diferencia de QR, en transferencia el banco es opcional (mismo criterio que venta).
    Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=Decimal('0'))

    response = client.post('/api/v1/movimientocuentacorriente/', {
        'cuenta': cuenta.id, 'tipo': CREDITO, 'importe': '5000.00', 'medio_pago': 'transferencia',
    }, format='json')

    assert response.status_code == 201, response.data


@pytest.mark.django_db
def test_credito_por_tarjeta_sin_plan_se_rechaza(client, cuenta, sucursal, usuario):
    Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=Decimal('0'))

    response = client.post('/api/v1/movimientocuentacorriente/', {
        'cuenta': cuenta.id, 'tipo': CREDITO, 'importe': '5000.00', 'medio_pago': 'tarjeta',
    }, format='json')

    assert response.status_code == 400
    assert 'plan_tarjeta' in response.data
    assert not MovimientoCuentaCorriente.objects.filter(cuenta=cuenta).exists()


@pytest.mark.django_db
def test_credito_por_tarjeta_no_genera_ingreso_sino_cupon_con_recargo(client, cuenta, sucursal, usuario, plan_tarjeta):
    caja = Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=Decimal('0'))

    response = client.post('/api/v1/movimientocuentacorriente/', {
        'cuenta': cuenta.id, 'tipo': CREDITO, 'importe': '5000.00', 'medio_pago': 'tarjeta',
        'plan_tarjeta': plan_tarjeta.id, 'numero_cupon': '001234', 'lote': '000987',
    }, format='json')

    assert response.status_code == 201, response.data
    assert not Ingreso.objects.exists()
    # Lo que cancela deuda es el importe base, nunca el importe con recargo -el recargo es un
    # costo financiero aparte a cargo del cliente, mismo criterio que cobrar_venta.
    movimiento = MovimientoCuentaCorriente.objects.get(cuenta=cuenta, tipo=CREDITO)
    assert movimiento.importe == Decimal('5000.00')
    assert movimiento.plan_tarjeta == plan_tarjeta
    # Se guarda también acá (no sólo en el cupón) para que la UI lo muestre sin tener que ir a
    # buscar el CuponPagoTarjeta aparte -ver CuentaCorrienteDetalleModal.tsx.
    assert movimiento.recargo == Decimal('500.00')
    cupon = CuponPagoTarjeta.objects.get(cliente=cuenta.cliente)
    assert cupon.plan_tarjeta == plan_tarjeta
    assert cupon.importe == Decimal('5000.00')
    assert cupon.recargo == Decimal('500.00')  # 10% de interés
    assert cupon.importe_con_recargo == Decimal('5500.00')
    assert cupon.numero_cupon == '001234'
    assert cupon.lote == '000987'
    assert cupon.venta is None
    # No es efectivo -> no tiene que contar para el arqueo de la caja.
    assert calcular_saldo_caja(caja) == Decimal('0')


@pytest.mark.django_db
def test_debito_dentro_del_tope_se_acepta_sin_saldo_a_favor_previo(client, cuenta):
    # Un débito no genera movimiento de caja -> no hace falta una caja abierta para esto.
    response = client.post('/api/v1/movimientocuentacorriente/', {
        'cuenta': cuenta.id, 'tipo': DEBITO, 'importe': '100000.00',
    }, format='json')

    assert response.status_code == 201, response.data


@pytest.mark.django_db
def test_debito_que_supera_el_tope_se_rechaza(client, cuenta):
    response = client.post('/api/v1/movimientocuentacorriente/', {
        'cuenta': cuenta.id, 'tipo': DEBITO, 'importe': '100000.01',
    }, format='json')

    assert response.status_code == 400
    assert 'importe' in response.data
    assert not MovimientoCuentaCorriente.objects.filter(cuenta=cuenta).exists()
