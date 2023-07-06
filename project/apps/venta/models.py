from django.db import models


# Create your models here.
from articulo.models import Articulo
from cliente.models import Cliente
from empleado.models import Sucursal
from usuario.models import Usuario


class CierreVentas(models.Model):
    class Meta:
        verbose_name = 'CierreVenta'
        verbose_name_plural = 'Cierres de Ventas'
        ordering = ['-numero_cierre']

    numero_cierre = models.AutoField(primary_key=True, verbose_name='Numero de Cierre')
    sucursal = models.ForeignKey(Sucursal, null=False, on_delete=models.CASCADE, verbose_name="Sucursal")
    fecha = models.DateTimeField(auto_now_add=True ,verbose_name='Fecha', null=False)
    ticket_desde = models.IntegerField(null=False,verbose_name='Ticket Desde')
    ticket_hasta = models.IntegerField(null=False, verbose_name='Ticket Hasta')
    ticket_cantidad = models.IntegerField(null=False, verbose_name='Ticket Cantidad')
    importe = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Importe Cierre Ticket')

    def __str__(self):
        return f'{self.numero_cierre}'

class Venta(models.Model):
    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-numero_ticket']

    numero_ticket = models.AutoField(primary_key=True, verbose_name='Numero de Ticket')
    fecha = models.DateTimeField(verbose_name='Fecha de venta', null=False)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=12, decimal_places=2)
    anulado = models.BooleanField(default=False)
    sucursal = models.ForeignKey(Sucursal, null=False,on_delete=models.PROTECT, verbose_name="Sucursal")
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name='Cliente', null=False)
    es_persona = models.BooleanField(default=True)
    usuario = models.ForeignKey(Usuario, null=False, on_delete=models.PROTECT, verbose_name='Usuario')
    cierreventa = models.ForeignKey(CierreVentas, on_delete=models.CASCADE, null=True, verbose_name='Cierre de Venta')
    cobrada = models.BooleanField(default=False)
    prueba = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.numero_ticket}'

class VentaArticulo(models.Model):
    class Meta:
        verbose_name = 'VentaArticulo'
        verbose_name_plural = 'Ventas Articulos'
        ordering = ['-id']

    total_articulo = models.DecimalField(max_digits=12, decimal_places=2)
    cantidad_peso = models.DecimalField(max_digits=12, decimal_places=2)
    precio_promocion = models.DecimalField(max_digits=12, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    nombre_articulo = models.CharField(max_length=30, verbose_name='Nombre de Articulo', null=False)
    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE, verbose_name='Articulo', null=False)
    codigo_articulo = models.CharField(max_length=10, verbose_name='Codigo de Articulo', null=False)
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, null=True, verbose_name='Venta')

    def __str__(self):
        return f'{self.nombre_articulo}'



