from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.utils import timezone
from rest_framework.test import APIClient

from caja.models import Banco, Caja, PlanTarjetaDeCredito, TarjetaDeCredito
from cliente.models import Cliente
from cuentacorriente.constants import CREDITO, DEBITO
from cuentacorriente.models import CuentaCorriente, MovimientoCuentaCorriente
from empleado.models import Sucursal
from persona.models import Persona

Usuario = get_user_model()


@pytest.fixture
def sucursal():
    return Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')


@pytest.fixture
def usuario(sucursal):
    return Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)


@pytest.fixture
def cliente():
    persona = Persona.objects.create(nombre='Juan', apellido='Cliente', documento_identidad='22222222')
    return Cliente.objects.create(persona=persona, condicion_iva=Cliente.CONSUMIDOR_FINAL)


@pytest.fixture
def cuenta(cliente):
    return CuentaCorriente.objects.create(cliente=cliente, tope=Decimal('100000.00'))


@pytest.fixture
def client(usuario):
    api_client = APIClient()
    api_client.force_authenticate(user=usuario)
    return api_client


@pytest.mark.django_db
def test_imprimir_cuenta_sin_movimientos_devuelve_pdf(client, cuenta):
    response = client.get(f'/api/v1/cuentacorriente/{cuenta.id}/imprimir/')

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert response.content.startswith(b'%PDF')


@pytest.mark.django_db
def test_imprimir_cuenta_con_movimientos_variados_devuelve_pdf(client, cuenta, usuario):
    # Un movimiento por cada combinación que el template tiene que poder renderizar sin romper:
    # efectivo (sin banco/plan), con banco (transferencia), con plan de tarjeta y débito.
    MovimientoCuentaCorriente.objects.create(
        cuenta=cuenta, tipo=CREDITO, importe=Decimal('1000.00'), usuario=usuario, medio_pago='efectivo',
        observaciones='Pago en efectivo',
    )
    banco = Banco.objects.create(nombre='Banco Nación')
    MovimientoCuentaCorriente.objects.create(
        cuenta=cuenta, tipo=CREDITO, importe=Decimal('2000.00'), usuario=usuario, medio_pago='transferencia',
        banco=banco,
    )
    tarjeta = TarjetaDeCredito.objects.create(nombre='Visa')
    plan = PlanTarjetaDeCredito.objects.create(tarjeta=tarjeta, nombre_plan='3 cuotas', interes=Decimal('10.00'))
    MovimientoCuentaCorriente.objects.create(
        cuenta=cuenta, tipo=CREDITO, importe=Decimal('3000.00'), usuario=usuario, medio_pago='tarjeta',
        plan_tarjeta=plan, recargo=Decimal('300.00'),
    )
    MovimientoCuentaCorriente.objects.create(
        cuenta=cuenta, tipo=DEBITO, importe=Decimal('500.00'), usuario=usuario, observaciones='Consumo RQ',
    )

    response = client.get(f'/api/v1/cuentacorriente/{cuenta.id}/imprimir/')

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert response.content.startswith(b'%PDF')


@pytest.mark.django_db
def test_template_cuenta_corriente_sin_observaciones_no_imprime_none(cuenta, usuario):
    # Regresión: un movimiento sin observaciones (campo None) imprimía literalmente la palabra
    # "None" en el ticket -Django renderiza None como ese string salvo que el template lo
    # resguarde con {% if %} también alrededor del {{ }}, no sólo alrededor del separador " · ".
    # Se verifica el HTML del template directamente (no el PDF final): WeasyPrint puede comprimir
    # los streams de texto, así que buscar bytes en el PDF no es confiable -mismo criterio que
    # caja.tests.test_totales_tarjeta_y_qr_en_cierre.
    banco = Banco.objects.create(nombre='Banco Nación')
    movimiento = MovimientoCuentaCorriente.objects.create(
        cuenta=cuenta, tipo=CREDITO, importe=Decimal('2000.00'), usuario=usuario, medio_pago='transferencia',
        banco=banco, observaciones=None,
    )
    movimiento.plan_tarjeta_detalle = None

    html = render_to_string(
        'admin/cuentacorriente/ticket_cuenta_corriente.html',
        {
            'cuenta': cuenta, 'movimientos': [movimiento], 'saldo': Decimal('-2000.00'),
            'etiqueta_saldo': '(A favor del cliente)', 'hoy': timezone.now(),
        },
        request=RequestFactory().get('/'),
    )

    assert 'None' not in html


@pytest.mark.django_db
def test_imprimir_cuenta_requiere_autenticacion(cuenta):
    client = APIClient()

    response = client.get(f'/api/v1/cuentacorriente/{cuenta.id}/imprimir/')

    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_imprimir_movimiento_devuelve_pdf(client, cuenta, usuario):
    movimiento = MovimientoCuentaCorriente.objects.create(
        cuenta=cuenta, tipo=CREDITO, importe=Decimal('1000.00'), usuario=usuario, medio_pago='efectivo',
        observaciones='Pago en efectivo',
    )

    response = client.get(f'/api/v1/movimientocuentacorriente/{movimiento.id}/imprimir/')

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert response.content.startswith(b'%PDF')


@pytest.mark.django_db
def test_imprimir_movimiento_con_tarjeta_devuelve_pdf(client, cuenta, usuario):
    tarjeta = TarjetaDeCredito.objects.create(nombre='Visa')
    plan = PlanTarjetaDeCredito.objects.create(tarjeta=tarjeta, nombre_plan='3 cuotas', interes=Decimal('10.00'))
    movimiento = MovimientoCuentaCorriente.objects.create(
        cuenta=cuenta, tipo=CREDITO, importe=Decimal('3000.00'), usuario=usuario, medio_pago='tarjeta',
        plan_tarjeta=plan, recargo=Decimal('300.00'),
    )

    response = client.get(f'/api/v1/movimientocuentacorriente/{movimiento.id}/imprimir/')

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert response.content.startswith(b'%PDF')


@pytest.mark.django_db
def test_imprimir_movimiento_debito_devuelve_pdf(client, cuenta, usuario):
    movimiento = MovimientoCuentaCorriente.objects.create(
        cuenta=cuenta, tipo=DEBITO, importe=Decimal('500.00'), usuario=usuario, observaciones='Consumo RQ',
    )

    response = client.get(f'/api/v1/movimientocuentacorriente/{movimiento.id}/imprimir/')

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert response.content.startswith(b'%PDF')


@pytest.mark.django_db
def test_imprimir_movimiento_requiere_autenticacion(cuenta, usuario):
    movimiento = MovimientoCuentaCorriente.objects.create(
        cuenta=cuenta, tipo=DEBITO, importe=Decimal('500.00'), usuario=usuario,
    )
    client = APIClient()

    response = client.get(f'/api/v1/movimientocuentacorriente/{movimiento.id}/imprimir/')

    assert response.status_code in (401, 403)
