from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from caja.models import Caja, TipoIngreso
from empleado.models import Sucursal

Usuario = get_user_model()


@pytest.fixture
def sucursal():
    return Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')


@pytest.fixture
def usuario(sucursal):
    # Cerrar caja ahora exige el permiso caja.change_caja (ver util.permissions.TienePermiso) —
    # ver comentario equivalente en caja/tests/test_caja_abierta.py.
    usuario = Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)
    usuario.groups.add(Group.objects.get(name='Acceso operativo (ventas y caja)'))
    return usuario


@pytest.fixture
def caja_abierta(sucursal, usuario):
    return Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=Decimal('100.00'))


@pytest.fixture
def client(usuario):
    api_client = APIClient()
    api_client.force_authenticate(user=usuario)
    return api_client


@pytest.mark.django_db
def test_previsualizar_cierre_no_cierra_la_caja(client, caja_abierta):
    response = client.get(f'/api/v1/caja/{caja_abierta.id}/previsualizar-cierre/')

    assert response.status_code == 200
    data = response.json()
    assert data['fecha_fin'] is None
    assert data['caja_final_calculado'] == '100.00'
    caja_abierta.refresh_from_db()
    assert caja_abierta.fecha_fin is None


@pytest.mark.django_db
def test_previsualizar_cierre_rechaza_si_ya_esta_cerrada(client, caja_abierta):
    client.post(f'/api/v1/caja/{caja_abierta.id}/cerrar/', {'arqueo': '100.00'})

    response = client.get(f'/api/v1/caja/{caja_abierta.id}/previsualizar-cierre/')

    assert response.status_code == 400


@pytest.mark.django_db
def test_cerrar_con_arqueo_insuficiente_rechaza_y_no_cierra(client, caja_abierta):
    tipo_ingreso = TipoIngreso.objects.create(descripcion='Varios')
    client.post('/api/v1/ingreso/', {'concepto': 'Ingreso extra', 'importe': '50.00', 'tipo_ingreso': tipo_ingreso.id})

    response = client.post(f'/api/v1/caja/{caja_abierta.id}/cerrar/', {'arqueo': '149.99'})

    assert response.status_code == 400
    caja_abierta.refresh_from_db()
    assert caja_abierta.fecha_fin is None
    assert caja_abierta.arqueo is None


@pytest.mark.django_db
def test_cerrar_con_arqueo_igual_al_calculado_cierra(client, caja_abierta):
    response = client.post(f'/api/v1/caja/{caja_abierta.id}/cerrar/', {'arqueo': '100.00'})

    assert response.status_code == 200
    data = response.json()
    assert data['caja_final_calculado'] == '100.00'
    caja_abierta.refresh_from_db()
    assert caja_abierta.fecha_fin is not None
    assert caja_abierta.arqueo == Decimal('100.00')
    assert caja_abierta.caja_final == Decimal('100.00')


@pytest.mark.django_db
def test_cerrar_con_sobrante_guarda_el_arqueo_como_caja_final(client, caja_abierta):
    # Regresión: cerrar_caja() guardaba el monto TEÓRICO calculado como caja_final, ignorando el
    # sobrante contado a mano — la próxima caja de la sucursal heredaba un monto inicial menor
    # al efectivo real que había en el cajón.
    response = client.post(f'/api/v1/caja/{caja_abierta.id}/cerrar/', {'arqueo': '120.00'})

    assert response.status_code == 200
    data = response.json()
    assert data['caja_final_calculado'] == '100.00'
    assert data['caja_final'] == '120.00'
    caja_abierta.refresh_from_db()
    assert caja_abierta.arqueo == Decimal('120.00')
    assert caja_abierta.caja_final == Decimal('120.00')


@pytest.mark.django_db
def test_siguiente_caja_hereda_el_sobrante_contado_no_el_calculado(client, caja_abierta, sucursal, usuario):
    client.post(f'/api/v1/caja/{caja_abierta.id}/cerrar/', {'arqueo': '120.00'})

    response = client.post('/api/v1/caja/abrir/')

    assert response.status_code == 201
    assert response.json()['caja_inicial'] == '120.00'


@pytest.mark.django_db
def test_cerrar_sin_arqueo_rechaza(client, caja_abierta):
    response = client.post(f'/api/v1/caja/{caja_abierta.id}/cerrar/', {})

    assert response.status_code == 400
