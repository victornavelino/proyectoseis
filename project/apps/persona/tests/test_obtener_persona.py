import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from persona.models import Persona

Usuario = get_user_model()

ENDPOINT = '/api/v1/persona/obtener_persona/'


@pytest.fixture
def usuario(db):
    return Usuario.objects.create_user(username='vendedor', password='password')


@pytest.mark.django_db
def test_devuelve_el_id_de_una_persona_existente(usuario):
    # Bug real encontrado probando en el navegador el alta combinada de Persona+Empleado+Usuario
    # (UsuarioSucursalFormModal): DocumentoSerializer heredaba el UniqueValidator automático de
    # ModelSerializer para `documento_identidad` (unique=True en el modelo) y rechazaba con 400
    # justo el caso que este endpoint existe para resolver — buscar una persona que YA existe.
    persona = Persona.objects.create(nombre='Juana', apellido='Pérez', documento_identidad='40555111')
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = client.post(ENDPOINT, {'documento_identidad': '40555111'}, format='json')

    assert response.status_code == 200
    assert response.data['persona_id'] == persona.id


@pytest.mark.django_db
def test_devuelve_null_si_no_existe(usuario):
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = client.post(ENDPOINT, {'documento_identidad': '99999999'}, format='json')

    assert response.status_code == 200
    assert response.data['persona_id'] is None
