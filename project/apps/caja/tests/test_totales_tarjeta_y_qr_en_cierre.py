from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from rest_framework.test import APIClient

from caja.models import Caja, CuponPagoTarjeta, PagoQr, PlanTarjetaDeCredito, TarjetaDeCredito
from cliente.models import Cliente
from empleado.models import Sucursal
from persona.models import Persona

Usuario = get_user_model()


@pytest.fixture
def contexto():
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    usuario = Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)
    usuario.groups.add(Group.objects.get(name='Acceso operativo (ventas y caja)'))
    persona_cliente = Persona.objects.create(nombre='Juan', apellido='Cliente', documento_identidad='22222222')
    cliente = Cliente.objects.create(persona=persona_cliente, condicion_iva=Cliente.CONSUMIDOR_FINAL)
    caja = Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=Decimal('0'))
    client = APIClient()
    client.force_authenticate(user=usuario)
    return {'caja': caja, 'cliente': cliente, 'client': client}


@pytest.mark.django_db
def test_previsualizar_cierre_incluye_total_tarjeta_y_total_qr(contexto):
    # Compra con tarjeta: el total que importa para el cierre es importe_con_recargo (lo que
    # realmente pagó el cliente), no `importe` solo.
    tarjeta = TarjetaDeCredito.objects.create(nombre='Visa')
    plan = PlanTarjetaDeCredito.objects.create(tarjeta=tarjeta, nombre_plan='1 pago')
    CuponPagoTarjeta.objects.create(
        cliente=contexto['cliente'], plan_tarjeta=plan, importe=Decimal('1000.00'), recargo=Decimal('50.00'),
        importe_con_recargo=Decimal('1050.00'),
    )
    PagoQr.objects.create(importe=Decimal('300.00'), documento_identidad='22222222')

    response = contexto['client'].get(f"/api/v1/caja/{contexto['caja'].id}/previsualizar-cierre/")

    assert response.status_code == 200, response.data
    data = response.json()
    # Sum() sobre un DecimalField preserva la escala en Postgres pero no en SQLite (motor de los
    # tests) -> se compara como Decimal, no como string, mismo criterio que
    # venta.api.VentaViewSet.resumen_dashboard._money.
    assert data['total_tarjeta']['concepto'] == 'TOTAL TARJETA'
    assert Decimal(data['total_tarjeta']['importe']) == Decimal('1050.00')
    assert data['total_qr']['concepto'] == 'TOTAL QR'
    assert Decimal(data['total_qr']['importe']) == Decimal('300.00')


@pytest.mark.django_db
def test_imprimir_ticket_de_cierre_no_rompe_con_tarjeta_y_qr_cargados(contexto):
    # El contenido del PDF no se puede inspeccionar de forma confiable (WeasyPrint puede
    # comprimir los streams de texto) -> mismo criterio que test_imprimir_caja.py: sólo se
    # confirma que la plantilla (ahora con las dos filas nuevas) sigue generando un PDF válido.
    CuponPagoTarjeta.objects.create(
        cliente=contexto['cliente'],
        plan_tarjeta=PlanTarjetaDeCredito.objects.create(
            tarjeta=TarjetaDeCredito.objects.create(nombre='Visa'), nombre_plan='1 pago',
        ),
        importe=Decimal('200.00'), recargo=Decimal('0'), importe_con_recargo=Decimal('200.00'),
    )
    PagoQr.objects.create(importe=Decimal('150.00'), documento_identidad='22222222')
    contexto['client'].post(f"/api/v1/caja/{contexto['caja'].id}/cerrar/", {'arqueo': '350.00'})

    response = contexto['client'].get(f"/api/v1/caja/{contexto['caja'].id}/imprimir/")

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert response.content.startswith(b'%PDF')
