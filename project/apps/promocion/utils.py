from django.db import DatabaseError

from promocion.models import Promocion, PromocionArticulo


def copiar_promocion(promocion, sucursal):
    print('entro create')
    try:
        articulos_promocion = PromocionArticulo.objects.filter(promocion=promocion)
        promo = Promocion.objects.create(nombre=promocion.nombre, fecha_inicio=promocion.fecha_inicio,
                                         fecha_fin=promocion.fecha_fin, es_por_precio=promocion.es_por_precio,
                                         porcentaje_todos=promocion.porcentaje_todos, dias_semana=promocion.dias_semana,
                                         habilitada=promocion.habilitada, prioridad=promocion.prioridad,
                                         sucursal=sucursal)

        for articulo_promo in articulos_promocion:
            PromocionArticulo.objects.create(valor=articulo_promo.valor, articulo=articulo_promo.articulo,
                                             promocion=promo)

        promo.refresh_from_db()
        data = {'resultado': 'COPIADA'}

    except DatabaseError as e:
        data = {'error': 'Error en la base de datos: ' + str(e)}
    return data


def eliminar_promociones(promociones_a_borrar):
    for promo in promociones_a_borrar:
        PromocionArticulo.objects.filter(promocion=promo).delete()
        promo.delete()


def copiar_todas(sucursal_origen, sucursal_destino):
    try:

        promocion_a_copiar = Promocion.objects.filter(sucursal=sucursal_origen, habilitada=True)
        Promocion.objects.filter(sucursal=sucursal_destino, habilitada=True).delete()
        for promocion in promocion_a_copiar:
            Promocion.objects.create(nombre=promocion.nombre, fecha_inicio=promocion.fecha_inicio,
                                     fecha_fin=promocion.fecha_fin, es_por_precio=promocion.es_por_precio,
                                     porcentaje_todos=promocion.porcentaje_todos, dias_semana=promocion.dias_semana,
                                     habilitada=promocion.habilitada, prioridad=promocion.prioridad,
                                     sucursal=sucursal_destino)
        print(promocion_a_copiar)
        promociones_destino= Promocion.objects.filter(sucursal=sucursal_destino, habilitada=True)
        print(promociones_destino)
        data = {'resultado': 'COPIADA'}
    except DatabaseError:
        data = {'error': 'Error al Realizar Copia'}

    return data
