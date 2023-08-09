from django.contrib import admin, messages

# Register your models here.
from django.shortcuts import render

from empleado.models import Sucursal
from promocion.models import Promocion, DiasSemana, PromocionArticulo, Descuento


class PromocionArticuloInline(admin.TabularInline):
    model = PromocionArticulo


@admin.register(Promocion)
class PromocionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'prioridad', 'fecha_inicio', 'fecha_fin', 'es_por_precio', 'dias_semana', 'sucursal', 'habilitada')
    search_fields = ('nombre', 'sucursal')
    list_filter =['sucursal',]
    list_per_page = 30
    inlines = [PromocionArticuloInline]
    actions = ['copiar_promociones']
    change_list_template = 'admin/promocion/promocion/promocion_changelist.html'

    @admin.action(description='Copiar Promocion')
    def copiar_promociones(self, request, queryset):
        if len(queryset) != 1:
            messages.error("Debe seleccionar Solo una Promocion para Copiar")
        promocion = queryset[0]
        sucursales = Sucursal.objects.all()
        promociones = Promocion.objects.filter(sucursal=promocion.sucursal)
        print(sucursales)
        return render(request, 'admin/promocion/copiar_promo.html',
                      context={'promocion': promocion,
                               'promociones': promociones,
                               'sucursales': sucursales})


@admin.register(DiasSemana)
class DiasSemanaAdmin(admin.ModelAdmin):
    list_display = ('lunes',)
    search_fields = ('lunes',)
    list_per_page = 30


@admin.register(PromocionArticulo)
class PromocionArticuloAdmin(admin.ModelAdmin):
    list_display = ('articulo', 'valor',)
    search_fields = ('articulo',)
    list_per_page = 30



@admin.register(Descuento)
class Descuento(admin.ModelAdmin):
    list_display = ('nombre', 'valor',)
    search_fields = ('nombre',)
    list_per_page = 30
