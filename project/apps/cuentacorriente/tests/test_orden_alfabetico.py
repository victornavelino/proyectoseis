import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from cliente.models import Cliente
from cuentacorriente.models import CuentaCorriente
from empleado.models import Sucursal
from persona.models import Persona

Usuario = get_user_model()


@pytest.fixture
def usuario():
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    return Usuario.objects.create_user(username='cajera', password='password', sucursal=sucursal)


@pytest.fixture
def client(usuario):
    api_client = APIClient()
    api_client.force_authenticate(user=usuario)
    return api_client


def _crear_cuenta(nombre, apellido):
    persona = Persona.objects.create(nombre=nombre, apellido=apellido, documento_identidad=f'{nombre}{apellido}')
    cliente = Cliente.objects.create(persona=persona, condicion_iva=Cliente.CONSUMIDOR_FINAL)
    return CuentaCorriente.objects.create(cliente=cliente)


@pytest.mark.django_db
def test_listado_se_ordena_alfabeticamente_por_apellido(client):
    # Se crean fuera de orden alfabético a propósito -con el `ordering = ['-id']` del modelo
    # (más reciente primero) habrían quedado en orden de alta, no alfabético (CuentasCorrientesPage.tsx).
    _crear_cuenta('Mario', 'Coronel')
    _crear_cuenta('Alejandra', 'Cudini')
    _crear_cuenta('Rodrigo', 'Perez')
    _crear_cuenta('Jorge', 'Guzman')

    response = client.get('/api/v1/cuentacorriente/', {'page_size': 10})

    assert response.status_code == 200, response.data
    nombres = [fila['cliente_nombre'] for fila in response.json()['results']]
    assert nombres == ['Coronel, Mario', 'Cudini, Alejandra', 'Guzman, Jorge', 'Perez, Rodrigo']
