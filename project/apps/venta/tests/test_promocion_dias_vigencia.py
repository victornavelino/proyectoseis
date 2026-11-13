from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from articulo.models import Articulo, Categoria, ListaPrecio, Precio, TipoIva, UnidadMedida
from cliente.models import Cliente
from empleado.models import Sucursal
from persona.models import Persona
from promocion.models import DiasSemana, Promocion, PromocionArticulo

Usuario = get_user_model()

DIAS_SEMANA_CAMPOS = ('lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo')


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
    )
    Precio.objects.create(articulo=articulo, sucursal=sucursal, lista_precio=lista_precio, precio=Decimal('1000.00'))
    return sucursal, usuario, cliente, articulo


def _crear_promocion_por_precio(*, sucursal, articulo, dias_habilitados, precio_promo=Decimal('500.00')):
    dias_semana = DiasSemana.objects.create(**{dia: True for dia in dias_habilitados})
    promocion = Promocion.objects.create(
        nombre='Promo de prueba',
        fecha_inicio=date.today() - timedelta(days=1),
        fecha_fin=date.today() + timedelta(days=1),
        es_por_precio=True,
        porcentaje_todos=None,
        dias_semana=dias_semana,
        habilitada=True,
        prioridad=1,
        sucursal=sucursal,
    )
    PromocionArticulo.objects.create(promocion=promocion, articulo=articulo, valor=precio_promo)
    return promocion


def _previsualizar(client, cliente, articulo):
    return client.post(
        '/api/v1/venta/previsualizar/',
        {'cliente': cliente.id, 'articulos': [{'articulo': articulo.id, 'cantidad_peso': '1.000'}]},
        format='json',
    )


@pytest.mark.django_db
def test_promocion_se_aplica_si_hoy_es_un_dia_habilitado(contexto):
    sucursal, usuario, cliente, articulo = contexto
    hoy = DIAS_SEMANA_CAMPOS[date.today().weekday()]
    _crear_promocion_por_precio(sucursal=sucursal, articulo=articulo, dias_habilitados=[hoy])
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = _previsualizar(client, cliente, articulo)

    assert response.status_code == 200, response.data
    assert response.data['articulos'][0]['precio_promocion'] == '500.00'


@pytest.mark.django_db
def test_promocion_no_se_aplica_si_hoy_no_es_un_dia_habilitado(contexto):
    # Antes de este fix, get_promociones_activas() no miraba dias_semana para nada -> esta
    # promoción (configurada para un día que NO es hoy) se habría aplicado de todas formas.
    sucursal, usuario, cliente, articulo = contexto
    otro_dia = DIAS_SEMANA_CAMPOS[(date.today().weekday() + 1) % 7]
    _crear_promocion_por_precio(sucursal=sucursal, articulo=articulo, dias_habilitados=[otro_dia])
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = _previsualizar(client, cliente, articulo)

    assert response.status_code == 200, response.data
    assert response.data['articulos'][0]['precio_promocion'] == '1000.00'
