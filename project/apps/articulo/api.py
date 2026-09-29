from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError

from articulo.models import Articulo, Categoria, ListaPrecio, Precio, TipoIva, UnidadMedida
from articulo.serializers import (
    ArticuloSerializer,
    CategoriaSerializer,
    ListaPrecioSerializer,
    PrecioSerializer,
    TipoIvaSerializer,
    UnidadMedidaSerializer,
)
from inventario.models import MovimientoInternoArticulo
from promocion.models import PromocionArticulo
from util.permissions import IsStaffOrReadOnly
from venta.models import VentaArticulo


class TipoIvaViewSet(viewsets.ModelViewSet):
    queryset = TipoIva.objects.all()
    serializer_class = TipoIvaSerializer
    permission_classes = (IsStaffOrReadOnly,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('nombre',)


class UnidadMedidaViewSet(viewsets.ModelViewSet):
    queryset = UnidadMedida.objects.all()
    serializer_class = UnidadMedidaSerializer
    permission_classes = (IsStaffOrReadOnly,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('nombre', 'abreviatura')


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = (IsStaffOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_fields = ('nodo_padre', 'tipo_iva')
    search_fields = ('nombre',)


class ListaPrecioViewSet(viewsets.ModelViewSet):
    queryset = ListaPrecio.objects.all()
    serializer_class = ListaPrecioSerializer
    permission_classes = (IsStaffOrReadOnly,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('nombre',)


class ArticuloViewSet(viewsets.ModelViewSet):
    # SoftDeleteObject: el manager por defecto ya excluye los borrados
    # (deleted_at no nulo) y `.delete()` hace soft-delete, no borrado físico.
    queryset = Articulo.objects.all()
    serializer_class = ArticuloSerializer
    permission_classes = (IsStaffOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_fields = ('categoria', 'unidad_medida', 'es_por_peso')
    search_fields = ('nombre', 'codigo', 'abreviatura')
    ordering_fields = ('nombre', 'codigo')

    def destroy(self, request, *args, **kwargs):
        # django-softdelete cascadea el borrado de un SoftDeleteObject a TODAS sus relaciones
        # reversas, sin importar si el modelo relacionado también es soft-delete. VentaArticulo,
        # MovimientoInternoArticulo y PromocionArticulo son Model comunes (no SoftDeleteObject),
        # así que la librería termina llamando su .delete() real y borra de verdad ese detalle
        # histórico (ver softdelete.models.SoftDeleteObject._do_delete). Se bloquea el borrado
        # si el artículo tiene algún registro de esos, para no perder historial de ventas ya
        # facturadas, movimientos de inventario o promociones.
        instance = self.get_object()
        if VentaArticulo.objects.filter(articulo=instance).exists():
            raise DRFValidationError('No se puede eliminar: el artículo tiene ventas registradas.')
        if MovimientoInternoArticulo.objects.filter(articulo=instance).exists():
            raise DRFValidationError(
                'No se puede eliminar: el artículo tiene movimientos de inventario registrados.'
            )
        if PromocionArticulo.objects.filter(articulo=instance).exists():
            raise DRFValidationError('No se puede eliminar: el artículo está incluido en una promoción.')
        return super().destroy(request, *args, **kwargs)


class PrecioViewSet(viewsets.ModelViewSet):
    queryset = Precio.objects.select_related('articulo', 'sucursal', 'lista_precio').all()
    serializer_class = PrecioSerializer
    permission_classes = (IsStaffOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    # Uso típico del mostrador: GET /api/v1/precio/?articulo=<id>&sucursal=<id>&lista_precio=<id>
    filterset_fields = ('articulo', 'sucursal', 'lista_precio')
