from django.contrib import admin

# Register your models here.
from mptt.admin import MPTTModelAdmin

from articulo.models import UnidadMedida, Articulo, ListaPrecio, Precio, Categoria, TipoIva
from cliente.models import Cliente


@admin.register(UnidadMedida)
class UnidadMedidaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'abreviatura')
    search_fields = ('nombre',)
    list_per_page = 30


@admin.register(Articulo)
class ArticuloAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'abreviatura', 'categoria', 'unidad_medida')
    search_fields = ('nombre',)
    list_filter = ('categoria',)
    list_per_page = 30


@admin.register(ListaPrecio)
class ListaPrecioAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)
    list_per_page = 30


@admin.register(TipoIva)
class TipoIvaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'porcentaje')
    search_fields = ('nombre',)
    list_per_page = 30


@admin.register(Precio)
class PrecioAdmin(admin.ModelAdmin):
    list_display = ('articulo', 'sucursal', 'lista_precio', 'precio')
    search_fields = ('articulo',)
    list_filter = ('sucursal', 'lista_precio')
    list_per_page = 30


@admin.register(Categoria)
class CategoriaAdmin(MPTTModelAdmin):
    list_display = ('nombre', 'tipo_iva')
    search_fields = ('nombre',)
    list_filter = ('tipo_iva',)

    list_per_page = 30
