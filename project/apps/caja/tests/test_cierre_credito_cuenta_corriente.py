from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from caja.models import Caja
from cliente.models import Cliente
from cuentacorriente.models import CuentaCorriente
from cuentacorriente.services import crear_movimiento_cuenta_corriente
from cuentacorriente.constants import CREDITO
from empleado.models import Sucursal
from persona.models import Persona

Usuario = get_user_model()


@pytest.fixture
def contexto():
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    usuario = Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)
    usuario.groups.add(Group.objects.get(name='Acceso operativo (ventas y caja)'))
    persona = Persona.objects.create(nombre='Adrian', apellido='Altamirano', documento_identidad='30999888')
    cliente = Cliente.objects.create(persona=persona, condicion_iva=Cliente.CONSUMIDOR_FINAL)
    cuenta = CuentaCorriente.objects.create(cliente=cliente, tope=Decimal('100000.00'))
    caja = Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=Decimal('0'))
    client = APIClient()
    client.force_authenticate(user=usuario)
    return {'caja': caja, 'cuenta': cuenta, 'usuario': usuario, 'client': client}


@pytest.mark.django_db
def test_credito_en_efectivo_no_se_duplica_en_el_resumen_de_cierre(contexto):
    """Regresión: "Cobranzas Cta Corriente" e "Ingresos Varios" mostraban el mismo crédito dos
    veces (una leyendo caja.Ingreso, otra leyendo MovimientoCuentaCorriente directo) -> TOTAL
    INGRESOS quedaba el doble de lo que realmente se cobró."""
    crear_movimiento_cuenta_corriente(
        cuenta=contexto['cuenta'], tipo=CREDITO, importe=Decimal('88000.00'),
        usuario=contexto['usuario'], medio_pago='efectivo',
    )

    response = contexto['client'].get(f"/api/v1/caja/{contexto['caja'].id}/previsualizar-cierre/")

    assert response.status_code == 200, response.data
    data = response.json()
    conceptos = {fila['concepto'] for fila in data['ingresos']}
    assert 'Cobranzas Cta Corriente' not in conceptos
    assert Decimal(data['total_ingresos']['importe']) == Decimal('88000.00')


@pytest.mark.django_db
def test_credito_por_qr_cuenta_en_total_qr_no_en_ingresos_ni_en_el_arqueo(contexto):
    crear_movimiento_cuenta_corriente(
        cuenta=contexto['cuenta'], tipo=CREDITO, importe=Decimal('88000.00'),
        usuario=contexto['usuario'], medio_pago='qr',
    )

    response = contexto['client'].get(f"/api/v1/caja/{contexto['caja'].id}/previsualizar-cierre/")

    assert response.status_code == 200, response.data
    data = response.json()
    assert Decimal(data['total_qr']['importe']) == Decimal('88000.00')
    assert Decimal(data['total_ingresos']['importe']) == Decimal('0')
    # El monto calculado (arqueo esperado) no tiene que incluir la plata que entró por QR.
    assert Decimal(data['caja_final_calculado']) == Decimal('0')
