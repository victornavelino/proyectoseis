"""Operaciones de negocio transaccionales del dominio caja, para los endpoints DRF nuevos
(caja/api.py). No tocan el flujo legacy (caja/views.py `cobrar_ticket`/`cerrar_caja`, admin
actions) — conviven (DEC-001) hasta que React reemplace esas pantallas.
"""
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone

from caja.exceptions import (
    CajaCerradaError,
    CajaYaAbiertaError,
    CajaYaCerradaError,
    SinCuentaCorrienteError,
    SinSucursalError,
    TopeCuentaCorrienteError,
    TotalPagosNoCoincideError,
    VentaAnuladaError,
    VentaFueraDeCajaError,
    VentaYaCobradaError,
    VentasSinCobrarError,
)
from caja.constants import INGRESO
from caja.models import Caja, CobroVenta, CuponPagoTarjeta, PagoTransferencia
from caja.utils import calcular_caja_final
from cuentacorriente.constants import DEBITO
from cuentacorriente.models import CuentaCorriente, MovimientoCuentaCorriente
from cuentacorriente.utils import calcular_saldo_cc
from venta.models import Venta

CENTAVO = Decimal('0.01')


def _caja_abierta_de(sucursal):
    if sucursal is None:
        raise SinSucursalError('El usuario no tiene una sucursal asignada.')
    caja_abierta = Caja.objects.filter(
        sucursal=sucursal, fecha_fin__isnull=True, fecha_inicio__isnull=False
    ).last()
    if not caja_abierta:
        raise CajaCerradaError('La caja de la sucursal está cerrada.')
    return caja_abierta


@transaction.atomic
def abrir_caja(*, usuario):
    sucursal = usuario.sucursal
    if sucursal is None:
        raise SinSucursalError('El usuario no tiene una sucursal asignada.')
    if Caja.objects.filter(sucursal=sucursal, fecha_fin__isnull=True, fecha_inicio__isnull=False).exists():
        raise CajaYaAbiertaError('Ya existe una caja abierta para esta sucursal.')
    ultima_cerrada = Caja.objects.filter(sucursal=sucursal, fecha_fin__isnull=False).order_by('-fecha_fin').first()
    caja_inicial = ultima_cerrada.caja_final if ultima_cerrada else Decimal('0')
    return Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=caja_inicial)


@transaction.atomic
def cerrar_caja(caja):
    if caja.fecha_fin:
        raise CajaYaCerradaError('Esta caja ya está cerrada.')
    # A diferencia del legacy (`caja.views.cerrar_caja` y `CajaAdmin.cerrar_caja`, que cuentan
    # TODAS las ventas sin cobrar del sistema sin filtrar por sucursal — SISTEMA_ACTUAL.md
    # §15.9), acá sólo se controlan las de la sucursal de esta caja.
    ventas_sin_cobrar = Venta.objects.filter(sucursal=caja.sucursal, cobrada=False, anulado=False).count()
    if ventas_sin_cobrar:
        raise VentasSinCobrarError(
            f'Hay {ventas_sin_cobrar} venta(s) sin cobrar en esta sucursal, no se puede cerrar la caja.'
        )
    caja.fecha_fin = timezone.now()
    caja.caja_final = calcular_caja_final(caja)
    caja.save(update_fields=['fecha_fin', 'caja_final'])
    caja.refresh_from_db()
    return caja


def _total(pagos):
    total = Decimal('0')
    for pago in pagos:
        total += pago['importe']
    return total


@transaction.atomic
def cobrar_venta(*, venta, pagos_efectivo, pagos_tarjeta, pagos_cuenta_corriente, pagos_transferencia, usuario):
    """Cobro combinado de una venta (efectivo + tarjeta + cuenta corriente + transferencia en la
    misma operación), reemplazando a `caja.views.cobrar_ticket` para el endpoint DRF nuevo.

    Dos correcciones deliberadas respecto al legacy, sólo en este flujo nuevo:
    1. La venta sólo se marca `cobrada=True` si TODOS los medios de pago se registraron sin
       error — el legacy la marcaba cobrada incluso si alguno fallaba a mitad de camino
       (comentario del propio equipo en el código, SISTEMA_ACTUAL.md §15.12). Acá, al estar todo
       dentro de `transaction.atomic()`, un error en cualquier pago revierte TODO (incluida la
       venta no queda marcada cobrada).
    2. La suma de los medios de pago debe cubrir EXACTAMENTE `venta.monto` — el legacy nunca
       validaba esto. El recargo de tarjeta no cuenta para este total (es un costo financiero
       aparte, no parte del precio de la venta).
    """
    sucursal = usuario.sucursal
    caja_abierta = _caja_abierta_de(sucursal)

    if venta.anulado:
        raise VentaAnuladaError('La venta está anulada, no se puede cobrar.')
    if venta.cobrada:
        raise VentaYaCobradaError('La venta ya fue cobrada.')
    if caja_abierta.fecha_inicio > venta.fecha:
        raise VentaFueraDeCajaError('La venta es anterior a la apertura de la caja actual.')

    total_pagado = (
        _total(pagos_efectivo) + _total(pagos_tarjeta) + _total(pagos_cuenta_corriente) + _total(pagos_transferencia)
    )
    if total_pagado != venta.monto:
        raise TotalPagosNoCoincideError(
            f'La suma de los medios de pago (${total_pagado}) no coincide con el monto de la '
            f'venta (${venta.monto}).'
        )

    try:
        for pago in pagos_efectivo:
            CobroVenta.objects.create(
                usuario=usuario, importe=pago['importe'], sucursal=sucursal, caja=caja_abierta,
                tipo=INGRESO, venta=venta,
            )

        for pago in pagos_tarjeta:
            plan = pago['plan_tarjeta']
            # Recargo recalculado en servidor a partir del interés del plan — el legacy
            # aceptaba `recargo`/`importe_con_recargo` tal cual venían del frontend
            # (SISTEMA_ACTUAL.md §15.5).
            recargo = (pago['importe'] * plan.interes / 100).quantize(CENTAVO, rounding=ROUND_HALF_UP)
            importe_con_recargo = pago['importe'] + recargo
            CuponPagoTarjeta.objects.create(
                cliente=venta.cliente, plan_tarjeta=plan, numero_tarjeta=pago.get('numero_tarjeta') or None,
                importe=pago['importe'], recargo=recargo, importe_con_recargo=importe_con_recargo,
                numero_cupon=pago.get('numero_cupon'), lote=pago.get('lote'), venta=venta,
                observaciones=pago.get('observaciones'),
            )

        for pago in pagos_cuenta_corriente:
            cuenta = CuentaCorriente.objects.filter(cliente=venta.cliente, activa=True).first()
            if cuenta is None:
                raise SinCuentaCorrienteError('El cliente no tiene una cuenta corriente activa.')
            saldo_actual = calcular_saldo_cc(cuenta)
            if cuenta.tope and (saldo_actual + pago['importe']) > cuenta.tope:
                raise TopeCuentaCorrienteError(
                    f"El pago a cuenta corriente supera el tope (tope: {cuenta.tope}, "
                    f"saldo actual: {saldo_actual})."
                )
            MovimientoCuentaCorriente.objects.create(
                cuenta=cuenta, importe=pago['importe'], tipo=DEBITO, venta=venta,
                observaciones=pago.get('observaciones'), usuario=usuario,
            )

        for pago in pagos_transferencia:
            PagoTransferencia.objects.create(
                importe=pago['importe'], nombre=pago.get('nombre'), apellido=pago.get('apellido'),
                documento_identidad=pago['documento_identidad'], banco=pago.get('banco'), venta=venta,
                observaciones=pago.get('observaciones'),
            )
    except DjangoValidationError as exc:
        # MovimientoCaja.clean() (base de CobroVenta) puede rechazar el movimiento si algo más
        # falla pese a haber una caja abierta para la sucursal (el problema de fondo —tomar la
        # caja de la sucursal equivocada— ya se corrigió a nivel modelo, SISTEMA_ACTUAL.md
        # §15.8; esto es sólo una red de seguridad por si acaso).
        raise CajaCerradaError('No se pudo registrar el cobro en caja: ' + '; '.join(exc.messages))

    venta.cobrada = True
    venta.save(update_fields=['cobrada'])
    return venta
