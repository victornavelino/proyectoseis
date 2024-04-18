from IPython.utils.sysinfo import pkg_info
from django.contrib import admin, messages

# Register your models here.
from django.db.models import Sum
from django.forms import forms
from import_export import resources
from wkhtmltopdf.views import PDFTemplateResponse
from caja.models import Caja
from caja.models import CobroVenta, CuponPagoTarjeta
from venta.forms import VentaAdminForm, CobrarVentaForm
from venta.models import VentaArticulo, Venta, CierreVentas
from django.shortcuts import render
from venta.forms import CobrarVentaForm
from import_export.admin import ExportMixin, ExportActionMixin, ExportActionModelAdmin
from import_export.fields import Field


from venta.utils import calcular_importe_eventuales, calcular_importe_descuentos, calcular_importe_asado, \
    calcular_importe_blandos


class VentaArticuloInline(admin.StackedInline):
    model = VentaArticulo
    extra = 0
    verbose_name = "Artículo"
    verbose_name_plural = "Artículos de la Venta"


class VentaResource(resources.ModelResource):

    usuario = Field(attribute='usuario__username', column_name='Usuario')
    sucursal = Field(attribute='sucursal__nombre', column_name='Sucursal')
    cliente = Field(attribute='cliente__persona__obtener_nombre_completo', column_name='Cliente')
    class Meta:
        model = Venta
        fields = ('numero_ticket', 'cliente', 'fecha', 'monto', 'descuento', 'anulado', 'sucursal', 'usuario',)
        export_order = ('fecha', 'cliente','numero_ticket','monto','descuento','anulado','usuario','sucursal',)


@admin.register(Venta)
class VentaAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = VentaResource
    list_display = ('cliente', 'monto', 'numero_ticket', 'fecha', 'anulado', 'cobrada', 'sucursal', 'cierreventa', 'usuario',)
    search_fields = ('numero_ticket',)
    exclude = ('es_persona', 'monto', 'descuento')
    list_filter = ['sucursal']
    readonly_fields = ('usuario',)
    list_per_page = 30
    add_form_template = 'admin/venta/venta/add.html'
    change_list_template = 'admin/venta/venta/change_list.html'
    inlines = (VentaArticuloInline,)
    actions = ['anular_venta', 'imprimir_ticket']


    @admin.action(description='Anular Venta')
    def anular_venta(self, request, queryset):
        if len(queryset) != 1:
            messages.error(request, 'Debe seleccionar solo una Venta para anular')
            return False
        venta=queryset[0]
        if venta.cobrada:
            cobro_venta=CobroVenta.objects.get(venta=venta)
            if cobro_venta.caja.fecha_fin:
                messages.error(request,'No se puede anular venta, la caja esta cerrada')
                return False
            else:
                cupon_tarjeta =CuponPagoTarjeta.objects.get(venta=venta)
                if cupon_tarjeta:
                    cupon_tarjeta.delete
                    cupon_tarjeta.save()    
                cobro_venta.delete
                cobro_venta.save()
                print('entro anular venta cobrada')
        venta.anulado=True
        venta.save()
        messages.success(request, 'Venta Anulada')
        return True

    @admin.action(description='Imprimir Ticket')
    def imprimir_ticket(self, request, queryset):
        if len(queryset) != 1:
            messages.error(request, 'Debe seleccionar solo Un Ticket')
            return False
        venta = queryset[0]
        nombre_archivo = "venta-" + str(venta.numero_ticket)+"-" + str(venta.fecha) + ".pdf"
        vendedor = venta.empleado
        articulos_venta = VentaArticulo.objects.filter(venta=venta)
        monto_descuento = 0
        for articulo in articulos_venta:
            descuento_individual = articulo.precio_unitario - articulo.precio_promocion
            monto_descuento = monto_descuento + descuento_individual
        response = PDFTemplateResponse(request=request,
                                       template='admin/venta/ticket_venta.html',
                                       filename=nombre_archivo,
                                       context={'venta': venta,
                                                'vendedor': vendedor,
                                                'articulos': articulos_venta,
                                                'monto_descuento': monto_descuento},
                                       show_content_in_browser=True,
                                       cmd_options={'margin-top': 3,
                                                    'margin-left': 0},
                                       )
        return response

"""@admin.register(CierreVentas)
class CierreVentasAdmin(admin.ModelAdmin):
    list_display = ('numero_cierre', 'ticket_desde', 'ticket_hasta', 'importe', 'ticket_cantidad', 'fecha', 'sucursal')
    search_fields = ('numero_cierre',)
    list_filter = ['sucursal']
    list_per_page = 30
    actions = ['imprimir_cierre_ventas']

    def get_form(self, request, obj=None, *args, **kwargs):
        form = super(CierreVentasAdmin, self).get_form(request, *args, **kwargs)
        if obj is None:
            ticket_desde = Venta.objects.filter(cierreventa=None, cobrada=True, anulado=False, sucursal=request.user.sucursal).order_by('-numero_ticket').last()
            ticket_hasta = Venta.objects.filter(cierreventa=None, cobrada=True, anulado=False, sucursal=request.user.sucursal).order_by('-numero_ticket').first()
            ticket_cantidad = Venta.objects.filter(cierreventa=None, cobrada=True, anulado=False, sucursal=request.user.sucursal).count()
            importe = Venta.objects.filter(cierreventa=None, cobrada=True, anulado=False, sucursal=request.user.sucursal).aggregate(Sum('monto'))['monto__sum'] or 0.00

            sucursal = request.user.sucursal
            form.base_fields['sucursal'].initial = sucursal
            #form.base_fields['sucursal'].disabled = True
            form.base_fields['ticket_desde'].initial = ticket_desde
            #form.base_fields['ticket_desde'].disabled = True
            form.base_fields['ticket_hasta'].initial = ticket_hasta
            #form.base_fields['ticket_hasta'].disabled = True
            form.base_fields['ticket_cantidad'].initial = ticket_cantidad
            #form.base_fields['ticket_cantidad'].disabled = True
            form.base_fields['importe'].initial = importe
            #form.base_fields['importe'].disabled = True
        return form

    def save_model(self, request, obj, form, change):
        print('entro obj is none savemodel')

        ventas = Venta.objects.filter(sucursal=request.user.sucursal, cobrada=False, anulado=False, cierreventa=None)
        print(ventas.count())
        if ventas.count() > 0:
            print('entro count +0')
            print(ventas.count())
            messages.error(request, 'Tiene Tickets sin cobrar, no puede cerrar ventas')
            return False
        print('paso el if')
        super().save_model(request, obj, form, change)
        ventasCobradas = Venta.objects.filter(sucursal=request.user.sucursal, cobrada=True, anulado=False, cierreventa=None)
        for venta in ventasCobradas:
            print('entro for cierre')
            venta.cierreventa=obj
            venta.save()

    def has_add_permission(self, request):
        ventas = Venta.objects.filter(sucursal=request.user.sucursal, cobrada=True, anulado=False, cierreventa=None)
        print('ventas sin cerrar')
        print(ventas.count())
        if ventas.count() > 0:
            return False
        return True

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    @admin.action(description='Imprimir Cierre Venta')
    def imprimir_cierre_ventas(self, request, queryset):
        if len(queryset) != 1:
            messages.error(request, 'Debe seleccionar solo Un Cierre de Ventas')
            return False
        cierre_venta = queryset[0]
        nombre_archivo = "venta-" + str(cierre_venta.numero_cierre) + "-" + str(cierre_venta.fecha) + ".pdf"
        usuario = request.user
        #articulos_venta = VentaArticulo.objects.filter(venta=venta)-
        print('IMPORTE EVENTUALES ' + str(calcular_importe_eventuales(cierre_venta)))
        response = PDFTemplateResponse(request=request,
                                       template='admin/venta/ticket_cierre_venta.html',
                                       filename=nombre_archivo,
                                       context={'cierre_venta': cierre_venta,
                                                'usuario': usuario,
                                                'importe_eventuales': calcular_importe_eventuales(cierre_venta),
                                                'importe_descuentos': calcular_importe_descuentos(cierre_venta),
                                                'importe_asados': calcular_importe_asado(cierre_venta),
                                                'importe_blandos': calcular_importe_blandos(cierre_venta)},
                                       show_content_in_browser=False,
                                       cmd_options={'margin-top': 3,
                                                    'margin-left': 0},
                                       )
        return response"""