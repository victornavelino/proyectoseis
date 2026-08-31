from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from promocion.models import Descuento, DiasSemana, Promocion, PromocionArticulo
from promocion.serializers import (
    DescuentoSerializer,
    DiasSemanaSerializer,
    PromocionArticuloSerializer,
    PromocionSerializer,
)
from util.mixins import TranslateDjangoValidationErrorMixin
from util.permissions import IsStaffOrReadOnly


class DiasSemanaViewSet(viewsets.ModelViewSet):
    queryset = DiasSemana.objects.all()
    serializer_class = DiasSemanaSerializer
    permission_classes = (IsStaffOrReadOnly,)


class PromocionViewSet(TranslateDjangoValidationErrorMixin, viewsets.ModelViewSet):
    # Promocion.save() corre full_clean() (reglas de negocio: es_por_precio/porcentaje_todos,
    # dias_semana obligatorio, prioridad única por sucursal). El mixin traduce esos errores a
    # 400 en vez de dejarlos escapar como 500. Ver promocion/serializers.py.
    queryset = Promocion.objects.select_related('sucursal', 'dias_semana').prefetch_related('promocionarticulo_set')
    serializer_class = PromocionSerializer
    permission_classes = (IsStaffOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    # Uso típico del punto de venta: GET /api/v1/promocion/?sucursal=<id>&habilitada=true
    filterset_fields = ('sucursal', 'habilitada', 'es_por_precio')
    search_fields = ('nombre',)
    ordering_fields = ('prioridad', 'fecha_inicio', 'fecha_fin')


class PromocionArticuloViewSet(viewsets.ModelViewSet):
    queryset = PromocionArticulo.objects.select_related('articulo', 'promocion').all()
    serializer_class = PromocionArticuloSerializer
    permission_classes = (IsStaffOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('promocion', 'articulo')


class DescuentoViewSet(viewsets.ModelViewSet):
    queryset = Descuento.objects.all()
    serializer_class = DescuentoSerializer
    permission_classes = (IsStaffOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('nombre',)
