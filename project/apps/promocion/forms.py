
from django import forms
from promocion.models import PromocionArticulo


class PromocionArticuloInlineForm(forms.ModelForm):
    
    class Meta:
        model = PromocionArticulo 
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        articulo = cleaned_data.get("articulo")
        if not articulo:
            raise forms.ValidationError("El Articulo no puede estar vacío.")
        return cleaned_data

    
