import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient

from cliente.models import Cliente
from empleado.models import Empleado, Sucursal
from persona.models import Persona

Usuario = get_user_model()


@pytest.fixture
def contexto():
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    usuario = Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)
    persona_empleado = Persona.objects.create(nombre='Ana', apellido='Vendedora', documento_identidad='11111111')
    empleado = Empleado.objects.create(persona=persona_empleado, cuil='20111111112')
    persona_cliente = Persona.objects.create(nombre='Juan', apellido='Perez', documento_identidad='30111222')
    cliente = Cliente.objects.create(persona=persona_cliente, condicion_iva=Cliente.CONSUMIDOR_FINAL)
    return usuario, empleado, cliente


@pytest.mark.django_db
def test_sin_permiso_add_venta_no_puede_cargar_una_venta(contexto):
    # Reproduce el bug reportado: un usuario sólo con permisos de caja (abrir/cerrar/cobrar) no
    # debería poder además cargar ventas si no se le dio el permiso aparte.
    usuario, empleado, cliente = contexto
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = client.post('/api/v1/venta/crear/', {
        'empleado': empleado.id, 'cliente': cliente.id, 'articulos': [],
    }, format='json')

    assert response.status_code == 403


@pytest.mark.django_db
def test_con_permiso_add_venta_pasa_el_chequeo_de_permiso(contexto):
    usuario, empleado, cliente = contexto
    content_type = ContentType.objects.get(app_label='venta', model='venta')
    usuario.user_permissions.add(Permission.objects.get(content_type=content_type, codename='add_venta'))
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = client.post('/api/v1/venta/crear/', {
        'empleado': empleado.id, 'cliente': cliente.id, 'articulos': [],
    }, format='json')

    # Sin artículos la validación de negocio rechaza (400) -> lo que importa acá es que ya no
    # sea 403: el permiso se concedió correctamente, lo que falla después es otra cosa.
    assert response.status_code == 400
