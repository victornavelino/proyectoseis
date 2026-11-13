from django.db import migrations

# Permisos "puros" (sin add_/change_/delete_ de ningún modelo real) para que el frontend oculte
# secciones enteras del menú según el rol (ver usuario.models.Usuario.Meta.permissions y
# frontend/src/components/AppLayout.tsx) — no es un cambio de esquema, sólo registra estos
# permisos en el estado de migraciones (los crea de verdad la señal post_migrate de
# django.contrib.auth, que corre en cualquier `migrate`, con o sin esta migración). El backfill
# al grupo "Acceso completo (staff)" lo hace usuario.permisos.sincronizar_grupo_acceso_completo
# (conectada a post_migrate desde UsuarioConfig.ready(), no acá) — ver esa función para el
# porqué de no duplicar esa lógica en una migración de datos.


class Migration(migrations.Migration):

    dependencies = [
        ('usuario', '0019_grupo_acceso_operativo_ventas_caja'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='usuario',
            options={
                'permissions': [
                    ('ver_seccion_dashboard', 'Puede ver la sección Dashboard del menú'),
                    ('ver_seccion_catalogo', 'Puede ver la sección Catálogo del menú'),
                    ('ver_seccion_personal', 'Puede ver la sección Personal del menú'),
                    ('ver_seccion_promociones', 'Puede ver la sección Promociones del menú'),
                    ('ver_seccion_caja', 'Puede ver la sección Caja del menú'),
                ]
            },
        ),
    ]
