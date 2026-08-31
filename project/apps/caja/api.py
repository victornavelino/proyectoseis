from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from caja.exceptions import CajaError
from caja.models import Caja, CuponPagoTarjeta, PagoTransferencia, PlanTarjetaDeCredito, TarjetaDeCredito
from caja.serializers import (
    CajaSerializer,
    CobrarVentaInputSerializer,
    CuponPagoTarjetaSerializer,
    PagoTransferenciaSerializer,
    PlanTarjetaDeCreditoSerializer,
    TarjetaDeCreditoSerializer,
)
from caja.services import abrir_caja, cerrar_caja
from caja.services import cobrar_venta as cobrar_venta_service
from caja.utils import (
    calcular_egresos_caja,
    calcular_ingresos_caja,
    calcular_total_compras_cc,
    calcular_total_egresos,
    calcular_total_ingresos,
)
from util.permissions import IsStaffOrReadOnly


class TarjetaDeCreditoViewSet(viewsets.ModelViewSet):
    queryset = TarjetaDeCredito.objects.all()
    serializer_class = TarjetaDeCreditoSerializer
    permission_classes = (IsStaffOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('nombre', 'banco')


class PlanTarjetaDeCreditoViewSet(viewsets.ModelViewSet):
    queryset = PlanTarjetaDeCredito.objects.select_related('tarjeta')
    serializer_class = PlanTarjetaDeCreditoSerializer
    permission_classes = (IsStaffOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('tarjeta',)


class CuponPagoTarjetaViewSet(viewsets.ReadOnlyModelViewSet):
    # Se crean sólo vía CajaViewSet.cobrar_venta (recargo recalculado en servidor) -> sólo lectura.
    queryset = CuponPagoTarjeta.objects.select_related('cliente__persona', 'plan_tarjeta__tarjeta', 'venta')
    serializer_class = CuponPagoTarjetaSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('cliente', 'venta', 'plan_tarjeta')


class PagoTransferenciaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PagoTransferencia.objects.select_related('venta')
    serializer_class = PagoTransferenciaSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('venta',)


class CajaViewSet(viewsets.ReadOnlyModelViewSet):
    # Abrir/cerrar/cobrar son acciones de negocio dedicadas (transaccionales), no un
    # create()/update() de CRUD genérico -> ReadOnlyModelViewSet (list/retrieve) + acciones.
    queryset = Caja.objects.select_related('sucursal', 'usuario')
    serializer_class = CajaSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('sucursal', 'fecha_fin')

    @action(detail=False, methods=['post'])
    def abrir(self, request):
        try:
            caja = abrir_caja(usuario=request.user)
        except CajaError as exc:
            raise DRFValidationError({'caja': str(exc)})
        return Response(CajaSerializer(caja).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cerrar(self, request, pk=None):
        caja = self.get_object()
        try:
            caja = cerrar_caja(caja)
        except CajaError as exc:
            raise DRFValidationError({'caja': str(exc)})
        data = CajaSerializer(caja).data
        # Desglose de cierre (reutiliza caja.utils, no se duplica la fórmula):
        data['ingresos'] = calcular_ingresos_caja(caja)
        data['total_ingresos'] = calcular_total_ingresos(caja)
        data['egresos'] = calcular_egresos_caja(caja)
        data['total_egresos'] = calcular_total_egresos(caja)
        data['total_cuenta_corriente'] = calcular_total_compras_cc(caja)
        return Response(data)

    @action(detail=False, methods=['post'], url_path='cobrar-venta')
    def cobrar_venta(self, request):
        """Cobro combinado de una venta. Body:
        `{"venta": <numero_ticket>, "pagos_efectivo": [...], "pagos_tarjeta": [...],
        "pagos_cuenta_corriente": [...], "pagos_transferencia": [...]}` (las 4 listas de pagos
        son opcionales, pero al menos una no puede estar vacía). Ver `caja/services.py` para el
        detalle de qué valida y qué corrige respecto al flujo legacy.
        """
        entrada = CobrarVentaInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data
        try:
            venta = cobrar_venta_service(
                venta=datos['venta'],
                pagos_efectivo=datos['pagos_efectivo'],
                pagos_tarjeta=datos['pagos_tarjeta'],
                pagos_cuenta_corriente=datos['pagos_cuenta_corriente'],
                pagos_transferencia=datos['pagos_transferencia'],
                usuario=request.user,
            )
        except CajaError as exc:
            raise DRFValidationError({'pagos': str(exc)})

        from venta.serializers import VentaSerializer  # import diferido: evita ciclo caja <-> venta

        return Response(VentaSerializer(venta).data, status=status.HTTP_200_OK)
