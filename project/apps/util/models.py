from enum import Enum

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Telefono(models.Model):
    class Meta:
        verbose_name = 'Teléfono'
        verbose_name_plural = 'Teléfonos'

    FAX = 'fax'
    TELEFONO = 'telefono'
    CELULAR = 'celular'

    TIPOS = (
        (FAX, 'Fax'),
        (TELEFONO, 'Teléfono'),
        (CELULAR, 'Celular'),
    )

    tipo = models.CharField(max_length=9, choices=TIPOS, verbose_name='Tipo de teléfono', default=TELEFONO)
    numero = models.CharField(max_length=40, verbose_name='Número')
    content_type = models.ForeignKey(
        ContentType,
        # limit_choices_to={'model__in': ('hotel', 'agency', 'transport')     # Add more after.},
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return "(%s) %s" % (self.get_tipo_display(), self.numero)


class TipoPagoVenta():

    EFECTIVO= 'Efectivo'
    TARJETA= 'Tarjeta'
    CCORRIENTE= 'CCorriente'

    TIPOS = (
        (EFECTIVO, 'Efectivo'),
        (TARJETA, 'Tarjeta'),
        (CCORRIENTE, 'CCorriente'),
    )

    tipo_pago = models.CharField(max_length=10, choices=TIPOS, verbose_name='Tipo de Pago', default=EFECTIVO)
    monto = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True)
    monto_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True)

