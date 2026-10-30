from rest_framework import serializers

from empleado.models import Empleado, Sucursal


class SucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = ('id', 'nombre', 'domicilio')


class EmpleadoSerializer(serializers.ModelSerializer):
    persona_nombre = serializers.CharField(source='persona.obtener_nombre_completo', read_only=True)
    activo = serializers.SerializerMethodField()

    class Meta:
        model = Empleado
        fields = ('id', 'persona', 'persona_nombre', 'cuil', 'fecha_baja', 'activo')

    def get_activo(self, obj):
        return obj.fecha_baja is None
