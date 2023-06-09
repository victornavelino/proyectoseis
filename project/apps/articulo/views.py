
from django.shortcuts import render
import json
# Create your views here.
from articulo.models import Precio, Articulo, ListaPrecio
from django.core import serializers
from django.http import HttpResponse
from articulo.utils import copiar_precios_sucursal, copiar_precios_sucursal_lista_precio, copiar_precios_sucursal_a_todas

from empleado.models import Sucursal


def get_precio_articulo(request, id_articulo):
    if request.user.is_authenticated:
        articulo = Articulo.objects.get(pk=id_articulo)
        #Aqui usamos la lista de precio comun siempre
        lista_precio, created = ListaPrecio.objects.get_or_create(nombre='COMUN')
        precio = Precio.objects.get(articulo=articulo, lista_precio=lista_precio)
        json_valores = {
            "precio": str(precio.precio),
            "articulo": precio.articulo.nombre,
            "codigo": precio.articulo.codigo,
            "es_por_peso": precio.articulo.es_por_peso
        }
        data = json.dumps(json_valores)
    else:
        valores = {}
        data = serializers.serialize('json', valores)
    return HttpResponse(data, content_type="application/json")


def copiar_precios(request):
    sucursales = Sucursal.objects.all()
    listaPrecios = ListaPrecio.objects.all()
    return render(request, 'admin/articulo/precio/copiar_precios.html',
                  context={'sucursales': sucursales, 'listaPrecios': listaPrecios})


def copiar_precios_proceso(request):
    data = ''
    if request.user.is_authenticated:
        json_data = json.loads(request.body)
        id_sucursal_origen = json_data['sucursal_origen']
        id_sucursal_destino = json_data['sucursal_destino']
        id_lista_precios = json_data['lista_precios']
        sucursal_origen = Sucursal.objects.get(pk=id_sucursal_origen)
        sucursal_destino = Sucursal.objects.get(pk=id_sucursal_destino)
        if id_lista_precios:
            lista_a_copiar = ListaPrecio.objects.get(pk=id_lista_precios)
            data = copiar_precios_sucursal_lista_precio(sucursal_origen, sucursal_destino, lista_a_copiar)
        else:
            data = copiar_precios_sucursal(sucursal_origen, sucursal_destino)

        data = json.dumps(data)
        return HttpResponse(data, content_type="application/json")
    return HttpResponse(data, content_type="application/json")


def get_listas_precio_sucursal(request, pk_sucursal):
    if request.user.is_authenticated:
        listas = ListaPrecio.objects.filter(sucursal__id=pk_sucursal, habilitada=True)
        results = []
        for lista in listas:
            json_datos = {
                'id': lista.id,
                'nombre': lista.nombre
            }
            results.append(json_datos)
        data = json.dumps(results)
    else:
        valores = {}
        data = serializers.serialize('json', valores)
    return HttpResponse(data, content_type="application/json")