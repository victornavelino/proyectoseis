from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from caja.models import Banco, CuponPagoTarjeta, PagoQr, PlanTarjetaDeCredito, TarjetaDeCredito
from cliente.models import Cliente
from cuentacorriente.constants import CREDITO
from cuentacorriente.models import CuentaCorriente, MovimientoCuentaCorriente
from empleado.models import Sucursal
from persona.models import Persona

Usuario = get_user_model()


@pytest.fixture
def sucursal():
    return Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')


@pytest.fixture
def encargado(sucursal):
    # Grupo creado en usuario.migrations.0018_grupo_acceso_completo_staff -> trae delete_ de
    # tarjetadecredito/plantarjetadecredito/banco (ver usuario.permisos.MODELOS_ACCESO_COMPLETO).
    usuario = Usuario.objects.create_user(username='encargada', password='password', sucursal=sucursal, is_staff=True)
    usuario.groups.add(Group.objects.get(name='Acceso completo (staff)'))
    return usuario


@pytest.fixture
def client(encargado):
    api_client = APIClient()
    api_client.force_authenticate(user=encargado)
    return api_client


@pytest.fixture
def cliente():
    persona = Persona.objects.create(nombre='Juan', apellido='Cliente', documento_identidad='22222222')
    return Cliente.objects.create(persona=persona, condicion_iva=Cliente.CONSUMIDOR_FINAL)


@pytest.mark.django_db
def test_eliminar_tarjeta_sin_planes_se_permite(client):
    tarjeta = TarjetaDeCredito.objects.create(nombre='Visa')

    response = client.delete(f'/api/v1/tarjetadecredito/{tarjeta.id}/')

    assert response.status_code == 204, response.data
    assert not TarjetaDeCredito.objects.filter(id=tarjeta.id).exists()


@pytest.mark.django_db
def test_eliminar_tarjeta_con_planes_se_rechaza(client):
    tarjeta = TarjetaDeCredito.objects.create(nombre='Visa')
    PlanTarjetaDeCredito.objects.create(tarjeta=tarjeta, nombre_plan='3 cuotas', interes=Decimal('10.00'))

    response = client.delete(f'/api/v1/tarjetadecredito/{tarjeta.id}/')

    assert response.status_code == 400, response.data
    assert TarjetaDeCredito.objects.filter(id=tarjeta.id).exists()


@pytest.mark.django_db
def test_eliminar_plan_sin_cobros_se_permite(client):
    tarjeta = TarjetaDeCredito.objects.create(nombre='Visa')
    plan = PlanTarjetaDeCredito.objects.create(tarjeta=tarjeta, nombre_plan='3 cuotas', interes=Decimal('10.00'))

    response = client.delete(f'/api/v1/plantarjetadecredito/{plan.id}/')

    assert response.status_code == 204, response.data
    assert not PlanTarjetaDeCredito.objects.filter(id=plan.id).exists()


@pytest.mark.django_db
def test_eliminar_plan_con_cupon_de_venta_se_rechaza(client, cliente):
    tarjeta = TarjetaDeCredito.objects.create(nombre='Visa')
    plan = PlanTarjetaDeCredito.objects.create(tarjeta=tarjeta, nombre_plan='3 cuotas', interes=Decimal('10.00'))
    CuponPagoTarjeta.objects.create(
        cliente=cliente, plan_tarjeta=plan, importe=Decimal('1000.00'), recargo=Decimal('100.00'),
        importe_con_recargo=Decimal('1100.00'),
    )

    response = client.delete(f'/api/v1/plantarjetadecredito/{plan.id}/')

    assert response.status_code == 400, response.data
    assert PlanTarjetaDeCredito.objects.filter(id=plan.id).exists()


@pytest.mark.django_db
def test_eliminar_plan_usado_en_cta_corriente_se_rechaza(client, cliente, encargado):
    tarjeta = TarjetaDeCredito.objects.create(nombre='Visa')
    plan = PlanTarjetaDeCredito.objects.create(tarjeta=tarjeta, nombre_plan='3 cuotas', interes=Decimal('10.00'))
    cuenta = CuentaCorriente.objects.create(cliente=cliente, tope=Decimal('100000.00'))
    MovimientoCuentaCorriente.objects.create(
        cuenta=cuenta, tipo=CREDITO, importe=Decimal('1000.00'), usuario=encargado,
        medio_pago='tarjeta', plan_tarjeta=plan, recargo=Decimal('100.00'),
    )

    response = client.delete(f'/api/v1/plantarjetadecredito/{plan.id}/')

    assert response.status_code == 400, response.data
    assert PlanTarjetaDeCredito.objects.filter(id=plan.id).exists()


@pytest.mark.django_db
def test_eliminar_banco_sin_pagos_se_permite(client):
    banco = Banco.objects.create(nombre='Banco Nación')

    response = client.delete(f'/api/v1/banco/{banco.id}/')

    assert response.status_code == 204, response.data
    assert not Banco.objects.filter(id=banco.id).exists()


@pytest.mark.django_db
def test_eliminar_banco_con_pago_qr_se_rechaza(client):
    banco = Banco.objects.create(nombre='Banco Nación')
    PagoQr.objects.create(importe=Decimal('500.00'), documento_identidad='1', banco=banco)

    response = client.delete(f'/api/v1/banco/{banco.id}/')

    assert response.status_code == 400, response.data
    assert Banco.objects.filter(id=banco.id).exists()
