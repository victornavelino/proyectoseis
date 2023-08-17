
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
        return cleaned_data
    
