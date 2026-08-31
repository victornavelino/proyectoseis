"""Excepciones de negocio del dominio venta, usadas por venta/services.py (endpoint DRF nuevo).

No reemplazan ni tocan el manejo de errores del flujo legacy (venta/views.py), que sigue
devolviendo sus propios dict de error tal cual estaba.
"""


class VentaError(Exception):
    """Base de errores de negocio de venta."""


class SinSucursalError(VentaError):
    """El usuario autenticado no tiene una sucursal asignada."""


class CajaCerradaError(VentaError):
    """No hay una caja abierta en la sucursal, no se pueden registrar/cobrar ventas."""


class ArticuloSinPrecioError(VentaError):
    """El artículo no tiene precio cargado para la lista de precios del cliente en la sucursal."""

    def __init__(self, articulo):
        self.articulo = articulo
        super().__init__(
            f"El artículo '{articulo.codigo}' no tiene precio para la lista de precios del "
            f"cliente en esta sucursal."
        )


class VentaYaAnuladaError(VentaError):
    """La venta ya estaba anulada."""


class VentaYaCobradaError(VentaError):
    """La venta ya fue cobrada: anularla implica revertir cobros/cupones ya generados, una
    decisión de negocio todavía no definida (ver DECISIONES.md PEND-J) — este endpoint, por
    ahora, sólo permite anular ventas no cobradas."""
