from django.contrib.admin import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

# Create your models here.

from articulo.models import Articulo, ListaPrecio, Precio
from empleado.models import Sucursal
from usuario.models import Usuario


class TipoInventario(models.Model):
    class Meta:
        verbose_name = 'Tipo de Inventario'
        verbose_name_plural = 'Tipos de Inventarios'
        ordering = ['-id']

    descripcion = models.CharField(max_length=30, verbose_name='Descripcion')

    def __str__(self):
        return f'{self.descripcion}'


class Inventario(models.Model):
    class Meta:
        verbose_name = 'Inventario'
        verbose_name_plural = 'Inventarios'
        ordering = ['-id']

    ENERO = 'enero'
    FEBRERO = 'febrero'
    MARZO = 'marzo'
    ABRIL = 'abril'
    MAYO = 'mayo'
    JUNIO = 'junio'
    JULIO = 'julio'
    AGOSTO = 'agosto'
    SEPTIEMBRE = 'septiembre'
    OCTUBRE = 'octubre'
    NOVIEMBRE = 'noviembre'
    DICIEMBRE = 'diciembre'

    MESES = (
        (ENERO, 'Enero'),
        (FEBRERO, 'Febrero'),
        (MARZO, 'Marzo'),
        (ABRIL, 'Abril'),
        (MAYO, 'Mayo'),
        (JUNIO, 'Junio'),
        (JULIO, 'Julio'),
        (AGOSTO, 'Agosto'),
        (SEPTIEMBRE, 'Septiembre'),
        (OCTUBRE, 'Octubre'),
        (NOVIEMBRE, 'Noviembre'),
        (DICIEMBRE, 'Diciembre'),
    )

    fecha = models.DateField(verbose_name='Fecha', null=True)
    mes = models.CharField(max_length=10, choices=MESES, verbose_name='Mes', default=ENERO)
    anio = models.IntegerField(null=False, validators=[MaxValueValidator(2040), MinValueValidator(2020)], default=2022)
    tipo_inventario = models.ForeignKey(TipoInventario, on_delete=models.PROTECT, null=True,
                                        verbose_name='Tipo de Inventario')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, null=True, verbose_name='Sucursal')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True)
    usuario = models.ForeignKey(Usuario, null=True, on_delete=models.PROTECT, verbose_name='Usuario')

    def __str__(self):
        return f'{self.fecha}'


class ArticuloInventario(models.Model):
    class Meta:
        verbose_name = 'Articulo Inventario'
        verbose_name_plural = 'Articulos Inventario'
        ordering = ['-id']

    precio = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True, verbose_name='Precio')
    cantidad_peso = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True,
                                        verbose_name='Cantidad / Peso')
    articulo_descripcion = models.CharField(max_length=50, verbose_name='Descripcion del articulo')
    codigo = models.CharField(max_length=5, verbose_name='Codigo del articulo')
    inventario = models.ForeignKey(Inventario, on_delete=models.CASCADE, null=True, verbose_name='Inventario')

    def __str__(self):
        return f'{self.articulo_descripcion}'


class MovimientoInterno(models.Model):
    class Meta:
        verbose_name = 'Movimiento Interno'
        verbose_name_plural = 'Movimientos Internos'
        ordering = ['-numero_lote']

    INGRESO = 'Ingreso'
    EGRESO = 'Egreso'
    DECOMISO = 'Decomiso'
    TR_ENTRADA = 'Transformacion Entrada'
    TR_SALIDA = 'Transformacion Salida'

    TIPOS = (
        (INGRESO, 'Ingreso'),
        (EGRESO, 'Egreso'),
        (DECOMISO, 'Decomiso'),
        (TR_ENTRADA, 'Transformacion Entrada'),
        (TR_SALIDA, 'Transformacion Salida'),
    )

    numero_lote = models.AutoField(primary_key=True, verbose_name='Numero de Lote')
    fecha = models.DateField(auto_now=True, verbose_name='Fecha', null=False)
    sucursal_origen = models.ForeignKey('empleado.Sucursal', on_delete=models.CASCADE, null=True,
                                        related_name='sucursal_origen', verbose_name='Sucursal Origen')
    sucursal_destino = models.ForeignKey('empleado.Sucursal', on_delete=models.CASCADE, null=True,
                                         related_name='sucursal_destino', verbose_name='Sucursal Destino')
    usuario_emisor = models.ForeignKey('usuario.Usuario', on_delete=models.CASCADE, null=True,
                                       related_name='usuario_emisor', verbose_name='Usuario Emisor')
    usuario_receptor = models.ForeignKey('usuario.Usuario', null=True, on_delete=models.CASCADE,
                                         related_name='usuario_receptor', verbose_name='Usuario Receptor')
    tipo_movimiento_interno = models.CharField(max_length=22, null=False, choices=TIPOS,
                                               verbose_name='Tipo de Movimiento Interno')
    abierto = models.BooleanField(default=True, verbose_name='Abierto')
    anulado = models.BooleanField(default=False, verbose_name='Anulado')
    principal = models.BooleanField(default=True, verbose_name='¿Es Principal?')
    movimiento_relacionado = models.ForeignKey('MovimientoInterno', null=True, blank=True, on_delete=models.CASCADE)

    def clean(self):
        if self.tipo_movimiento_interno == MovimientoInterno.DECOMISO and self.sucursal_origen != self.sucursal_destino:
            raise ValidationError('Los decomisos se efectuan sobre una misma sucursal')
        if self.sucursal_origen == self.sucursal_destino and self.tipo_movimiento_interno != MovimientoInterno.DECOMISO:
            raise ValidationError('La sucursal de origen y destino deben ser distintas')
        if self.tipo_movimiento_interno == MovimientoInterno.DECOMISO and self.usuario_emisor != self.usuario_receptor:
            raise ValidationError('Para los decomisos el Usuario debe ser el mismo')
        if self.usuario_emisor == self.usuario_receptor and self.tipo_movimiento_interno != MovimientoInterno.DECOMISO:
            raise ValidationError('El usuario emisor y receptor deben ser distintos')

    def save(self, *args, **kwargs):
        self.full_clean()
        nuevo = False
        if self.numero_lote is None:
            nuevo = True
        super(MovimientoInterno, self).save(*args, **kwargs)
        if nuevo and self.tipo_movimiento_interno == MovimientoInterno.EGRESO:
            tipo_movimiento_secundario = MovimientoInterno.INGRESO
            movimiento_secundario = MovimientoInterno.objects.create(fecha=self.fecha,
                                                                     sucursal_origen=self.sucursal_origen,
                                                                     sucursal_destino=self.sucursal_destino,
                                                                     usuario_emisor=self.usuario_emisor,
                                                                     usuario_receptor=self.usuario_receptor,
                                                                     tipo_movimiento_interno=tipo_movimiento_secundario,
                                                                     movimiento_relacionado=self,
                                                                     principal=False)
            self.movimiento_relacionado = movimiento_secundario
            self.save()


def __str__(self):
    return f'{self.numero_lote}'


class MovimientoInternoArticulo(models.Model):
    class Meta:
        verbose_name = 'Movimiento Interno Articulo'
        verbose_name_plural = 'Movimiento Interno Articulos'
        ordering = ['-id']

    articulo = models.ForeignKey('articulo.Articulo', null=False, on_delete=models.CASCADE, verbose_name='Articulo')
    cantidad_peso = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True,
                                        verbose_name='Cantidad / Peso')
    monto = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True, verbose_name='Monto')
    movimiento_interno = models.ForeignKey('MovimientoInterno', on_delete=models.CASCADE,
                                           verbose_name='Movimiento Interno')

    def clean(self):
        if self.articulo is None:
            raise ValidationError('Debe selecciona un Articulo')
        if self.monto is None or self.monto <= 0:
            raise ValidationError('El monto debe ser mayor que Cero')
        if self.cantidad_peso is None or self.cantidad_peso <= 0:
            raise ValidationError('La Cantidad debe ser mayor que Cero')

    def save(self, *args, **kwargs):
        self.full_clean()
        nuevo = False
        lista_precio, created = ListaPrecio.objects.get_or_create(nombre='COMUN')
        precio = Precio.objects.get(articulo=self.articulo, lista_precio=lista_precio)
        monto = self.cantidad_peso * precio.precio
        self.monto = monto
        if self.pk is None:
            nuevo = True
        super(MovimientoInternoArticulo, self).save(*args, **kwargs)
        if nuevo and self.movimiento_interno.tipo_movimiento_interno == MovimientoInterno.EGRESO:
            articulo_secundario = self
            articulo_secundario.movimiento_interno = articulo_secundario.movimiento_interno.movimiento_relacionado
            articulo_secundario.pk = None
            articulo_secundario.save()

    def __str__(self):
        return f'{self.articulo}'
