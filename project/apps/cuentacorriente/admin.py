from django.contrib import admin, messages
from django.db.models import Sum
from jet.filters import RelatedFieldAjaxListFilter

from caja.models import Caja
from cuentacorriente.constants import DEBITO, CREDITO
from cuentacorriente.models import CuentaCorriente, MovimientoCuentaCorriente


class MovimientoCuentaCorrienteInline(admin.TabularInline):
    model = MovimientoCuentaCorriente
    extra = 0
    verbose_name = "Movimiento"
    verbose_name_plural = "Movimientos"
    fields = ('importe', 'fecha', 'tipo', 'usuario', 'venta')
    readonly_fields = ('usuario', 'venta', 'fecha')


@admin.register(CuentaCorriente)
class CuentaCorrienteAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'fecha', 'activa', 'saldo')
    list_display_links = ('saldo',)
    list_filter = (('cliente', RelatedFieldAjaxListFilter),)
    list_per_page = 30
    inlines = (MovimientoCuentaCorrienteInline,)

    def saldo(self, obj):
        debito = MovimientoCuentaCorriente.objects.filter(cuenta=obj, tipo=DEBITO).aggregate(Sum('importe'))[
            'importe__sum']
        credito = MovimientoCuentaCorriente.objects.filter(cuenta=obj, tipo=CREDITO).aggregate(Sum('importe'))[
            'importe__sum']
        try:
            return debito - credito
        except:
            return 0

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
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
        formset.save_m2m()



