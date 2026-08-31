"""Excepciones de negocio del dominio caja, usadas por caja/services.py (endpoints DRF nuevos).

No reemplazan el manejo de errores del flujo legacy (caja/views.py), que sigue devolviendo sus
propios dict de error tal cual estaba.
"""


class CajaError(Exception):
    """Base de errores de negocio de caja."""


class SinSucursalError(CajaError):
    """El usuario autenticado no tiene una sucursal asignada."""


class CajaCerradaError(CajaError):
    """No hay una caja abierta en la sucursal."""


class CajaYaAbiertaError(CajaError):
    """Ya existe una caja abierta para la sucursal, no se puede abrir otra."""


class CajaYaCerradaError(CajaError):
    """La caja ya estaba cerrada."""


class VentasSinCobrarError(CajaError):
    """Hay ventas sin cobrar en la sucursal, no se puede cerrar la caja."""


class VentaAnuladaError(CajaError):
    """La venta está anulada, no se puede cobrar."""


class VentaYaCobradaError(CajaError):
    """La venta ya fue cobrada."""


class VentaFueraDeCajaError(CajaError):
    """La venta es anterior a la apertura de la caja actual."""


class TotalPagosNoCoincideError(CajaError):
    """La suma de los medios de pago no cubre exactamente el monto de la venta."""


class SinCuentaCorrienteError(CajaError):
    """El cliente no tiene una cuenta corriente activa para pagar con ese medio."""


class TopeCuentaCorrienteError(CajaError):
    """El pago a cuenta corriente supera el tope de la cuenta."""
