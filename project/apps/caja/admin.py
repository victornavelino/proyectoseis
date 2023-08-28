import datetime
import json
import decimal
from decimal import Decimal
from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import Sum, F
from jet.filters import RelatedFieldAjaxListFilter
from wkhtmltopdf.views import PDFTemplateResponse


# Register your models here.
from django.shortcuts import render
from psycopg2 import Date

from caja.constants import EGRESO, INGRESO
from caja.models import Caja, CobroVenta, Sueldo, Ingreso, TipoIngreso, RetiroEfectivo, TipoGasto, Gasto, \
    Adelanto, TarjetaDeCredito, PlanTarjetaDeCredito, CuponPagoTarjeta, MovimientoCaja
from caja.utils import calcular_saldo_caja, calcular_caja_final, calcular_ingresos_caja, calcular_total_ingresos, \
    calcular_egresos_caja, calcular_total_egresos, calcular_total_compras_cc
from cuentacorriente.constants import DEBITO, CREDITO
from cuentacorriente.models import CuentaCorriente, MovimientoCuentaCorriente
from empleado.models import Sucursal
from cuentacorriente.constants import TIPOS_MOVIMIENTO_CTA_CTE
from venta.forms import CobrarVentaForm
from venta.models import Venta
from import_export import resources
from import_export.admin import ExportMixin, ExportActionMixin
from import_export.fields import Field


@admin.register(Caja)
class CajaAdmin(admin.ModelAdmin):
    list_display = ('caja_pk','usuario', 'caja_inicial', 'caja_final', 'fecha_inicio', 'fecha_fin',)
    search_fields = ('usuario__username',)
    readonly_fields = ('caja_final',)
    actions = ['cerrar_caja', 'imprimir_cierre_caja', 'exportar_movimientos']
    list_per_page = 30

    def caja_pk(self, obj):
        return obj.pk
    caja_pk.short_description = 'Numero de Caja'

    def get_form(self, request, obj=None, *args, **kwargs):
        form = super(CajaAdmin, self).get_form(request, *args, **kwargs)
        if obj is None:
            caja_cerrada = Caja.objects.filter(sucursal=request.user.sucursal, fecha_fin__isnull=False,
                                               fecha_inicio__isnull=False).first()
            #print('caja cerrada: '+ str(caja_cerrada.caja_final))
            print('entro por try')
            if caja_cerrada:
                print('entro por if si')
                form.base_fields['caja_inicial'].initial = caja_cerrada.caja_final
                #form.base_fields['caja_inicial'].disabled = True
            else:
                if Caja.DoesNotExist:
                    form.base_fields['caja_inicial'].initial = 0.0
                    print('entro por else')
                else:
                    self.readonly_fields = ["sucursal", "usuario", "fecha_inicio", "caja_inicial", ]
                    return form
        return form

    def get_queryset(self, request):
        qs = super(CajaAdmin, self).get_queryset(request)
        return qs.filter(sucursal=request.user.sucursal)
    

    def save_model(self, request, obj, form, change):
        obj.usuario = request.user
        try:
            request.user.sucursal.DoesNotExist
        except Exception as e:
            messages.error(request, 'Debe existir sucursal asociada al usuario')
            return False
        obj.sucursal = request.user.sucursal

        if change:
            print('entro por change')
            obj.fecha_fin = datetime.datetime.now()
            obj.caja_final = calcular_caja_final(obj)
            super().save_model(request, obj, form, change)
            return True
        # Controlamos si hay una caja abierta
        caja_abierta = Caja.objects.filter(sucursal=request.user.sucursal, fecha_fin__isnull=True,
                                           fecha_inicio__isnull=False).last()
        if caja_abierta:
            messages.error(request, 'Existe Caja abierta, no puede abrir otra')
            return False
        else:
            super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        self.readonly_fields=['usuario',]
        self.exclude = ('caja_final', 'fecha_fin','sucursal',)
        return True

    def has_change_permission(self, request, obj=None):
        if obj:
            if obj.caja_final and obj.fecha_fin:
                return False
            print('modificando caja final')
            obj.caja_final = calcular_saldo_caja(obj)
        self.readonly_fields = ["sucursal", "usuario", "fecha_inicio", "caja_inicial", "caja_final", ]
        self.exclude = ('fecha_fin',)
        return True

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            if obj:
                if obj.caja_final and obj.fecha_fin:
                    return False
        return True

    @admin.action(description='Cerrar Caja')
    def cerrar_caja(self, request, queryset):
        if len(queryset) != 1:
            messages.error(request, 'Debe seleccionar solo Una Caja')
            return False
        caja = queryset[0]
        if caja.fecha_fin:
            messages.error(request, 'Debe seleccionar una Caja Abierta para poder Cerrarla')
            return False
        movimientos_caja = MovimientoCaja.objects.filter(caja=caja)
        ventas_sin_cobrar=Venta.objects.filter(cobrada=False)
        if len(ventas_sin_cobrar) > 0:
            messages.error(request, 'Existen ventas sin cobrar, no puede cerrar la caja')
            return False
        total_ingresos = MovimientoCaja.objects.filter(caja=caja, tipo=INGRESO).aggregate(Sum('importe'))['importe__sum'] or 0.00
        results = []
        json_valores = {
            "tipo": "Movimientos de Ingreso",
            "importe": str(total_ingresos)
        }
        results.append(json_valores)
        total_egresos = MovimientoCaja.objects.filter(caja=caja, tipo=EGRESO).aggregate(Sum('importe'))[
                            'importe__sum'] or 0.00
        json_valores = {
            "tipo": "Movimientos de Egreso",
            "importe": str(total_egresos)
        }
        results.append(json_valores)

        total_tarjeta = \
            CuponPagoTarjeta.objects.filter(fecha__gte=caja.fecha_inicio).aggregate(Sum('importe_con_recargo'))[
                'importe_con_recargo__sum'] or 0.00
        json_valores = {
            "tipo": "Compras Con Tarjeta",
            "importe": str(total_tarjeta)
        }
        results.append(json_valores)
        total_comprascc = \
            MovimientoCuentaCorriente.objects.filter(fecha__gte=caja.fecha_inicio, tipo=DEBITO).aggregate(
                Sum('importe'))[
                'importe__sum'] or 0.00
        json_valores = {
            "tipo": "Compras en Cuenta Corriente",
            "importe": str(total_comprascc)
        }
        results.append(json_valores)

        total_acreditacionescc = \
            MovimientoCuentaCorriente.objects.filter(fecha__gte=caja.fecha_inicio, tipo=CREDITO).aggregate(
                Sum('importe'))['importe__sum'] or 0.00
        json_valores = {
            "tipo": "Acreditacion en Cuenta Corriente",
            "importe": str(total_acreditacionescc)
        }
        # CALCULAMOS EL SALDO FINAL DE CAJA
        caja.caja_final = caja.caja_inicial + Decimal(total_acreditacionescc) + Decimal(total_ingresos) - Decimal(
            total_egresos)
        print("MOSTRAMOS CAJA FINAL")
        print(caja.caja_final)
        results.append(json_valores)
        data = json.dumps(results)
        data = json.loads(data)
        return render(request, 'admin/caja/cierre_caja.html',
                      context={'caja': caja,
                               'lista_movimientos': movimientos_caja,
                               'data': data})

    @admin.action(description='Imprimir Cierre')
    def imprimir_cierre_caja(self, request, queryset):
        if len(queryset) != 1:
            messages.error(request, 'Debe seleccionar solo Una Caja')
            return False
        caja = queryset[0]
        if caja.fecha_fin is None:
            messages.error(request, 'Debe seleccionar una Caja Cerrada para imprimir el ticket de cierre')
            return False
        nombre_archivo = "caja-" + str(caja.fecha_fin) + ".pdf"
        response = PDFTemplateResponse(request=request,
                                       template='admin/caja/ticket_cierre_caja.html',
                                       filename=nombre_archivo,
                                       context={'caja': caja,
                                                'ingresos': calcular_ingresos_caja(caja),
                                                'total_ingresos': calcular_total_ingresos(caja),
                                                'egresos': calcular_egresos_caja(caja),
                                                'total_egresos': calcular_total_egresos(caja),
                                                'total_ccorrientes': calcular_total_compras_cc(caja)},
                                       show_content_in_browser=False,
                                       cmd_options={'margin-top': 50, },
                                       )
        return response
    
    @admin.action(description='Exportar Movimientos')
    def exportar_movimientos(self, request, queryset):
        if len(queryset) != 1:
            messages.error(request, 'Debe seleccionar solo Una Caja')
            return False
        caja = queryset[0]
        movimientos_caja = MovimientoCaja.objects.filter(caja=caja).select_subclasses()
        for movimiento in movimientos_caja:
            print(movimiento.__class__.__name__)
        #print(movimientos_caja)
        response = None
        return response


class MovimientoCajaResource(resources.ModelResource):

    movimiento = Field()
    usuario = Field(attribute='usuario__username', column_name='Usuario')
    sucursal = Field(attribute='sucursal__nombre', column_name='Sucursal')
    caja = Field(attribute='caja__pk', column_name='Nro de Caja')

    class Meta:
        model = MovimientoCaja
        fields = ( 'caja', 'movimiento', 'tipo', 'fecha', 'importe', 'sucursal', 'usuario',)
    
    def dehydrate_movimiento(self, movimientocaja):
        clase = movimientocaja.clase()
        return clase

@admin.register(MovimientoCaja)
class MovimientoCajaAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = MovimientoCajaResource
    list_display = ('clase', 'importe', 'fecha', 'usuario','cerrado', 'importe')
    search_fields = ('usuario',)
    list_per_page = 30


    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return False
     
    def save_model(self, request, obj, form, change):
        messages.error(request, 'No Puede modificar movimientos desde este panel')
        return False




@admin.register(Sueldo)
class SueldoAdmin(admin.ModelAdmin):
    list_display = ('descripcion', 'importe', 'fecha', 'usuario','cerrado')
    search_fields = ('descripcion',)
    list_per_page = 30

    def get_queryset(self, request):
        qs = super(SueldoAdmin, self).get_queryset(request)
        return qs.filter(sucursal=request.user.sucursal)

    def has_add_permission(self, request):
        self.exclude = ('cerrado', 'usuario', 'sucursal', 'caja', 'tipo')
        return True

    def has_change_permission(self, request, obj=None):
        self.exclude = ('cerrado', 'usuario', 'sucursal', 'caja', 'tipo')
        return True

    def save_model(self, request, obj, form, change):
        obj.usuario = request.user
        obj.sucursal = request.user.sucursal
        obj.tipo = EGRESO
        if change:
            if obj.cerrado:
                raise messages.error(request, "No Puede Modificar este Movimiento, la caja esta Cerrada")
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            if obj:
                if obj.cerrado:
                    return False
        return True


@admin.register(Adelanto)
class AdelantoAdmin(admin.ModelAdmin):
    list_display = ('descripcion', 'importe', 'fecha', 'empleado', 'cerrado',)
    search_fields = ('descripcion',)
    list_per_page = 30

    def get_queryset(self, request):
        qs = super(AdelantoAdmin, self).get_queryset(request)
        return qs.filter(sucursal=request.user.sucursal)

    def has_add_permission(self, request):
        self.exclude = ('cerrado', 'usuario', 'sucursal', 'caja', 'tipo')
        return True

    def has_change_permission(self, request, obj=None):
        self.exclude = ('cerrado', 'usuario', 'sucursal', 'caja', 'tipo')
        return True

    def save_model(self, request, obj, form, change):
        obj.usuario = request.user
        obj.sucursal = request.user.sucursal
        obj.tipo = EGRESO
        if change:
            if obj.cerrado:
                raise messages.error(request, "No Puede Modificar este Movimiento, la caja esta Cerrada")
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            if obj:
                if obj.cerrado:
                    return False
        return True


@admin.register(Ingreso)
class IngresoAdmin(admin.ModelAdmin):
    list_display = ('concepto', 'importe', 'fecha', 'tipo_ingreso', 'usuario','cerrado')
    search_fields = ('concepto',)
    list_per_page = 30

    def get_queryset(self, request):
        qs = super(IngresoAdmin, self).get_queryset(request)
        return qs.filter(sucursal=request.user.sucursal)

    def has_add_permission(self, request):
        self.exclude = ('cerrado', 'usuario', 'sucursal', 'caja', 'tipo')
        return True

    def has_change_permission(self, request, obj=None):
        self.exclude = ('cerrado', 'usuario', 'sucursal', 'caja', 'tipo')
        return True

    def save_model(self, request, obj, form, change):
        obj.usuario = request.user
        obj.sucursal = request.user.sucursal
        obj.tipo = INGRESO
        if change:
            if obj.cerrado:
                raise forms.ValidationError("No Puede Modificar este Movimiento, la caja esta Cerrada")
        super().save_model(request, obj, form, change)
    
    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            if obj:
                if obj.cerrado:
                    return False
        return True


@admin.register(RetiroEfectivo)
class RetiroEfectivoAdmin(admin.ModelAdmin):
    list_display = ('concepto', 'importe', 'fecha', 'usuario','cerrado')
    search_fields = ('concepto',)
    list_per_page = 30

    def get_queryset(self, request):
        qs = super(RetiroEfectivoAdmin, self).get_queryset(request)
        return qs.filter(sucursal=request.user.sucursal)

    def has_add_permission(self, request):
        self.exclude = ('cerrado', 'usuario', 'sucursal', 'caja', 'tipo')
        return True

    def has_change_permission(self, request, obj=None):
        self.exclude = ('cerrado', 'usuario', 'sucursal', 'caja', 'tipo')
        return True

    def save_model(self, request, obj, form, change):
        obj.usuario = request.user
        obj.sucursal = request.user.sucursal
        obj.tipo = EGRESO
        if change:
            if obj.cerrado:
                raise forms.ValidationError("No Puede Modificar este Movimiento, la caja esta Cerrada")
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            if obj:
                if obj.cerrado:
                    return False
        return True


@admin.register(TipoIngreso)
class TipoIngresoAdmin(admin.ModelAdmin):
    list_display = ('descripcion',)
    search_fields = ('descripcion',)
    list_per_page = 30


@admin.register(TipoGasto)
class TipoGastoAdmin(admin.ModelAdmin):
    list_display = ('descripcion',)
    search_fields = ('descripcion',)
    list_per_page = 30


@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = ('tipo_gasto', 'concepto', 'importe', 'fecha', 'usuario', 'cerrado')
    search_fields = ('concepto',)
    list_per_page = 30

    def get_queryset(self, request):
        qs = super(GastoAdmin, self).get_queryset(request)
        return qs.filter(sucursal=request.user.sucursal)

    def has_add_permission(self, request):
        self.exclude = ('cerrado', 'usuario', 'sucursal', 'caja', 'tipo')
        return True

    def has_change_permission(self, request, obj=None):
        self.exclude = ('cerrado', 'usuario', 'sucursal', 'caja', 'tipo')
        return True

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            if obj:
                if obj.cerrado:
                    return False
        return True

    def save_model(self, request, obj, form, change):
        obj.usuario = request.user
        obj.sucursal = request.user.sucursal
        obj.tipo = EGRESO
        if change:
            if obj.cerrado:
                raise forms.ValidationError("No Puede Modificar este Movimiento, la caja esta Cerrada")
            return False
        super().save_model(request, obj, form, change)


@admin.register(TarjetaDeCredito)
class TarjetaDeCreditoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'banco',)
    search_fields = ('nombre',)
    list_per_page = 30


@admin.register(PlanTarjetaDeCredito)
class PlanTarjetaDeCreditoAdmin(admin.ModelAdmin):
    list_display = ('tarjeta', 'nombre_plan', 'interes')
    search_fields = ('nombre_plan',)
    list_per_page = 30

    def save_model(self, request, obj, form, change):
        if change:
            super().save_model(request, obj, form, change)
        else:
            valor = str(obj.tarjeta.nombre)+' - '+ str(obj.nombre_plan)
            obj.nombre_plan = valor
            print(obj.nombre_plan)
            super().save_model(request, obj, form, change)


@admin.register(CobroVenta)
class CobroVentaAdmin(admin.ModelAdmin):
    list_display = ('venta',)
    change_list_template = 'admin/venta/cobro_venta/changelist.html'
    add_form_template = 'admin/venta/cobro_venta/changelist.html'


class CuponPagoTarjetaResource(resources.ModelResource):
    fields = ('cliente', 'plan_tarjeta', 'importe',
              'importe_con_recargo', 'fecha',)
    class Meta:
        model = CuponPagoTarjeta
        fields = ('cliente__persona__apellido', 'plan_tarjeta__nombre_plan', 'importe', 'importe_con_recargo', 'fecha',)

@admin.register(CuponPagoTarjeta)
class CuponPagoTarjetaAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = CuponPagoTarjetaResource
    list_display = ('cliente', 'plan_tarjeta', 'importe', 'importe_con_recargo', 'fecha', 'caja')
    search_fields = ('cliente__persona__apellido',)
    list_per_page = 30
    ordering = ('-fecha',)
    change_form_template = 'admin/caja/cuponpagotarjeta_changeform.html'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Si estás editando un objeto existente, oculta el campo 'campo_a_ocultar'
        form.base_fields['venta'].widget = forms.HiddenInput()
        return form

    def caja(self, obj):
        cobro_venta = CobroVenta.objects.get(venta=obj.venta)
        print(cobro_venta.caja)
        return cobro_venta.caja.pk
    caja.short_description = 'Numero de Caja'
    
    
    def save_model(self, request, obj, form, change):
        if obj.importe_con_recargo ==0:
            messages.error(request, 'El importe tiene que ser mayor que CERO')
            return False
        try:
            cuenta_corriente = CuentaCorriente.objects.get(cliente=obj.cliente)
            print(cuenta_corriente)
            if cuenta_corriente.activa:
                #Creamos el movimiento de cuenta corriente
                print('entro activa')
                if change:
                    fecha=obj.fecha
                    movimiento_cc = MovimientoCuentaCorriente.objects.get(cuenta=cuenta_corriente, fecha=F('fecha'),
                                                                           tipo=CREDITO)
                    movimiento_cc.importe=obj.importe_con_recargo
                    movimiento_cc.save()
                else:
                    movimiento_cc = MovimientoCuentaCorriente.objects.create(cuenta=cuenta_corriente, importe=obj.importe_con_recargo,
                                                                           tipo=CREDITO,
                                                                           usuario=request.user,
                                                                           venta=None, observaciones=' Cupon tarjeta Cuenta Corriente')
                    movimiento_cc.refresh_from_db()
                super().save_model(request, obj, form, change)
            else:
                 messages.error(request, 'El Cliente tiene cuenta corriente inactiva')
                 return False
        except:
            messages.error(request, "El cliente no tiene cuenta corriente")
            return False

        

    """def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False"""