from django.conf import settings


def nombre_negocio(request):
    """Expone el nombre, el logo y el ancho de ticket del negocio a TODOS los templates (login,
    tickets impresos, etc.) sin tener que agregarlos a mano en cada `render()` — una sola fuente
    de verdad, configurable por variable de entorno (PROJECT_NAME_HEADER / PROJECT_NAME_TITLE /
    LOGO_URL / TICKET_ANCHO_MM, ver settings/base.py), para poder reutilizar este sistema con
    otro negocio (u otra impresora) sin tocar templates."""
    return {
        'PROJECT_NAME_HEADER': settings.PROJECT_NAME_HEADER,
        'PROJECT_NAME_TITLE': settings.PROJECT_NAME_TITLE,
        'LOGO_URL': settings.LOGO_URL,
        'TICKET_ANCHO_MM': settings.TICKET_ANCHO_MM,
    }
