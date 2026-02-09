from django.http import HttpResponse
from django.shortcuts import render
import json
from django.core import serializers
from stock.models import ArticuloDeposito, Deposito
from django.contrib.contenttypes.models import ContentType

# Create your views here.
def get_articulos_deposito(request, id_deposito):
    if request.user.is_authenticated:
        print("id deposito que viene del front")
        print(id_deposito)
        # separamos el id de deposito
        partes = id_deposito.split('-')
        tipo = int(partes[0]) 
        id_objeto = int(partes[1])
        ct = ContentType.objects.get_for_id(tipo)
        print('imprimo contentype origen en get deposito')
        print(ct.model_class)
        print('imprimo objeto id origen en get deposito')
        print(id_objeto)
        obj_get = ct.get_object_for_this_type(pk=id_objeto)
        if isinstance(obj_get, Deposito):
            articulosdeposito = ArticuloDeposito.objects.filter(deposito=obj_get)
            if len(articulosdeposito) > 0:
                results = [] 
                for articulo in articulosdeposito:
                    json_valores = {
                        "id_articulo": str(articulo.articulo.pk),
                        "articulo": articulo.articulo.nombre,
                        "cantidad": str(articulo.cantidad),
                        "deposito": articulo.deposito.nombre
                        }
                    results.append(json_valores)
                data = json.dumps(results)
            else:
                json_valores = {'error': 'El Deposito No tiene articulos'}
                data = json.dumps(json_valores)
        
    else:
        valores = {}
        data = serializers.serialize('json', valores)
    return HttpResponse(data, content_type="application/json")