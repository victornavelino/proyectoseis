import decimal
from decimal import Decimal
import json
from django.db.models import Sum
from caja.constants import INGRESO, EGRESO
from caja.models import MovimientoCaja, CobroVenta, Caja, PagoTransferencia, PlanTarjetaDeCredito, CuponPagoTarjeta, TipoIngreso, Ingreso, \
    Sueldo, Adelanto, RetiroEfectivo, Gasto
from cuentacorriente.constants import DEBITO, CREDITO
from cuentacorriente.models import CuentaCorriente, MovimientoCuentaCorriente
from venta.models import Venta



def calcular_caja_final(caja):
    ingreso_caja = Decimal(0.0)
    egreso_caja = Decimal(0.0)
    saldo_caja = Decimal(0.0)
    movimientos_ingreso = MovimientoCaja.objects.filter(caja_id=caja.id, tipo=INGRESO)
    for i in movimientos_ingreso:
        ingreso_caja = ingreso_caja + i.importe
        i.cerrado = True
        i.save()
    movimientos_egreso = MovimientoCaja.objects.filter(caja_id=caja.id, tipo=EGRESO)
    for e in movimientos_egreso:
        egreso_caja = egreso_caja + e.importe
        e.cerrado = True
        e.save()
    saldo_caja = caja.caja_inicial + ingreso_caja - egreso_caja
    return saldo_caja


def calcular_saldo_caja(caja):
    ingreso_caja = decimal.Decimal(0.0)
    egreso_caja = decimal.Decimal(0.0)
    saldo_caja = decimal.Decimal(0.0)
    movimientos_ingreso = MovimientoCaja.objects.filter(caja_id=caja.id, tipo=INGRESO)
    for i in movimientos_ingreso:
        ingreso_caja = ingreso_caja + i.importe

    movimientos_egreso = MovimientoCaja.objects.filter(caja_id=caja.id, tipo=EGRESO)
    for e in movimientos_egreso:
        egreso_caja = egreso_caja + e.importe
    saldo_caja = caja.caja_inicial + ingreso_caja - egreso_caja
    return saldo_caja


def guardar_movimiento_cobro_venta(pago_efectivo, numero_ticket, usuario, sucursal):
    caja_abierta = Caja.objects.filter(sucursal=sucursal, fecha_fin__isnull=True,
                                       fecha_inicio__isnull=False).last()
    total_efectivo = pago_efectivo['importe']
    venta = Venta.objects.get(numero_ticket=numero_ticket)
    cobro_venta = CobroVenta.objects.create(usuario=usuario, importe=total_efectivo, sucursal=sucursal,
                                            caja=caja_abierta, tipo=INGRESO, venta=venta)
    cobro_venta.refresh_from_db()
    return cobro_venta


def guardar_cupon_tarjeta(pago_tarjeta, numero_ticket, usuario, sucursal):
    id_plan_tarjeta = pago_tarjeta['plan_tarjeta']
    nro_tarjeta = pago_tarjeta['nro_tarjeta']
    if not nro_tarjeta:
        nro_tarjeta = 0

    importe = pago_tarjeta['importe']
    recargo = pago_tarjeta['recargo']
    importe_con_recargo = pago_tarjeta['importe_con_recargo']
    nro_cupon = pago_tarjeta['nro_cupon']
    nro_lote = pago_tarjeta['nro_lote']
    observaciones = pago_tarjeta['observaciones']
    plan_tarjeta = PlanTarjetaDeCredito.objects.get(pk=id_plan_tarjeta)
    venta = Venta.objects.get(numero_ticket=numero_ticket)
    # CREAMOS EL REGISTRO EN LA BASE
    cupon_tarjeta = CuponPagoTarjeta.objects.create(cliente=venta.cliente, plan_tarjeta=plan_tarjeta,
                                                    numero_tarjeta=nro_tarjeta,
                                                    importe=importe, recargo=recargo,
                                                    importe_con_recargo=importe_con_recargo,
                                                    numero_cupon=nro_cupon, lote=nro_lote, venta=venta,
                                                    observaciones=observaciones)
    cupon_tarjeta.refresh_from_db()
    return cupon_tarjeta

def guardar_cupon_transferencia(pago_transferencia, numero_ticket):
    
    nombre = pago_transferencia['nombre']
    apellido = pago_transferencia['apellido']
    importe = pago_transferencia['importe']
    documento = pago_transferencia['documento']
    banco = pago_transferencia['banco']
    observaciones = pago_transferencia['observaciones']
    venta = Venta.objects.get(numero_ticket=numero_ticket)
    # CUPON TRANSFERENCIA
    transferencia = PagoTransferencia.objects.create(importe=importe, nombre=nombre, apellido=apellido, documento_identidad=documento,
                                                     banco=banco, venta=venta, observaciones=observaciones)
    transferencia.refresh_from_db()
    return transferencia



def calcular_ingresos_caja(caja):
    results = []
    total_ingreso_ventas = CobroVenta.objects.filter(caja=caja, tipo=INGRESO).aggregate(Sum('importe'))[
                               'importe__sum'] or 0.00
    json_valores = {
        "concepto": "Ventas",
        "importe": str(total_ingreso_ventas)
    }
    results.append(json_valores)
    #######
    total_ingreso_cobranza_cc = MovimientoCuentaCorriente.objects.filter(
        fecha__gte=caja.fecha_inicio,
        fecha__lte=caja.fecha_fin, tipo=CREDITO).aggregate(
        Sum('importe'))['importe__sum'] or 0.00
    json_valores = {
        "concepto": "Cobranzas Cta Corriente",
        "importe": str(total_ingreso_cobranza_cc)
    }
    results.append(json_valores)
    #########
    total_ingreso_varios = Ingreso.objects.filter(caja=caja, tipo=INGRESO).aggregate(Sum('importe'))[
                               'importe__sum'] or 0.00
    json_valores = {
        "concepto": "Ingresos Varios",
        "importe": str(total_ingreso_varios)
    }
    results.append(json_valores)
    ## GENERAMOS JSON ingresos
    ingresos = json.dumps(results)
    ingresos = json.loads(ingresos)
    return ingresos


def calcular_total_ingresos(caja):
    ingreso_caja = Decimal(0.0)
    total_movimientos_ingreso = MovimientoCaja.objects.filter(caja=caja, tipo=INGRESO).aggregate(Sum('importe'))[
                               'importe__sum'] or Decimal(0.0)

    #for i in movimientos_ingreso:
    #    ingreso_caja = ingreso_caja + i.importe
    ###le sumamos los ingreso por credito en CC
    total_ingreso_cobranza_cc = MovimientoCuentaCorriente.objects.filter(
        fecha__gte=caja.fecha_inicio,
        fecha__lte=caja.fecha_fin, tipo=CREDITO).aggregate(
        Sum('importe'))['importe__sum'] or Decimal(0.0)
    ingreso_caja = total_ingreso_cobranza_cc + total_movimientos_ingreso
    json_valores = {
        "concepto": "TOTAL INGRESOS",
        "importe": str(ingreso_caja)
    }
    total_ingreso = json.dumps(json_valores)
    total_ingreso = json.loads(total_ingreso)
    return total_ingreso


def calcular_egresos_caja(caja):
    results = []
    total_egreso_sueldos = Sueldo.objects.filter(caja=caja, tipo=EGRESO).aggregate(Sum('importe'))[
                               'importe__sum'] or 0.00
    json_valores = {
        'concepto': 'Sueldos',
        'importe': str(total_egreso_sueldos)
    }
    results.append(json_valores)
    total_egreso_adelantos = Adelanto.objects.filter(caja=caja, tipo=EGRESO).aggregate(Sum('importe'))[
                               'importe__sum'] or 0.00
    json_valores = {
        'concepto': 'Adelantos',
        'importe': str(total_egreso_adelantos)
    }
    results.append(json_valores)
    total_egreso_retiroefectivo = RetiroEfectivo.objects.filter(caja=caja, tipo=EGRESO).aggregate(Sum('importe'))[
                               'importe__sum'] or 0.00
    json_valores = {
        'concepto': 'Retiros Efectivo',
        'importe': str(total_egreso_retiroefectivo)
    }
    results.append(json_valores)
    total_egreso_gastos = Gasto.objects.filter(caja=caja, tipo=EGRESO).aggregate(Sum('importe'))[
                               'importe__sum'] or 0.00
    json_valores = {
        'concepto': 'Gastos',
        'importe': str(total_egreso_gastos)
    }
    results.append(json_valores)
    ## GENERAMOS JSON ingresos
    egresos = json.dumps(results)
    egresos = json.loads(egresos)
    return egresos


def calcular_total_egresos(caja):
    egreso_caja = Decimal(0.0)
    total_movimientos_egreso = MovimientoCaja.objects.filter(caja=caja, tipo=EGRESO).aggregate(Sum('importe'))[
                               'importe__sum'] or 0.00

    #for egreso in movimientos_egreso:
    #    egreso_caja = egreso_caja + egreso.importe
    json_valores = {
        "concepto": "TOTAL EGRESOS",
        "importe": str(total_movimientos_egreso)
    }
    total_egreso = json.dumps(json_valores)
    total_egreso = json.loads(total_egreso)
    return total_egreso

def calcular_total_compras_cc(caja):

    total_compras_cc = MovimientoCuentaCorriente.objects.filter(
        fecha__gte=caja.fecha_inicio,
        fecha__lte=caja.fecha_fin, tipo=DEBITO).aggregate(
        Sum('importe'))['importe__sum'] or 0.00

    json_valores = {
        "concepto": "TOTAL C.CORRIENTE",
        "importe": str(total_compras_cc)
    }
    total = json.dumps(json_valores)
    total = json.loads(total)
    return total

def calcular_total_compras_transf(caja):

    total_compras_transf = PagoTransferencia.objects.filter(
        fecha__gte=caja.fecha_inicio,
        fecha__lte=caja.fecha_fin).aggregate(
        Sum('importe'))['importe__sum'] or 0.00
    json_valores = {
        "concepto": "TOTAL TRANSFERENCIA",
        "importe": str(total_compras_transf)
    }
    total = json.dumps(json_valores)
    total = json.loads(total)
    return total
