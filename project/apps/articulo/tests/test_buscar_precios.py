from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from articulo.models import Articulo, Categoria, ListaPrecio, Precio, TipoIva, UnidadMedida
from empleado.models import Sucursal

Usuario = get_user_model()


@pytest.fixture
def contexto(db):
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    usuario = Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)
    lista_precio = ListaPrecio.objects.create(nombre='COMUN')
    tipo_iva = TipoIva.objects.create(nombre='21%', porcentaje=Decimal('21.00'))
    categoria = Categoria.objects.create(nombre='Carnes', tipo_iva=tipo_iva)
    unidad_medida = UnidadMedida.objects.create(nombre='Kilogramo', abreviatura='kg')
    asado = Articulo.objects.create(
        nombre='Asado', abreviatura='ASADO', codigo='0001', categoria=categoria, unidad_medida=unidad_medida,
    )
    vacio = Articulo.objects.create(
        nombre='Vacío', abreviatura='VACIO', codigo='0002', categoria=categoria, unidad_medida=unidad_medida,
    )
    Precio.objects.create(articulo=asado, sucursal=sucursal, lista_precio=lista_precio, precio=Decimal('1000.00'))
    Precio.objects.create(articulo=vacio, sucursal=sucursal, lista_precio=lista_precio, precio=Decimal('1200.00'))
    return usuario


@pytest.mark.django_db
def test_buscar_precio_por_nombre_de_articulo(contexto):
    usuario = contexto
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = client.get('/api/v1/precio/', {'search': 'asado'})

    assert response.status_code == 200
    resultados = response.json()['results']
    assert [r['articulo_nombre'] for r in resultados] == ['Asado']


@pytest.mark.django_db
def test_buscar_precio_por_codigo_de_articulo(contexto):
    usuario = contexto
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = client.get('/api/v1/precio/', {'search': '0002'})

    assert response.status_code == 200
    resultados = response.json()['results']
    assert [r['articulo_nombre'] for r in resultados] == ['Vacío']
