import copy

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from caja.exceptions import CajaError
from caja.models import (
    Adelanto,
    Caja,
    CuponPagoTarjeta,
    Gasto,
    Ingreso,
    PagoTransferencia,
    PlanTarjetaDeCredito,
    RetiroEfectivo,
    Sueldo,
    TarjetaDeCredito,
    TipoGasto,
    TipoIngreso,
)
from caja.serializers import (
    AdelantoSerializer,
    CajaSerializer,
    CerrarCajaInputSerializer,
    CobrarVentaInputSerializer,
    CuponPagoTarjetaSerializer,
    GastoSerializer,
    IngresoSerializer,
    PagoTransferenciaSerializer,
    PlanTarjetaDeCreditoSerializer,
    RetiroEfectivoSerializer,
    SueldoSerializer,
    TarjetaDeCreditoSerializer,
    TipoGastoSerializer,
    TipoIngresoSerializer,
)
from caja.services import abrir_caja, cerrar_caja
from caja.services import cobrar_venta as cobrar_venta_service
from caja.services import crear_adelanto, crear_gasto, crear_ingreso, crear_retiro_efectivo, crear_sueldo
from caja.utils import (
    calcular_egresos_caja,
    calcular_ingresos_caja,
    calcular_saldo_caja,
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


class TipoIngresoViewSet(viewsets.ModelViewSet):
    queryset = TipoIngreso.objects.all()
    serializer_class = TipoIngresoSerializer
    permission_classes = (IsStaffOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('descripcion',)


class TipoGastoViewSet(viewsets.ModelViewSet):
    queryset = TipoGasto.objects.all()
    serializer_class = TipoGastoSerializer
    permission_classes = (IsStaffOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('descripcion',)


class MovimientoCajaViewSetMixin:
    """Comportamiento compartido por los ViewSets de los movimientos "simples" de caja (Sueldo,
    Adelanto, Ingreso, RetiroEfectivo, Gasto):

    - `get_queryset` acota a la sucursal del usuario autenticado (mismo criterio que cada
      `ModelAdmin.get_queryset` en `caja/admin.py` — acá se centraliza una sola vez).
    - `perform_create` delega en el servicio de negocio correspondiente (`crear_fn`, definido
      por cada subclase) en vez de `serializer.save()`: ahí es donde se resuelven `usuario`,
      `sucursal`, `caja` y `tipo`, y donde se valida que la caja de la sucursal esté abierta.
    - `perform_update`/`perform_destroy` bloquean si el movimiento ya quedó `cerrado` (la caja
      donde vive ya se cerró) — mismo criterio que `has_change_permission`/`has_delete_permission`
      de esos Admin para un usuario no superusuario.
    """
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = ('caja',)
    crear_fn = None

    def get_queryset(self):
        sucursal = self.request.user.sucursal
        if sucursal is None:
            return self.queryset.none()
        return self.queryset.filter(sucursal=sucursal)

    def perform_create(self, serializer):
        try:
            instancia = self.crear_fn(usuario=self.request.user, **serializer.validated_data)
        except CajaError as exc:
            raise DRFValidationError({'caja': str(exc)})
        serializer.instance = instancia

    def _bloquear_si_cerrado(self, instance):
        if instance.cerrado:
            raise DRFValidationError({'cerrado': 'La caja ya se cerró, no se puede modificar este movimiento.'})

    def perform_update(self, serializer):
        self._bloquear_si_cerrado(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._bloquear_si_cerrado(instance)
        instance.delete()


class SueldoViewSet(MovimientoCajaViewSetMixin, viewsets.ModelViewSet):
    queryset = Sueldo.objects.select_related('usuario', 'empleado__persona')
    serializer_class = SueldoSerializer
    search_fields = ('descripcion',)
    crear_fn = staticmethod(crear_sueldo)


class AdelantoViewSet(MovimientoCajaViewSetMixin, viewsets.ModelViewSet):
    queryset = Adelanto.objects.select_related('usuario', 'empleado__persona')
    serializer_class = AdelantoSerializer
    search_fields = ('descripcion',)
    crear_fn = staticmethod(crear_adelanto)


class IngresoViewSet(MovimientoCajaViewSetMixin, viewsets.ModelViewSet):
    queryset = Ingreso.objects.select_related('usuario', 'tipo_ingreso')
    serializer_class = IngresoSerializer
    search_fields = ('concepto',)
    crear_fn = staticmethod(crear_ingreso)


class RetiroEfectivoViewSet(MovimientoCajaViewSetMixin, viewsets.ModelViewSet):
    queryset = RetiroEfectivo.objects.select_related('usuario')
    serializer_class = RetiroEfectivoSerializer
    search_fields = ('concepto',)
    crear_fn = staticmethod(crear_retiro_efectivo)


class GastoViewSet(MovimientoCajaViewSetMixin, viewsets.ModelViewSet):
    queryset = Gasto.objects.select_related('usuario', 'tipo_gasto')
    serializer_class = GastoSerializer
    search_fields = ('concepto',)
    crear_fn = staticmethod(crear_gasto)


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

    @staticmethod
    def _serializar_resumen_cierre(caja):
        """Desglose de cierre (ingresos/egresos/totales, reutiliza caja.utils, no se duplica la
        fórmula) — compartido por `cerrar` (recién cerrada) y `resumen` (una ya cerrada, para
        volver a mostrarla desde el historial sin tener que cerrarla de nuevo)."""
        data = CajaSerializer(caja).data
        data['ingresos'] = calcular_ingresos_caja(caja)
        data['total_ingresos'] = calcular_total_ingresos(caja)
        data['egresos'] = calcular_egresos_caja(caja)
        data['total_egresos'] = calcular_total_egresos(caja)
        data['total_cuenta_corriente'] = calcular_total_compras_cc(caja)
        # Ya cerrada: `caja_final` (fijado por cerrar_caja) ES el monto calculado — se expone
        # también acá para que el frontend use siempre el mismo campo, esté la caja abierta
        # (preview) o cerrada (ver `previsualizar_cierre`).
        data['caja_final_calculado'] = data['caja_final']
        return data

    @action(detail=True, methods=['get'], url_path='previsualizar-cierre')
    def previsualizar_cierre(self, request, pk=None):
        """Mismo desglose que `cerrar`/`resumen`, pero para la caja TODAVÍA abierta — sin cerrarla
        ni tocar nada en la base. Se usa para mostrar el diálogo "Resumen de cierre" ANTES de
        confirmar el cierre, así el cajero puede cotejar el arqueo físico contra el monto
        calculado (ver CajaPage.tsx) y recién ahí decide cerrar.

        Como `calcular_ingresos_caja`/`calcular_total_compras_cc`/`calcular_total_compras_transf`
        (caja/utils.py) filtran por `fecha__lte=caja.fecha_fin` -y ese campo todavía es None-, se
        arma una copia en memoria (nunca persistida) de la caja con `fecha_fin=ahora` sólo para
        que esas consultas tengan con qué filtrar; la respuesta sigue mostrando `fecha_fin: null`
        (viene de la caja real), dejando claro que todavía no se cerró.
        """
        caja = self.get_object()
        if caja.fecha_fin is not None:
            raise DRFValidationError({'caja': 'La caja ya está cerrada.'})
        caja_al_corte = copy.copy(caja)
        caja_al_corte.fecha_fin = timezone.now()

        data = CajaSerializer(caja).data
        data['ingresos'] = calcular_ingresos_caja(caja_al_corte)
        data['total_ingresos'] = calcular_total_ingresos(caja_al_corte)
        data['egresos'] = calcular_egresos_caja(caja_al_corte)
        data['total_egresos'] = calcular_total_egresos(caja_al_corte)
        data['total_cuenta_corriente'] = calcular_total_compras_cc(caja_al_corte)
        # A diferencia de `_serializar_resumen_cierre`, acá `caja_final` todavía no existe (la
        # caja sigue abierta) -> el monto a cotejar contra el arqueo es `calcular_saldo_caja`
        # (misma fórmula que `cerrar_caja` usa para validar, sin el efecto secundario de marcar
        # movimientos como `cerrado`).
        data['caja_final_calculado'] = str(calcular_saldo_caja(caja))
        return Response(data)

    @action(detail=True, methods=['post'])
    def cerrar(self, request, pk=None):
        caja = self.get_object()
        entrada = CerrarCajaInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            caja = cerrar_caja(caja, arqueo=entrada.validated_data['arqueo'])
        except CajaError as exc:
            raise DRFValidationError({'caja': str(exc)})
        return Response(self._serializar_resumen_cierre(caja))

    @action(detail=True, methods=['get'])
    def resumen(self, request, pk=None):
        """Mismo desglose que devuelve `cerrar` (ingresos/egresos/totales), pero de sólo lectura
        para una caja que ya está cerrada — usado por el historial para reabrir el mismo diálogo
        "Resumen de cierre" que se ve justo al cerrar, sin tener que cerrarla de nuevo (ver
        CajaPage.tsx). Sólo válido para cajas cerradas: mismo motivo que `imprimir`, los totales
        de cta. cte./transferencias del período filtran por `fecha__lte=caja.fecha_fin`, que es
        None mientras la caja sigue abierta.
        """
        caja = self.get_object()
        if caja.fecha_fin is None:
            raise DRFValidationError({'caja': 'La caja está abierta: no tiene un resumen de cierre todavía.'})
        return Response(self._serializar_resumen_cierre(caja))

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
