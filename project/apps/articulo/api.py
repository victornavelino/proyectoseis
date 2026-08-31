from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from articulo.models import Articulo, Categoria, ListaPrecio, Precio, TipoIva, UnidadMedida
from articulo.serializers import (
    ArticuloSerializer,
    CategoriaSerializer,
    ListaPrecioSerializer,
    PrecioSerializer,
    TipoIvaSerializer,
    UnidadMedidaSerializer,
)
from util.permissions import IsStaffOrReadOnly


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


class PrecioViewSet(viewsets.ModelViewSet):
    queryset = Precio.objects.select_related('articulo', 'sucursal', 'lista_precio').all()
    serializer_class = PrecioSerializer
    permission_classes = (IsStaffOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    # Uso típico del mostrador: GET /api/v1/precio/?articulo=<id>&sucursal=<id>&lista_precio=<id>
    filterset_fields = ('articulo', 'sucursal', 'lista_precio')
