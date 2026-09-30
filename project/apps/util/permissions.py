from rest_framework.permissions import BasePermission, DjangoModelPermissions


class TienePermisoDeModelo(DjangoModelPermissions):
    """Cualquier autenticado puede leer (list/retrieve); para crear/editar/eliminar exige el
    permiso Django del modelo (`<app>.add_<modelo>`, `<app>.change_<modelo>`,
    `<app>.delete_<modelo>`) en vez de exigir `is_staff` a secas.

    Reemplaza al viejo `IsStaffOrReadOnly` (que sólo distinguía "staff" vs "no staff"). Estos
    permisos se otorgan por grupo desde /admin -> Autenticación y autorización -> Grupos, así se
    pueden armar roles (ej. "Cajero", "Encargado de stock") que ven sólo lo que necesitan, sin
    tener que ser staff completo ni tocar cuenta por cuenta. Superusuario tiene todos los
    permisos automáticamente (comportamiento estándar de Django). Las cuentas `is_staff` que ya
    existían antes de este esquema quedaron en el grupo "Acceso completo (staff)" -ver
    usuario.migrations.0018_grupo_acceso_completo_staff- así conservan exactamente el mismo
    acceso que tenían con `IsStaffOrReadOnly`.
    """


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
