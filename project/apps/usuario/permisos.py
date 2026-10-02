"""Grupo "Acceso completo (staff)": junta los permisos add_/change_/delete_ de todos los
modelos protegidos por util.permissions.TienePermisoDeModelo, para que las cuentas is_staff que
ya existían antes de ese esquema (y cualquier otra a la que se le quiera dar el mismo nivel de
acceso) no pierdan capacidad de escritura sin que alguien se lo asigne a mano desde /admin.

`sincronizar_grupo_acceso_completo` se llama desde `UsuarioConfig.ready()` en cada post_migrate
(ver abajo) -no sólo desde la migración de datos- porque el test suite corre con
`--nomigrations` (pytest.ini): ahí las migraciones no se aplican y el grupo nunca se crearía si
sólo viviera en `usuario.migrations.0018_grupo_acceso_completo_staff`. La migración además hace
el backfill ÚNICO de las cuentas is_staff existentes al momento del deploy -eso no puede vivir
acá, porque esta función corre en cada `migrate` y agregar cuentas nuevas automáticamente
rompería el propósito de los permisos granulares (una cuenta is_staff nueva ya no debería
heredar acceso completo sin que alguien lo decida)-.

Esta lista está deliberadamente duplicada en la migración en vez de importada desde acá: el
contenido de una migración no debería depender de código de la app que puede cambiar más
adelante (si un modelo se renombra o se borra, la migración vieja tiene que seguir siendo capaz
de reproducirse desde cero tal como estaba escrita en su momento).
"""

NOMBRE_GRUPO_ACCESO_COMPLETO = 'Acceso completo (staff)'

MODELOS_ACCESO_COMPLETO = (
    ('articulo', 'tipoiva'),
    ('articulo', 'unidadmedida'),
    ('articulo', 'categoria'),
    ('articulo', 'listaprecio'),
    ('articulo', 'articulo'),
    ('articulo', 'precio'),
    ('empleado', 'sucursal'),
    ('empleado', 'empleado'),
    ('promocion', 'diassemana'),
    ('promocion', 'promocion'),
    ('promocion', 'promocionarticulo'),
    ('promocion', 'descuento'),
    ('caja', 'tarjetadecredito'),
    ('caja', 'plantarjetadecredito'),
    ('caja', 'tipoingreso'),
    ('caja', 'tipogasto'),
    ('cuentacorriente', 'cuentacorriente'),
    ('cliente', 'cliente'),
)


def sincronizar_grupo_acceso_completo():
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType

    grupo, _ = Group.objects.get_or_create(name=NOMBRE_GRUPO_ACCESO_COMPLETO)

    permisos = []
    for app_label, model_name in MODELOS_ACCESO_COMPLETO:
        try:
            content_type = ContentType.objects.get(app_label=app_label, model=model_name)
        except ContentType.DoesNotExist:
            # post_migrate se emite una vez POR APP, en el orden de INSTALLED_APPS -> en las
            # primeras emisiones (ej. la de 'usuario', que está primero) todavía no se crearon
            # los ContentType/Permission de apps que aparecen después ('articulo', 'caja', etc).
            # Se salta acá y se completa en una emisión posterior dentro del mismo `migrate`.
            continue
        permisos += list(
            Permission.objects.filter(
                content_type=content_type,
                codename__in=[f'{accion}_{model_name}' for accion in ('add', 'change', 'delete')],
            )
        )

    if permisos:
        grupo.permissions.add(*permisos)


NOMBRE_GRUPO_OPERATIVO = 'Acceso operativo (ventas y caja)'

# (app_label, nombre de modelo, codename) — acá sí hace falta el nombre de modelo aparte del
# codename porque `cobroventa` (modelo `CobroVenta`) no se puede derivar recortando el prefijo
# `add_`/`change_` del codename de forma genérica como en MODELOS_ACCESO_COMPLETO.
PERMISOS_OPERATIVO = (
    ('venta', 'venta', 'add_venta'),
    ('caja', 'caja', 'add_caja'),
    ('caja', 'caja', 'change_caja'),
    ('caja', 'cobroventa', 'add_cobroventa'),
)


def sincronizar_grupo_operativo():
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType

    grupo, _ = Group.objects.get_or_create(name=NOMBRE_GRUPO_OPERATIVO)

    permisos = []
    for app_label, model_name, codename in PERMISOS_OPERATIVO:
        try:
            content_type = ContentType.objects.get(app_label=app_label, model=model_name)
            permisos.append(Permission.objects.get(content_type=content_type, codename=codename))
        except (ContentType.DoesNotExist, Permission.DoesNotExist):
            continue

    if permisos:
        grupo.permissions.add(*permisos)
