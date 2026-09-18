from decimal import Decimal

from rest_framework import serializers

from cuentacorriente.constants import DEBITO
from cuentacorriente.models import CuentaCorriente, MovimientoCuentaCorriente
from cuentacorriente.utils import calcular_saldo_cc


class CuentaCorrienteSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cliente.persona.obtener_nombre_completo', read_only=True)
    # Reutiliza el mismo cálculo que usa hoy el Admin/JS legacy (cuentacorriente.utils), no se
    # duplica la fórmula acá — especificaciones.md §14.
    saldo = serializers.SerializerMethodField()

    class Meta:
        model = CuentaCorriente
        fields = ('id', 'cliente', 'cliente_nombre', 'tope', 'fecha', 'observaciones', 'activa', 'saldo')
        read_only_fields = ('fecha',)

    def get_saldo(self, obj):
        # str() explícito: un SerializerMethodField no pasa por el formateo de DecimalField, y el
        # encoder JSON de DRF convierte Decimal "suelto" a float — riesgo de precisión en dinero.
        # Así queda consistente con el resto de los campos monetarios (ej. `tope`, `importe`).
        return str(calcular_saldo_cc(obj))


class MovimientoCuentaCorrienteSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(
        source='cuenta.cliente.persona.obtener_nombre_completo', read_only=True
    )
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = MovimientoCuentaCorriente
        fields = (
            'id',
            'cuenta',
            'cliente_nombre',
            'importe',
            'fecha',
            'tipo',
            'tipo_display',
            'usuario',
            'usuario_username',
            'venta',
            'observaciones',
        )
        # `usuario` se asigna server-side desde request.user (ver
        # CuentaCorrienteApi.MovimientoCuentaCorrienteViewSet.perform_create), nunca se confía en
        # quién dice el frontend que hizo el movimiento.
        read_only_fields = ('fecha', 'usuario')

    def validate_importe(self, value):
        if value <= 0:
            raise serializers.ValidationError('El importe debe ser mayor que cero.')
        return value

    def validate(self, attrs):
        # El modelo no valida esto (riesgo detectado en la auditoría, SISTEMA_ACTUAL.md §15.6:
        # hoy se puede superar sin aviso). Lo agregamos acá, en la capa nueva, sin tocar el
        # modelo ni el código legacy que lo sigue usando sin este control.
        #
        # La cuenta corriente es un saldo a favor del cliente, no una línea de crédito: no se le
        # permite quedar debiendo dinero al negocio, así que un débito nunca puede superar lo que
        # tiene disponible (saldo negativo = a favor).
        tipo = attrs.get('tipo', getattr(self.instance, 'tipo', None))
        if self.instance is None and tipo == DEBITO:
            cuenta = attrs['cuenta']
            importe = attrs['importe']
            saldo_actual = calcular_saldo_cc(cuenta)
            disponible = -saldo_actual if saldo_actual < 0 else Decimal('0')
            if importe > disponible:
                raise serializers.ValidationError({
                    'importe': (
                        f'El movimiento (${importe}) supera el saldo a favor disponible del '
                        f'cliente (${disponible}).'
                    )
                })
        return attrs
