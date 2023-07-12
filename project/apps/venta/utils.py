from datetime import datetime, date

from django.db.models import Sum

from articulo.models import Precio, Articulo
from cliente.models import Cliente
from empleado.models import Empleado
from promocion.models import Promocion, Descuento
from venta.models import VentaArticulo, Venta


def get_precio_promocion(cliente, articulo, sucursal, precio_unitario):
    if cumpleanio(cliente.pk) or empleado(cliente.persona):
        valor = precio_unitario
    else:
        # SI ES EVENTUAL o cliente Comun
        if cliente.lista_precio.nombre.__contains__('COMUN'):
            # verificamos si entra en alguna promocion
            promos_activas = get_promociones_activas(sucursal)
            valor = buscar_precio_articulo_en_promo(cliente, articulo, promos_activas, sucursal)
            # en caso que no entre.. se le asigna el precio comun
            if valor == 0:
                precio = get_precio_articulo(articulo, cliente.lista_precio, sucursal)
                valor = precio.precio
        else:
            # Cliente lista No COMUN
            precio = get_precio_articulo(articulo, cliente.lista_precio, sucursal)
            valor = precio.precio
    return valor


def guardar_venta_cliente_articulos(id_cliente, articulos, usuario):
    precio_total = 0
    cliente = Cliente.objects.get(pk=id_cliente)

    if cumpleanio(id_cliente):
        try:
            descuento_cumpleanio = Descuento.objects.get(nombre='CUMPLEAÑOS')
        except Descuento.DoesNotExist:
            descuento_cumpleanio = None
        if descuento_cumpleanio!= None and descuento_cumpleanio.valor > 0:
            print('aplicamos descuento CUMPLEAÑO ya que el descuento existe y es mayor que 0')
            precio_total = calcular_total_con_descuento(articulos)
        else:
            if empleado(cliente.persona):
                try:
                    descuento_empleado = Descuento.objects.get(nombre='EMPLEADOS')
                except Descuento.DoesNotExist:
                    descuento_empleado = None
                if descuento_empleado!= None and descuento_empleado.valor > 0:
                    print('aplicamos descuento EMPLEADO ya que el descuento existe y es mayor que 0')
                    precio_total = calcular_total_con_descuento(articulos)
                else:
                    print('No aplicamos descuento cumpleaño. ni empleado y aplicamos cualquier promocion de la lista o precio de su lista')
                    precio_total = calcular_total_cliente(cliente, articulos, usuario)
            else:
                print('No aplicamos descuento cumpleaño. ni empleado y aplicamos cualquier promocion de la lista o precio de su lista')
                precio_total = calcular_total_cliente(cliente, articulos, usuario)
    else:
        if empleado(cliente.persona):
            try:
                descuento_empleado = Descuento.objects.get(nombre='EMPLEADOS')
            except Descuento.DoesNotExist:
                descuento_empleado = None
            if descuento_empleado!= None and descuento_empleado.valor > 0:
                print('aplicamos descuento EMPLEADO ya que el descuento existe y es mayor que 0')
                precio_total = calcular_total_con_descuento(articulos)
            else:
                print('No aplicamos descuento cumpleaño. ni empleado y aplicamos cualquier promocion de la lista o precio de su lista')
                precio_total = calcular_total_cliente(cliente, articulos, usuario)
        else:
            print('No aplicamos descuento cumpleaño. ni empleado y aplicamos cualquier promocion de la lista o precio de su lista')
            precio_total = calcular_total_cliente(cliente, articulos, usuario)

    #if cumpleanio(id_cliente) or empleado(cliente.persona):
    #    precio_total = calcular_total_con_descuento(articulos)
    #else:
    #    precio_total = calcular_total_cliente(cliente, articulos, usuario)

    venta = Venta.objects.create(fecha=datetime.now(), monto=precio_total, descuento=0, sucursal=usuario.sucursal,
                                 cliente=cliente, usuario=usuario)
    for a in articulos:
        id_articulo = a['id_articulo']
        cantidad_peso = a['cantidad_peso']
        precio_unitario = a['precio_unitario']
        articulo = Articulo.objects.get(codigo=id_articulo)
        precio_promocion = get_precio_promocion(cliente, articulo, usuario.sucursal, precio_unitario)
        precio = get_precio_articulo(articulo, cliente.lista_precio, usuario.sucursal)
        monto = (float(precio_promocion) * float(cantidad_peso))
        VentaArticulo.objects.create(total_articulo=monto, cantidad_peso=cantidad_peso,
                                     precio_promocion=precio_promocion,
                                     precio_unitario=precio.precio, nombre_articulo=articulo.nombre, articulo=articulo,
                                     codigo_articulo=articulo.codigo, venta=venta)
    venta.refresh_from_db()
    return venta


def calcular_total_con_descuento(articulos):
    total = 0
    for a in articulos:
        id_articulo = a['id_articulo']
        cantidad_peso = a['cantidad_peso']
        articulo = Articulo.objects.get(codigo=id_articulo)
        # en este caso el precio unitario con el descuento del cumple o de empleado, viene
        # desde el front
        precio = a['precio_unitario'];
        total = total + (float(precio) * float(cantidad_peso))
    return total


def calcular_total_cliente(cliente, articulos, usuario):
    total = 0
    for a in articulos:
        id_articulo = a['id_articulo']
        cantidad_peso = a['cantidad_peso']
        articulo = Articulo.objects.get(codigo=id_articulo)
        # Obtenemos promociones activas
        promociones_activas = get_promociones_activas(usuario.sucursal)
        # buscamos el articulo en alguna promo activa
        # SI ES EVENTUAL o cliente con lista Comun
        if cliente.lista_precio.nombre.__contains__('COMUN'):
            precio = buscar_precio_articulo_en_promo(cliente, articulo, promociones_activas, usuario.sucursal)
            if precio == 0:
                # si es el articulo no matchea en ninguna promo, tomamos el precio de su lista
                precio = get_precio_articulo(articulo, cliente.lista_precio, usuario.sucursal)
                precio = precio.precio
        else:
            # CLIENTE (NO lista Comun  )
            precio = get_precio_articulo(articulo, cliente.lista_precio, usuario.sucursal)
            precio = precio.precio
        total = total + (float(precio) * float(cantidad_peso))
    return total


def calcular_importe_eventuales(cierre_venta):
    importe_eventual = Venta.objects.filter(numero_ticket__gte=cierre_venta.ticket_desde,
                                            numero_ticket__lte=cierre_venta.ticket_hasta,
                                            cliente__persona__apellido__icontains='EVENTUAL').aggregate(Sum('monto'))[
                           'monto__sum'] or 0.00
    return importe_eventual


def calcular_importe_descuentos(cierre_venta):
    importe_descuento = Venta.objects.filter(numero_ticket__gte=cierre_venta.ticket_desde,
                                             numero_ticket__lte=cierre_venta.ticket_hasta,
                                             cliente__lista_precio__nombre__icontains='EMPLEADO').aggregate(
        Sum('monto'))['monto__sum'] or 0.00
    return importe_descuento


def calcular_importe_asado(cierre_venta):
    ventas_asado = Venta.objects.filter(numero_ticket__gte=cierre_venta.ticket_desde,
                                         numero_ticket__lte=cierre_venta.ticket_hasta,
                                         ventaarticulo__articulo__categoria__nombre__icontains='ASADO')

    if ventas_asado:
        importe_asado = Venta.objects.filter(numero_ticket__gte=cierre_venta.ticket_desde,
                                         numero_ticket__lte=cierre_venta.ticket_hasta,
                                         ventaarticulo__articulo__categoria__nombre__icontains='ASADO').aggregate(Sum('monto'))['monto__sum']
    else:
        importe_asado = 0.00
    return importe_asado


def calcular_importe_blandos(cierre_venta):
    importe_blandos = Venta.objects.filter(numero_ticket__gte=cierre_venta.ticket_desde,
                                           numero_ticket__lte=cierre_venta.ticket_hasta,
                                           ventaarticulo__articulo__categoria__nombre__icontains='BLANDO').aggregate(
        Sum('monto'))['monto__sum'] or 0.00
    return importe_blandos


def cumpleanio(pk_cliente):
    result = False
    cliente = Cliente.objects.get(pk=pk_cliente)
    if (cliente.persona.fecha_nacimiento):
        nacimiento_cliente = cliente.persona.fecha_nacimiento
        fecha_actual = date.today()
        if (fecha_actual.month == nacimiento_cliente.month) & (fecha_actual.day == nacimiento_cliente.day):
            result = True
        else:
            result = False
    return result


def empleado(persona):
    try:
        Empleado.objects.get(persona=persona, fecha_baja=None)
        result = True
    except:
        result = False
    return result


def get_promociones_activas(sucursal):
    hoy = datetime.now()
    promociones = Promocion.objects.filter(habilitada=True, sucursal=sucursal, fecha_inicio__lte=hoy,
                                           fecha_fin__gte=hoy).order_by('prioridad')
    return promociones


def buscar_precio_articulo_en_promo(cliente, articulo, promociones_activas, sucursal):
    precio_promo = 0
    print('Promooooos activas desordenadas')
    print(promociones_activas)
    found = False
    for promocion in promociones_activas:
        if not found:
            if promocion.porcentaje_todos:
                precio = Precio.objects.filter(articulo=articulo, lista_precio__cliente=cliente,
                                               sucursal=sucursal).last()
                monto_a_descontar = precio.precio * promocion.porcentaje_todos / 100
                precio_promo = round(precio.precio - monto_a_descontar, 2)
                found = True
                break
            else:
                if promocion.es_por_precio:
                    for articulo_promo in promocion.promocionarticulo_set.all():
                        if articulo_promo.articulo == articulo:
                            precio_promo = round(articulo_promo.valor, 2)
                            found = True
                            break
    return precio_promo


def obtener_precio_promo(cliente, articulo, promocion_seleccionada, sucursal):
    precio = Precio.objects.filter(articulo=articulo, lista_precio__cliente=cliente,
                                   sucursal=sucursal).last()
    monto_a_descontar = precio.precio * promocion_seleccionada.porcentaje_todos / 100
    precio_final = precio.precio - monto_a_descontar


def get_precio_articulo(articulo, lista_precio, sucursal):
    precio = Precio.objects.filter(articulo=articulo,
                                   lista_precio=lista_precio,
                                   sucursal=sucursal).last()
    return precio
