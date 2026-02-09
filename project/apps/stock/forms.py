
from django import forms
from dal import autocomplete
from queryset_sequence import QuerySetSequence
from django.core.exceptions import ValidationError
from articulo.models import Articulo
from empleado.models import Sucursal
from project.apps.stock.utils import verificar_minimo_en_deposito, verificar_minimo_en_sucursal
from stock.models import ArticuloDeposito, Deposito, MovimientoArticulo
from usuario.models import Usuario
from django.contrib.contenttypes.models import ContentType


class MovimientoArticuloForm(autocomplete.FutureModelForm):

    origen= autocomplete.Select2GenericForeignKeyModelField(
        queryset=QuerySetSequence(Deposito.objects.all(), Sucursal.objects.all()),
        label='Origen',
        required=False,
    )   

    destino= autocomplete.Select2GenericForeignKeyModelField(
        queryset=QuerySetSequence(Deposito.objects.all(), Sucursal.objects.all()),
        label='Destino',
        required=True,
    )

    articulo_foraneo = forms.ModelChoiceField(
        queryset=None,
        label="Articulo",
        widget=forms.Select()
    )

    usuario_foraneo = forms.ModelChoiceField(
        queryset=Usuario.objects.all(),
        label="Usuario",
        widget=forms.Select()
    )

    class Meta:
        model = MovimientoArticulo
        fields = ['origen','destino', 'articulo_foraneo', 'cantidad','usuario_foraneo', 'observaciones']

 
    def clean(self):
        cleaned_data = super().clean()
        origen = cleaned_data.get('origen')
        destino = cleaned_data.get('destino')

        #VALIDACIONES
        
        #ORIGEN Y DESTINO VACIO
        if not origen and not destino:
            raise ValidationError("Debes seleccionar al menos un contenido.")
        
        #ORIGEN VACIO Y DESTINO SUCURSAL
        if origen==None and isinstance(destino, Sucursal):
            raise ValidationError('No indico un Deposito de Origen valido, No se realizo la operacion')
                
        #ORIGEN DEPOSITO Y DESTINO DEPOSITO
        if isinstance(origen, Deposito) and isinstance(destino, Deposito):
            raise ValidationError('Opción movimiento entre depositos no disponible')
        
        #ORIGEN SUCURSAL Y DESTINO SUCURSAL
        if isinstance(origen, Sucursal) and isinstance(destino, Sucursal):
            raise ValidationError('Opción movimiento entre Sucursales no esta permitido')
        
        # ORIGEN IGUAL A DESTINO
        if origen == destino:
            print('ORIGEN IGUAL A DESTINO')
            print(origen)
            print(destino)
            raise ValidationError('El Origen y Destino del movimiento deben ser diferentes')
        
        # CANTIDAD ES NULO
        if cleaned_data.get('cantidad') is None:
            raise ValidationError('El valor de cantidad no puede ser Nulo')
        # CANTIDAD MENOR QUE CERO
        if cleaned_data.get('cantidad') < 0:
            raise ValidationError('El valor de cantidad no puede ser Negativo (<0)')
        
        #MOVIMIENTO DE DEPOSITO A SUCURSAL MAYOR DEL DISPONIBLE EN DEPOSITO (CANT NEGATIVA EN DEPOSITO)
        if isinstance(origen, Deposito) and isinstance(destino, Sucursal):
            if not verificar_minimo_en_deposito(cleaned_data):
                raise ValidationError('Cantidad insuficiente en deposito para este movimiento')
            
        #DEVOLUCION DE SUCURSAL a DEPOSITO MAYOR DEL DISPONIBLE EN SUCURSAL (CANT NEGATIVA EN SUCURSAL)
        if isinstance(origen, Sucursal) and isinstance(destino, Deposito):
            if not verificar_minimo_en_sucursal(cleaned_data):
                raise ValidationError('Cantidad insuficiente en sucursal para este movimiento')
        
        return cleaned_data

    def clean_origen(self):
        origen = self.cleaned_data['origen']
        print('aqui seteamos None en caso de que el origen venga vacio')
        try:
            if not origen:
                print('entro not origen')
                return None
            else:
                return origen
        except:
            return origen
        

    def clean_destino(self):
        destino = self.cleaned_data['destino']
        print('imprimo validacion destino')
        if not destino:
            raise ValidationError("Campo Destino no puede estar vacío.")
        return destino   
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['origen'].label_from_instance = self.label_from_instance
        self.fields['destino'].label_from_instance = self.label_from_instance
        self.fields['articulo_foraneo'].queryset = Articulo.objects.all()

    def label_from_instance(self, obj):
        # Personaliza cómo se muestra cada objeto en el campo queryset_sequence
        if isinstance(obj, Deposito):
            return f'DEPOSITO - {obj.nombre}'
        elif isinstance(obj, Sucursal):
            return f'SUCURSAL - {obj.nombre}'
        return str(obj)
    