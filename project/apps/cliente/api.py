from django.db.models import ProtectedError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, permissions, viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError

from cliente.models import Cliente
from cliente.serializers import ClienteSerializer
from util.permissions import TienePermisoDeModelo
from venta.models import Venta


class ClienteViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    # Orden por defecto igual al de la pantalla de venta legacy (venta/views.get_clientes):
    # apellido de la persona asociada.
    queryset = Cliente.objects.select_related('persona', 'lista_precio').order_by('persona__apellido')
    serializer_class = ClienteSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_fields = ('condicion_iva', 'lista_precio')
    search_fields = ('persona__nombre', 'persona__apellido', 'persona__documento_identidad')
    ordering_fields = ('persona__apellido', 'fecha_alta')

    def get_permissions(self):
        # Crear/editar un cliente es operación normal de mostrador (cualquier autenticado, ver
        # arriba), pero eliminarlo es una acción más delicada -> exige el permiso Django
        # `cliente.delete_cliente` (otorgable por grupo desde /admin), mismo criterio que el
        # resto del catálogo (artículos, categorías, etc.).
        if self.action == 'destroy':
            return [TienePermisoDeModelo()]
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        # Venta.cliente es on_delete=CASCADE (a diferencia de CuentaCorriente.cliente y
        # CobroVenta.cliente, que son PROTECT): sin este chequeo, borrar un cliente con ventas
        # borraría TODO su historial de ventas de verdad, no algo recuperable. Se bloquea ese
        # caso explícitamente, y se atrapa ProtectedError como red de seguridad para las
        # relaciones PROTECT (cuenta corriente, cobros de caja).
        instance = self.get_object()
        if Venta.objects.filter(cliente=instance).exists():
            raise DRFValidationError('No se puede eliminar: el cliente tiene ventas registradas.')
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            raise DRFValidationError(
                'No se puede eliminar: el cliente tiene una cuenta corriente o cobros registrados.'
            )
