from django.db import DatabaseError

from articulo.models import Articulo, Precio, ListaPrecio
from empleado.models import Sucursal


def copiar_precios_sucursal(sucursal_origen: Sucursal, sucursal_destino: Sucursal):
    try:
        precios = Precio.objects.filter(sucursal=sucursal_origen)
        for precio in precios:
            articulo, created_a = Articulo.objects.get_or_create(nombre=precio.articulo.nombre,
                                                                 abreviatura=precio.articulo.abreviatura,
                                                                 codigo=precio.articulo.codigo,
                                                                 categoria=precio.articulo.categoria,
                                                                 unidad_medida=precio.articulo.unidad_medida,
                                                                 es_por_peso=precio.articulo.es_por_peso, )
            lista_precio, created_l = ListaPrecio.objects.get_or_create(nombre=precio.lista_precio.nombre, )
            p, created_p = Precio.objects.update_or_create(articulo=articulo, sucursal=sucursal_destino,
                                                           lista_precio=lista_precio,
                                                           precio=precio.precio)
        data = {'resultado': 'COPIADA'}

    except DatabaseError as e:
        data = {'error': 'Error en la base de datos: ' + str(e)}
    return data


def copiar_precios_sucursal_lista_precio(sucursal_origen: Sucursal, sucursal_destino: Sucursal,
                                         lista_precio: ListaPrecio):
    try:
        precios = Precio.objects.filter(sucursal=sucursal_origen, lista_precio=lista_precio)
        for precio in precios:
            articulo, created_a = Articulo.objects.get_or_create(nombre=precio.articulo.nombre,
                                                                 abreviatura=precio.articulo.abreviatura,
                                                                 codigo=precio.articulo.codigo,
                                                                 categoria=precio.articulo.categoria,
                                                                 unidad_medida=precio.articulo.unidad_medida,
                                                                 es_por_peso=precio.articulo.es_por_peso, )
            lista_precio, created_l = ListaPrecio.objects.get_or_create(nombre=lista_precio.nombre, )
            p, created_p = Precio.objects.update_or_create(articulo=articulo, sucursal=sucursal_destino,
                                                           lista_precio=lista_precio,
                                                           precio=precio.precio)
        data = {'resultado': 'COPIADAS'}

    except DatabaseError as e:
        data = {'error': 'Error en la base de datos: ' + str(e)}
    return data



def copiar_precios_sucursal_a_todas(sucursal_origen: Sucursal):
    try:
        sucursales = Sucursal.objects.exclude(pk=sucursal_origen.pk)
        for sucursal in sucursales:
            copiar_precios_sucursal(sucursal_origen, sucursal)

        data = {'resultado': 'COPIADAS'}

    except DatabaseError as e:
        data = {'error': 'Error en la base de datos: ' + str(e)}
    return data