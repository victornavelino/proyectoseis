from rest_framework import serializers

from facturacion.models import ComprobanteVenta


class ComprobanteVentaSerializer(serializers.ModelSerializer):
    numero_formateado = serializers.CharField(source='receipt.formatted_number', read_only=True, default=None)
    cae = serializers.CharField(source='receipt.validation.cae', read_only=True, default=None)

    class Meta:
        model = ComprobanteVenta
        fields = (
            'id',
            'venta',
            'estado',
            'mensaje_error',
            'numero_formateado',
            'cae',
            'fecha_creacion',
            'fecha_actualizacion',
        )
        read_only_fields = fields
