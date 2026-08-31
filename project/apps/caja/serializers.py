from decimal import Decimal

from rest_framework import serializers

from caja.models import Caja, CuponPagoTarjeta, PagoTransferencia, PlanTarjetaDeCredito, TarjetaDeCredito
from caja.utils import calcular_saldo_caja
from venta.models import Venta


class TarjetaDeCreditoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TarjetaDeCredito
        fields = ('id', 'nombre', 'banco')


class PlanTarjetaDeCreditoSerializer(serializers.ModelSerializer):
    tarjeta_nombre = serializers.CharField(source='tarjeta.nombre', read_only=True)

    class Meta:
        model = PlanTarjetaDeCredito
        fields = ('id', 'tarjeta', 'tarjeta_nombre', 'nombre_plan', 'interes', 'es_vale')


class CajaSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    sucursal_nombre = serializers.CharField(source='sucursal.nombre', read_only=True)
    # Reutiliza el mismo cálculo que el Admin/JS legacy (caja.utils.calcular_saldo_caja), no se
    # duplica la fórmula acá — especificaciones.md §14.
    saldo_actual = serializers.SerializerMethodField()

    class Meta:
        model = Caja
        fields = (
            'id',
            'sucursal',
            'sucursal_nombre',
            'usuario',
            'usuario_username',
            'fecha_inicio',
            'fecha_fin',
            'caja_inicial',
            'caja_final',
            'saldo_actual',
        )
        # Todo de sólo lectura: abrir/cerrar son las acciones dedicadas del ViewSet (no un
        # create()/update() de CRUD genérico), igual criterio que `venta`.
        read_only_fields = fields

    def get_saldo_actual(self, obj):
        return str(calcular_saldo_caja(obj))


class CuponPagoTarjetaSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cliente.persona.obtener_nombre_completo', read_only=True)
    plan_nombre = serializers.CharField(source='plan_tarjeta.nombre_plan', read_only=True)
    tarjeta_nombre = serializers.CharField(source='plan_tarjeta.tarjeta.nombre', read_only=True)

    class Meta:
        model = CuponPagoTarjeta
        fields = (
            'id',
            'cliente',
            'cliente_nombre',
            'plan_tarjeta',
            'plan_nombre',
            'tarjeta_nombre',
            'numero_tarjeta',
            'importe',
            'recargo',
            'importe_con_recargo',
            'numero_cupon',
            'lote',
            'fecha',
            'venta',
            'observaciones',
        )
        # Sólo lectura: se crean exclusivamente vía CajaViewSet.cobrar_venta (recargo
        # recalculado en servidor) — ver caja/services.py.
        read_only_fields = fields


class PagoTransferenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PagoTransferencia
        fields = (
            'id',
            'importe',
            'nombre',
            'apellido',
            'documento_identidad',
            'banco',
            'fecha',
            'venta',
            'observaciones',
        )
        read_only_fields = fields


# --- Entrada de CajaViewSet.cobrar_venta (no son ModelSerializer: no persisten solas) ---

class PagoEfectivoInputSerializer(serializers.Serializer):
    importe = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))


class PagoTarjetaInputSerializer(serializers.Serializer):
    plan_tarjeta = serializers.PrimaryKeyRelatedField(queryset=PlanTarjetaDeCredito.objects.all())
    numero_tarjeta = serializers.CharField(max_length=16, required=False, allow_blank=True)
    importe = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    numero_cupon = serializers.CharField(max_length=10, required=False, allow_blank=True, allow_null=True)
    lote = serializers.CharField(max_length=10, required=False, allow_blank=True, allow_null=True)
    observaciones = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    # Nota: `recargo`/`importe_con_recargo` NO se reciben acá a propósito — se recalculan en
    # servidor a partir de `plan_tarjeta.interes` (caja/services.py), nunca se confían del
    # frontend (SISTEMA_ACTUAL.md §15.5).


class PagoCuentaCorrienteInputSerializer(serializers.Serializer):
    importe = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    observaciones = serializers.CharField(max_length=40, required=False, allow_blank=True, allow_null=True)


class PagoTransferenciaInputSerializer(serializers.Serializer):
    importe = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    nombre = serializers.CharField(max_length=40, required=False, allow_blank=True, allow_null=True)
    apellido = serializers.CharField(max_length=30, required=False, allow_blank=True, allow_null=True)
    documento_identidad = serializers.CharField(max_length=12)
    banco = serializers.CharField(max_length=60, required=False, allow_blank=True, allow_null=True)
    observaciones = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)


class CobrarVentaInputSerializer(serializers.Serializer):
    venta = serializers.PrimaryKeyRelatedField(queryset=Venta.objects.all())
    pagos_efectivo = PagoEfectivoInputSerializer(many=True, required=False, default=list)
    pagos_tarjeta = PagoTarjetaInputSerializer(many=True, required=False, default=list)
    pagos_cuenta_corriente = PagoCuentaCorrienteInputSerializer(many=True, required=False, default=list)
    pagos_transferencia = PagoTransferenciaInputSerializer(many=True, required=False, default=list)

    def validate(self, attrs):
        if not any([
            attrs.get('pagos_efectivo'),
            attrs.get('pagos_tarjeta'),
            attrs.get('pagos_cuenta_corriente'),
            attrs.get('pagos_transferencia'),
        ]):
            raise serializers.ValidationError('Debe incluir al menos un medio de pago.')
        return attrs
