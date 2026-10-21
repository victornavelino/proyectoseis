from django.contrib import admin, messages

from facturacion.exceptions import FacturacionError
from facturacion.models import ComprobanteVenta
from facturacion.services import generar_y_emitir_comprobante


@admin.register(ComprobanteVenta)
class ComprobanteVentaAdmin(admin.ModelAdmin):
    list_display = ('venta', 'estado', 'receipt', 'fecha_actualizacion')
    list_filter = ('estado',)
    search_fields = ('venta__numero_ticket',)
    readonly_fields = ('venta', 'receipt', 'estado', 'mensaje_error', 'fecha_creacion', 'fecha_actualizacion')
    list_per_page = 30
    actions = ['emitir_comprobantes']

    @admin.action(description='Emitir (o reintentar) comprobante ARCA')
    def emitir_comprobantes(self, request, queryset):
        emitidos, errores = 0, 0
        for comprobante in queryset:
            try:
                resultado = generar_y_emitir_comprobante(comprobante.venta)
            except FacturacionError as exc:
                self.message_user(request, f'Venta #{comprobante.venta_id}: {exc}', level=messages.ERROR)
                continue
            if resultado.estado == ComprobanteVenta.EMITIDO:
                emitidos += 1
            else:
                errores += 1
                self.message_user(
                    request, f'Venta #{comprobante.venta_id}: {resultado.mensaje_error}', level=messages.WARNING,
                )
        if emitidos:
            self.message_user(request, f'Se emitieron {emitidos} comprobante(s).')
        if errores:
            self.message_user(request, f'{errores} comprobante(s) quedaron en error (revisá el detalle arriba).', level=messages.WARNING)

    def has_add_permission(self, request):
        # Se crean sólo desde el service (generar_y_emitir_comprobante), nunca a mano.
        return False
