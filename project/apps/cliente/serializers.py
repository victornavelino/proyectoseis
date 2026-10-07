from rest_framework import serializers

from cliente.models import Cliente
from persona.serializers import PersonaSerializer


class ClienteSerializer(serializers.ModelSerializer):
    persona_detalle = PersonaSerializer(source='persona', read_only=True)
    condicion_iva_display = serializers.CharField(source='get_condicion_iva_display', read_only=True)
    lista_precio_nombre = serializers.CharField(source='lista_precio.nombre', read_only=True, default=None)

    class Meta:
        model = Cliente
        fields = (
            'id',
            'persona',
            'persona_detalle',
            'condicion_iva',
            'condicion_iva_display',
            'lista_precio',
            'lista_precio_nombre',
            'fecha_alta',
        )
        read_only_fields = ('fecha_alta',)
