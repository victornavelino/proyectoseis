from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets

from cuentacorriente.models import CuentaCorriente, MovimientoCuentaCorriente
from cuentacorriente.serializers import CuentaCorrienteSerializer, MovimientoCuentaCorrienteSerializer
from util.permissions import IsStaffOrReadOnly


class CuentaCorrienteViewSet(viewsets.ModelViewSet):
    # Abrir/configurar una cuenta corriente (tope, activa) es una decisión de crédito, no una
    # operación de mostrador del día a día -> igual criterio que articulo: sólo staff escribe.
    queryset = CuentaCorriente.objects.select_related('cliente__persona')
    serializer_class = CuentaCorrienteSerializer
    permission_classes = (IsStaffOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = ('cliente', 'activa')
    search_fields = (
        'cliente__persona__nombre',
        'cliente__persona__apellido',
        'cliente__persona__documento_identidad',
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
        serializer.save(usuario=self.request.user)
