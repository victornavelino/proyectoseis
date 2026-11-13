from datetime import date
from decimal import Decimal

import pytest

from articulo.models import Articulo, Categoria, ListaPrecio, Precio, TipoIva, UnidadMedida
from cliente.models import Cliente
from empleado.models import Sucursal
from persona.models import Persona
from promocion.models import Descuento
from venta.utils import calcular_precio_venta_articulo


@pytest.fixture
def contexto(db):
    """lista_precio sin 'COMUN' en el nombre a propósito: así ningún test de acá dispara el
    fallback de promociones activas (buscar_precio_articulo_en_promo) y cada caso queda
    aislado al mecanismo de descuento que está probando."""
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    persona = Persona.objects.create(nombre='Juan', apellido='Perez', documento_identidad='30111222')
    lista_precio = ListaPrecio.objects.create(nombre='MAYORISTA')
    cliente = Cliente.objects.create(persona=persona, condicion_iva=Cliente.CONSUMIDOR_FINAL, lista_precio=lista_precio)
    tipo_iva = TipoIva.objects.create(nombre='21%', porcentaje=Decimal('21.00'))
    categoria = Categoria.objects.create(nombre='Carnes', tipo_iva=tipo_iva)
    unidad_medida = UnidadMedida.objects.create(nombre='Kilogramo', abreviatura='kg')
    articulo = Articulo.objects.create(
        nombre='Asado', abreviatura='ASADO', codigo='0001', categoria=categoria, unidad_medida=unidad_medida,
    )
    Precio.objects.create(articulo=articulo, sucursal=sucursal, lista_precio=lista_precio, precio=Decimal('1000.00'))
    return sucursal, cliente, articulo


@pytest.mark.django_db
def test_sin_descuento_asignado_devuelve_el_precio_de_lista(contexto):
    sucursal, cliente, articulo = contexto

    precio_lista, precio_final = calcular_precio_venta_articulo(cliente, articulo, sucursal)

    assert precio_lista == Decimal('1000.00')
    assert precio_final == Decimal('1000.00')


@pytest.mark.django_db
def test_descuento_asignado_al_cliente_se_aplica_sobre_el_precio_de_lista(contexto):
    sucursal, cliente, articulo = contexto
    cliente.descuento = Descuento.objects.create(nombre='Gastronómicos', valor=10)
    cliente.save()

    _, precio_final = calcular_precio_venta_articulo(cliente, articulo, sucursal)

    assert precio_final == Decimal('900.00')


@pytest.mark.django_db
def test_descuento_con_valor_cero_no_descuenta_nada(contexto):
    sucursal, cliente, articulo = contexto
    cliente.descuento = Descuento.objects.create(nombre='EMPLEADOS', valor=0)
    cliente.save()

    _, precio_final = calcular_precio_venta_articulo(cliente, articulo, sucursal)

    assert precio_final == Decimal('1000.00')


@pytest.mark.django_db
def test_cumpleanios_tiene_prioridad_sobre_el_descuento_del_cliente(contexto):
    sucursal, cliente, articulo = contexto
    cliente.descuento = Descuento.objects.create(nombre='Gastronómicos', valor=10)
    cliente.save()
    cliente.persona.fecha_nacimiento = date.today()
    cliente.persona.save()
    Descuento.objects.create(nombre='CUMPLEAÑOS', valor=20)

    _, precio_final = calcular_precio_venta_articulo(cliente, articulo, sucursal)

    assert precio_final == Decimal('800.00')  # 20% (cumpleaños), no el 10% del descuento manual
