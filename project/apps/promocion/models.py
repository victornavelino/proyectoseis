from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

# Create your models here.
from softdelete.models import SoftDeleteObject

from articulo.models import Articulo
from empleado.models import Sucursal


class DiasSemana(models.Model):
    class Meta:
        verbose_name = 'Dia Semana'
        verbose_name_plural = 'Dias de la Semana'
        ordering = ['-id']

    lunes = models.BooleanField(default=False)
    martes = models.BooleanField(default=False)
    miercoles = models.BooleanField(default=False)
    jueves = models.BooleanField(default=False)
    viernes = models.BooleanField(default=False)
    sabado = models.BooleanField(default=False)
    domingo = models.BooleanField(default=False)

    def __str__(self):
        return self.obtener_dias()

    def obtener_dias(self):
        dias = []
        if self.lunes:
            dias.append("Lunes")
        if self.martes:
            dias.append("Martes")
        if self.miercoles:
            dias.append("Miercoles")
        if self.jueves:
            dias.append("Jueves")
        if self.viernes:
            dias.append("Viernes")
        if self.sabado:
            dias.append("Sabado")
        if self.domingo:
            dias.append("Domingo")
        dias_to_string = ', '.join(dias)
        return dias_to_string


class Promocion(models.Model):
    class Meta:
        verbose_name = 'Promocion'
        verbose_name_plural = 'Promociones'
        ordering = ['-id']
        unique_together = ('nombre', 'sucursal',)

    nombre = models.CharField(max_length=100, verbose_name='Nombre', null=False)
    fecha_inicio = models.DateField(verbose_name='Fecha Inicio de Promocion', null=False)
    fecha_fin = models.DateField(verbose_name='Fecha Fin de Promocion', null=False)
    es_por_precio = models.BooleanField(default=False)
    porcentaje_todos = models.DecimalField(max_digits=12, decimal_places=2, null=True, default=0, blank=True)
    dias_semana = models.ForeignKey(DiasSemana, on_delete=models.CASCADE, null=True, verbose_name='Dias de Promocion')
    habilitada = models.BooleanField(default=False)
    prioridad = models.IntegerField(null=False, validators=[MaxValueValidator(10), MinValueValidator(1)], default=10)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, null=True, verbose_name='Sucursal')
    observaciones = models.CharField(max_length=200, verbose_name='Observaciones', blank=True, null=True)

    def __str__(self):
        return f'{self.nombre}'

    def clean(self, *args, **kwargs):
        if self.es_por_precio is False and self.porcentaje_todos is None:
            raise ValidationError("Debe haber un valor en Porcentaje para los articulos en promocion")
        if self.es_por_precio is True and self.porcentaje_todos is not None:
            raise ValidationError("Si elige Promociones por precio, debe dejar vacio el campo Porcentaje a Todos")
        if self.dias_semana is None:
            raise ValidationError("Debe seleccionar dias de la semana")
        promocion=Promocion.objects.filter(prioridad=self.prioridad, sucursal=self.sucursal)
        if promocion and self.pk is None:
            raise ValidationError('Ya existe promocion con esa priodidad para esa sucursal')
        super().clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Promocion, self).save(*args, **kwargs)


class PromocionArticulo(models.Model):
    class Meta:
        verbose_name = 'Promocion Articulo'
        verbose_name_plural = 'Articulos'
        ordering = ['-id']

    valor = models.DecimalField(max_digits=12, decimal_places=2)
    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE, null=False, verbose_name='Articulo Promocion')
    promocion = models.ForeignKey(Promocion, on_delete=models.CASCADE, null=True, verbose_name='Promocion')

    def __str__(self):
        return f'{self.articulo}'


class Descuento(models.Model):
    class Meta:
        verbose_name = 'Descuento'
        verbose_name_plural = 'Descuentos'
        ordering = ['-id']

    nombre = models.CharField(max_length=100, verbose_name='Nombre', null=False)
    valor = models.IntegerField(validators=[MaxValueValidator(100), MinValueValidator(0)], default=0,
                                verbose_name='Valor(%)', null=False)

    def __str__(self):
        return f'{self.nombre}'
