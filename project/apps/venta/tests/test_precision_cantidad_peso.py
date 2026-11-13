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
def contexto():
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    usuario = Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)
    persona = Persona.objects.create(nombre='Juan', apellido='Perez', documento_identidad='30111222')
    lista_precio = ListaPrecio.objects.create(nombre='COMUN')
    cliente = Cliente.objects.create(persona=persona, condicion_iva=Cliente.CONSUMIDOR_FINAL, lista_precio=lista_precio)
    tipo_iva = TipoIva.objects.create(nombre='21%', porcentaje=Decimal('21.00'))
    categoria = Categoria.objects.create(nombre='Carnes', tipo_iva=tipo_iva)
    unidad_medida = UnidadMedida.objects.create(nombre='Kilogramo', abreviatura='kg')
    articulo = Articulo.objects.create(
        nombre='Asado', abreviatura='ASADO', codigo='0001', categoria=categoria, unidad_medida=unidad_medida,
        es_por_peso=True,
    )
    Precio.objects.create(articulo=articulo, sucursal=sucursal, lista_precio=lista_precio, precio=Decimal('1000.00'))
    return sucursal, usuario, cliente, articulo


@pytest.mark.django_db
def test_previsualizar_acepta_peso_con_tres_decimales(contexto):
    # La balanza del mostrador reporta con precisión de gramos (0.001 kg) — antes del fix,
    # ItemVentaInputSerializer.cantidad_peso sólo admitía 2 decimales y esto tiraba 400.
    _sucursal, usuario, cliente, articulo = contexto
    client = APIClient()
    client.force_authenticate(user=usuario)

    respuesta = client.post(
        '/api/v1/venta/previsualizar/',
        {'cliente': cliente.id, 'articulos': [{'articulo': articulo.id, 'cantidad_peso': '1.235'}]},
        format='json',
    )

    assert respuesta.status_code == 200, respuesta.data
    item = respuesta.data['articulos'][0]
    assert Decimal(str(item['cantidad_peso'])) == Decimal('1.235')
    assert Decimal(str(item['total_articulo'])) == Decimal('1235.00')


@pytest.mark.django_db
def test_previsualizar_sigue_aceptando_peso_con_dos_decimales(contexto):
    _sucursal, usuario, cliente, articulo = contexto
    client = APIClient()
    client.force_authenticate(user=usuario)

    respuesta = client.post(
        '/api/v1/venta/previsualizar/',
        {'cliente': cliente.id, 'articulos': [{'articulo': articulo.id, 'cantidad_peso': '2.50'}]},
        format='json',
    )

    assert respuesta.status_code == 200, respuesta.data
