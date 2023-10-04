from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models

# Create your models here.
from caja.constants import TIPOS_MOVIMIENTO_CAJA
from cliente.models import Cliente
from empleado.models import Sucursal, Empleado
from usuario.models import Usuario
from venta.models import Venta
from model_utils.managers import InheritanceManager


class Caja(models.Model):
    class Meta:
        verbose_name = 'Caja'
        verbose_name_plural = 'Cajas'
        ordering = ['-id']

    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(blank=True, null=True)
    caja_inicial = models.DecimalField(max_digits=12, decimal_places=2, null=True, default=0, blank=True)
    caja_final = models.DecimalField(max_digits=12, decimal_places=2, null=True, default=0, blank=True)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, null=True, verbose_name='Sucursal')
    usuario = models.ForeignKey(Usuario, null=False, on_delete=models.PROTECT, verbose_name='Usuario')

    def __str__(self):
        return f'{self.sucursal}'


class MovimientoCaja(models.Model):
    class Meta:
        verbose_name = 'Movimiento de Caja'
        verbose_name_plural = 'Movimientos de Caja'
        ordering = ['-id']
    objects = InheritanceManager()

    fecha = models.DateTimeField(auto_now=True)
    usuario = models.ForeignKey(Usuario, null=False, on_delete=models.PROTECT, verbose_name='Usuario')
    importe = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True)
    cerrado = models.BooleanField(default=False)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, null=True, verbose_name='Sucursal')
    caja = models.ForeignKey(Caja, on_delete=models.PROTECT, null=True, verbose_name='Caja')
    tipo = models.CharField(max_length=7, choices=TIPOS_MOVIMIENTO_CAJA, verbose_name='Tipo')


    def clean(self):
        if self.importe <= 0.0:
            raise ValidationError("El importe del movimiento tiene que ser mayor que Cero")
        try:
            first = Caja.objects.latest('id')
            self.caja = first
            if self.caja.fecha_fin:
                raise ValidationError("La Caja se encuentra Cerrada")
        except Exception as e:
            raise ValidationError("La Caja se encuentra Cerrada")

    def save(self, *args, **kwargs):
        self.full_clean()
        super(MovimientoCaja, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.sucursal}'

    def clase(self):
        try:
            if self.cobroventa:
                return 'Cobro de Venta'
        except:
            pass
        try:
            if self.sueldo:
                return 'Sueldo'
        except:
            pass
        try:
            if self.adelanto:
                return 'Adelanto'
        except:
            pass
        try:
            if self.ingreso:
                return 'Ingreso'
        except:
            pass
        try:
            if self.retiroefectivo:
                return 'Retiro de Efectivo'
        except:
            pass
        try:
            if self.gasto:
                return 'Gasto'
        except:
            pass
    clase.short_description = 'Movimiento'



class TipoIngreso(models.Model):
    class Meta:
        verbose_name = 'Tipo de Ingreso'
        verbose_name_plural = 'Tipos de Ingreso'
        ordering = ['-id']

    descripcion = models.CharField(max_length=30, verbose_name='Descripcion', unique=True)

    def __str__(self):
        return f'{self.descripcion}'


class TipoGasto(models.Model):
    class Meta:
        verbose_name = 'Tipo de Gasto'
        verbose_name_plural = 'Tipos de Gasto'
        ordering = ['-id']

    descripcion = models.CharField(max_length=30, verbose_name='Descripcion', unique=True)

    def __str__(self):
        return f'{self.descripcion}'


class CobroVenta(MovimientoCaja):
    class Meta:
        db_table = 'caja_movimientocaja_cobroventa'
        verbose_name = 'Cobro de Venta'
        verbose_name_plural = 'Cobros de Venta'
        ordering = ['-id']

    venta = models.ForeignKey(Venta, on_delete=models.PROTECT, null=True, verbose_name='Venta')

    def __str__(self):
        return f'{self.venta}'


class Sueldo(MovimientoCaja):
    class Meta:
        db_table = 'caja_movimientocaja_sueldo'
        verbose_name = 'Sueldo'
        verbose_name_plural = 'Sueldos'
        ordering = ['-id']

    descripcion = models.CharField(max_length=30, verbose_name='Descripcion')
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, null=True, verbose_name='Empleado')

    def __str__(self):
        return f'{self.descripcion}'

    def clase(self):
        return 'Sueldo'


class Adelanto(MovimientoCaja):
    class Meta:
        db_table = 'caja_movimientocaja_adelanto'
        verbose_name = 'Adelanto'
        verbose_name_plural = 'Adelantos'
        ordering = ['-id']

    descripcion = models.CharField(max_length=30, verbose_name='Descripcion')
    empleado = models.ForeignKey('empleado.Empleado', on_delete=models.PROTECT, null=True, verbose_name='Empleado')

    def __str__(self):
        return f'{self.descripcion}'


class Ingreso(MovimientoCaja):
    class Meta:
        db_table = 'caja_movimientocaja_ingreso'
        verbose_name = 'Ingreso'
        verbose_name_plural = 'Ingresos'
        ordering = ['-id']

    tipo_ingreso = models.ForeignKey(TipoIngreso, on_delete=models.PROTECT, null=True, verbose_name='Tipo de Ingreso')
    concepto = models.CharField(max_length=30, verbose_name='Concepto')

    def __str__(self):
        return f'{self.concepto}'


class RetiroEfectivo(MovimientoCaja):
    class Meta:
        db_table = 'caja_movimientocaja_retiroefectivo'
        verbose_name = 'Retiro de Efectivo'
        verbose_name_plural = 'Retiros de Efectivo'
        ordering = ['-id']

    concepto = models.CharField(max_length=30, verbose_name='Concepto')

    def __str__(self):
        return f'{self.concepto}'


class Gasto(MovimientoCaja):
    class Meta:
        db_table = 'caja_movimientocaja_gasto'
        verbose_name = 'Gasto'
        verbose_name_plural = 'Gastos'
        ordering = ['-id']

    tipo_gasto = models.ForeignKey(TipoGasto, on_delete=models.PROTECT, null=True, verbose_name='Tipo de Gasto')
    concepto = models.CharField(max_length=30, verbose_name='Concepto')

    def __str__(self):
        return f'{self.tipo_gasto}'



class TarjetaDeCredito(models.Model):
    class Meta:
        db_table = 'tarjeta_de_credito'
        verbose_name = 'Tarjeta de Credito'
        verbose_name_plural = 'Tarjetas de Credito'

    nombre = models.CharField(max_length=30, null=False, verbose_name='Nombre Tarjeta de Credito')
    banco = models.CharField(max_length=30, null=True, verbose_name='Banco Tarjeta')

    def __str__(self):
        return f'{self.nombre}'


class PlanTarjetaDeCredito(models.Model):
    class Meta:
        db_table = 'plan_tarjeta_de_credito'
        verbose_name = 'Plan Tarjeta de Credito'
        verbose_name_plural = 'Planes Tarjetas de Credito'

    tarjeta = models.ForeignKey(TarjetaDeCredito, null=False, on_delete=models.PROTECT,
                                verbose_name='Tarjeta de Credito')
    nombre_plan = models.CharField(max_length=75, null=False, verbose_name='Nombre del Plan')
    interes = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Interes')
    es_vale = models.BooleanField(default=False, verbose_name="Es Vale?")

    def __str__(self):
        return f'{self.nombre_plan}'


class CuponPagoTarjeta(models.Model):
    class Meta:
        verbose_name = 'Cupon de Pago Tarjeta'
        verbose_name_plural = 'Cupones de Pago Tarjetas'
        ordering = ['-id']

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, null=True, verbose_name='Cliente')
    plan_tarjeta = models.ForeignKey(PlanTarjetaDeCredito, on_delete=models.PROTECT, null=False,
                                     verbose_name='Plan Tarjeta')
    numero_tarjeta = models.CharField(max_length=16, null=True, blank=True, verbose_name='Numero de Tarjeta')
    importe = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=False, verbose_name='Importe Pago')
    recargo = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=False, verbose_name='Recargo')
    importe_con_recargo = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=False,
                                              verbose_name='Importe con Recargo')
    numero_cupon = models.CharField(null=True, blank=True, max_length=10, verbose_name='Numero de Cupon')
    lote = models.CharField(null=True, blank=True, max_length=10, verbose_name='Lote')
    fecha = models.DateTimeField(auto_now=True, verbose_name='Fecha')
    venta = models.ForeignKey(Venta, on_delete=models.PROTECT, blank=True, null=True, verbose_name='Venta')
    observaciones = models.CharField(max_length=100, null=True, blank=True, verbose_name='Observaciones')

    def __str__(self):
        return f'{self.cliente}'
    
class PagoTransferencia(models.Model):
    class Meta:
        verbose_name = 'Pago Con Tranferencia'
        verbose_name_plural = 'Pagos Con Tranferencia'
        ordering = ['-id']

    nombre = models.CharField(max_length=40, null=True, blank=True, verbose_name='Nombre')
    apellido = models.CharField(max_length=30, null=True, blank=True, verbose_name='Apellido')
    documento_identidad = models.CharField(max_length=12, verbose_name='Documento Identidad')
    banco = models.CharField(max_length=60, null=True, blank=True, verbose_name='Banco')
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, null=True, verbose_name='Cliente')
    fecha = models.DateTimeField(auto_now=True, verbose_name='Fecha')
    venta = models.ForeignKey(Venta, on_delete=models.PROTECT, blank=True, null=True, verbose_name='Venta')
    observaciones = models.CharField(max_length=100, null=True, blank=True, verbose_name='Observaciones')
    
    def __str__(self):
        return "{} {}".format(self.nombre, self.apellido)