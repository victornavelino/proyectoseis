from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsStaffOrReadOnly(BasePermission):
    """Cualquier usuario autenticado puede leer (list/retrieve); sólo el
    staff (mismo criterio que el acceso a Django Admin, `is_staff`) puede
    crear/editar/borrar.

    Pensado para catálogos sensibles (artículos, precios, categorías) donde
    el mostrador necesita consultar para vender pero no debería poder
    modificar precios/artículos vía API — ver especificaciones.md §15
    (nunca confiar en el frontend para datos críticos, y acotar quién puede
    tocar precios/stock).
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user.is_staff)
