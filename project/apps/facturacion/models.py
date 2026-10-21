from django.db import models


class ComprobanteVenta(models.Model):
    """Vínculo entre una Venta y el comprobante fiscal (factura electrónica ARCA) que le
    corresponde. No duplica datos de `afip.Receipt` -ahí vive el comprobante real: numeración,
    totales, CAE- esto sólo engancha ese Receipt con la Venta y lleva el estado de la emisión.

    La emisión no es automática al cobrar la venta (ver facturacion/services.py): si ARCA está
    caído no tiene que afectar el cobro, se reintenta después sobre este mismo registro.
    """

    PENDIENTE = 'pendiente'
    EMITIDO = 'emitido'
    ERROR = 'error'

    ESTADOS = (
        (PENDIENTE, 'Pendiente'),
        (EMITIDO, 'Emitido'),
        (ERROR, 'Error'),
    )

    venta = models.OneToOneField(
        'venta.Venta', on_delete=models.PROTECT, related_name='comprobante', verbose_name='Venta',
    )
    receipt = models.OneToOneField(
        'afip.Receipt', on_delete=models.PROTECT, null=True, blank=True,
        related_name='comprobante_venta', verbose_name='Comprobante ARCA',
    )
    estado = models.CharField(max_length=10, choices=ESTADOS, default=PENDIENTE, verbose_name='Estado')
    mensaje_error = models.TextField(blank=True, verbose_name='Mensaje de error')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name='Última actualización')

    class Meta:
        verbose_name = 'Comprobante de venta'
        verbose_name_plural = 'Comprobantes de venta'
        ordering = ['-id']

    def __str__(self):
        if self.receipt_id and self.receipt.receipt_number:
            return f'{self.receipt} (venta #{self.venta_id})'
        return f'Comprobante de venta #{self.venta_id} ({self.get_estado_display()})'
