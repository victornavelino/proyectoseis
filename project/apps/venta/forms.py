#from bootstrap_modal_forms.forms import BSModalModelForm, BSModalForm
from django import forms

from venta.models import Venta, VentaArticulo


class VentaAdminForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = '__all__'
    ventaarticulo_set = forms.ModelMultipleChoiceField(queryset=VentaArticulo.objects.all())


class CobrarVentaForm(forms.Form):
    nombre = forms.CharField(widget=forms.TextInput(attrs={'class': 'special'}))
    fecha = forms.DateField(help_text="Ingrese una Fecha")


# class BookModelForm(BSModalModelForm):
#     nombre = forms.CharField(widget=forms.TextInput(attrs={'class': 'special'}))
#     fecha = forms.DateField(help_text="Ingrese una Fecha")


class form_dialog_pago(forms.Form):
    saldo = forms.IntegerField(label="Saldo", required=True, disabled=True)
    a_pagar = forms.IntegerField(label="A pagar", required=True)
    paga_con = forms.IntegerField(label="Paga con", required=False)
    vuelto = forms.IntegerField(label="Vuelto", required=True, disabled=True)

