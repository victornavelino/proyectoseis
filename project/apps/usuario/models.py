from django.contrib.auth.models import AbstractUser
from django.db import models

from empleado.models import Sucursal, Empleado


class Usuario(AbstractUser):
    class Meta:
        db_table = 'auth_user'
        # No corresponden a ningún modelo real -> son permisos "puros" (sin add_/change_/
        # delete_ asociado) para que el frontend oculte secciones enteras del menú según el rol
        # (ver frontend/src/components/AppLayout.tsx), sin pedir prestado el permiso de
        # escritura de un modelo que no tiene relación real con "puede ver esta sección" (lo que
        # hacía antes: Dashboard reusaba el mismo permiso que Catálogo). Otorgables por grupo
        # desde /admin, igual que cualquier otro permiso Django — ver usuario.permisos
        # .sincronizar_grupo_acceso_completo, que se los asigna automáticamente al grupo
        # "Acceso completo (staff)" en cada deploy.
        permissions = [
            ('ver_seccion_dashboard', 'Puede ver la sección Dashboard del menú'),
            ('ver_seccion_catalogo', 'Puede ver la sección Catálogo del menú'),
            ('ver_seccion_personal', 'Puede ver la sección Personal del menú'),
            ('ver_seccion_promociones', 'Puede ver la sección Promociones del menú'),
            ('ver_seccion_caja', 'Puede ver la sección Caja del menú'),
        ]

    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, null=True, verbose_name='Empleado')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, null=True, verbose_name='Sucursal')

    def __str__(self):
        return f'{self.username}'

    @staticmethod
    def autocomplete_search_fields():
        return 'first_name', 'last_name'
