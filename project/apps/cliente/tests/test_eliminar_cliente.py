from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from rest_framework.test import APIClient

from cliente.models import Cliente
from cuentacorriente.models import CuentaCorriente
from empleado.models import Empleado, Sucursal
from persona.models import Persona
from venta.models import Venta

Usuario = get_user_model()


@pytest.fixture
def cliente():
    persona = Persona.objects.create(nombre='Juan', apellido='Cliente', documento_identidad='22222222')
    return Cliente.objects.create(persona=persona, condicion_iva=Cliente.CONSUMIDOR_FINAL)


@pytest.fixture
def usuario_staff():
    # Ver comentario equivalente en articulo/tests/test_eliminar_catalogo.py: is_staff ya no
    # alcanza solo, ClienteViewSet.destroy ahora exige el permiso cliente.delete_cliente.
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    usuario = Usuario.objects.create_user(
        username='admin', password='password', sucursal=sucursal, is_staff=True,
    )
    usuario.groups.add(Group.objects.get(name='Acceso completo (staff)'))
    return usuario


@pytest.mark.django_db
def test_se_puede_eliminar_un_cliente_sin_historial(cliente, usuario_staff):
    client = APIClient()
    client.force_authenticate(user=usuario_staff)
    response = client.delete(f'/api/v1/cliente/{cliente.id}/')

    assert response.status_code == 204
    assert not Cliente.objects.filter(id=cliente.id).exists()


@pytest.mark.django_db
def test_no_se_puede_eliminar_un_cliente_con_ventas(cliente, usuario_staff):
    persona_empleado = Persona.objects.create(nombre='Ana', apellido='Vendedora', documento_identidad='11111111')
    empleado = Empleado.objects.create(persona=persona_empleado, cuil='20111111112')
    venta = Venta.objects.create(
        empleado=empleado,
        fecha=timezone.now(),
        monto=Decimal('1000.00'),
        descuento=Decimal('0.00'),
        sucursal=usuario_staff.sucursal,
        cliente=cliente,
        usuario=usuario_staff,
    )

    client = APIClient()
    client.force_authenticate(user=usuario_staff)
    response = client.delete(f'/api/v1/cliente/{cliente.id}/')

    assert response.status_code == 400
    assert Cliente.objects.filter(id=cliente.id).exists()
    assert Venta.objects.filter(numero_ticket=venta.numero_ticket).exists()


@pytest.mark.django_db
def test_no_se_puede_eliminar_un_cliente_con_cuenta_corriente(cliente, usuario_staff):
    CuentaCorriente.objects.create(cliente=cliente)

    client = APIClient()
    client.force_authenticate(user=usuario_staff)
    response = client.delete(f'/api/v1/cliente/{cliente.id}/')

    assert response.status_code == 400
    assert Cliente.objects.filter(id=cliente.id).exists()


@pytest.mark.django_db
def test_no_staff_no_puede_eliminar_clientes(cliente):
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    usuario_no_staff = Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)

    client = APIClient()
    client.force_authenticate(user=usuario_no_staff)
    response = client.delete(f'/api/v1/cliente/{cliente.id}/')

    assert response.status_code == 403
    assert Cliente.objects.filter(id=cliente.id).exists()


@pytest.mark.django_db
def test_cualquier_autenticado_puede_editar_un_cliente(cliente):
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    usuario_no_staff = Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)

    client = APIClient()
    client.force_authenticate(user=usuario_no_staff)
    response = client.patch(f'/api/v1/cliente/{cliente.id}/', {'condicion_iva': Cliente.EXENTO}, format='json')

    assert response.status_code == 200
    cliente.refresh_from_db()
    assert cliente.condicion_iva == Cliente.EXENTO
