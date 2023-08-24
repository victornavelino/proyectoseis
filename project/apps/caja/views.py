from datetime import datetime

from IPython.utils.path import target_update
from django.contrib import messages
from django.core import serializers
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import render
import json

from django.template import loader, RequestContext
from django.views import View

from caja.constants import INGRESO
# Create your views here.
from caja.models import PlanTarjetaDeCredito, Caja, MovimientoCaja, CobroVenta, Ingreso
from caja.utils import guardar_movimiento_cobro_venta, guardar_cupon_tarjeta, calcular_ingresos_caja, \
    calcular_total_ingresos, calcular_egresos_caja, calcular_total_egresos, calcular_total_compras_cc
from cuentacorriente.constants import CREDITO
from cuentacorriente.models import MovimientoCuentaCorriente
from cuentacorriente.utils import guardar_pago_ccorriente
from venta.models import Venta
from wkhtmltopdf.views import PDFTemplateResponse


def planes_tarjeta(request, pk_tarjeta):
    if request.user.is_authenticated:
        planes = PlanTarjetaDeCredito.objects.filter(tarjeta_id=pk_tarjeta)
        results = []
        for plan in planes:
            json_valores = {
                "id": str(plan.pk),
                "nombre_plan": plan.nombre_plan,
                "interes": str(plan.interes)
            }
            results.append(json_valores)
        data = json.dumps(results)
    else:
        valores = {}
        data = serializers.serialize('json', valores)
    return HttpResponse(data, content_type="application/json")

def plan_tarjeta(request, id_plan_tarjeta):
    if request.user.is_authenticated:
        plan = PlanTarjetaDeCredito.objects.get(pk=id_plan_tarjeta)
        if plan:
            json_valores = {
                "id": str(plan.pk),
                "nombre_plan": plan.nombre_plan,
                "interes": str(plan.interes)
            }           
            data = json.dumps(json_valores)
        else:
            valores = {}
            data = serializers.serialize('json', valores)
    else:
        valores = {}
        data = serializers.serialize('json', valores)
    return HttpResponse(data, content_type="application/json")

def cobrar_ticket(request):
    if request.user.is_authenticated:
        caja_abierta = Caja.objects.filter(sucursal=request.user.sucursal, fecha_fin__isnull=True,
                                           fecha_inicio__isnull=False).last()
        json_data = json.loads(request.body)
        pagos = json_data['pagos']
        numero_ticket = pagos['nroticket']
        venta = Venta.objects.get(numero_ticket=numero_ticket)
        print('ventaaaa obtenida')
        print(venta)
        if caja_abierta:
            if request.method == 'POST' and caja_abierta.fecha_inicio <= venta.fecha:
                try:
                    print('entro try')
                    # json_data = json.loads(request.body)
                    total_efectivo = 0
                    total_tarjeta = 0
                    total_ccorriente = 0
                    # pagos = json_data['pagos']
                    # numero_ticket = pagos['nroticket']
                    lista_pagos = pagos['pagos']
                    lista_pagos_efectivo = pagos['pagosEfectivo']
                    lista_pagos_tarjeta = pagos['pagosTarjeta']
                    lista_pagos_ccorriente = pagos['pagosCCorriente']
                    data = {'numero_cobro': numero_ticket}
                    for pago in lista_pagos:
                        if pago['tipo_de_pago'] == 'EFECTIVO':
                            total_efectivo += float(pago['monto_total'])
                        if pago['tipo_de_pago'] == 'TARJETA':
                            total_tarjeta += float(pago['monto_total'])
                        if pago['tipo_de_pago'] == 'CCORRIENTE':
                            total_ccorriente += float(pago['monto_total'])
                    # EFECTIVO
                    if lista_pagos_efectivo:
                        for pago_efectivo in lista_pagos_efectivo:
                            try:
                                print("entro cobrar efectivo")
                                cobro_venta = guardar_movimiento_cobro_venta(pago_efectivo, numero_ticket, request.user,
                                                                             request.user.sucursal)
                                print(cobro_venta.pk)
                            except ValidationError:
                                data = {'error': 'No se puede cobrar ticket la Caja esta Cerrada XD'}
                    # PAGOS TARJETA
                    if lista_pagos_tarjeta:
                        for pago_tarjeta in lista_pagos_tarjeta:
                            try:
                                cupon_tarjeta = guardar_cupon_tarjeta(pago_tarjeta, numero_ticket, request.user,
                                                                      request.user.sucursal)
                                print("lista tarjeta con datos")
                                print(cupon_tarjeta.pk)
                            except ValidationError:
                                data = {'error': 'Datos erroneos'}
                    else:
                        print("lista tarjeta sin datos")

                    # PAGOS CUENTA CORRIENTE
                    if lista_pagos_ccorriente:
                        for pago_ccorriente in lista_pagos_ccorriente:
                            try:
                                ccorriente = guardar_pago_ccorriente(pago_ccorriente, numero_ticket,
                                                                     request.user)
                                print(lista_pagos_ccorriente)
                            except ValidationError:
                                data = {'error': 'Datos erroneos'}
                    else:
                        print('lista_pagos_ccorriente vacia')
                    # REVISAR BIEN PORQUE LO MISMO LA SETEA COMO COBRADA CUANDO
                    # NO SE LA COBRO POR UN ERROR DE VALIDACION
                    venta = Venta.objects.get(numero_ticket=numero_ticket)
                    venta.cobrada = True
                    venta.save()
                    data = json.dumps(data)
                except ValidationError:
                    print('entro except')
            else:
                messages.error(request, 'La venta posee Fecha anterior a la caja')
                data = {'error': ' Venta fuera de caja'}
                data = json.dumps(data)
        else:
            messages.error(request, 'La caja esta Cerrada, no se pueden Cobrar Ventas')
            data = {'error': ' La caja esta cerrada'}
            data = json.dumps(data)
    else:
        valores = {}
        data = serializers.serialize('json', valores)
    return HttpResponse(data, content_type="application/json")


def cerrar_caja(request):
    if request.user.is_authenticated:
        caja_abierta = Caja.objects.filter(sucursal=request.user.sucursal, fecha_fin__isnull=True,
                                           fecha_inicio__isnull=False).last()
        if caja_abierta:
            print("cerrando caja")
            print(datetime.today())
            json_data = json.loads(request.body)
            id_caja = json_data['id_caja']
            caja_final = json_data['caja_final']
            caja = Caja.objects.get(pk=id_caja)
            caja.caja_final = float(caja_final)
            caja.fecha_fin = datetime.today()
            caja.save()
            caja.refresh_from_db()
            data = {'data': 'CERRADA'}
            data = json.dumps(data)
        else:
            data = {'error': ' La caja esta cerrada'}
            data = json.dumps(data)
        return HttpResponse(data, content_type="application/json")


def imprimir_cierre_caja_pdf(request, id_caja):
    if request.user.is_authenticated:
        print('entro imprimir cierre pdf')
        caja = Caja.objects.get(pk=id_caja)
        nombre_archivo = "caja-" + str(caja.fecha_fin) + ".pdf"
        response = PDFTemplateResponse(request=request,
                                       template='admin/caja/ticket_cierre_caja.html',
                                       filename=nombre_archivo,
                                       context={'caja': caja,
                                                'ingresos': calcular_ingresos_caja(caja),
                                                'total_ingresos': calcular_total_ingresos(caja),
                                                'egresos': calcular_egresos_caja(caja),
                                                'total_egresos': calcular_total_egresos(caja),
                                                'total_ccorrientes': calcular_total_compras_cc(caja)},
                                       show_content_in_browser=False,
                                       cmd_options={'margin-top': 50, },
                                       )
        return response


def imprimir_cierre_caja(request, id_caja):
    if request.user.is_authenticated:
        print('entro a la vista imprimir cierre caja')
        print('el id de la caja para imprimir', id_caja)
        caja = Caja.objects.get(pk=id_caja)

        return render(request, 'admin/caja/ticket_cierre_caja.html', context={'caja': caja,
                                                                              'ingresos': calcular_ingresos_caja(caja),
                                                                              'total_ingresos': calcular_total_ingresos(caja),
                                                                              'egresos': calcular_egresos_caja(caja),
                                                                              'total_egresos': calcular_total_egresos(caja),
                                                                              'total_ccorrientes': calcular_total_compras_cc(caja)})





