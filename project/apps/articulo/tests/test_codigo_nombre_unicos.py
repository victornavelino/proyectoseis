from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from articulo.models import Articulo, Categoria, TipoIva, UnidadMedida
from empleado.models import Sucursal

Usuario = get_user_model()


@pytest.fixture
def categoria_y_unidad():
    tipo_iva = TipoIva.objects.create(nombre='21%', porcentaje=Decimal('21.00'))
    categoria = Categoria.objects.create(nombre='Carnes', tipo_iva=tipo_iva)
    unidad_medida = UnidadMedida.objects.create(nombre='Kilogramo', abreviatura='kg')
    return categoria, unidad_medida


@pytest.fixture
def usuario_staff():
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    return Usuario.objects.create_user(
        username='admin', password='password', sucursal=sucursal, is_staff=True,
    )


def _datos_articulo(categoria, unidad_medida, **overrides):
    datos = {
        'nombre': 'Vacío',
        'abreviatura': 'VACIO',
        'codigo': '0001',
        'categoria': categoria.id,
        'unidad_medida': unidad_medida.id,
        'es_por_peso': True,
    }
    datos.update(overrides)
    return datos


@pytest.mark.django_db
def test_no_se_puede_crear_articulo_con_codigo_duplicado(categoria_y_unidad, usuario_staff):
    categoria, unidad_medida = categoria_y_unidad
    Articulo.objects.create(
        nombre='Vacío', abreviatura='VACIO', codigo='0001', categoria=categoria, unidad_medida=unidad_medida,
    )

    client = APIClient()
    client.force_authenticate(user=usuario_staff)
    response = client.post(
        '/api/v1/articulo/',
        _datos_articulo(categoria, unidad_medida, nombre='Otro nombre'),
        format='json',
    )

    assert response.status_code == 400
    assert 'código de barras' in str(response.data)


@pytest.mark.django_db
def test_no_se_puede_crear_articulo_con_nombre_duplicado(categoria_y_unidad, usuario_staff):
    categoria, unidad_medida = categoria_y_unidad
    Articulo.objects.create(
        nombre='Vacío', abreviatura='VACIO', codigo='0001', categoria=categoria, unidad_medida=unidad_medida,
    )

    client = APIClient()
    client.force_authenticate(user=usuario_staff)
    response = client.post(
        '/api/v1/articulo/',
        _datos_articulo(categoria, unidad_medida, codigo='0002'),
        format='json',
    )

    assert response.status_code == 400
    assert 'nombre' in str(response.data)


@pytest.mark.django_db
def test_se_puede_reusar_codigo_y_nombre_de_un_articulo_eliminado(categoria_y_unidad, usuario_staff):
    # Regresión: el borrado de un articulo es logico (SoftDeleteObject), pero antes el codigo/
    # nombre seguian "ocupados" para siempre por la restriccion unique=True a nivel de columna,
    # y crear un articulo nuevo con el mismo valor rompia con un IntegrityError (500) en vez de
    # dejarlo pasar. Ahora la restriccion solo aplica entre articulos activos.
    categoria, unidad_medida = categoria_y_unidad
    original = Articulo.objects.create(
        nombre='Vacío', abreviatura='VACIO', codigo='0001', categoria=categoria, unidad_medida=unidad_medida,
    )
    original.delete()
    assert not Articulo.objects.filter(id=original.id).exists()  # soft-delete: no aparece en el manager por defecto

    client = APIClient()
    client.force_authenticate(user=usuario_staff)
    response = client.post(
        '/api/v1/articulo/',
        _datos_articulo(categoria, unidad_medida),
        format='json',
    )

    assert response.status_code == 201
