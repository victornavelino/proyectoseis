from django.apps import apps as apps_globales
from django.conf import settings
from django.contrib.auth.management import create_permissions
from django.db import migrations

# Antes de este cambio, cargar una venta y abrir/cerrar caja/cobrar ventas no pedían ningún
# permiso puntual (sólo estar autenticado) -> cualquier cuenta ya existente podía hacer las
# cuatro cosas. Al exigir ahora un permiso Django por acción (ver venta.api.VentaViewSet.
# get_permissions y caja.api.CajaViewSet.get_permissions), hay que conservarle ese mismo acceso
# a TODAS las cuentas que ya existían -no sólo las is_staff, a diferencia del grupo "Acceso
# completo (staff)" de la migración 0018- porque hoy cualquier cajero/vendedor sin is_staff ya
# hace estas cuatro operaciones día a día.
PERMISOS_OPERATIVO = (
    ('venta', 'venta', 'add_venta'),
    ('caja', 'caja', 'add_caja'),
    ('caja', 'caja', 'change_caja'),
    ('caja', 'cobroventa', 'add_cobroventa'),
)

NOMBRE_GRUPO = 'Acceso operativo (ventas y caja)'


def crear_grupo_y_migrar_usuarios(apps, schema_editor):
    # Mismo workaround que en 0018_grupo_acceso_completo_staff: los permisos todavía no existen
    # en este punto (se crean en post_migrate, que corre recién al final de todo el `migrate`).
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
    permisos = [
        Permission.objects.get(
            content_type=ContentType.objects.get(app_label=app_label, model=model_name), codename=codename,
        )
        for app_label, model_name, codename in PERMISOS_OPERATIVO
    ]
    grupo.permissions.set(permisos)

    # TODAS las cuentas existentes, is_staff o no -ver comentario arriba-.
    for usuario in Usuario.objects.all():
        usuario.groups.add(grupo)


def eliminar_grupo(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name=NOMBRE_GRUPO).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('usuario', '0018_grupo_acceso_completo_staff'),
        ('venta', '0032_alter_ventaarticulo_cantidad_peso'),
        ('caja', '0039_caja_arqueo'),
    ]

    operations = [
        migrations.RunPython(crear_grupo_y_migrar_usuarios, eliminar_grupo),
    ]
