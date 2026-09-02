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


class EsEncargadoDeSucursal(BasePermission):
    """Gestión de usuarios operativos (no-staff) de una sucursal, para que un encargado no
    necesite acceso al /admin de Django (que además le daría manejo de TODOS los modelos del
    sistema, no sólo usuarios).

    Sólo staff puede entrar. Un encargado sin sucursal asignada no puede crear usuarios (¿de
    qué sucursal serían?). Ver `UsuarioSucursalViewSet.get_queryset` para el filtro por
    sucursal en list/retrieve — acá sólo se valida create y el resto de las acciones de
    detalle; superuser (equivalente a acceso total por /admin) queda exento del filtro.
    """

    message = 'No tenés permiso para gestionar usuarios de esta sucursal.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.is_staff:
            return False
        if request.method == 'POST' and not user.is_superuser and user.sucursal_id is None:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser:
            return True
        return obj.sucursal_id == user.sucursal_id
