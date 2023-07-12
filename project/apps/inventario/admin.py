from django.contrib import admin, messages
from import_export.admin import ImportExportModelAdmin
from import_export import resources
# Register your models here.
from django.contrib.admin import forms
from django.shortcuts import render
import inventario.models
from articulo.models import Articulo, Precio, ListaPrecio
from inventario.forms import InventarioAdminForm, MovimientoInternoArticuloInlineForm, MovimientoInternoAdminForm
from inventario.models import Inventario, TipoInventario, ArticuloInventario, MovimientoInterno, \
    MovimientoInternoArticulo

"""
class ArticuloInventarioInline(admin.TabularInline):
    model = ArticuloInventario
    extra = 0


@admin.register(ArticuloInventario)
class ArticuloInventarioAdmin(admin.ModelAdmin):
    list_display = ('precio', 'cantidad_peso', 'articulo_descripcion', 'codigo', 'inventario',)
    search_fields = ('articulo_descripcion',)
    list_per_page = 30


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'mes',)
    search_fields = ('fecha',)
    list_per_page = 30
    inlines = [ArticuloInventarioInline]
    form = InventarioAdminForm


@admin.register(TipoInventario)
class TipoInventarioAdmin(admin.ModelAdmin):
    list_display = ('descripcion',)
    search_fields = ('descripcion',)
    list_per_page = 30


class MovimientoInternoArticuloInline(admin.TabularInline):
    model = MovimientoInternoArticulo
    form = MovimientoInternoArticuloInlineForm
    min_num = 0


class MovimientoInternoResource(resources.ModelResource):
    fields = ('numero_lote', 'fecha', 'sucursal_origen',
              'sucursal_destino', 'usuario_emisor', 'usuario_receptor', 'abierto', 'tipo_movimiento_interno',)

    class Meta:
        model = MovimientoInterno
        fields = ('numero_lote', 'fecha', 'sucursal_origen__nombre',
                  'sucursal_destino__nombre', 'usuario_emisor__username', 'usuario_receptor__username', 'abierto',
                  'tipo_movimiento_interno',)


@admin.register(MovimientoInterno)
class MovimientoInternoAdmin(ImportExportModelAdmin):
    resource_class = MovimientoInternoResource
    list_display = ('numero_lote', 'fecha', 'sucursal_origen',
                    'sucursal_destino', 'usuario_emisor', 'usuario_receptor', 'abierto', 'tipo_movimiento_interno')
    search_fields = ('numero_lote', 'sucursal_destino')
    list_filter = ['tipo_movimiento_interno', 'abierto', 'sucursal_origen']
    list_per_page = 30
    inlines = [MovimientoInternoArticuloInline]
    actions = ['recepcionar_movimiento_interno']
    readonly_fields = ('principal', 'movimiento_relacionado', 'fecha')
    form = MovimientoInternoAdminForm

    @admin.action(description='Recepcionar Movimiento')
    def recepcionar_movimiento_interno(self, request, queryset):
        # ventas = Venta.objects.filter(sucursal=request.user.sucursal, cobrada=False)
        if len(queryset) != 1:
            messages.error(request, 'Debe seleccionar solo UN Movimiento')
            return False
        movimiento = queryset[0]
        if movimiento.tipo_movimiento_interno != MovimientoInterno.INGRESO:
            messages.error(request, 'Solo pueden recepcionarse Ingresos')
            return False
        if not movimiento.abierto:
            messages.error(request, 'El movimiento ya fue recepcionado')
            return False
        articulos_movimiento_interno = MovimientoInternoArticulo.objects.filter(movimiento_interno=movimiento)
        return render(request, 'admin/inventario/movimientointerno/recepcion_movimiento.html',
                      context={'movimiento': movimiento,
                               'lista_articulos': articulos_movimiento_interno})

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.sucursal_origen = request.user.sucursal
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return self.readonly_fields
        return self.readonly_fields + ('sucursal_origen',)
"""