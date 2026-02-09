from typing import Any
from django.contrib import admin, messages
from django.contrib.contenttypes.models import ContentType
from empleado.models import Sucursal
from stock.utils import calcular_stock
from stock.forms import MovimientoArticuloForm
from stock.models import Deposito, ArticuloSucursal, MovimientoArticulo, ArticuloDeposito


@admin.register(Deposito)
class DepositoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'domicilio',)
    search_fields = ('nombre',)
    list_per_page = 30


@admin.register(ArticuloSucursal)
class ArticuloSucursalAdmin(admin.ModelAdmin):
    list_display = ('articulo', 'sucursal','cantidad')
    search_fields = ('articulo',)
    list_per_page = 30

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return True
     
    def save_model(self, request, obj, form, change):
        messages.error(request, 'No Puede modificar movimientos desde este panel')
        return False


@admin.register(ArticuloDeposito)
class ArticuloDepositoAdmin(admin.ModelAdmin):
    list_display = ('articulo', 'deposito','cantidad')
    search_fields = ('articulo',)
    list_per_page = 30


@admin.register(MovimientoArticulo)
class MovimientoArticuloAdmin(admin.ModelAdmin):
    form = MovimientoArticuloForm
    list_display = ('origen', 'destino', 'articulo', 'cantidad', 'fecha', 'observaciones')
    search_fields = ('articulo',)
    list_per_page = 30
    change_form_template = 'admin/stock/movimientoarticulo/movimientoarticulo_form.html'


    def origen(self, obj):
        from django.contrib.contenttypes.models import ContentType
        try:
            ct = ContentType.objects.get_for_id(obj.origen_type.id)
            print('imprimo contentype origen')
            print(ct.model_class)
            obj_get = ct.get_object_for_this_type(pk=obj.origen_object_id)
            return obj_get.nombre
        except:
            return None
        
    def destino(self, obj):
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_id(obj.destino_type.id)
        print('imprimo contentype destino')
        print(ct.model_class)
        obj_get = ct.get_object_for_this_type(pk=obj.destino_object_id)
        return obj_get.nombre
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return True

    def save_model(self, request, obj, form, change):
        print("save_model is called")
        if obj.origen:
            print('objeto origen con datos')
        else:
            print('objeto vacio')
            obj.origen_type=None
            obj.origen_object_id=None

        if form.cleaned_data["articulo_foraneo"]:
            obj.articulo = form.cleaned_data["articulo_foraneo"].nombre
        if form.cleaned_data["usuario_foraneo"]:
            obj.usuario = form.cleaned_data["usuario_foraneo"]
        if form.cleaned_data["origen"]:
            obj.origen = form.cleaned_data["origen"]
        if form.cleaned_data["destino"]:
            obj.destino = form.cleaned_data["destino"]
        
        #VALIDACIONES
        print('IMPRIMO ORIGEN: ', obj.origen)
        print('IMPRIMO DESTINO: ', obj.destino)
        print('IMPRIMO ARTICULO: ', obj.articulo)


        # CASO MOVIMIENTO DEPOSITO -> SUCURSAL
        if obj.origen and isinstance(obj.origen, Deposito) and isinstance(obj.destino, Sucursal):
            print('Entro Deposito a sucursal')
            try:

                articulo_sucursal=ArticuloSucursal.objects.get(articulo=form.cleaned_data["articulo_foraneo"],
                                                         sucursal=form.cleaned_data["destino"])
                #SE INCREMENTA EN CANTIDAD EN SUCURSAL
                articulo_sucursal.cantidad+=obj.cantidad
                articulo_sucursal.save()

                articulo_deposito=ArticuloDeposito.objects.get(articulo=form.cleaned_data["articulo_foraneo"],
                                                               deposito=form.cleaned_data["origen"])
                #SE DISMINUYE LA MISMA CANTIDAD EN DEPOSITO
                articulo_deposito.cantidad-=obj.cantidad
                articulo_deposito.save()
            except:
                ArticuloSucursal.objects.create(articulo=form.cleaned_data["articulo_foraneo"],
                                            sucursal=form.cleaned_data["destino"],
                                            cantidad=obj.cantidad)
                articulo_deposito=ArticuloDeposito.objects.get(articulo=form.cleaned_data["articulo_foraneo"],
                                                               deposito=form.cleaned_data["origen"])
                #SE DISMINUYE LA MISMA CANTIDAD EN DEPOSITO
                articulo_deposito.cantidad-=obj.cantidad
                articulo_deposito.save()
                
        #CASO INGRESO DE MERCADERIA A DEPOSITO
        if not obj.origen and isinstance(obj.destino, Deposito):
            print('Entro INGRESO DE MERCADERIA a DEPOSITO')
            print(obj.destino)
            try:
                articulo_deposito=ArticuloDeposito.objects.get(articulo=form.cleaned_data["articulo_foraneo"],
                                                         deposito=obj.destino)
                articulo_deposito.cantidad+=obj.cantidad
                articulo_deposito.save()
            except:
                ArticuloDeposito.objects.create(articulo=form.cleaned_data["articulo_foraneo"],
                                            deposito=obj.destino,
                                            cantidad=obj.cantidad)

        # CASO DEVOLUCION DE SUCURSAL -> DEPOSITO
        if obj.origen and isinstance(obj.origen, Sucursal) and isinstance(obj.destino, Deposito):
            print('Entro SUCURSAL a DEPOSITO')
            try:
                articulo_deposito=ArticuloDeposito.objects.get(articulo=form.cleaned_data["articulo_foraneo"],
                                                         deposito=form.cleaned_data["destino"])
                #SE INCREMENTA EN CANTIDAD EN DEPOSITO
                articulo_deposito.cantidad+=obj.cantidad
                articulo_deposito.save()

                articulo_sucursal=ArticuloSucursal.objects.get(articulo=form.cleaned_data["articulo_foraneo"],
                                                         sucursal=form.cleaned_data["origen"])
                #SE DISMINUYE LA MISMA CANTIDAD EN SUCURSAL
                articulo_sucursal.cantidad-=obj.cantidad
                articulo_sucursal.save()
            except:
                ArticuloDeposito.objects.create(articulo=form.cleaned_data["articulo_foraneo"],
                                            deposito=form.cleaned_data["destino"],
                                            cantidad=obj.cantidad)
                articulo_sucursal=ArticuloSucursal.objects.get(articulo=form.cleaned_data["articulo_foraneo"],
                                                         sucursal=form.cleaned_data["origen"])
                #SE DISMINUYE LA MISMA CANTIDAD EN SUCURSAL
                articulo_sucursal.cantidad-=obj.cantidad
                articulo_sucursal.save()
        
        obj.save()
    

