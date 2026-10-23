from django.db.models import ProtectedError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError

from caja.exceptions import CajaError
from cuentacorriente.models import CuentaCorriente, MovimientoCuentaCorriente
from cuentacorriente.serializers import CuentaCorrienteSerializer, MovimientoCuentaCorrienteSerializer
from cuentacorriente.services import crear_movimiento_cuenta_corriente
from util.permissions import TienePermisoDeModelo


class CuentaCorrienteViewSet(viewsets.ModelViewSet):
    # Abrir/configurar una cuenta corriente (tope, activa) es una decisión de crédito, no una
    # operación de mostrador del día a día -> igual criterio que articulo: sólo staff escribe.
    queryset = CuentaCorriente.objects.select_related('cliente__persona')
    serializer_class = CuentaCorrienteSerializer
    permission_classes = (TienePermisoDeModelo,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = ('cliente', 'activa')
    search_fields = (
        'cliente__persona__nombre',
        'cliente__persona__apellido',
        'cliente__persona__documento_identidad',
    )

    def destroy(self, request, *args, **kwargs):
        # MovimientoCuentaCorriente.cuenta es on_delete=PROTECT (no se quiere perder historial
        # de cobros por accidente) -> sin este try/except, borrar una cuenta con movimientos
        # tira un ProtectedError sin atrapar y responde 500 en vez de un 400 explicable.
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            raise DRFValidationError(
                'No se puede eliminar: la cuenta corriente tiene movimientos registrados.'
            )


class MovimientoCuentaCorrienteViewSet(viewsets.ModelViewSet):
    # Registrar un pago o un consumo a cuenta corriente sí es operación normal de mostrador
    # (igual que cobrar una venta) -> cualquier autenticado, no sólo staff.
    queryset = MovimientoCuentaCorriente.objects.select_related('cuenta__cliente__persona', 'usuario', 'venta')
    serializer_class = MovimientoCuentaCorrienteSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    # Uso típico: GET /api/v1/movimientocuentacorriente/?cuenta=<id> para el historial de un cliente.
    filterset_fields = ('cuenta', 'tipo', 'venta')

    def perform_create(self, serializer):
        # Delega en el service (no serializer.save() directo): un Crédito tiene que generar
        # además un Ingreso en caja, y un Débito se valida contra el tope de la cuenta -ver
        # cuentacorriente.services.crear_movimiento_cuenta_corriente, mismo código que usa
        # caja.services.cobrar_venta para el pago con este medio-.
        try:
            instancia = crear_movimiento_cuenta_corriente(usuario=self.request.user, **serializer.validated_data)
        except CajaError as exc:
            raise DRFValidationError({'importe': str(exc)})
        serializer.instance = instancia
