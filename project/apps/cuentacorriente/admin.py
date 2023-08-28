from django.contrib import admin, messages
from django.db.models import Sum
from jet.filters import RelatedFieldAjaxListFilter
from decimal import Decimal
from caja.models import Caja
from cuentacorriente.constants import DEBITO, CREDITO
from cuentacorriente.models import CuentaCorriente, MovimientoCuentaCorriente


class MovimientoCuentaCorrienteInline(admin.TabularInline):
    model = MovimientoCuentaCorriente
    extra = 0
    verbose_name = "Movimiento"
    verbose_name_plural = "Movimientos"
    fields = ('importe', 'fecha', 'tipo', 'usuario', 'venta', 'observaciones')
    readonly_fields = ('usuario', 'venta', 'fecha')
    can_delete = True


@admin.register(CuentaCorriente)
class CuentaCorrienteAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'fecha', 'activa', 'saldo')
    list_display_links = ('cliente', 'saldo',)
    list_filter = (('cliente', RelatedFieldAjaxListFilter), 'cliente__persona__documento_identidad')
    list_per_page = 30
    inlines = (MovimientoCuentaCorrienteInline,)

    def saldo(self, obj):
        debito = MovimientoCuentaCorriente.objects.filter(cuenta=obj, tipo=DEBITO).aggregate(Sum('importe'))[
            'importe__sum'] or Decimal(0.0)
        credito = MovimientoCuentaCorriente.objects.filter(cuenta=obj, tipo=CREDITO).aggregate(Sum('importe'))[
            'importe__sum'] or Decimal(0.0)
        try:
            return debito - credito
        except:
            return 0

    def save_formset(self, request, form, formset, change):
        instances = formset.save()
        caja_abierta = Caja.objects.filter(sucursal=request.user.sucursal, fecha_fin__isnull=True,
                                           fecha_inicio__isnull=False).last()
        for instance in instances:
            # Do something with `instance`
            if not instance.usuario_id:
                instance.usuario = request.user
                if caja_abierta is None and instance.tipo == CREDITO:
                    messages.error(request, 'La caja esta Cerrada')
                    return False
        
            instance.save()
        #formset.save_m2m()



