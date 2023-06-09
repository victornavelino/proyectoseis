import decimal
from decimal import Decimal

from caja.constants import INGRESO, EGRESO
from caja.models import MovimientoCaja, CobroVenta, Caja, PlanTarjetaDeCredito, CuponPagoTarjeta, TipoIngreso, Ingreso
from cuentacorriente.constants import DEBITO, CREDITO
from cuentacorriente.models import CuentaCorriente, MovimientoCuentaCorriente
from venta.models import Venta


def guardar_pago_ccorriente(pago_ccorriente, numero_ticket, usuario):
    venta = Venta.objects.get(numero_ticket=numero_ticket)
    importe = pago_ccorriente['importe']
    observaciones = pago_ccorriente['observaciones']
    cuenta = CuentaCorriente.objects.filter(cliente=venta.cliente).first()
    ccorriente = MovimientoCuentaCorriente.objects.create(cuenta=cuenta, importe=importe, tipo=DEBITO, venta=venta,
                                                          observaciones=observaciones, usuario=usuario)
    ccorriente.refresh_from_db()
    return ccorriente


def cobrar_ccorriente(cliente, importe, observaciones, usuario, caja):
    cuenta = CuentaCorriente.objects.filter(cliente=cliente).first()
    ccorriente = MovimientoCuentaCorriente.objects.create(cuenta=cuenta, importe=importe, tipo=CREDITO,
                                                          observaciones=observaciones, usuario=usuario)
    tipo_ingreso, created = TipoIngreso.objects.get_or_create(descripcion='Pago de cuenta corriente')

    Ingreso.objects.create(tipo_ingreso=tipo_ingreso, tipo=INGRESO, concepto=observaciones, importe=importe,
                           sucursal=usuario.sucursal, caja=caja, usuario=usuario)
    ccorriente.refresh_from_db()
    return ccorriente
