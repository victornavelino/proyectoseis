import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from articulo.models import ListaPrecio
from cliente.models import Cliente
from persona.models import Persona

Usuario = get_user_model()


@pytest.mark.django_db
def test_force_login_no_tira_defaultstrategymissingerror():
    """Regresión: `drf_social_oauth2.backends.DjangoOAuth2` (uno de los AUTHENTICATION_BACKENDS)
    necesita `social_core.registry.REGISTRY.default_strategy`, que se arma importando
    `social_django.utils` -algo que antes sólo pasaba de rebote cuando DRF resolvía
    DEFAULT_AUTHENTICATION_CLASSES (drf_social_oauth2.authentication.SocialAuthentication
    importa social_django), es decir, recién en el primer request a la API.

    Cualquier login o `user.has_perm(...)` llama a `get_backends()`, que instancia CADA backend
    -si el proceso todavía no sirvió ningún request a la API (ej. el primer worker de gunicorn
    que atiende una página del admin antes que la API, después de un deploy), ese import nunca
    pasó y la instanciación de DjangoOAuth2() tira `DefaultStrategyMissingError` -> 500
    intermitente en el admin, según a qué worker le toque el request (ver THIRD_PARTY_APPS en
    settings/base.py: agregar 'social_django' ahí hace que Django la importe al arrancar,
    para todos los workers, antes de servir nada).
    """
    lp = ListaPrecio.objects.create(nombre='COMUN')
    p = Persona.objects.create(documento_identidad='12345678', nombre='Juan', apellido='Perez')
    Cliente.objects.create(persona=p, condicion_iva=Cliente.CONSUMIDOR_FINAL, lista_precio=lp)
    usuario = Usuario.objects.create_superuser(username='admintest', password='test12345', email='a@a.com')
    client = Client()

    client.force_login(usuario)  # pasa por get_backends() de verdad
    response = client.get('/admin/cliente/cliente/')

    assert response.status_code == 200
