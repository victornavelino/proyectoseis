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
def venta():
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    persona_empleado = Persona.objects.create(nombre='Ana', apellido='Vendedora', documento_identidad='11111111')
    empleado = Empleado.objects.create(persona=persona_empleado, cuil='20111111112')
    persona_cliente = Persona.objects.create(nombre='Juan', apellido='Cliente', documento_identidad='22222222')
    cliente = Cliente.objects.create(persona=persona_cliente, condicion_iva=Cliente.CONSUMIDOR_FINAL)
    usuario = Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)

    tipo_iva = TipoIva.objects.create(nombre='21%', porcentaje=Decimal('21.00'))
    categoria = Categoria.objects.create(nombre='Carnes', tipo_iva=tipo_iva)
    unidad_medida = UnidadMedida.objects.create(nombre='Kilogramo', abreviatura='kg')
    articulo = Articulo.objects.create(
        nombre='Vacío', abreviatura='VACIO', codigo='0001', categoria=categoria, unidad_medida=unidad_medida,
    )

    venta = Venta.objects.create(
        empleado=empleado,
        fecha=timezone.now(),
        monto=Decimal('1000.00'),
        descuento=Decimal('0.00'),
        sucursal=sucursal,
        cliente=cliente,
        usuario=usuario,
    )
    VentaArticulo.objects.create(
        venta=venta,
        articulo=articulo,
        nombre_articulo=articulo.nombre,
        codigo_articulo=articulo.codigo,
        cantidad_peso=Decimal('1.000'),
        precio_unitario=Decimal('1000.00'),
        precio_promocion=Decimal('1000.00'),
        total_articulo=Decimal('1000.00'),
    )
    return venta


@pytest.mark.django_db
def test_imprimir_ticket_devuelve_pdf(venta):
    client = APIClient()
    client.force_authenticate(user=venta.usuario)

    response = client.get(f'/api/v1/venta/{venta.numero_ticket}/imprimir/')

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert response.content.startswith(b'%PDF')


@pytest.mark.django_db
def test_imprimir_ticket_requiere_autenticacion(venta):
    client = APIClient()

    response = client.get(f'/api/v1/venta/{venta.numero_ticket}/imprimir/')

    assert response.status_code in (401, 403)
