from rest_framework import serializers

from articulo.models import Articulo
from cliente.models import Cliente
from empleado.models import Empleado
from venta.models import Venta, VentaArticulo


class VentaArticuloSerializer(serializers.ModelSerializer):
    articulo_codigo = serializers.CharField(source='articulo.codigo', read_only=True)

    class Meta:
        model = VentaArticulo
        fields = (
            'id',
            'articulo',
            'articulo_codigo',
            'nombre_articulo',
            'codigo_articulo',
            'cantidad_peso',
            'precio_unitario',
            'precio_promocion',
            'total_articulo',
        )
        read_only_fields = fields


class VentaSerializer(serializers.ModelSerializer):
    """Sólo lectura: la venta se crea exclusivamente vía la acción `crear` del ViewSet
    (transaccional, con recálculo de precio server-side), nunca por `POST` directo sobre este
    serializer — ver `venta/services.py` y `especificaciones.md` §4 ("una operación de venta
    probablemente no deba consistir simplemente en CRUD directo")."""

    cliente_nombre = serializers.CharField(source='cliente.persona.obtener_nombre_completo', read_only=True)
    empleado_nombre = serializers.CharField(source='empleado.persona.obtener_nombre_completo', read_only=True)
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    sucursal_nombre = serializers.CharField(source='sucursal.nombre', read_only=True)
    articulos = VentaArticuloSerializer(source='ventaarticulo_set', many=True, read_only=True)

    class Meta:
        model = Venta
        fields = (
            'numero_ticket',
            'fecha',
            'monto',
            'descuento',
            'anulado',
            'cobrada',
            'sucursal',
            'sucursal_nombre',
            'cliente',
            'cliente_nombre',
            'empleado',
            'empleado_nombre',
            'usuario',
            'usuario_username',
            'articulos',
        )
        read_only_fields = fields


class ItemVentaInputSerializer(serializers.Serializer):
    articulo = serializers.PrimaryKeyRelatedField(queryset=Articulo.objects.all())
    # El peso/cantidad sí viene del frontend (lo lee la balanza física del mostrador, PEND-F); lo
    # que NUNCA viene del frontend es el precio — eso se recalcula en servidor.
    cantidad_peso = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate_cantidad_peso(self, value):
        if value <= 0:
            raise serializers.ValidationError('La cantidad/peso debe ser mayor que cero.')
        return value


class CrearVentaInputSerializer(serializers.Serializer):
    empleado = serializers.PrimaryKeyRelatedField(queryset=Empleado.objects.filter(fecha_baja__isnull=True))
    cliente = serializers.PrimaryKeyRelatedField(queryset=Cliente.objects.all())
    articulos = ItemVentaInputSerializer(many=True)

    def validate_articulos(self, value):
        if not value:
            raise serializers.ValidationError('Debe incluir al menos un artículo.')
        return value


class PrevisualizarVentaInputSerializer(serializers.Serializer):
    """Entrada de la acción `previsualizar` — mismos datos que `crear` pero sin `empleado` (no
    hace falta para calcular precio) y no persiste nada. Ver venta/api.py."""

    cliente = serializers.PrimaryKeyRelatedField(queryset=Cliente.objects.all())
    articulos = ItemVentaInputSerializer(many=True)

    def validate_articulos(self, value):
        if not value:
            raise serializers.ValidationError('Debe incluir al menos un artículo.')
        return value


class ItemPrevisualizadoSerializer(serializers.Serializer):
    articulo = serializers.IntegerField()
    articulo_nombre = serializers.CharField()
    cantidad_peso = serializers.DecimalField(max_digits=12, decimal_places=2)
    precio_unitario = serializers.DecimalField(max_digits=12, decimal_places=2)
    precio_promocion = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_articulo = serializers.DecimalField(max_digits=12, decimal_places=2)


class VentaPrevisualizadaSerializer(serializers.Serializer):
    articulos = ItemPrevisualizadoSerializer(many=True)
    monto = serializers.DecimalField(max_digits=12, decimal_places=2)
