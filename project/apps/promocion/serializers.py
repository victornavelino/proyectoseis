from rest_framework import serializers

from promocion.models import Descuento, DiasSemana, Promocion, PromocionArticulo


class DiasSemanaSerializer(serializers.ModelSerializer):
    dias_texto = serializers.CharField(source='obtener_dias', read_only=True)

    class Meta:
        model = DiasSemana
        fields = (
            'id',
            'lunes',
            'martes',
            'miercoles',
            'jueves',
            'viernes',
            'sabado',
            'domingo',
            'dias_texto',
        )


class PromocionArticuloSerializer(serializers.ModelSerializer):
    articulo_nombre = serializers.CharField(source='articulo.nombre', read_only=True)
    articulo_codigo = serializers.CharField(source='articulo.codigo', read_only=True)

    class Meta:
        model = PromocionArticulo
        fields = ('id', 'promocion', 'articulo', 'articulo_nombre', 'articulo_codigo', 'valor')


class PromocionSerializer(serializers.ModelSerializer):
    # El modelo permite `dias_semana` nulo a nivel de base (para no romper datos viejos), pero
    # `Promocion.clean()` lo exige siempre — lo pedimos también acá para que el error se vea ya
    # en la validación del serializer, sin depender sólo del full_clean() del modelo.
    dias_semana = serializers.PrimaryKeyRelatedField(queryset=DiasSemana.objects.all())
    dias_semana_detalle = DiasSemanaSerializer(source='dias_semana', read_only=True)
    sucursal_nombre = serializers.CharField(source='sucursal.nombre', read_only=True, default=None)
    articulos = PromocionArticuloSerializer(source='promocionarticulo_set', many=True, read_only=True)

    class Meta:
        model = Promocion
        fields = (
            'id',
            'nombre',
            'fecha_inicio',
            'fecha_fin',
            'es_por_precio',
            'porcentaje_todos',
            'dias_semana',
            'dias_semana_detalle',
            'habilitada',
            'prioridad',
            'sucursal',
            'sucursal_nombre',
            'observaciones',
            'articulos',
        )

    # Nota: las reglas de negocio (es_por_precio vs. porcentaje_todos, prioridad única por
    # sucursal, etc.) están en `Promocion.clean()`, que se ejecuta desde `Promocion.save()`. No
    # se duplican acá a propósito — así Django Admin y esta API comparten la misma validación
    # (especificaciones.md §14). El ViewSet traduce el `django.core.exceptions.ValidationError`
    # resultante a un 400 de DRF (ver `util.mixins.TranslateDjangoValidationErrorMixin`).


class DescuentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Descuento
        fields = ('id', 'nombre', 'valor')
