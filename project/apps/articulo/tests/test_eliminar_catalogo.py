from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from articulo.models import Articulo, Categoria, ListaPrecio, Precio, TipoIva, UnidadMedida
from cliente.models import Cliente
from empleado.models import Sucursal
from persona.models import Persona

Usuario = get_user_model()


@pytest.fixture
def usuario_staff():
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    return Usuario.objects.create_user(
        username='admin', password='password', sucursal=sucursal, is_staff=True,
    )


# --- TipoIva ---

@pytest.mark.django_db
def test_se_puede_eliminar_tipo_iva_sin_categorias(usuario_staff):
    tipo_iva = TipoIva.objects.create(nombre='21%', porcentaje=Decimal('21.00'))

    client = APIClient()
    client.force_authenticate(user=usuario_staff)
    response = client.delete(f'/api/v1/tipoiva/{tipo_iva.id}/')

    assert response.status_code == 204
    assert not TipoIva.objects.filter(id=tipo_iva.id).exists()


@pytest.mark.django_db
def test_no_se_puede_eliminar_tipo_iva_con_categorias(usuario_staff):
    tipo_iva = TipoIva.objects.create(nombre='21%', porcentaje=Decimal('21.00'))
    Categoria.objects.create(nombre='Carnes', tipo_iva=tipo_iva)

    client = APIClient()
    client.force_authenticate(user=usuario_staff)
    response = client.delete(f'/api/v1/tipoiva/{tipo_iva.id}/')

    assert response.status_code == 400
    assert TipoIva.objects.filter(id=tipo_iva.id).exists()


# --- UnidadMedida ---

@pytest.mark.django_db
def test_se_puede_eliminar_unidad_medida_sin_articulos(usuario_staff):
    unidad = UnidadMedida.objects.create(nombre='Kilogramo', abreviatura='kg')

    client = APIClient()
    client.force_authenticate(user=usuario_staff)
    response = client.delete(f'/api/v1/unidadmedida/{unidad.id}/')

    assert response.status_code == 204
    assert not UnidadMedida.objects.filter(id=unidad.id).exists()


@pytest.mark.django_db
def test_no_se_puede_eliminar_unidad_medida_con_articulos(usuario_staff):
    tipo_iva = TipoIva.objects.create(nombre='21%', porcentaje=Decimal('21.00'))
    categoria = Categoria.objects.create(nombre='Carnes', tipo_iva=tipo_iva)
    unidad = UnidadMedida.objects.create(nombre='Kilogramo', abreviatura='kg')
    Articulo.objects.create(nombre='Vacío', abreviatura='VACIO', codigo='0001', categoria=categoria, unidad_medida=unidad)

    client = APIClient()
    client.force_authenticate(user=usuario_staff)
    response = client.delete(f'/api/v1/unidadmedida/{unidad.id}/')

    assert response.status_code == 400
    assert UnidadMedida.objects.filter(id=unidad.id).exists()


# --- Categoria ---

@pytest.mark.django_db
def test_se_puede_eliminar_categoria_sin_articulos_ni_subcategorias(usuario_staff):
    tipo_iva = TipoIva.objects.create(nombre='21%', porcentaje=Decimal('21.00'))
    categoria = Categoria.objects.create(nombre='Carnes', tipo_iva=tipo_iva)

    client = APIClient()
    client.force_authenticate(user=usuario_staff)
    response = client.delete(f'/api/v1/categoria/{categoria.id}/')

    assert response.status_code == 204
    assert not Categoria.objects.filter(id=categoria.id).exists()


@pytest.mark.django_db
def test_no_se_puede_eliminar_categoria_con_articulos(usuario_staff):
    tipo_iva = TipoIva.objects.create(nombre='21%', porcentaje=Decimal('21.00'))
    categoria = Categoria.objects.create(nombre='Carnes', tipo_iva=tipo_iva)
    unidad = UnidadMedida.objects.create(nombre='Kilogramo', abreviatura='kg')
    Articulo.objects.create(nombre='Vacío', abreviatura='VACIO', codigo='0001', categoria=categoria, unidad_medida=unidad)

    client = APIClient()
    client.force_authenticate(user=usuario_staff)
    response = client.delete(f'/api/v1/categoria/{categoria.id}/')

    assert response.status_code == 400
    assert Categoria.objects.filter(id=categoria.id).exists()


@pytest.mark.django_db
def test_no_se_puede_eliminar_categoria_con_subcategorias(usuario_staff):
    tipo_iva = TipoIva.objects.create(nombre='21%', porcentaje=Decimal('21.00'))
    padre = Categoria.objects.create(nombre='Carnes', tipo_iva=tipo_iva)
    Categoria.objects.create(nombre='Vacuno', tipo_iva=tipo_iva, nodo_padre=padre)

    client = APIClient()
    client.force_authenticate(user=usuario_staff)
    response = client.delete(f'/api/v1/categoria/{padre.id}/')

    assert response.status_code == 400
    assert Categoria.objects.filter(id=padre.id).exists()


# --- ListaPrecio ---

@pytest.mark.django_db
def test_se_puede_eliminar_lista_precio_sin_uso(usuario_staff):
    lista = ListaPrecio.objects.create(nombre='Mayorista')

    client = APIClient()
    client.force_authenticate(user=usuario_staff)
    response = client.delete(f'/api/v1/listaprecio/{lista.id}/')

    assert response.status_code == 204
    assert not ListaPrecio.objects.filter(id=lista.id).exists()


@pytest.mark.django_db
def test_no_se_puede_eliminar_lista_precio_con_clientes(usuario_staff):
    lista = ListaPrecio.objects.create(nombre='Mayorista')
    persona = Persona.objects.create(nombre='Juan', apellido='Cliente', documento_identidad='22222222')
    Cliente.objects.create(persona=persona, condicion_iva=Cliente.CONSUMIDOR_FINAL, lista_precio=lista)

    client = APIClient()
    client.force_authenticate(user=usuario_staff)
    response = client.delete(f'/api/v1/listaprecio/{lista.id}/')

    assert response.status_code == 400
    assert ListaPrecio.objects.filter(id=lista.id).exists()


@pytest.mark.django_db
def test_no_se_puede_eliminar_lista_precio_con_precios(usuario_staff):
    tipo_iva = TipoIva.objects.create(nombre='21%', porcentaje=Decimal('21.00'))
    categoria = Categoria.objects.create(nombre='Carnes', tipo_iva=tipo_iva)
    unidad = UnidadMedida.objects.create(nombre='Kilogramo', abreviatura='kg')
    articulo = Articulo.objects.create(
        nombre='Vacío', abreviatura='VACIO', codigo='0001', categoria=categoria, unidad_medida=unidad,
    )
    lista = ListaPrecio.objects.create(nombre='Mayorista')
    Precio.objects.create(
        articulo=articulo, sucursal=usuario_staff.sucursal, lista_precio=lista, precio=Decimal('1000.00'),
    )

    client = APIClient()
    client.force_authenticate(user=usuario_staff)
    response = client.delete(f'/api/v1/listaprecio/{lista.id}/')

    assert response.status_code == 400
    assert ListaPrecio.objects.filter(id=lista.id).exists()


# --- Precio (sin restricciones: nada lo referencia) ---

@pytest.mark.django_db
def test_se_puede_eliminar_precio(usuario_staff):
    tipo_iva = TipoIva.objects.create(nombre='21%', porcentaje=Decimal('21.00'))
    categoria = Categoria.objects.create(nombre='Carnes', tipo_iva=tipo_iva)
    unidad = UnidadMedida.objects.create(nombre='Kilogramo', abreviatura='kg')
    articulo = Articulo.objects.create(
        nombre='Vacío', abreviatura='VACIO', codigo='0001', categoria=categoria, unidad_medida=unidad,
    )
    lista = ListaPrecio.objects.create(nombre='Mayorista')
    precio = Precio.objects.create(
        articulo=articulo, sucursal=usuario_staff.sucursal, lista_precio=lista, precio=Decimal('1000.00'),
    )

    client = APIClient()
    client.force_authenticate(user=usuario_staff)
    response = client.delete(f'/api/v1/precio/{precio.id}/')

    assert response.status_code == 204
    assert not Precio.objects.filter(id=precio.id).exists()
