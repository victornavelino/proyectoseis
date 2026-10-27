"""Operaciones de negocio transaccionales del dominio cuenta corriente, para
`cuentacorriente/api.py` y consumido también por `caja/services.py` al cobrar una venta con este
medio de pago (import diferido ahí, para evitar un ciclo caja <-> cuentacorriente).
"""
from django.db import transaction

from caja.exceptions import TopeCuentaCorrienteError
from cuentacorriente.constants import CREDITO, DEBITO
from cuentacorriente.models import CuentaCorriente, MovimientoCuentaCorriente
from cuentacorriente.utils import calcular_saldo_cc

DESCRIPCION_TIPO_INGRESO_CC = 'Pago de cuenta corriente'


@transaction.atomic
def crear_movimiento_cuenta_corriente(*, cuenta, tipo, importe, usuario, venta=None, observaciones=None, medio_pago=None):
    """Alta de un movimiento de cuenta corriente.

    La cuenta corriente funciona como una línea de crédito: el saldo (débitos - créditos) puede
    llegar hasta `cuenta.tope` en contra del cliente -no sólo gastar un saldo a favor ya
    cargado-, así que un Débito se valida contra ese tope (bloqueado con `select_for_update` para
    que dos movimientos simultáneos no superen juntos el tope aunque cada uno por separado
    pasara el chequeo).

    Un Crédito es plata real que el cliente puso en el mostrador -> además de anotarse acá,
    genera un Ingreso en la caja de la sucursal del usuario (ver `caja.services.crear_ingreso`);
    por eso cargar un crédito exige que haya una caja abierta, igual que cualquier otro ingreso
    (`CajaCerradaError`/`SinSucursalError` se propagan tal cual desde ahí). `medio_pago` (con qué
    pagó el cliente: efectivo/transferencia/QR) se exige en el serializer sólo para un Crédito
    -acá se guarda igual, por si se llama a esta función directo sin pasar por esa validación-;
    para un Débito se descarta, no tiene sentido (no es plata entrando).
    """
    cuenta = CuentaCorriente.objects.select_for_update().get(pk=cuenta.pk)

    if tipo == DEBITO:
        saldo_actual = calcular_saldo_cc(cuenta)
        disponible = cuenta.tope - saldo_actual
        if importe > disponible:
            raise TopeCuentaCorrienteError(
                f'El movimiento (${importe}) supera el disponible de la cuenta corriente '
                f'(${disponible}, sobre un tope de ${cuenta.tope}).'
            )

    movimiento = MovimientoCuentaCorriente.objects.create(
        cuenta=cuenta, tipo=tipo, importe=importe, usuario=usuario, venta=venta, observaciones=observaciones,
        medio_pago=medio_pago if tipo == CREDITO else None,
    )

    if tipo == CREDITO:
        from caja.models import TipoIngreso  # import diferido: evita ciclo caja <-> cuentacorriente
        from caja.services import crear_ingreso

        tipo_ingreso, _ = TipoIngreso.objects.get_or_create(descripcion=DESCRIPCION_TIPO_INGRESO_CC)
        crear_ingreso(
            usuario=usuario, tipo_ingreso=tipo_ingreso,
            concepto=(observaciones or DESCRIPCION_TIPO_INGRESO_CC)[:30], importe=importe,
        )

    return movimiento
