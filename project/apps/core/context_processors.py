from django.conf import settings


def nombre_negocio(request):
    """Expone el nombre y el logo del negocio a TODOS los templates (login, tickets impresos,
    etc.) sin tener que agregarlos a mano en cada `render()` — una sola fuente de verdad,
    configurable por variable de entorno (PROJECT_NAME_HEADER / PROJECT_NAME_TITLE / LOGO_URL,
    ver settings/base.py), para poder reutilizar este sistema con otro negocio sin tocar
    templates."""
    return {
        'PROJECT_NAME_HEADER': settings.PROJECT_NAME_HEADER,
        'PROJECT_NAME_TITLE': settings.PROJECT_NAME_TITLE,
        'LOGO_URL': settings.LOGO_URL,
    }
