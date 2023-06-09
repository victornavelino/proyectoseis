from django.contrib import admin

# Register your models here.
from empleado.models import Sucursal, Empleado


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)
    list_per_page = 30


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('persona',)
    search_fields = ('persona__nombre','persona__apellido')
    list_per_page = 30