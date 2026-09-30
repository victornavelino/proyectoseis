import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from empleado.models import Sucursal
from usuario.permisos import MODELOS_ACCESO_COMPLETO, NOMBRE_GRUPO_ACCESO_COMPLETO

Usuario = get_user_model()


@pytest.mark.django_db
def test_grupo_acceso_completo_tiene_los_permisos_esperados():
    # El grupo lo crea la señal post_migrate (usuario.apps.UsuarioConfig.ready), no la migración
    # de datos -el test suite corre con --nomigrations (pytest.ini)-, así que para cuando un
    # test arranca ya debería existir con el set completo de permisos.
    grupo = Group.objects.get(name=NOMBRE_GRUPO_ACCESO_COMPLETO)
    codenames = {f'{p.content_type.app_label}.{p.codename}' for p in grupo.permissions.all()}
    esperados = {
        f'{app_label}.{accion}_{model_name}'
        for app_label, model_name in MODELOS_ACCESO_COMPLETO
        for accion in ('add', 'change', 'delete')
    }
    assert esperados <= codenames


@pytest.mark.django_db
def test_perfil_expone_los_permisos_del_usuario():
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    usuario = Usuario.objects.create_user(username='encargado', password='password', sucursal=sucursal)
    usuario.groups.add(Group.objects.get(name=NOMBRE_GRUPO_ACCESO_COMPLETO))

    client = APIClient()
    client.force_authenticate(user=usuario)
    respuesta = client.get('/api/v1/usuario/me/')

    assert respuesta.status_code == 200
    assert 'articulo.delete_articulo' in respuesta.data['permisos']
    assert 'cliente.delete_cliente' in respuesta.data['permisos']
