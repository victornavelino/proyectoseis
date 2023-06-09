"""
Django settings for settings settings.

Generated by 'django-admin startproject' using Django 3.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""
import sys
import environ

CORS_ORIGIN_ALLOW_ALL = True

ROOT_DIR = environ.Path(__file__) - 3
PROJECT_DIR = ROOT_DIR.path('project')
APPS_DIR = PROJECT_DIR.path('apps')

sys.path.insert(0, str(APPS_DIR))

# Load operating system environment variables and then prepare to use them
env = environ.Env()
#  patch for https://github.com/joke2k/django-environ/issues/119
env_file = str(ROOT_DIR.path('.env'))
env.read_env(env_file)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('DJANGO_SECRET_KEY', default='CHANGEME!!!')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DJANGO_DEBUG', True)

# PROJECT
PROJECT_NAME_HEADER = env('PROJECT_NAME_HEADER', default='SISTEMA DE GESTION CARNICERIA VIRGEN DEL VALLE')
PROJECT_NAME_TITLE = env('PROJECT_NAME_TITLE', default='CARNICERIA VIRGEN DEL VALLE')

ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default='*')  # noqa
WKHTMLTOPDF_CMD = env.str('WKHTMLTOPDF_CMD', default='wkhtmltopdf')
# Application definition

DJANGO_APPS = [
    'jet',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework_social_oauth2',
    'mptt',
    'oauth2_provider',
    'rest_framework',
    'corsheaders',
    'django_filters',
    'dal',
    'dal_queryset_sequence',
    'dal_select2',
    'import_export',
    'softdelete',
]

PROJECT_APPS = [
    'usuario',
    'core',
    'persona',
    'util',
    'empleado',
    'articulo',
    'cliente',
    'promocion',
    'venta',
    'caja',
    'inventario',
    'cuentacorriente'
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + PROJECT_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

X_FRAME_OPTIONS = 'SAMEORIGIN'

JET_SIDE_MENU_COMPACT = True

ROOT_URLCONF = 'project.urls'

AUTH_USER_MODEL = 'usuario.Usuario'

DATABASES = {'default': env.db('DATABASE_URL')}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [str(PROJECT_DIR.path('templates'))],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/
LOCALE_PATHS = [str(PROJECT_DIR.path('translations'))]

LANGUAGE_CODE = env.str('DJANGO_LANGUAGE_CODE', default='es')

TIME_ZONE = env.str('DJANGO_TIME_ZONE', default='America/Argentina/Catamarca')

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = env('DJANGO_STATIC_URL', default='/static/')

STATIC_ROOT = env('DJANGO_STATIC_ROOT', default='./static/')

STATICFILES_DIRS = [str(PROJECT_DIR.path('assets')), ]

AUTHENTICATION_BACKENDS = (
    'rest_framework_social_oauth2.backends.DjangoOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)
JET_DEFAULT_THEME = env.str('DJANGO_JET_DEFAULT_THEME', default='default')

REST_FRAMEWORK = {
    'PAGE_SIZE': 50,
    'EXCEPTION_HANDLER': 'rest_framework_json_api.exceptions.exception_handler',
    'DEFAULT_PAGINATION_CLASS': 'util.paginations.LargePagination',
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework_json_api.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser'
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'rest_framework_social_oauth2.authentication.SocialAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': ('rest_framework_json_api.renderers.JSONRenderer',),
    'DEFAULT_METADATA_CLASS': 'rest_framework_json_api.metadata.JSONAPIMetadata',
    'NON_FIELD_ERRORS_KEY': 'error_messages'
}

ACTIVAR_HERRAMIENTAS_DEBUGGING = env.bool('ACTIVAR_HERRAMIENTAS_DEBUGGING', default=False)
if ACTIVAR_HERRAMIENTAS_DEBUGGING:
    INTERNAL_IPS = ['127.0.0.1']
    INSTALLED_APPS += ('debug_toolbar', 'django_extensions')
    MIDDLEWARE += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] += ('rest_framework.renderers.BrowsableAPIRenderer',)
    REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] += ('rest_framework.authentication.SessionAuthentication',)

