from django.db.models import ProtectedError
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError

from caja.exceptions import CajaError
from cuentacorriente.models import CuentaCorriente, MovimientoCuentaCorriente
from cuentacorriente.serializers import CuentaCorrienteSerializer, MovimientoCuentaCorrienteSerializer
from cuentacorriente.services import crear_movimiento_cuenta_corriente
from cuentacorriente.utils import calcular_saldo_cc, etiqueta_saldo
from util.permissions import TienePermisoDeModelo
from util.pdf import render_pdf_response


def _plan_tarjeta_detalle(movimiento):
    # Mismo criterio que cuentacorriente.serializers.MovimientoCuentaCorrienteSerializer
    # .get_plan_tarjeta_detalle -se duplica acá (no un método del modelo) porque sólo lo usan
    # estos tickets en PDF, el serializer lo sigue calculando aparte para la API.
    if not movimiento.plan_tarjeta:
        return None
    return f'{movimiento.plan_tarjeta.tarjeta.nombre} — {movimiento.plan_tarjeta.nombre_plan}'


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

    @action(detail=True, methods=['get'])
    def imprimir(self, request, pk=None):
        """Estado de cuenta en PDF con TODOS los movimientos, para entregarle al cliente
        (CuentaCorrienteDetalleModal.tsx) -mismo mecanismo que venta.api.VentaViewSet.imprimir/
        caja.api.CajaViewSet.imprimir (WeasyPrint, ver util/pdf.py)."""
        cuenta = self.get_object()
        movimientos = list(
            MovimientoCuentaCorriente.objects.filter(cuenta=cuenta)
            .select_related('banco', 'plan_tarjeta__tarjeta')
            .order_by('-id')
        )
        # No es un campo del modelo: se calcula una vez acá y se cuelga de cada instancia para
        # que el template lo lea como atributo (Django templates no evalúan f-strings).
        for movimiento in movimientos:
            movimiento.plan_tarjeta_detalle = _plan_tarjeta_detalle(movimiento)
        saldo = calcular_saldo_cc(cuenta)
        return render_pdf_response(
            request=request._request,
            template='admin/cuentacorriente/ticket_cuenta_corriente.html',
            filename=f'cuenta-corriente-{cuenta.id}.pdf',
            context={
                'cuenta': cuenta,
                'movimientos': movimientos,
                'saldo': saldo,
                'etiqueta_saldo': etiqueta_saldo(saldo),
                'hoy': timezone.now(),
            },
            show_content_in_browser=True,
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

    @action(detail=True, methods=['get'])
    def imprimir(self, request, pk=None):
        """Comprobante en PDF de un único movimiento (pago o consumo), para entregarle al
        cliente en el momento -mismo mecanismo que venta.api.VentaViewSet.imprimir (WeasyPrint,
        ver util/pdf.py)."""
        movimiento = self.get_object()
        cuenta = movimiento.cuenta
        saldo = calcular_saldo_cc(cuenta)
        return render_pdf_response(
            request=request._request,
            template='admin/cuentacorriente/ticket_movimiento.html',
            filename=f'cuenta-corriente-{cuenta.id}-movimiento-{movimiento.id}.pdf',
            context={
                'movimiento': movimiento,
                'cuenta': cuenta,
                'plan_tarjeta_detalle': _plan_tarjeta_detalle(movimiento),
                'saldo': saldo,
                'etiqueta_saldo': etiqueta_saldo(saldo),
            },
            show_content_in_browser=True,
        )
