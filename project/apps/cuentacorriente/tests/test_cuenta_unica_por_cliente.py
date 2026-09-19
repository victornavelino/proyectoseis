from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from cliente.models import Cliente
from cuentacorriente.models import CuentaCorriente
from empleado.models import Sucursal
from persona.models import Persona

Usuario = get_user_model()

MENSAJE_ESPERADO = 'El cliente ya tiene una cuenta corriente!'


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
def test_no_se_puede_crear_una_segunda_cuenta_a_nivel_de_modelo(cliente):
    CuentaCorriente.objects.create(cliente=cliente)

    segunda = CuentaCorriente(cliente=cliente)
    with pytest.raises(ValidationError) as excinfo:
        segunda.full_clean()

    assert MENSAJE_ESPERADO in excinfo.value.message_dict.get('cliente', [])


@pytest.mark.django_db
def test_no_se_puede_crear_una_segunda_cuenta_por_api(cliente, usuario_staff):
    CuentaCorriente.objects.create(cliente=cliente)

    client = APIClient()
    client.force_authenticate(user=usuario_staff)
    response = client.post(
        '/api/v1/cuentacorriente/',
        {'cliente': cliente.id, 'tope': '100000.00', 'activa': True},
        format='json',
    )

    assert response.status_code == 400
    assert MENSAJE_ESPERADO in response.data['cliente']


@pytest.mark.django_db
def test_se_puede_editar_la_cuenta_existente_sin_disparar_el_error(cliente, usuario_staff):
    """El UniqueValidator/full_clean no debe confundir una edición (mismo cliente, misma
    cuenta) con un alta duplicada."""
    cuenta = CuentaCorriente.objects.create(cliente=cliente, tope=Decimal('100000.00'))

    client = APIClient()
    client.force_authenticate(user=usuario_staff)
    response = client.patch(
        f'/api/v1/cuentacorriente/{cuenta.id}/',
        {'tope': '200000.00'},
        format='json',
    )

    assert response.status_code == 200
    cuenta.refresh_from_db()
    assert cuenta.tope == Decimal('200000.00')
