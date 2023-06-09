from django.core import serializers
from django.shortcuts import render
from django.http import HttpResponse
import json

from empleado.models import Sucursal
from promocion.models import Promocion, PromocionArticulo

# Create your views here.
from promocion.utils import copiar_promocion, copiar_todas, eliminar_promociones


def copiar_promociones(request):
    sucursales = Sucursal.objects.all()
    return render(request, 'admin/promocion/copiar_promo.html',
                  context={'sucursales': sucursales})


def copiar_promos(request):
    data = ''
    resultado = ''
    if request.user.is_authenticated:

        json_data = json.loads(request.body)
        id_sucursal_origen = json_data['sucursal_origen']
        id_sucursal_destino = json_data['sucursal_destino']
        id_promocion = json_data['promocion']
        sucursal_origen = Sucursal.objects.get(pk=id_sucursal_origen)
        sucursal_destino = Sucursal.objects.get(pk=id_sucursal_destino)
        if id_promocion:
            promocion_a_copiar = Promocion.objects.get(pk=id_promocion)

            promociones_a_borrar = Promocion.objects.filter(nombre=promocion_a_copiar.nombre, sucursal=sucursal_destino,
                                                            prioridad=promocion_a_copiar.prioridad,
                                                            habilitada=promocion_a_copiar.habilitada)
            if not promociones_a_borrar:
                print('entro copiar una promo sin borrar')
                data = copiar_promocion(promocion_a_copiar, sucursal_destino)

            else:
                print('entro copiar una promo Borrando')
                eliminar_promociones(promociones_a_borrar)
                data = copiar_promocion(promocion_a_copiar, sucursal_destino)

        else:
            print('entro copiar todas')
            data = copiar_todas(sucursal_origen, sucursal_destino)

        data = json.dumps(data)
        return HttpResponse(data, content_type="application/json")
    return HttpResponse(data, content_type="application/json")


def get_promociones_sucursal(request, pk_sucursal):
    if request.user.is_authenticated:
        promociones = Promocion.objects.filter(sucursal__id=pk_sucursal, habilitada=True)
        results = []
        for promocion in promociones:
            json_datos = {
                'id': promocion.id,
                'nombre': promocion.nombre
            }
            results.append(json_datos)
        data = json.dumps(results)
    else:
        valores = {}
        data = serializers.serialize('json', valores)
    return HttpResponse(data, content_type="application/json")
