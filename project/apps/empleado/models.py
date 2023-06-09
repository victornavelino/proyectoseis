from django.db import models


# Create your models here.
class Sucursal(models.Model):
    class Meta:
        verbose_name = 'Sucursal'
        verbose_name_plural = 'Sucursales'
        ordering = ['-id']

    nombre = models.CharField(max_length=100, verbose_name='Nombre', unique=True)
    domicilio = models.CharField(max_length=100, verbose_name='Domicilio', unique=True)

    def __str__(self):
        return f'{self.nombre}'


class Empleado(models.Model):
    class Meta:
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
        ordering = ['-id']
    persona = models.ForeignKey('persona.Persona', verbose_name='Persona', on_delete=models.CASCADE)
    cuil = models.CharField(max_length=12, verbose_name='Cuil', unique=True)
    fecha_baja = models.DateField(blank=True, null=True)

    def __str__(self):
        return f'{self.persona.obtener_nombre_completo()}'