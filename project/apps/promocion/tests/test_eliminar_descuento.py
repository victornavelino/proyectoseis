import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from empleado.models import Sucursal
from promocion.models import Descuento

Usuario = get_user_model()


@pytest.fixture
def descuento():
    return Descuento.objects.create(nombre='CUMPLEAÑOS', valor=10)


@pytest.fixture
def usuario_staff():
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    usuario = Usuario.objects.create_user(username='admin', password='password', sucursal=sucursal, is_staff=True)
    usuario.groups.add(Group.objects.get(name='Acceso completo (staff)'))
    return usuario


@pytest.mark.django_db
def test_se_puede_eliminar_un_descuento(descuento, usuario_staff):
    client = APIClient()
    client.force_authenticate(user=usuario_staff)

    response = client.delete(f'/api/v1/descuento/{descuento.id}/')

    assert response.status_code == 204
    assert not Descuento.objects.filter(id=descuento.id).exists()


@pytest.mark.django_db
def test_sin_permiso_no_puede_eliminar_un_descuento(descuento):
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    usuario_sin_permiso = Usuario.objects.create_user(username='vendedor', password='password', sucursal=sucursal)
    client = APIClient()
    client.force_authenticate(user=usuario_sin_permiso)

    response = client.delete(f'/api/v1/descuento/{descuento.id}/')

    assert response.status_code == 403
    assert Descuento.objects.filter(id=descuento.id).exists()
