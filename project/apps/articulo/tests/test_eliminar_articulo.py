from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from articulo.models import Articulo, Categoria, TipoIva, UnidadMedida
from cliente.models import Cliente
from empleado.models import Empleado, Sucursal
from persona.models import Persona
from venta.models import Venta, VentaArticulo

Usuario = get_user_model()


@pytest.fixture
def articulo():
    tipo_iva = TipoIva.objects.create(nombre='21%', porcentaje=Decimal('21.00'))
    categoria = Categoria.objects.create(nombre='Carnes', tipo_iva=tipo_iva)
    unidad_medida = UnidadMedida.objects.create(nombre='Kilogramo', abreviatura='kg')
    return Articulo.objects.create(
        nombre='Vacío', abreviatura='VACIO', codigo='0001', categoria=categoria, unidad_medida=unidad_medida,
    )


@pytest.fixture
def usuario_staff():
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    return Usuario.objects.create_user(
        username='admin', password='password', sucursal=sucursal, is_staff=True,
    )


@pytest.mark.django_db
def test_se_puede_eliminar_un_articulo_sin_ventas(articulo, usuario_staff):
    client = APIClient()
    client.force_authenticate(user=usuario_staff)

    response = client.delete(f'/api/v1/articulo/{articulo.id}/')

    assert response.status_code == 204
    assert not Articulo.objects.filter(id=articulo.id).exists()


@pytest.mark.django_db
def test_no_se_puede_eliminar_un_articulo_con_ventas(articulo, usuario_staff):
    # Regresión: django-softdelete cascadea el borrado a TODAS las relaciones reversas, sin
    # importar si el modelo relacionado es soft-delete o no. VentaArticulo es un Model común,
    # así que sin el chequeo en ArticuloViewSet.destroy() la librería terminaba borrando de
    # verdad (hard delete) el detalle de la venta, y reimprimir el ticket salía sin artículos.
    persona_empleado = Persona.objects.create(nombre='Ana', apellido='Vendedora', documento_identidad='11111111')
    empleado = Empleado.objects.create(persona=persona_empleado, cuil='20111111112')
    persona_cliente = Persona.objects.create(nombre='Juan', apellido='Cliente', documento_identidad='22222222')
    cliente = Cliente.objects.create(persona=persona_cliente, condicion_iva=Cliente.CONSUMIDOR_FINAL)

    venta = Venta.objects.create(
        empleado=empleado,
        fecha=timezone.now(),
        monto=Decimal('1000.00'),
        descuento=Decimal('0.00'),
        sucursal=usuario_staff.sucursal,
        cliente=cliente,
        usuario=usuario_staff,
    )
    venta_articulo = VentaArticulo.objects.create(
        venta=venta,
        articulo=articulo,
        nombre_articulo=articulo.nombre,
        codigo_articulo=articulo.codigo,
        cantidad_peso=Decimal('1.000'),
        precio_unitario=Decimal('1000.00'),
        precio_promocion=Decimal('1000.00'),
        total_articulo=Decimal('1000.00'),
    )

    client = APIClient()
    client.force_authenticate(user=usuario_staff)
    response = client.delete(f'/api/v1/articulo/{articulo.id}/')

    assert response.status_code == 400
    assert Articulo.objects.filter(id=articulo.id).exists()
    assert VentaArticulo.objects.filter(id=venta_articulo.id).exists()


@pytest.mark.django_db
def test_no_staff_no_puede_eliminar_articulos(articulo):
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    usuario_no_staff = Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)

    client = APIClient()
    client.force_authenticate(user=usuario_no_staff)
    response = client.delete(f'/api/v1/articulo/{articulo.id}/')

    assert response.status_code == 403
    assert Articulo.objects.filter(id=articulo.id).exists()
