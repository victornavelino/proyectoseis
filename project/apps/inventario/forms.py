from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Choices
from django.forms import Select, NumberInput

from articulo.models import Articulo, Precio, ListaPrecio
from inventario.models import ArticuloInventario, Inventario, MovimientoInternoArticulo, MovimientoInterno
from venta.models import Venta, VentaArticulo


class InventarioAdminForm(forms.ModelForm):
    class Meta:
        model = Inventario
        fields = '__all__'
  #  ArticuloInventario_set = forms.ModelMultipleChoiceField(queryset=ArticuloInventario.objects.all())


class MovimientoInternoAdminForm(forms.ModelForm):
    class Meta:
        model = MovimientoInterno
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            fields = list(self.fields['tipo_movimiento_interno'].choices)
            fields.pop(1)
            self.fields['tipo_movimiento_interno'].choices = fields

class MovimientoInternoArticuloInlineForm(forms.ModelForm):
    class Meta:
        model = MovimientoInternoArticulo
        fields = ('articulo', 'cantidad_peso', 'monto',)
        readonly_fields = ('monto',)
        widgets = {
            'articulo': Select(attrs={'onchange': "cargarPrecioArticulo(this.value, this.id);", 'required': 'true'}),
            'cantidad_peso': NumberInput(attrs={'onchange': "calcularMonto(this.value, this.id);", 'required': 'true'}),
        }
    precio_articulo = forms.DecimalField(required=False, disabled=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        mov_inv_art = self.instance
        if mov_inv_art.pk:
            lista_precio, created = ListaPrecio.objects.get_or_create(nombre='COMUN')
            precio = Precio.objects.get(articulo=mov_inv_art.articulo, lista_precio=lista_precio)
        self.initial = {
            "articulo": mov_inv_art.articulo if mov_inv_art.pk else None,
            "cantidad_peso": mov_inv_art.cantidad_peso if mov_inv_art.pk else None,
            "monto": mov_inv_art.monto if mov_inv_art.pk else None,
            "precio_articulo": precio.precio if mov_inv_art.pk else None
        }

    def clean(self):
        cleaned_data = super().clean()
        cantidad_peso = cleaned_data.get("cantidad_peso")
        articulo = cleaned_data.get("articulo")
        monto = cleaned_data.get("monto")
        if cantidad_peso == 0 or cantidad_peso is None:
            raise ValidationError('La cantidad / peso no puede ser nulo')
        if articulo is None:
            raise ValidationError('El Articulo no puede ser nulo')
        if monto is None or monto ==0:
            raise ValidationError('El monto no puede ser nulo')
        return cleaned_data


