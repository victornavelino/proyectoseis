from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from caja.models import Caja, TipoIngreso
from empleado.models import Sucursal

Usuario = get_user_model()


@pytest.fixture
def sucursal():
    return Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')


@pytest.fixture
def usuario(sucursal):
    return Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)


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


@pytest.mark.django_db
def test_cerrar_con_sobrante_cierra_igual(client, caja_abierta):
    response = client.post(f'/api/v1/caja/{caja_abierta.id}/cerrar/', {'arqueo': '120.00'})

    assert response.status_code == 200
    caja_abierta.refresh_from_db()
    assert caja_abierta.arqueo == Decimal('120.00')


@pytest.mark.django_db
def test_cerrar_sin_arqueo_rechaza(client, caja_abierta):
    response = client.post(f'/api/v1/caja/{caja_abierta.id}/cerrar/', {})

    assert response.status_code == 400
