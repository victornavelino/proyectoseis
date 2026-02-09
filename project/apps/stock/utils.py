
from django.forms import ValidationError
from stock.models import ArticuloDeposito, ArticuloSucursal


def calcular_stock(form):
    if form.cleaned_data["articulo_foraneo"]:
        articulo_mov = form.cleaned_data["articulo_foraneo"]
        articulo_sucursal = ArticuloSucursal.objects.get(articulo=articulo_mov)

def verificar_minimo_en_deposito(cleaned_data):
    if cleaned_data.get('articulo_foraneo') and cleaned_data.get('cantidad'):
        try:
            articulo_deposito=ArticuloDeposito.objects.get(articulo=cleaned_data.get('articulo_foraneo'),
                                                               deposito=cleaned_data.get('origen'))
            if articulo_deposito.cantidad-cleaned_data.get('cantidad') < 0:
                return False
            else:
                return True
        except:
            raise ValidationError('Articulo no existente en deposito')
    else:
        return False

def verificar_minimo_en_sucursal(cleaned_data):
    if cleaned_data.get('articulo_foraneo') and cleaned_data.get('cantidad'):
        articulo_sucursal=ArticuloSucursal.objects.get(articulo=cleaned_data.get('articulo_foraneo'),
                                                               sucursal=cleaned_data.get('origen'))
        if articulo_sucursal.cantidad-cleaned_data.get('cantidad') < 0:
            return False
        else:
            return True
    else:
        return False
    