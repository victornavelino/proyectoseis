from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from caja.models import Adelanto, Caja, Gasto, Ingreso, RetiroEfectivo, Sueldo, TipoGasto, TipoIngreso
from empleado.models import Empleado, Sucursal
from persona.models import Persona

Usuario = get_user_model()

# (url, payload_extra) para cada endpoint "simple" de movimiento de caja. `payload_extra` se
# completa en cada test con lo que haga falta (empleado/tipo_ingreso/tipo_gasto).
ENDPOINTS = {
    'sueldo': ('/api/v1/sueldo/', lambda ctx: {'descripcion': 'Sueldo agosto', 'importe': '1000.00', 'empleado': ctx['empleado'].id}),
    'adelanto': ('/api/v1/adelanto/', lambda ctx: {'descripcion': 'Adelanto', 'importe': '500.00', 'empleado': ctx['empleado'].id}),
    'ingreso': ('/api/v1/ingreso/', lambda ctx: {'concepto': 'Alquiler cobrado', 'importe': '2000.00', 'tipo_ingreso': ctx['tipo_ingreso'].id}),
    'retiroefectivo': ('/api/v1/retiroefectivo/', lambda ctx: {'concepto': 'Retiro socio', 'importe': '300.00'}),
    'gasto': ('/api/v1/gasto/', lambda ctx: {'concepto': 'Papelería', 'importe': '150.00', 'tipo_gasto': ctx['tipo_gasto'].id}),
}
MODELOS = {
    'sueldo': Sueldo, 'adelanto': Adelanto, 'ingreso': Ingreso, 'retiroefectivo': RetiroEfectivo, 'gasto': Gasto,
}


@pytest.fixture
def sucursal():
    return Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')


@pytest.fixture
def otra_sucursal():
    return Sucursal.objects.create(nombre='Sucursal 2', domicilio='Otra 456')


@pytest.fixture
def usuario(sucursal):
    return Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)


@pytest.fixture
def empleado():
    persona = Persona.objects.create(nombre='Ana', apellido='Vendedora', documento_identidad='11111111')
    return Empleado.objects.create(persona=persona, cuil='20111111112')


@pytest.fixture
def tipo_ingreso():
    return TipoIngreso.objects.create(descripcion='Alquileres')


@pytest.fixture
def tipo_gasto():
    return TipoGasto.objects.create(descripcion='Insumos')


@pytest.fixture
def contexto(empleado, tipo_ingreso, tipo_gasto):
    return {'empleado': empleado, 'tipo_ingreso': tipo_ingreso, 'tipo_gasto': tipo_gasto}


@pytest.fixture
def client(usuario):
    client = APIClient()
    client.force_authenticate(user=usuario)
    return client


@pytest.mark.django_db
@pytest.mark.parametrize('recurso', ENDPOINTS.keys())
def test_crear_movimiento_con_caja_abierta(recurso, client, usuario, sucursal, contexto):
    Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=Decimal('0'))
    url, payload_fn = ENDPOINTS[recurso]

    response = client.post(url, payload_fn(contexto))

    assert response.status_code == 201, response.data
    creado = MODELOS[recurso].objects.get(pk=response.data['id'])
    # usuario/sucursal/caja/tipo los pone el servidor, no vienen del payload.
    assert creado.usuario_id == usuario.id
    assert creado.sucursal_id == sucursal.id
    assert creado.cerrado is False


@pytest.mark.django_db
@pytest.mark.parametrize('recurso', ENDPOINTS.keys())
def test_crear_movimiento_sin_caja_abierta_falla(recurso, client, contexto):
    url, payload_fn = ENDPOINTS[recurso]

    response = client.post(url, payload_fn(contexto))

    assert response.status_code == 400
    assert 'caja' in response.data


@pytest.mark.django_db
@pytest.mark.parametrize('recurso', ENDPOINTS.keys())
def test_crear_movimiento_sin_sucursal_falla(recurso, contexto):
    usuario_sin_sucursal = Usuario.objects.create_user(username='sin_sucursal', password='password')
    client = APIClient()
    client.force_authenticate(user=usuario_sin_sucursal)
    url, payload_fn = ENDPOINTS[recurso]

    response = client.post(url, payload_fn(contexto))

    assert response.status_code == 400
    assert 'caja' in response.data


@pytest.mark.django_db
@pytest.mark.parametrize('recurso', ENDPOINTS.keys())
def test_no_se_puede_editar_ni_borrar_un_movimiento_cerrado(recurso, client, usuario, sucursal, contexto):
    caja = Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=Decimal('0'))
    url, payload_fn = ENDPOINTS[recurso]
    creado_id = client.post(url, payload_fn(contexto)).data['id']
    modelo = MODELOS[recurso]
    modelo.objects.filter(pk=creado_id).update(cerrado=True)

    resp_patch = client.patch(f'{url}{creado_id}/', {'importe': '1.00'})
    resp_delete = client.delete(f'{url}{creado_id}/')

    assert resp_patch.status_code == 400
    assert 'cerrado' in resp_patch.data
    assert resp_delete.status_code == 400
    assert 'cerrado' in resp_delete.data
    assert modelo.objects.filter(pk=creado_id).exists()


@pytest.mark.django_db
@pytest.mark.parametrize('recurso', ENDPOINTS.keys())
def test_scoping_por_sucursal(recurso, client, usuario, sucursal, otra_sucursal, contexto):
    """Un movimiento de otra sucursal no debe listarse ni ser editable/borrable desde acá."""
    Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=Decimal('0'))
    usuario_otra = Usuario.objects.create_user(username='otra_cajera', password='password', sucursal=otra_sucursal)
    Caja.objects.create(sucursal=otra_sucursal, usuario=usuario_otra, caja_inicial=Decimal('0'))
    client_otra = APIClient()
    client_otra.force_authenticate(user=usuario_otra)
    url, payload_fn = ENDPOINTS[recurso]
    ajeno_id = client_otra.post(url, payload_fn(contexto)).data['id']

    listado = client.get(url)
    detalle = client.get(f'{url}{ajeno_id}/')

    assert ajeno_id not in [item['id'] for item in listado.data['results']]
    assert detalle.status_code == 404
