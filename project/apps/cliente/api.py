from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, permissions, viewsets

from cliente.models import Cliente
from cliente.serializers import ClienteSerializer


class ClienteViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    # Sin destroy() a propósito: Venta.cliente es on_delete=CASCADE, así que borrar un Cliente
    # borraría TODO su historial de ventas. No hay ningún caso de uso real de "borrar un
    # cliente" (a lo sumo, dar de baja/desactivar, que ni siquiera existe como campo hoy) — más
    # vale no exponer la acción que arriesgar un borrado en cascada por error.
    #
    # Orden por defecto igual al de la pantalla de venta legacy (venta/views.get_clientes):
    # apellido de la persona asociada.
    queryset = Cliente.objects.select_related('persona', 'lista_precio').order_by('persona__apellido')
    serializer_class = ClienteSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_fields = ('condicion_iva', 'lista_precio')
    search_fields = ('persona__nombre', 'persona__apellido', 'persona__documento_identidad')
    ordering_fields = ('persona__apellido', 'fecha_alta')
