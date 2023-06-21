import json

# from bootstrap_modal_forms.generic import BSModalCreateView, BSModalFormView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseServerError
from django.shortcuts import render
from django.core import serializers
from django.urls import reverse_lazy
from django.views.generic import ListView, FormView
from datetime import date

from articulo.models import Precio, ListaPrecio, Articulo

# Create your views here.
from caja.models import TarjetaDeCredito, Caja
from cliente.models import Cliente
from promocion.models import Promocion, Descuento
from venta.forms import CobrarVentaForm, form_dialog_pago
from venta.models import Venta
from venta.utils import guardar_venta_cliente_articulos, cumpleanio, get_promociones_activas, \
    buscar_precio_articulo_en_promo, get_precio_articulo, empleado


def get_valores(request, articulo_codigo, cliente_pk):
    if request.user.is_authenticated:
        print("cliente que viene del front")
        print(cliente_pk)
        cliente = Cliente.objects.get(pk=cliente_pk)
        articulo = Articulo.objects.get(codigo=articulo_codigo)
        precio_normal = get_precio_articulo(articulo, cliente.lista_precio, request.user.sucursal)
        results = []
        # SI ES EMPLEADO CALCULAMOS DESCUENTO EMPLEADO
        if empleado(cliente.persona):
            try:
                print('entro descuento empleado')
                descuento_empleado = Descuento.objects.get(nombre='EMPLEADOS')
                print('descuento emplead prueba')
                if descuento_empleado.valor > 0:
                    print('entrooooo iiiiiiiiiiffffffff')
                    precio = get_precio_articulo(articulo, cliente.lista_precio, request.user.sucursal)
                    monto_a_descontar = precio.precio * descuento_empleado.valor / 100
                    precio_final = round(precio.precio - monto_a_descontar, 2)
                    json_valores = {
                    "precio": str(precio.precio),
                    "precio_promo": str(precio_final),
                    "articulo": precio.articulo.nombre,
                    "codigo": precio.articulo.codigo,
                    "es_por_peso": precio.articulo.es_por_peso
                    }
                    data = json.dumps(json_valores)
                else:
                    print("entro else descuento")
                    
            except:
                print("entro except")
                json_valores = {'error': 'No existe Descuento de Empleado cargado'}
                data = json.dumps(json_valores)

        else:
            if cumpleanio(cliente_pk):
                try:
                    descuento_cumple = Descuento.objects.get(nombre='CUMPLEAÑOS')
                    precio = Precio.objects.filter(articulo__codigo=articulo_codigo,
                                                   lista_precio__cliente__pk=cliente_pk,
                                                   sucursal=request.user.sucursal).last()
                    monto_a_descontar = precio.precio * descuento_cumple.valor / 100
                    precio_final = round(precio.precio - monto_a_descontar, 2)
                    json_valores = {
                        "precio": str(precio.precio),
                        "precio_promo": str(precio_final),
                        "articulo": precio.articulo.nombre,
                        "codigo": precio.articulo.codigo,
                        "es_por_peso": precio.articulo.es_por_peso
                    }
                    data = json.dumps(json_valores)
                except:
                    print("entro except")
                    json_valores = {'error': 'No existe Descuento de cumpleanios cargado'}
                    data = json.dumps(json_valores)
            else:
                # SI ES EVENTUAL o cliente Comun
                if cliente.lista_precio.nombre.__contains__('COMUN'):
                    print('entro lista comunes')
                    # verificamos si entra en alguna promocion
                    promos_activas = get_promociones_activas(request.user.sucursal)
                    precio = buscar_precio_articulo_en_promo(cliente, articulo, promos_activas, request.user.sucursal)
                    # en caso que no entre.. se le asigna el precio comun
                    if precio == 0:
                        precio_normal = Precio.objects.filter(articulo__codigo=articulo_codigo,
                                                       lista_precio__cliente__pk=cliente_pk,
                                                       sucursal=request.user.sucursal).last()
                        articulo = precio_normal.articulo
                        precio = precio_normal.precio

                    json_valores = {
                        "precio": str(precio_normal.precio),
                        "precio_promo": str(precio),
                        "articulo": articulo.nombre,
                        "codigo": articulo.codigo,
                        "es_por_peso": articulo.es_por_peso
                    }
                    data = json.dumps(json_valores)
                else:
                    # ES CLIENTE (NO lista comun)
                    try:
                        json_valores = {
                            "precio": str(precio_normal.precio),
                            "precio_promo": str(precio_normal.precio),
                            "articulo": precio_normal.articulo.nombre,
                            "codigo": precio_normal.articulo.codigo,
                            "es_por_peso": precio_normal.articulo.es_por_peso
                        }
                        data = json.dumps(json_valores)
                    except:
                        print("articulo sin precio en la lista del cliente")
                        json_valores = {'error': 'El articulo seleccionado no tiene Precio en la lista del Cliente'}
                        data = json.dumps(json_valores)

        print(data)
    else:
        valores = {}
        data = serializers.serialize('json', valores)
    return HttpResponse(data, content_type="application/json")


def get_articulos(request, articulo):
    if request.user.is_authenticated:
        articulos = Articulo.objects.filter(nombre__icontains=articulo)
        results = []
        for a in articulos:
            json_valores = {
                "articulo": a.nombre,
                "codigo": a.codigo,
                "es_por_peso": a.es_por_peso
            }
            results.append(json_valores)
        data = json.dumps(results)
    else:
        valores = {}
        data = serializers.serialize('json', valores)
    return HttpResponse(data, content_type="application/json")


def get_articulos_todos(request):
    if request.user.is_authenticated:
        articulos = Articulo.objects.all()
        results = []
        for a in articulos:
            json_valores = {
                "articulo": a.nombre,
                "codigo": a.codigo,
                "es_por_peso": a.es_por_peso
            }
            results.append(json_valores)
        data = json.dumps(results)
    else:
        valores = {}
        data = serializers.serialize('json', valores)
    return HttpResponse(data, content_type="application/json")


def get_clientes(request):
    if request.user.is_authenticated:
        clientes = Cliente.objects.all()
        results = []
        for a in clientes:
            json_valores = {
                "id": a.id,
                "nombre": a.persona.obtener_nombre_completo(),
                "dni": a.persona.documento_identidad,
                "fecha_nacimiento": str(a.persona.fecha_nacimiento)
            }
            results.append(json_valores)
        data = json.dumps(results)
    else:
        valores = {}
        data = serializers.serialize('json', valores)
    return HttpResponse(data, content_type="application/json")


def verificar_cumpleanios(request, pk_cliente):
    if request.user.is_authenticated:
        if cumpleanio(pk_cliente):
            data = {'resultado': True}
        else:
            data = {'resultado': False}
        print(data)
        data = json.dumps(data)
    else:
        valores = {}
        data = serializers.serialize('json', valores)
    return HttpResponse(data, content_type="application/json")


def get_tarjetas(request):
    if request.user.is_authenticated:
        tarjetas = TarjetaDeCredito.objects.all()
        results = []
        for t in tarjetas:
            json_valores = {
                "id": t.pk,
                "nombre": t.nombre,
                "banco": t.banco
            }
            results.append(json_valores)
        data = json.dumps(results)
    else:
        valores = {}
        data = serializers.serialize('json', valores)
    return HttpResponse(data, content_type="application/json")


def guardar_venta(request):
    if request.user.is_authenticated:
        caja_abierta = Caja.objects.filter(sucursal=request.user.sucursal, fecha_fin__isnull=True,
                                           fecha_inicio__isnull=False).last()
        if caja_abierta:
            if request.method == 'POST':
                json_data = json.loads(request.body)
                try:
                    venta = json_data['venta']
                    venta_realizada = guardar_venta_cliente_articulos(venta['cliente'], venta['articulos'],
                                                                      request.user)
                    data = {'cliente': venta_realizada.cliente.pk, 'numero_ticket': venta_realizada.numero_ticket,
                            'sucursal': venta_realizada.sucursal.pk, 'importe': str(venta_realizada.monto)}
                except KeyError:
                    data = {'error': 'Datos erroneos'}
            else:
                data = {'error': 'Metodo no soportado'}
        else:
            print('Caja Cerrada')
            data = {'caja': 'cerrada'}
    else:
        data = {'error': 'No autenticado'}
    data = json.dumps(data)
    return HttpResponse(data, content_type="application/json")


def nuevo_pago_efectivo(request):
    form = CobrarVentaForm()
    print("entro a la vista nuevo pago efectivo EFECTIVO")
    return render(request,
                  'admin/venta/cobro_venta/efectivo.html',
                  context={'cobrar_venta_form': form})


def listar_ventas(request):
    if request.user.is_authenticated:
        print("Entro a vista listar_ventas")
        ventas = Venta.objects.filter(sucursal=request.user.sucursal, cobrada=False)
        # ventas = Venta.objects.all()
        return render(request,
                      'admin/venta/cobro_venta/listado_de_ventas.html',
                      context={'ventas': ventas})


def cobrar_venta(request, numero_ticket):
    # tipo_pago_ventas = []
    venta = Venta.objects.get(numero_ticket=numero_ticket)
    return render(request,
                  'admin/venta/cobro_venta/cobrar_venta.html',
                  context={'venta': venta})


def get_ventas(request):
    if request.user.is_authenticated:
        print("Entro a vista get_ventas")
        ventas = Venta.objects.filter(sucursal=request.user.sucursal, cobrada=False)
        # ventas = Venta.objects.all()
        return render(request,
                      'admin/venta/cobro_venta/listado_de_ventas.html',
                      context={'ventas': ventas})


# class BookCreateView(BSModalCreateView):
#     print("CREATE BOOK")
#     template_name = 'admin/venta/new_pago.html'
#     form_class = BookModelForm
#     success_message = 'Success: Book was created.'
#     success_url = reverse_lazy('index')

class mostrar_dialog_pago(ListView):
    print("MOSTRAR DIALOG PAGO")
    template_name = 'admin/venta/cobro_venta/new_pago.html'
    form_class = form_dialog_pago
    success_message = 'Success: Book was created.'
    success_url = reverse_lazy('cobrar_venta')


def mostrar_dialog(request):
    form = form_dialog_pago
    print("diaolooooogogogogoggo")
    return render(request,
                  'admin/venta/cobro_venta/new_pago.html',
                  context={'form': form})


#
# class mostrar_dialog(FormView):
#     template_name = "admin/venta/new_pago.html"
#     form_class = form_dialog_pago


def form_test(request, *args, **kwargs):
    form = form_dialog_pago()
    context = {
        'form': form
    }
    return render(request, 'admin/venta/cobro_venta/new_pago.html', context)
