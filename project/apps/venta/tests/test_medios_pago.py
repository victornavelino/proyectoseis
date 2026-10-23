from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from caja.constants import INGRESO
from caja.models import Caja, CobroVenta, CuponPagoTarjeta, PagoQr, PagoTransferencia, PlanTarjetaDeCredito, TarjetaDeCredito
from cliente.models import Cliente
from cuentacorriente.constants import DEBITO
from cuentacorriente.models import CuentaCorriente, MovimientoCuentaCorriente
from empleado.models import Empleado, Sucursal
from persona.models import Persona
from venta.models import Venta

Usuario = get_user_model()


@pytest.fixture
def escenario():
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    persona_empleado = Persona.objects.create(nombre='Ana', apellido='Vendedora', documento_identidad='11111111')
    empleado = Empleado.objects.create(persona=persona_empleado, cuil='20111111112')
    usuario = Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)
    persona_cliente = Persona.objects.create(nombre='Juan', apellido='Cliente', documento_identidad='22222222')
    cliente = Cliente.objects.create(persona=persona_cliente, condicion_iva=Cliente.CONSUMIDOR_FINAL)
    caja = Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=Decimal('0'))

    def crear_venta():
        return Venta.objects.create(
            empleado=empleado, fecha=timezone.now(), monto=Decimal('1000.00'), descuento=Decimal('0.00'),
            sucursal=sucursal, cliente=cliente, usuario=usuario,
        )

    return {'sucursal': sucursal, 'usuario': usuario, 'cliente': cliente, 'caja': caja, 'crear_venta': crear_venta}


@pytest.mark.django_db
def test_venta_sin_cobrar_no_tiene_medios_de_pago(escenario):
    venta = escenario['crear_venta']()
    client = APIClient()
    client.force_authenticate(user=escenario['usuario'])

    response = client.get('/api/v1/venta/', {'search': f"#{venta.numero_ticket}"})

    assert response.status_code == 200
    assert response.json()['results'][0]['medios_pago'] == []


@pytest.mark.django_db
def test_venta_cobrada_en_efectivo(escenario):
    venta = escenario['crear_venta']()
    CobroVenta.objects.create(
        usuario=escenario['usuario'], importe=venta.monto, sucursal=escenario['sucursal'], caja=escenario['caja'],
        tipo=INGRESO, venta=venta,
    )
    client = APIClient()
    client.force_authenticate(user=escenario['usuario'])

    response = client.get('/api/v1/venta/', {'search': f"#{venta.numero_ticket}"})

    assert response.json()['results'][0]['medios_pago'] == ['efectivo']


@pytest.mark.django_db
def test_venta_cobrada_combinada_efectivo_y_tarjeta(escenario):
    # cobrar_venta (venta.services) permite combinar medios en una sola operación -> el campo
    # tiene que poder reflejar más de uno a la vez.
    venta = escenario['crear_venta']()
    CobroVenta.objects.create(
        usuario=escenario['usuario'], importe=Decimal('500'), sucursal=escenario['sucursal'], caja=escenario['caja'],
        tipo=INGRESO, venta=venta,
    )
    tarjeta = TarjetaDeCredito.objects.create(nombre='Visa')
    plan = PlanTarjetaDeCredito.objects.create(tarjeta=tarjeta, nombre_plan='1 pago')
    CuponPagoTarjeta.objects.create(
        cliente=escenario['cliente'], plan_tarjeta=plan, importe=Decimal('500'),
        importe_con_recargo=Decimal('500'), venta=venta,
    )
    client = APIClient()
    client.force_authenticate(user=escenario['usuario'])

    response = client.get('/api/v1/venta/', {'search': f"#{venta.numero_ticket}"})

    assert response.json()['results'][0]['medios_pago'] == ['efectivo', 'tarjeta']


@pytest.mark.django_db
def test_venta_cobrada_por_transferencia(escenario):
    venta = escenario['crear_venta']()
    PagoTransferencia.objects.create(importe=venta.monto, documento_identidad='22222222', venta=venta)
    client = APIClient()
    client.force_authenticate(user=escenario['usuario'])

    response = client.get('/api/v1/venta/', {'search': f"#{venta.numero_ticket}"})

    assert response.json()['results'][0]['medios_pago'] == ['transferencia']


@pytest.mark.django_db
def test_venta_cobrada_por_qr(escenario):
    venta = escenario['crear_venta']()
    PagoQr.objects.create(importe=venta.monto, documento_identidad='22222222', venta=venta)
    client = APIClient()
    client.force_authenticate(user=escenario['usuario'])

    response = client.get('/api/v1/venta/', {'search': f"#{venta.numero_ticket}"})

    assert response.json()['results'][0]['medios_pago'] == ['qr']


@pytest.mark.django_db
def test_venta_cobrada_con_cuenta_corriente(escenario):
    venta = escenario['crear_venta']()
    cuenta = CuentaCorriente.objects.create(cliente=escenario['cliente'])
    MovimientoCuentaCorriente.objects.create(
        cuenta=cuenta, importe=venta.monto, tipo=DEBITO, usuario=escenario['usuario'], venta=venta,
    )
    client = APIClient()
    client.force_authenticate(user=escenario['usuario'])

    response = client.get('/api/v1/venta/', {'search': f"#{venta.numero_ticket}"})

    assert response.json()['results'][0]['medios_pago'] == ['cuenta_corriente']
