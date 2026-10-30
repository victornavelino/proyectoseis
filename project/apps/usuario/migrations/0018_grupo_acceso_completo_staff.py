from django.apps import apps as apps_globales
from django.conf import settings
from django.contrib.auth.management import create_permissions
from django.db import migrations

# Modelos que hasta ahora estaban protegidos por util.permissions.IsStaffOrReadOnly (cualquier
# autenticado lee, sólo is_staff escribe) y pasan a estar protegidos por TienePermisoDeModelo
# (exige el permiso Django add_/change_/delete_<modelo> del modelo, otorgable por grupo).
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

NOMBRE_GRUPO = 'Acceso completo (staff)'


def crear_grupo_y_migrar_staff(apps, schema_editor):
    # Los permisos add_/change_/delete_<modelo> recién se crean en la señal post_migrate, que
    # todavía no corrió cuando esta migración se ejecuta (post_migrate se dispara al final de
    # TODO el comando `migrate`, después de aplicar todas las migraciones) -> hay que generarlos
    # ahora mismo para poder asignarlos. Mismo workaround documentado para "crear permisos desde
    # una data migration".
    for app_config in apps_globales.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, verbosity=0)
        app_config.models_module = None

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    app_label_usuario, model_name_usuario = settings.AUTH_USER_MODEL.split('.')
    Usuario = apps.get_model(app_label_usuario, model_name_usuario)

    grupo, _ = Group.objects.get_or_create(name=NOMBRE_GRUPO)

    permisos = []
    for app_label, model_name in MODELOS_ACCESO_COMPLETO:
        content_type = ContentType.objects.get(app_label=app_label, model=model_name)
        for accion in ('add', 'change', 'delete'):
            permisos.append(
                Permission.objects.get(content_type=content_type, codename=f'{accion}_{model_name}')
            )
    grupo.permissions.set(permisos)

    # Las cuentas que ya eran is_staff conservan exactamente el mismo acceso que tenían con
    # IsStaffOrReadOnly (podían crear/editar/borrar en todos estos modelos) — sin este paso,
    # pasarían a no poder hacer nada en esas pantallas hasta que alguien les asigne el grupo a
    # mano desde /admin.
    for usuario in Usuario.objects.filter(is_staff=True):
        usuario.groups.add(grupo)


def eliminar_grupo(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name=NOMBRE_GRUPO).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('usuario', '0017_alter_usuario_id'),
        ('articulo', '0028_nombre_codigo_unicos_solo_entre_activos'),
        ('empleado', '0016_merge_0015_auto_20220521_2126_0015_auto_20220526_1718'),
        ('promocion', '0004_alter_promocionarticulo_promocion'),
        ('caja', '0039_caja_arqueo'),
        ('cuentacorriente', '0008_cliente_unico'),
        ('cliente', '0016_remove_cliente_fidelizado'),
    ]

    operations = [
        migrations.RunPython(crear_grupo_y_migrar_staff, eliminar_grupo),
    ]
