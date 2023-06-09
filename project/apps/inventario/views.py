from django.shortcuts import render
import json
from django.http import JsonResponse, HttpResponse, HttpResponseServerError
# Create your views here.
from inventario.models import MovimientoInterno


def recepcionar_movimiento_ingreso(request, numero_lote):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            print("NUMERO de LOTE")
            print(numero_lote)
            try:
                movimiento_interno = MovimientoInterno.objects.get(numero_lote=numero_lote)
                movimiento_interno.abierto=False
                movimiento_interno.save()
                data = {'data': 'RECEPCIONADO'}

            except KeyError:
                data = {'error': 'Error al Recepcionar Movimiento de Ingreso'}
        print('imprimiento dataaaa')
        print(data)
        data = json.dumps(data)
        return HttpResponse(data, content_type="application/json")