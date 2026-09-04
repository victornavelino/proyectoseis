from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from decimal import Decimal, ROUND_HALF_UP

from cuentacorriente.models import CuentaCorriente
from cuentacorriente.utils import calcular_saldo_cc
from util.pdf import render_pdf_response
from venta.exceptions import (
    ArticuloSinPrecioError,
    CajaCerradaError,
    SinSucursalError,
    VentaYaAnuladaError,
    VentaYaCobradaError,
)
from venta.models import Venta, VentaArticulo
from venta.serializers import (
    CrearVentaInputSerializer,
    PrevisualizarVentaInputSerializer,
    VentaPrevisualizadaSerializer,
    VentaSerializer,
)
from venta.services import anular_venta, crear_venta
from venta.utils import calcular_precio_venta_articulo


class VentaViewSet(viewsets.ReadOnlyModelViewSet):
    # El alta y la anulación son operaciones de negocio dedicadas (transaccionales, con
    # recálculo/validaciones server-side), no un create()/destroy() de CRUD genérico ->
    # ReadOnlyModelViewSet (list/retrieve) + acciones explícitas `crear`/`anular`.
    queryset = Venta.objects.select_related(
        'cliente__persona', 'empleado__persona', 'usuario', 'sucursal'
    ).prefetch_related('ventaarticulo_set')
    serializer_class = VentaSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_fields = ('sucursal', 'cliente', 'cobrada', 'anulado')
    ordering_fields = ('numero_ticket', 'fecha')

    def get_queryset(self):
        # Búsqueda libre por ?search=: nro de ticket, apellido o DNI del cliente. No se usa
        # filters.SearchFilter porque numero_ticket es un IntegerField -> un icontains ahí
        # rompe en Postgres (LIKE no admite comparar contra integer sin cast); por eso el
        # numero_ticket sólo entra en el filtro cuando el término buscado es numérico.
        queryset = super().get_queryset()
        busqueda = self.request.query_params.get('search', '').strip().lstrip('#')
        if busqueda:
            filtro = Q(cliente__persona__apellido__icontains=busqueda) | Q(
                cliente__persona__documento_identidad__icontains=busqueda
            )
            if busqueda.isdigit():
                filtro |= Q(numero_ticket=int(busqueda))
            queryset = queryset.filter(filtro)
        return queryset

    def get_permissions(self):
        if self.action == 'anular':
            # Anular reversa una venta -> mismo nivel de acceso que hoy tiene esa acción en
            # Django Admin (a él sólo llegan usuarios staff).
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    @action(detail=False, methods=['post'])
    def crear(self, request):
        """Alta transaccional de una venta. Body:
        `{"empleado": <id>, "cliente": <id>, "articulos": [{"articulo": <id>, "cantidad_peso": "1.250"}, ...]}`
        El precio de cada artículo se recalcula siempre en servidor (nunca se recibe del
        frontend) — ver `venta.utils.calcular_precio_venta_articulo`.
        """
        entrada = CrearVentaInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            venta = crear_venta(
                empleado=entrada.validated_data['empleado'],
                cliente=entrada.validated_data['cliente'],
                items=entrada.validated_data['articulos'],
                usuario=request.user,
            )
        except SinSucursalError as exc:
            raise DRFValidationError({'usuario': str(exc)})
        except CajaCerradaError as exc:
            raise DRFValidationError({'caja': str(exc)})
        except ArticuloSinPrecioError as exc:
            raise DRFValidationError({'articulos': str(exc)})
        return Response(VentaSerializer(venta).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def previsualizar(self, request):
        """Calcula el precio de cada artículo (misma lógica exacta que `crear`, reutilizando
        `calcular_precio_venta_articulo`) SIN persistir nada — pensado para que el frontend
        muestre el total en tiempo real mientras se arma el carrito (especificaciones.md §6:
        "feedback inmediato"). No exige caja abierta (es sólo un cálculo, no una venta).
        Body: `{"cliente": <id>, "articulos": [{"articulo": <id>, "cantidad_peso": "1.250"}]}`.
        """
        entrada = PrevisualizarVentaInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        cliente = entrada.validated_data['cliente']
        sucursal = request.user.sucursal
        if sucursal is None:
            raise DRFValidationError({'usuario': 'El usuario no tiene una sucursal asignada.'})

        items = []
        total = Decimal('0')
        for item in entrada.validated_data['articulos']:
            articulo = item['articulo']
            cantidad_peso = item['cantidad_peso']
            try:
                precio_lista, precio_final = calcular_precio_venta_articulo(cliente, articulo, sucursal)
            except ArticuloSinPrecioError as exc:
                raise DRFValidationError({'articulos': str(exc)})
            monto_articulo = (precio_final * cantidad_peso).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            items.append({
                'articulo': articulo.pk,
                'articulo_nombre': articulo.nombre,
                'cantidad_peso': cantidad_peso,
                'precio_unitario': precio_lista,
                'precio_promocion': precio_final,
                'total_articulo': monto_articulo,
            })
            total += monto_articulo

        salida = VentaPrevisualizadaSerializer({'articulos': items, 'monto': total})
        return Response(salida.data)

    @action(detail=True, methods=['post'])
    def anular(self, request, pk=None):
        """Anula una venta no cobrada. Anular una venta ya cobrada no está soportado todavía
        (DECISIONES.md PEND-J) — responde 400 explicando por qué en vez de hacerlo a medias."""
        venta = self.get_object()
        try:
            venta = anular_venta(venta)
        except VentaYaAnuladaError as exc:
            raise DRFValidationError({'anulado': str(exc)})
        except VentaYaCobradaError as exc:
            raise DRFValidationError({'cobrada': str(exc)})
        return Response(VentaSerializer(venta).data)

    @action(detail=True, methods=['get'])
    def imprimir(self, request, pk=None):
        """Ticket de venta en PDF (WeasyPrint, ver util/pdf.py). Mismo template y cálculo que la
        vista legacy `venta.views.imprimir_ticket`/la acción de admin equivalente — ver
        ROADMAP.md etapa 16: ninguna de esas dos era alcanzable desde el frontend nuevo (una
        exige sesión de Django, no el Bearer token de la API), así que quedaba huérfana."""
        venta = self.get_object()
        articulos_venta = VentaArticulo.objects.filter(venta=venta)
        try:
            cuenta_corriente = CuentaCorriente.objects.get(cliente_id=venta.cliente_id, activa=True)
            saldo_cc = calcular_saldo_cc(cuenta_corriente)
        except CuentaCorriente.DoesNotExist:
            saldo_cc = '--'
        monto_descuento = sum(
            (articulo.precio_unitario - articulo.precio_promocion for articulo in articulos_venta),
            Decimal('0'),
        )
        return render_pdf_response(
            request=request._request,
            template='admin/venta/ticket_venta.html',
            filename=f'venta-{venta.numero_ticket}-{venta.fecha}.pdf',
            context={
                'venta': venta,
                'vendedor': venta.empleado,
                'articulos': articulos_venta,
                'monto_descuento': monto_descuento,
                'saldo_cc': saldo_cc,
            },
            show_content_in_browser=True,
        )
