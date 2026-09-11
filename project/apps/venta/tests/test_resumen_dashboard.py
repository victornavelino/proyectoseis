from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from articulo.models import Articulo, Categoria, TipoIva, UnidadMedida
from caja.constants import INGRESO
from caja.models import Caja, CobroVenta
from cliente.models import Cliente
from empleado.models import Empleado, Sucursal
from persona.models import Persona
from venta.models import Venta, VentaArticulo

Usuario = get_user_model()


@pytest.fixture
def contexto():
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    otra_sucursal = Sucursal.objects.create(nombre='Sucursal 2', domicilio='Otra 456')
    persona_empleado = Persona.objects.create(nombre='Ana', apellido='Vendedora', documento_identidad='11111111')
    empleado = Empleado.objects.create(persona=persona_empleado, cuil='20111111112')
    usuario = Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)
    persona_cliente = Persona.objects.create(nombre='Juan', apellido='Perez', documento_identidad='30111222')
    cliente = Cliente.objects.create(persona=persona_cliente, condicion_iva=Cliente.CONSUMIDOR_FINAL)
    tipo_iva = TipoIva.objects.create(nombre='21%', porcentaje=Decimal('21.00'))
    categoria = Categoria.objects.create(nombre='Carnes', tipo_iva=tipo_iva)
    unidad_medida = UnidadMedida.objects.create(nombre='Kilogramo', abreviatura='kg')
    articulo = Articulo.objects.create(
        nombre='Asado', abreviatura='ASADO', codigo='0001', categoria=categoria, unidad_medida=unidad_medida,
    )

    venta_hoy = Venta.objects.create(
        empleado=empleado, fecha=timezone.now(), monto=Decimal('1000.00'), descuento=Decimal('0.00'),
        sucursal=sucursal, cliente=cliente, usuario=usuario, cobrada=True,
    )
    VentaArticulo.objects.create(
        venta=venta_hoy, articulo=articulo, nombre_articulo=articulo.nombre, codigo_articulo=articulo.codigo,
        cantidad_peso=Decimal('2.5'), precio_unitario=Decimal('400'), precio_promocion=Decimal('400'),
        total_articulo=Decimal('1000.00'),
    )
    caja = Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=Decimal('500.00'))
    CobroVenta.objects.create(
        usuario=usuario, importe=Decimal('1000.00'), sucursal=sucursal, caja=caja, tipo=INGRESO, venta=venta_hoy,
    )

    # Venta anulada: no debería sumar a ningún total.
    Venta.objects.create(
        empleado=empleado, fecha=timezone.now(), monto=Decimal('5000.00'), descuento=Decimal('0.00'),
        sucursal=sucursal, cliente=cliente, usuario=usuario, anulado=True,
    )

    # Venta de otra sucursal: no debería filtrarse en el resumen de `usuario`.
    otro_usuario = Usuario.objects.create_user(username='otra-cajera', password='password', sucursal=otra_sucursal)
    Venta.objects.create(
        empleado=empleado, fecha=timezone.now(), monto=Decimal('9999.00'), descuento=Decimal('0.00'),
        sucursal=otra_sucursal, cliente=cliente, usuario=otro_usuario,
    )

    return usuario, venta_hoy, caja


@pytest.mark.django_db
def test_resumen_dashboard_agrega_solo_la_sucursal_del_usuario(contexto):
    usuario, venta_hoy, caja = contexto
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = client.get('/api/v1/venta/resumen-dashboard/')

    assert response.status_code == 200
    data = response.json()

    assert data['hoy']['total'] == '1000.00'
    assert data['hoy']['cantidad_tickets'] == 1
    assert data['hoy']['ticket_promedio'] == '1000.00'

    assert data['caja']['abierta'] is True
    assert data['caja']['saldo'] == str(caja.caja_inicial + venta_hoy.monto)

    hoy_iso = timezone.localdate().isoformat()
    fila_hoy = next(f for f in data['ventas_por_dia'] if f['fecha'] == hoy_iso)
    assert fila_hoy['total'] == '1000.00'

    assert data['top_articulos'][0]['nombre'] == 'Asado'
    assert data['top_articulos'][0]['total'] == '1000.00'

    efectivo = next(m for m in data['medios_pago'] if m['medio'] == 'efectivo')
    assert efectivo['total'] == '1000.00'


@pytest.mark.django_db
def test_resumen_dashboard_sin_caja_abierta(contexto):
    usuario, _venta_hoy, caja = contexto
    caja.fecha_fin = timezone.now()
    caja.save(update_fields=['fecha_fin'])
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = client.get('/api/v1/venta/resumen-dashboard/')

    assert response.status_code == 200
    assert response.json()['caja'] == {'abierta': False}
