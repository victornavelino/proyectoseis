"""Emisión de comprobantes fiscales (factura electrónica) para ARCA/AFIP, vía django-afip.

Por ahora sólo cubre el caso de un emisor Monotributo: Factura C, sin discriminar IVA (el
emisor no es responsable inscripto, así que `net_taxed` es igual al total y no se adjunta
ningún `Vat`). Las 3 instancias de este sistema (carnicería, verdulería, pollería) son
comercios chicos inscriptos en Monotributo -Responsable Inscripto (Factura A/B, con IVA
discriminado) queda pendiente para si hiciera falta más adelante.

La emisión es a demanda, no automática al cobrar la venta: si ARCA está caído no tiene que
afectar el cobro -se reintenta después llamando de nuevo a `generar_y_emitir_comprobante`
sobre la misma venta, que reutiliza el Receipt ya creado en vez de duplicarlo-.

IMPORTANTE: `Receipt.validate()` (django_afip) levanta RuntimeError si se la llama dentro de
una transacción -por eso nada de esta función corre dentro de `transaction.atomic`-.
"""
from django_afip.models import ConceptType, CurrencyType, DocumentType, PointOfSales, Receipt, ReceiptType

from facturacion.exceptions import ComprobanteYaEmitidoError, SinConfiguracionAfipError
from facturacion.models import ComprobanteVenta

CODIGO_CONCEPTO_PRODUCTOS = 1
CODIGO_DOCUMENTO_DNI = 96
CODIGO_MONEDA_PESOS = 'PES'
CODIGO_FACTURA_C = 11


def _obtener_punto_venta():
    punto_venta = PointOfSales.objects.filter(blocked=False).select_related('owner').first()
    if punto_venta is None:
        raise SinConfiguracionAfipError(
            'No hay un punto de venta de ARCA configurado. Cargá el TaxPayer (CUIT + '
            'certificado) y su punto de venta desde /admin/afip/.'
        )
    return punto_venta


def _obtener_o_crear_receipt(comprobante, venta):
    """Devuelve el Receipt a validar para este comprobante: el que ya tenía (reintento de un
    ERROR anterior) o uno nuevo armado a partir de la venta."""
    if comprobante.receipt_id:
        return comprobante.receipt

    punto_venta = _obtener_punto_venta()
    persona = venta.cliente.persona
    total = venta.monto - venta.descuento

    receipt = Receipt.objects.create(
        point_of_sales=punto_venta,
        receipt_type=ReceiptType.objects.get(code=CODIGO_FACTURA_C),
        concept=ConceptType.objects.get(code=CODIGO_CONCEPTO_PRODUCTOS),
        document_type=DocumentType.objects.get(code=CODIGO_DOCUMENTO_DNI),
        document_number=int(persona.documento_identidad),
        issued_date=venta.fecha.date(),
        total_amount=total,
        net_untaxed=0,
        net_taxed=total,
        exempt_amount=0,
        currency=CurrencyType.objects.get(code=CODIGO_MONEDA_PESOS),
    )
    comprobante.receipt = receipt
    comprobante.save(update_fields=['receipt'])
    return receipt


def generar_y_emitir_comprobante(venta):
    """Genera (si no existe) el ComprobanteVenta de `venta` y lo emite contra ARCA.

    Si ya hay un comprobante EMITIDO para esta venta, no se puede volver a facturar. Si el
    intento anterior quedó en ERROR, reintenta sobre el mismo Receipt ya creado.
    """
    comprobante, _ = ComprobanteVenta.objects.get_or_create(venta=venta)
    if comprobante.estado == ComprobanteVenta.EMITIDO:
        raise ComprobanteYaEmitidoError(f'La venta #{venta.pk} ya tiene un comprobante emitido.')

    receipt = _obtener_o_crear_receipt(comprobante, venta)

    # Cualquier falla de este paso -auth, validación, red, falla de ARCA- se guarda como ERROR
    # en vez de propagar: es la llamada a un servicio de terceros (WSAA/WSFEv1), y una caída de
    # ARCA no tiene que tirar abajo el endpoint que dispara la emisión. `receipt` ya quedó
    # creado y se reintenta sobre el mismo en la próxima llamada.
    try:
        errores = receipt.validate()
    except Exception as exc:
        comprobante.estado = ComprobanteVenta.ERROR
        comprobante.mensaje_error = str(exc)
        comprobante.save(update_fields=['estado', 'mensaje_error', 'fecha_actualizacion'])
        return comprobante

    if errores:
        comprobante.estado = ComprobanteVenta.ERROR
        comprobante.mensaje_error = '; '.join(errores)
    else:
        comprobante.estado = ComprobanteVenta.EMITIDO
        comprobante.mensaje_error = ''
    comprobante.save(update_fields=['estado', 'mensaje_error', 'fecha_actualizacion'])
    return comprobante
