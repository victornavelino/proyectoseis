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
    # El signo va antes del '$' ("-$ 5.000,00", no "$ -5.000,00") -mismo criterio que
    # `formatearMonto` en frontend/src/features/ventas/dinero.ts (Intl con currency: 'ARS').
    # Hasta ahora todo lo que pasaba por acá era siempre positivo (montos de venta/caja); el
    # saldo de cuenta corriente (cuentacorriente/api.py) es el primer caso que puede ser negativo.
    signo = '-' if numero < 0 else ''
    entero, _, decimales = f'{abs(numero):,.2f}'.partition('.')
    return f'{signo}$ {entero.replace(",", ".")},{decimales}'
