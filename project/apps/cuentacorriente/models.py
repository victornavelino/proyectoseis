from django.contrib import messages
from django.contrib.admin import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.http import request

from caja.models import Caja
from cuentacorriente.constants import TIPOS_MOVIMIENTO_CTA_CTE, CREDITO


class CuentaCorriente(models.Model):
    class Meta:
        verbose_name = 'Cuenta Corriente'
        verbose_name_plural = 'Cuentas Corrientes'
        ordering = ['-id']

    cliente = models.ForeignKey('cliente.Cliente', on_delete=models.PROTECT, verbose_name='Cliente')
    tope = models.DecimalField(max_digits=12, decimal_places=2, default=100000,
                               verbose_name='Tope máximo de cuenta')
    fecha = models.DateTimeField(auto_now=True, verbose_name='Fecha de apertura')
    observaciones = models.CharField(max_length=100, verbose_name='Observaciones', null=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.cliente}'


# Create your models here.
class MovimientoCuentaCorriente(models.Model):
    class Meta:
        verbose_name = 'Movimiento cuenta corriente'
        verbose_name_plural = 'Movimientos cuentas corrientes'
        ordering = ['-id']

    cuenta = models.ForeignKey('CuentaCorriente', on_delete=models.PROTECT, verbose_name='Cuenta corriente')
    importe = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                  verbose_name='Importe')
    fecha = models.DateTimeField(auto_now=True, verbose_name='Fecha de movimiento')
    tipo = models.CharField(max_length=1,choices=TIPOS_MOVIMIENTO_CTA_CTE, verbose_name='Tipo de movimiento')
    usuario = models.ForeignKey('usuario.Usuario', on_delete=models.PROTECT, verbose_name='Usuario')
    venta = models.ForeignKey('venta.Venta', on_delete=models.PROTECT, null=True, verbose_name='Venta relacionada')
    observaciones = models.TextField(max_length=30, verbose_name='Observaciones', null=True)


    def __str__(self):
        return f'{self.cuenta.cliente}'
