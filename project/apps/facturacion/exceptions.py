"""Excepciones de negocio del dominio facturación, usadas por facturacion/services.py."""


class FacturacionError(Exception):
    """Base de errores de negocio de facturación."""


class SinConfiguracionAfipError(FacturacionError):
    """No hay un punto de venta de ARCA configurado todavía (TaxPayer/PointOfSales, se cargan
    desde /admin/afip/ una vez que el dueño tenga el CUIT, certificado y punto de venta
    habilitados en el sitio de ARCA)."""


class ComprobanteYaEmitidoError(FacturacionError):
    """La venta ya tiene un comprobante fiscal emitido, no se puede volver a facturar."""
