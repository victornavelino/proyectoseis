from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from caja.models import Caja
from empleado.models import Empleado, Sucursal
from persona.models import Persona

Usuario = get_user_model()

ENDPOINT = '/api/v1/usuario-sucursal/'


def crear_sucursal(nombre='Sucursal 1'):
    return Sucursal.objects.create(nombre=nombre, domicilio=f'Domicilio {nombre}')


def crear_encargado(sucursal, **extra):
    return Usuario.objects.create_user(
        username=extra.pop('username', 'encargado'),
        password='password',
        is_staff=True,
        sucursal=sucursal,
        **extra,
    )


@pytest.mark.django_db
def test_encargado_puede_crear_usuario_en_su_sucursal():
    sucursal = crear_sucursal()
    encargado = crear_encargado(sucursal)
    client = APIClient()
    client.force_authenticate(user=encargado)

    response = client.post(ENDPOINT, {
        'username': 'cajero1',
        'password': 'una-contraseña-segura-123',
        'first_name': 'Cajero',
        'last_name': 'Uno',
        'email': 'cajero1@example.com',
    })

    assert response.status_code == 201, response.data
    usuario = Usuario.objects.get(username='cajero1')
    assert usuario.sucursal_id == sucursal.id
    assert usuario.is_staff is False
    assert usuario.check_password('una-contraseña-segura-123')


@pytest.mark.django_db
def test_no_puede_asignarse_a_otra_sucursal_ni_marcarse_staff():
    sucursal_propia = crear_sucursal('Propia')
    otra_sucursal = crear_sucursal('Otra')
    encargado = crear_encargado(sucursal_propia)
    client = APIClient()
    client.force_authenticate(user=encargado)

    response = client.post(ENDPOINT, {
        'username': 'cajero2',
        'password': 'una-contraseña-segura-123',
        'sucursal': otra_sucursal.id,
        'is_staff': True,
    })

    assert response.status_code == 201, response.data
    usuario = Usuario.objects.get(username='cajero2')
    # El payload intentó otra sucursal y is_staff=True: ambos campos se ignoran, no se exponen
    # en el serializer (UsuarioSucursalSerializer sólo expone campos operativos).
    assert usuario.sucursal_id == sucursal_propia.id
    assert usuario.is_staff is False


@pytest.mark.django_db
def test_usuario_no_staff_no_puede_crear():
    sucursal = crear_sucursal()
    cajero = Usuario.objects.create_user(username='cajero', password='password', sucursal=sucursal, is_staff=False)
    client = APIClient()
    client.force_authenticate(user=cajero)

    response = client.post(ENDPOINT, {'username': 'nuevo', 'password': 'una-contraseña-segura-123'})

    assert response.status_code == 403


@pytest.mark.django_db
def test_encargado_sin_sucursal_no_puede_crear():
    encargado = Usuario.objects.create_user(username='encargado_sin_sucursal', password='password', is_staff=True)
    client = APIClient()
    client.force_authenticate(user=encargado)

    response = client.post(ENDPOINT, {'username': 'nuevo', 'password': 'una-contraseña-segura-123'})

    assert response.status_code == 403


@pytest.mark.django_db
def test_password_requerida_al_crear():
    sucursal = crear_sucursal()
    encargado = crear_encargado(sucursal)
    client = APIClient()
    client.force_authenticate(user=encargado)

    response = client.post(ENDPOINT, {'username': 'sin_clave'})

    assert response.status_code == 400
    assert 'password' in response.data


@pytest.mark.django_db
def test_encargado_puede_vincular_un_empleado_al_crear():
    # El frontend arma Persona + Empleado + Usuario en una sola pantalla (ver
    # UsuarioSucursalFormModal) — acá se simula el último paso, con el Empleado ya creado.
    sucursal = crear_sucursal()
    encargado = crear_encargado(sucursal)
    persona = Persona.objects.create(nombre='Ana', apellido='Vendedora', documento_identidad='30111222')
    empleado = Empleado.objects.create(persona=persona, cuil='20301112223')
    client = APIClient()
    client.force_authenticate(user=encargado)

    response = client.post(ENDPOINT, {
        'username': 'cajero3',
        'password': 'una-contraseña-segura-123',
        'empleado': empleado.id,
    })

    assert response.status_code == 201, response.data
    usuario = Usuario.objects.get(username='cajero3')
    assert usuario.empleado_id == empleado.id
    assert response.data['empleado_detalle'] == {
        'persona': persona.id,
        'nombre': 'Ana',
        'apellido': 'Vendedora',
        'documento_identidad': '30111222',
        'cuil': '20301112223',
    }


@pytest.mark.django_db
def test_sin_empleado_vinculado_empleado_detalle_es_null():
    sucursal = crear_sucursal()
    encargado = crear_encargado(sucursal)
    client = APIClient()
    client.force_authenticate(user=encargado)

    response = client.post(ENDPOINT, {'username': 'sin_empleado', 'password': 'una-contraseña-segura-123'})

    assert response.status_code == 201, response.data
    assert response.data['empleado'] is None
    assert response.data['empleado_detalle'] is None


@pytest.mark.django_db
def test_encargado_solo_ve_usuarios_de_su_propia_sucursal():
    sucursal_propia = crear_sucursal('Propia')
    otra_sucursal = crear_sucursal('Otra')
    encargado = crear_encargado(sucursal_propia)
    Usuario.objects.create_user(username='de_mi_sucursal', password='password', sucursal=sucursal_propia)
    Usuario.objects.create_user(username='de_otra_sucursal', password='password', sucursal=otra_sucursal)
    client = APIClient()
    client.force_authenticate(user=encargado)

    response = client.get(ENDPOINT)

    assert response.status_code == 200
    usernames = {u['username'] for u in response.data['results']}
    assert usernames == {'de_mi_sucursal'}


@pytest.mark.django_db
def test_encargado_puede_eliminar_un_usuario_sin_historial():
    sucursal = crear_sucursal()
    encargado = crear_encargado(sucursal)
    sin_uso = Usuario.objects.create_user(username='sin_uso', password='password', sucursal=sucursal)
    client = APIClient()
    client.force_authenticate(user=encargado)

    response = client.delete(f'{ENDPOINT}{sin_uso.id}/')

    assert response.status_code == 204
    assert not Usuario.objects.filter(id=sin_uso.id).exists()


@pytest.mark.django_db
def test_no_se_puede_eliminar_un_usuario_con_historial_de_caja():
    # Caja.usuario es on_delete=PROTECT — borrar debe rechazarse con un mensaje claro, no un
    # 500 crudo por ProtectedError (mismo criterio que cliente.api.ClienteViewSet.destroy).
    sucursal = crear_sucursal()
    encargado = crear_encargado(sucursal)
    cajero = Usuario.objects.create_user(username='cajero_con_historial', password='password', sucursal=sucursal)
    Caja.objects.create(sucursal=sucursal, usuario=cajero, caja_inicial=Decimal('0'))
    client = APIClient()
    client.force_authenticate(user=encargado)

    response = client.delete(f'{ENDPOINT}{cajero.id}/')

    assert response.status_code == 400
    assert Usuario.objects.filter(id=cajero.id).exists()
