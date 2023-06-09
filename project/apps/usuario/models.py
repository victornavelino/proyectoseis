from django.contrib.auth.models import AbstractUser
from django.db import models

from empleado.models import Sucursal, Empleado


class Usuario(AbstractUser):
    class Meta:
        db_table = 'auth_user'

    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, null=True, verbose_name='Empleado')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, null=True, verbose_name='Sucursal')

    def __str__(self):
        return f'{self.username}'

    @staticmethod
    def autocomplete_search_fields():
        return 'first_name', 'last_name'
