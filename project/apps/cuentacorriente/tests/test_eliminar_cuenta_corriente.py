import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from cliente.models import Cliente
from cuentacorriente.constants import DEBITO
from cuentacorriente.models import CuentaCorriente, MovimientoCuentaCorriente
from empleado.models import Sucursal
from persona.models import Persona

Usuario = get_user_model()


@pytest.fixture
def cliente():
    persona = Persona.objects.create(nombre='Juan', apellido='Cliente', documento_identidad='22222222')
    return Cliente.objects.create(persona=persona, condicion_iva=Cliente.CONSUMIDOR_FINAL)


@pytest.fixture
def usuario_staff():
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    return Usuario.objects.create_user(
        username='admin', password='password', sucursal=sucursal, is_staff=True,
    )


@pytest.mark.django_db
def test_se_puede_eliminar_una_cuenta_sin_movimientos(cliente, usuario_staff):
    cuenta = CuentaCorriente.objects.create(cliente=cliente)

    client = APIClient()
    client.force_authenticate(user=usuario_staff)
    response = client.delete(f'/api/v1/cuentacorriente/{cuenta.id}/')

    assert response.status_code == 204
    assert not CuentaCorriente.objects.filter(id=cuenta.id).exists()


@pytest.mark.django_db
def test_no_se_puede_eliminar_una_cuenta_con_movimientos(cliente, usuario_staff):
    cuenta = CuentaCorriente.objects.create(cliente=cliente)
    MovimientoCuentaCorriente.objects.create(cuenta=cuenta, importe=100, tipo=DEBITO, usuario=usuario_staff)

    client = APIClient()
    client.force_authenticate(user=usuario_staff)
    response = client.delete(f'/api/v1/cuentacorriente/{cuenta.id}/')

    assert response.status_code == 400
    assert CuentaCorriente.objects.filter(id=cuenta.id).exists()


@pytest.mark.django_db
def test_no_staff_no_puede_eliminar_cuentas(cliente):
    cuenta = CuentaCorriente.objects.create(cliente=cliente)
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    usuario_no_staff = Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)

    client = APIClient()
    client.force_authenticate(user=usuario_no_staff)
    response = client.delete(f'/api/v1/cuentacorriente/{cuenta.id}/')

    assert response.status_code == 403
    assert CuentaCorriente.objects.filter(id=cuenta.id).exists()
