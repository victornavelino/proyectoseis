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
    calcular_total_compras_transf,
    calcular_total_egresos,
    calcular_total_ingresos,
)
from util.pdf import render_pdf_response
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
    # 'fecha_fin' necesita el lookup 'isnull' explícito: el frontend usa
    # ?fecha_fin__isnull=true para pedir la caja abierta de la sucursal
    # (api/caja.ts cajaAbiertaActual). Con filterset_fields como tupla plana,
    # django-filter sólo genera el lookup 'exact' -> ese query param no matcheaba
    # ningún filtro y se ignoraba en silencio, así que "caja abierta" devolvía
    # simplemente la última caja de la sucursal (esté abierta o cerrada).
    filterset_fields = {
        'sucursal': ['exact'],
        'fecha_fin': ['exact', 'isnull'],
    }

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

    @action(detail=True, methods=['get'])
    def imprimir(self, request, pk=None):
        """Resumen de cierre de caja en PDF (ticket imprimible). Mismo template y misma
        construcción de contexto que la acción de admin equivalente
        (`CajaAdmin.imprimir_cierre_caja`/la vista legacy `caja.views.imprimir_cierre_caja_pdf`)
        — ver ROADMAP.md etapa 16: ninguna de esas dos era alcanzable desde el frontend nuevo (una
        exige sesión de Django, no el Bearer token de la API), así que quedaba huérfana.
        Sólo para cajas ya cerradas: los totales de cta. cte./transferencias del período
        (`caja/utils.py`) filtran por `fecha__lte=caja.fecha_fin`, que es None mientras la caja
        sigue abierta.
        """
        caja = self.get_object()
        if caja.fecha_fin is None:
            raise DRFValidationError({'caja': 'La caja está abierta: cerrala primero para poder imprimir el resumen.'})
        return render_pdf_response(
            request=request._request,
            template='admin/caja/ticket_cierre_caja.html',
            filename=f'caja-{caja.fecha_fin}.pdf',
            context={
                'caja': caja,
                'ingresos': calcular_ingresos_caja(caja),
                'total_ingresos': calcular_total_ingresos(caja),
                'egresos': calcular_egresos_caja(caja),
                'total_egresos': calcular_total_egresos(caja),
                'total_ccorrientes': calcular_total_compras_cc(caja),
                'total_transferencias': calcular_total_compras_transf(caja),
            },
            show_content_in_browser=True,
        )

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
