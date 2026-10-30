from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from cuentacorriente.constants import CREDITO, QR
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
        # DRF ya arma un UniqueValidator solo a partir de `unique=True` en el modelo, pero con el
        # mensaje genérico de DRF ("this field must be unique") en vez del `error_messages` del
        # modelo — se lo pisa acá explícitamente para que sea el mismo cartel en toda la app.
        extra_kwargs = {
            'cliente': {
                'validators': [
                    UniqueValidator(
                        queryset=CuentaCorriente.objects.all(),
                        message='El cliente ya tiene una cuenta corriente!',
                    )
                ]
            }
        }

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
    medio_pago_display = serializers.CharField(source='get_medio_pago_display', read_only=True, default=None)
    banco_nombre = serializers.CharField(source='banco.nombre', read_only=True, default=None)
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
            'medio_pago',
            'medio_pago_display',
            'banco',
            'banco_nombre',
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

    def validate(self, data):
        # Sólo tiene sentido en un Crédito (con qué pagó el cliente) -un Débito es un consumo a
        # cuenta, no hay plata entrando para la que elegir medio de pago-.
        if data.get('tipo') == CREDITO and not data.get('medio_pago'):
            raise serializers.ValidationError({'medio_pago': 'Elegí con qué medio de pago se cargó el crédito.'})
        # Mismo criterio que venta.CobroVentaPage: en QR el cajero tiene que poder identificar el
        # pago sí o sí -> banco obligatorio. En transferencia queda opcional (dato que puede no
        # tenerse a mano en el momento).
        if data.get('medio_pago') == QR and not data.get('banco'):
            raise serializers.ValidationError({'banco': 'Elegí con qué banco se recibió el pago por QR.'})
        return data
    # El tope de la cuenta (para un Débito) se valida en cuentacorriente.services
    # .crear_movimiento_cuenta_corriente -no acá-, porque ese mismo chequeo también lo necesita
    # caja.services.cobrar_venta al pagar una venta con este medio; mantenerlo en un solo lugar
    # evita que las dos fórmulas se desincronicen.
