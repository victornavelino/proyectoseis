
from django import forms
from promocion.models import Promocion
from promocion.models import PromocionArticulo

class PromocionForm(forms.ModelForm):
    class Meta:
        model= Promocion
        fields = "__all__"
    
    def clean(self):
        cleaned_data = super().clean()
        print('self.data:  ', self.data)
        """promocionesarticulos = [int(self.data[key]) for key in self.data if
                        key.startswith('promocionarticulo_set-') and self.data[key] != '']
        print('PROMOCIONES ARTICULOS', promocionesarticulos)"""
        return cleaned_data
    
