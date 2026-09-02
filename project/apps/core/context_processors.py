from django.conf import settings


def nombre_negocio(request):
    """Expone el nombre del negocio a TODOS los templates (login, tickets impresos, etc.) sin
    tener que agregarlo a mano en cada `render()` — una sola fuente de verdad, configurable por
    variable de entorno (PROJECT_NAME_HEADER / PROJECT_NAME_TITLE, ver settings/base.py), para
    poder reutilizar este sistema con otro negocio sin tocar templates."""
    return {
        'PROJECT_NAME_HEADER': settings.PROJECT_NAME_HEADER,
        'PROJECT_NAME_TITLE': settings.PROJECT_NAME_TITLE,
    }
