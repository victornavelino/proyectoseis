from django.contrib import admin

from cliente.models import Cliente
from persona.models import Persona
from import_export.admin import ExportMixin, ExportActionMixin
from import_export import resources


class ClienteResource(resources.ModelResource):
    fields = ('persona__nombre', 'persona__apellido' ,'condicion_iva', 'persona__documento_identidad','lista_precio__nombre')
    class Meta:
        model = Cliente
        fields = ('condicion_iva', 'persona__documento_identidad', 'lista_precio__nombre',)
    def dehydrate_full_title(self, Cliente):
        book_name = getattr(Cliente, "name", "unknown")
        author_name = getattr(Cliente.persona.obtener_nombre_completo(), "name", "unknown")
        return '%s by %s' % (book_name, author_name)


@admin.register(Cliente)
class ClienteAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = ClienteResource
    list_display = ('cliente', 'condicion_iva', 'get_dni', 'get_lista_precio')
    search_fields = ('condicion_iva','persona__apellido', 'persona__nombre', 'persona__documento_identidad')
    list_per_page = 30

    @admin.display(description='Cliente')
    def cliente(self, obj):
        return obj.persona.obtener_nombre_completo()

    @admin.display(ordering='dni', description='DNI')
    def get_dni(self, obj):
        return obj.persona.documento_identidad

    @admin.display(ordering='listaprecio', description='ListaPrecio')
    def get_lista_precio(self, obj):
        return obj.lista_precio.nombre
