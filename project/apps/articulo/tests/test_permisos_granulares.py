import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient

from articulo.models import TipoIva
from empleado.models import Sucursal

Usuario = get_user_model()


@pytest.fixture
def sucursal():
    return Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')


@pytest.fixture
def permiso_add_tipoiva():
    content_type = ContentType.objects.get_for_model(TipoIva)
    return Permission.objects.get(content_type=content_type, codename='add_tipoiva')


@pytest.mark.django_db
def test_autenticado_sin_permiso_puede_leer_pero_no_crear(sucursal):
    usuario = Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)
    client = APIClient()
    client.force_authenticate(user=usuario)

    respuesta_lectura = client.get('/api/v1/tipoiva/')
    assert respuesta_lectura.status_code == 200

    respuesta_alta = client.post('/api/v1/tipoiva/', {'nombre': '10.5%', 'porcentaje': '10.50'})
    assert respuesta_alta.status_code == 403


@pytest.mark.django_db
def test_is_staff_sin_permiso_explicito_no_puede_crear(sucursal):
    # TienePermisoDeModelo reemplazó a IsStaffOrReadOnly: ser is_staff ya no alcanza por sí
    # solo, hace falta el permiso Django concreto (otorgado por grupo o individualmente).
    usuario = Usuario.objects.create_user(username='admin', password='password', sucursal=sucursal, is_staff=True)
    client = APIClient()
    client.force_authenticate(user=usuario)

    respuesta = client.post('/api/v1/tipoiva/', {'nombre': '10.5%', 'porcentaje': '10.50'})
    assert respuesta.status_code == 403


@pytest.mark.django_db
def test_permiso_especifico_alcanza_sin_ser_staff(sucursal, permiso_add_tipoiva):
    # El punto central del esquema: una cuenta NO staff con sólo el permiso puntual puede
    # escribir en ese modelo, y sólo en ese.
    usuario = Usuario.objects.create_user(username='encargado_stock', password='password', sucursal=sucursal)
    usuario.user_permissions.add(permiso_add_tipoiva)

    client = APIClient()
    client.force_authenticate(user=usuario)

    respuesta = client.post('/api/v1/tipoiva/', {'nombre': '10.5%', 'porcentaje': '10.50'})
    assert respuesta.status_code == 201
    assert TipoIva.objects.filter(nombre='10.5%').exists()

    # Pero no puede borrar (no tiene delete_tipoiva).
    creado = TipoIva.objects.get(nombre='10.5%')
    respuesta_borrado = client.delete(f'/api/v1/tipoiva/{creado.id}/')
    assert respuesta_borrado.status_code == 403


@pytest.mark.django_db
def test_superusuario_no_necesita_permisos_explicitos(sucursal):
    usuario = Usuario.objects.create_user(
        username='dueño', password='password', sucursal=sucursal, is_superuser=True, is_staff=True,
    )
    client = APIClient()
    client.force_authenticate(user=usuario)

    respuesta = client.post('/api/v1/tipoiva/', {'nombre': '10.5%', 'porcentaje': '10.50'})
    assert respuesta.status_code == 201
