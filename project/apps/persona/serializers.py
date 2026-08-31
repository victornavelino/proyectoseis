from rest_framework import serializers

from persona.models import Persona
from util.models import Telefono
from util.serializers import TelefonoSerializer


class PersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = (
            'id',
            'nombre',
            'apellido',
            'documento_identidad',
            'fecha_nacimiento',
            'domicilio',
            'correo_electronico',
            'telefonos',
        )

    telefonos = TelefonoSerializer(many=True, required=False)

    def extraer_telefono(self):
        telefono = ''
        if hasattr(self, 'initial_data') and 'telefono' in self.initial_data:
            telefono = self.initial_data.pop('telefono')
        return telefono

    # `telefonos` es una GenericRelation (relación inversa) — un ModelSerializer plano no sabe
    # crear/actualizar relaciones inversas solo, hay que decirle cómo. Sin esto,
    # `Persona.objects.create(**validated_data)` intenta pasarle `telefonos` como si fuera un
    # campo propio del modelo y Django lo rechaza (`TypeError: Direct assignment to the reverse
    # side...`) — bug real encontrado al probar el alta de clientes desde el frontend.
    def create(self, validated_data):
        telefonos_data = validated_data.pop('telefonos', [])
        persona = Persona.objects.create(**validated_data)
        for telefono_data in telefonos_data:
            persona.telefonos.add(Telefono(**telefono_data), bulk=False)
        return persona

    def update(self, instance, validated_data):
        telefonos_data = validated_data.pop('telefonos', None)
        instance = super().update(instance, validated_data)
        if telefonos_data is not None:
            instance.telefonos.all().delete()
            for telefono_data in telefonos_data:
                instance.telefonos.add(Telefono(**telefono_data), bulk=False)
        return instance


class DocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = (
            'documento_identidad',
        )
