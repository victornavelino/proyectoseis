"""Operaciones de negocio transaccionales del dominio cuenta corriente, para
`cuentacorriente/api.py` y consumido también por `caja/services.py` al cobrar una venta con este
medio de pago (import diferido ahí, para evitar un ciclo caja <-> cuentacorriente).
"""
from django.db import transaction

from caja.exceptions import TopeCuentaCorrienteError
from cuentacorriente.constants import CREDITO, DEBITO, EFECTIVO, QR, TRANSFERENCIA
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

    Un Crédito es plata real que el cliente puso en el mostrador -> además de anotarse acá, deja
    un movimiento en la caja de la sucursal del usuario, con la MISMA lógica que un pago de venta
    (ver `caja.services.cobrar_venta`): si fue en `efectivo`, un `Ingreso` (plata física, cuenta
    para el arqueo); si fue por `transferencia`/`qr`, un `PagoTransferencia`/`PagoQr` -esos NO
    tocan el efectivo de caja (no heredan de `MovimientoCaja`), así que no se mezclan con los
    billetes reales ni hacen falta en el arqueo, y en el cierre quedan en TOTAL TRANSFERENCIA/
    TOTAL QR, no en "Ingresos" (antes todo crédito -sin importar el medio- caía como Ingreso
    genérico, inflando el efectivo esperado con plata que en realidad nunca pisó el cajón).
    Por eso cargar un crédito exige que haya una caja abierta en cualquier caso, igual que
    cualquier otro cobro (`CajaCerradaError`/`SinSucursalError` se propagan tal cual desde ahí).
    `medio_pago` se exige en el serializer sólo para un Crédito; para un Débito se descarta, no
    tiene sentido (no es plata entrando).
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
        _registrar_cobro_en_caja(cuenta=cuenta, importe=importe, usuario=usuario, medio_pago=medio_pago, observaciones=observaciones)

    return movimiento


def _registrar_cobro_en_caja(*, cuenta, importe, usuario, medio_pago, observaciones):
    # import diferido: evita ciclo caja <-> cuentacorriente (caja.services importa
    # cuentacorriente.services para el lado Débito de cobrar_venta).
    from caja.models import PagoQr, PagoTransferencia, TipoIngreso
    from caja.services import _caja_abierta_de, crear_ingreso

    # Hace falta caja abierta para CUALQUIER medio, no sólo efectivo -mismo criterio que un
    # cobro de venta-: PagoTransferencia/PagoQr no tienen FK a Caja (se ubican por fecha, igual
    # que al cobrar una venta), pero igual tiene que haber una caja de la sucursal abierta en
    # este momento para que el movimiento quede dentro de algún cierre.
    _caja_abierta_de(usuario.sucursal)

    persona = cuenta.cliente.persona
    concepto = (observaciones or DESCRIPCION_TIPO_INGRESO_CC)[:30]

    # medio_pago en None cubre datos viejos (créditos cargados antes de que este campo
    # existiera): se tratan como efectivo, que era el único comportamiento que había.
    if medio_pago == TRANSFERENCIA:
        PagoTransferencia.objects.create(
            importe=importe, nombre=persona.nombre, apellido=persona.apellido,
            documento_identidad=persona.documento_identidad, observaciones=observaciones,
        )
    elif medio_pago == QR:
        PagoQr.objects.create(
            importe=importe, nombre=persona.nombre, apellido=persona.apellido,
            documento_identidad=persona.documento_identidad, observaciones=observaciones,
        )
    else:
        assert medio_pago in (EFECTIVO, None)
        tipo_ingreso, _ = TipoIngreso.objects.get_or_create(descripcion=DESCRIPCION_TIPO_INGRESO_CC)
        crear_ingreso(usuario=usuario, tipo_ingreso=tipo_ingreso, concepto=concepto, importe=importe)
