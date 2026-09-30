from django.apps import AppConfig
from django.db.models.signals import post_migrate


class UsuarioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuario'

    def ready(self):
        post_migrate.connect(_sincronizar_grupo_acceso_completo, dispatch_uid='usuario.sincronizar_grupo_acceso_completo')


def _sincronizar_grupo_acceso_completo(**kwargs):
    from usuario.permisos import sincronizar_grupo_acceso_completo

    sincronizar_grupo_acceso_completo()
