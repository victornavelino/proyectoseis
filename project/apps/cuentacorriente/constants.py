DEBITO = 'D'
CREDITO = 'C'

TIPOS_MOVIMIENTO_CTA_CTE = (
    (DEBITO, 'Débito'),
    (CREDITO, 'Crédito'),
)

EFECTIVO = 'efectivo'
TRANSFERENCIA = 'transferencia'
QR = 'qr'

# Con qué pagó el cliente un Crédito (no aplica a un Débito: ahí no hay plata entrando, es un
# consumo a cuenta) -ver MovimientoCuentaCorriente.medio_pago.
MEDIOS_PAGO_CTA_CTE = (
    (EFECTIVO, 'Efectivo'),
    (TRANSFERENCIA, 'Transferencia'),
    (QR, 'QR'),
)
