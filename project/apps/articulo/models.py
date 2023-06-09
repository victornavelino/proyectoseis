from django.db import models

# Create your models here.
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
from softdelete.models import SoftDeleteObject


class TipoIva(models.Model):
    class Meta:
        verbose_name = 'Tipo de IVA'
        verbose_name_plural = 'Tipos de IVA'

    nombre = models.CharField(max_length=100, verbose_name='Nombre', unique=True)
    porcentaje = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return self.nombre


class Categoria(MPTTModel):
    class MPTTMeta:
        order_insertion_by = ['nombre']
        parent_attr = 'nodo_padre'

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    nodo_padre = TreeForeignKey(
        'self',
        blank=True, null=True,
        on_delete=models.CASCADE,
        db_index=True,
        verbose_name='Categoría Padre',
        related_name='nodo_hijo',
        help_text='Ejemplo: Carnes'
    )
    nombre = models.CharField(max_length=150)
    tipo_iva = models.ForeignKey(TipoIva, on_delete=models.CASCADE, verbose_name='Tipo IVA')

    def __str__(self):
        return "{} - {} ".format(self.nombre, self.tipo_iva.nombre)


class UnidadMedida(models.Model):
    class Meta:
        verbose_name = 'Unidad de Medida'
        verbose_name_plural = 'Unidades de Medida'
        ordering = ['-id']

    nombre = models.CharField(max_length=50, verbose_name='Nombre', unique=True, help_text='Ejemplo: gramo')
    abreviatura = models.CharField(max_length=5, verbose_name='Abreviatura', help_text='Ejemplo: gr')

    def __str__(self):
        return f'{self.nombre}'



class Articulo(SoftDeleteObject):
    class Meta:
        verbose_name = 'Artículo'
        verbose_name_plural = 'Artículos'
        ordering = ['-id']

    nombre = models.CharField(max_length=50, verbose_name='Nombre', unique=True, help_text='Ejemplo: Vacío especial')
    abreviatura = models.CharField(max_length=10, verbose_name='Abreviatura', help_text='Ejemplo: VACÍO ESP.')
    codigo = models.CharField(max_length=10, verbose_name='Código de barras',
                              help_text='Ingrese el código de barras del artículo', unique=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, verbose_name='Categoría')
    unidad_medida = models.ForeignKey(UnidadMedida, on_delete=models.CASCADE, verbose_name='Unidad de medida')
    es_por_peso = models.BooleanField(verbose_name='¿Es Peso?', help_text='Indique si el artículo se pesa',
                                      default=True)



    def __str__(self):
        return f'{self.nombre}'


class ListaPrecio(models.Model):
    class Meta:
        verbose_name = 'Lista de Precios'
        verbose_name_plural = 'Listas de Precios'
        ordering = ['-id']

    nombre = models.CharField(max_length=50, verbose_name='Nombre', unique=True, help_text='Ejemplo: Clientes')

    def __str__(self):
        return f'{self.nombre}'


class Precio(SoftDeleteObject):
    class Meta:
        verbose_name = 'Precio'
        verbose_name_plural = 'Precios'
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(fields=['articulo', 'sucursal', 'lista_precio'],
                                    name='unique_articulo_sucusal_lista'),
        ]

    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE, verbose_name='Artículo')
    sucursal = models.ForeignKey('empleado.Sucursal', on_delete=models.CASCADE, verbose_name='Sucursal')
    lista_precio = models.ForeignKey('articulo.ListaPrecio', on_delete=models.CASCADE, verbose_name='Lista de Precios')
    precio = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return "{} - {} ".format(self.articulo.abreviatura, self.precio)
