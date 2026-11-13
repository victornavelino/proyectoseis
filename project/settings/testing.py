from .base import *


SECRET_KEY = 'CHANGEME!!!'
DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

MEDIA_ROOT = str(PROJECT_DIR.path('test_media'))

# OAUTH2_PROVIDER_ACCESS_TOKEN_MODEL = 'oauth2_provider.AccessToken'
# OAUTH2_PROVIDER_APPLICATION_MODEL = 'oauth2_provider.Application'
# OAUTH2_PROVIDER_GRANT_MODEL = 'oauth2_provider.Grant'
# OAUTH2_PROVIDER_REFRESH_TOKEN_MODEL = 'oauth2_provider.RefreshToken'

# OAUTH2_PROVIDER se hereda de base.py (`from .base import *`). Antes este archivo lo
# redefinía acá con `'SCOPES': ['read', 'write', 'groups']` (una lista) — incompatible con
# la versión de django-oauth-toolkit instalada, que espera `SCOPES` como dict
# (`oauth2_settings._SCOPES` hace `self.SCOPES.keys()`) y rompe con `AttributeError: 'list'
# object has no attribute 'keys'` en cuanto se ejercita un flujo de autorización real — se
# detectó al probar el flujo OAuth2 PKCE de la etapa 5. Se saca la redefinición para que
# testing use el mismo `OAUTH2_PROVIDER` (dict) que development/production.


