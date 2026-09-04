from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from caja.models import Caja
from empleado.models import Sucursal

Usuario = get_user_model()


@pytest.fixture
def sucursal():
    return Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')


@pytest.fixture
def usuario(sucursal):
    return Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)


@pytest.mark.django_db
def test_filtro_fecha_fin_isnull_no_devuelve_cajas_cerradas(sucursal, usuario):
    """Regresión: filterset_fields como tupla plana sólo generaba el lookup 'exact' para
    fecha_fin, así que ?fecha_fin__isnull=true (lo que usa el frontend para pedir la caja
    abierta, api/caja.ts cajaAbiertaActual) no filtraba nada y devolvía la última caja de la
    sucursal aunque estuviera cerrada -> el frontend seguía mostrando "Cerrar caja" después
    de cerrarla.
    """
    Caja.objects.create(
        sucursal=sucursal, usuario=usuario, fecha_fin=timezone.now(), caja_inicial=Decimal('0'),
        caja_final=Decimal('500.00'),
    )
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = client.get('/api/v1/caja/', {'sucursal': sucursal.id, 'fecha_fin__isnull': 'true', 'page_size': 1})

    assert response.status_code == 200
    assert response.json()['results'] == []


@pytest.mark.django_db
def test_filtro_fecha_fin_isnull_devuelve_la_caja_abierta(sucursal, usuario):
    cerrada = Caja.objects.create(
        sucursal=sucursal, usuario=usuario, fecha_fin=timezone.now(), caja_inicial=Decimal('0'),
        caja_final=Decimal('500.00'),
    )
    abierta = Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=cerrada.caja_final)
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = client.get('/api/v1/caja/', {'sucursal': sucursal.id, 'fecha_fin__isnull': 'true', 'page_size': 1})

    assert response.status_code == 200
    resultados = response.json()['results']
    assert [c['id'] for c in resultados] == [abierta.id]


@pytest.mark.django_db
def test_abrir_caja_hereda_el_saldo_de_la_caja_anterior(sucursal, usuario):
    Caja.objects.create(
        sucursal=sucursal, usuario=usuario, fecha_fin=timezone.now(), caja_inicial=Decimal('0'),
        caja_final=Decimal('750.50'),
    )
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = client.post('/api/v1/caja/abrir/')

    assert response.status_code == 201
    assert response.json()['caja_inicial'] == '750.50'
