from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from facturacion.exceptions import FacturacionError
from facturacion.models import ComprobanteVenta
from facturacion.serializers import ComprobanteVentaSerializer
from facturacion.services import generar_y_emitir_comprobante
from util.permissions import TienePermiso
from venta.models import Venta


class ComprobanteVentaViewSet(viewsets.ReadOnlyModelViewSet):
    # Nunca se crea/edita por CRUD genérico: sólo se genera (y reintenta) vía la acción
    # 'emitir', que delega en facturacion.services.generar_y_emitir_comprobante.
    queryset = ComprobanteVenta.objects.select_related('venta', 'receipt', 'receipt__validation')
    serializer_class = ComprobanteVentaSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('venta', 'estado')

    def get_permissions(self):
        # Emitir un comprobante fiscal es más sensible que ver el listado -> permiso puntual
        # propio, no cualquier autenticado (ver CajaViewSet.get_permissions, mismo criterio).
        if self.action == 'emitir':
            return [TienePermiso('facturacion.add_comprobanteventa')]
        return super().get_permissions()

    @action(detail=False, methods=['post'], url_path='emitir')
    def emitir(self, request):
        venta_id = request.data.get('venta')
        if not venta_id:
            raise DRFValidationError({'venta': 'Este campo es obligatorio.'})
        try:
            venta = Venta.objects.get(pk=venta_id)
        except Venta.DoesNotExist:
            raise DRFValidationError({'venta': 'No existe esa venta.'})

        try:
            comprobante = generar_y_emitir_comprobante(venta)
        except FacturacionError as exc:
            raise DRFValidationError({'venta': str(exc)})

        return Response(ComprobanteVentaSerializer(comprobante).data)
