from django.conf import settings
from django.core.management.base import BaseCommand
from oauth2_provider.models import get_application_model

Application = get_application_model()


class Command(BaseCommand):
    help = (
        "Crea (o actualiza) la Application de OAuth2 pública para el frontend SPA — "
        "Authorization Code + PKCE, DEC-002 (ver docs/modernizacion/DECISIONES.md). "
        "Idempotente: se puede correr de nuevo (por ejemplo, para cambiar las redirect URIs al "
        "pasar de desarrollo a producción) sin generar un client_id nuevo."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--nombre', default='Frontend SPA',
            help="Nombre de la Application en Django Admin (identifica cuál actualizar). Default: 'Frontend SPA'.",
        )
        parser.add_argument(
            '--redirect-uris', nargs='*', default=None,
            help=(
                "Redirect URIs, separadas por espacio. Si no se pasa, se toma de la variable de "
                "entorno OAUTH2_SPA_REDIRECT_URIS (settings.OAUTH2_SPA_REDIRECT_URIS)."
            ),
        )

    def handle(self, *args, **options):
        redirect_uris = options['redirect_uris'] or settings.OAUTH2_SPA_REDIRECT_URIS
        if not redirect_uris:
            self.stderr.write(self.style.ERROR(
                "No hay redirect URIs configuradas. Pasá --redirect-uris o seteá "
                "OAUTH2_SPA_REDIRECT_URIS en el entorno (.env)."
            ))
            return

        app, created = Application.objects.update_or_create(
            name=options['nombre'],
            defaults={
                'client_type': Application.CLIENT_PUBLIC,
                'authorization_grant_type': Application.GRANT_AUTHORIZATION_CODE,
                'redirect_uris': ' '.join(redirect_uris),
                # False: el usuario ve la pantalla de "¿Autorizar a Frontend SPA?" la primera
                # vez (comportamiento estándar de OAuth2). Ponerlo en True la saltearía.
                'skip_authorization': False,
            },
        )
        accion = 'creada' if created else 'actualizada'
        self.stdout.write(self.style.SUCCESS(f"Application '{app.name}' {accion}."))
        self.stdout.write(f"client_id: {app.client_id}")
        self.stdout.write("client_secret: (ninguno — client_type=public, no lleva secret; el flujo usa PKCE)")
        self.stdout.write(f"redirect_uris: {app.redirect_uris}")
        self.stdout.write(f"authorization_grant_type: {app.authorization_grant_type}")
