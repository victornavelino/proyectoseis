from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter(name='moneda')
def moneda(valor):
    """Formatea un monto en pesos: separador de miles '.', decimales ',' — mismo criterio que
    `formatearMonto` en frontend/src/features/ventas/dinero.ts. Valores no numéricos (p. ej. el
    '--' que usa venta.api cuando el cliente no tiene cuenta corriente) se devuelven sin tocar."""
    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        return valor
    entero, _, decimales = f'{numero:,.2f}'.partition('.')
    return f'$ {entero.replace(",", ".")},{decimales}'
