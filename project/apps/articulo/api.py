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
from cliente.models import Cliente
from inventario.models import MovimientoInternoArticulo
from promocion.models import PromocionArticulo
from util.permissions import TienePermisoDeModelo
from venta.models import VentaArticulo


class TipoIvaViewSet(viewsets.ModelViewSet):
    queryset = TipoIva.objects.all()
    serializer_class = TipoIvaSerializer
    permission_classes = (TienePermisoDeModelo,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('nombre',)

    def destroy(self, request, *args, **kwargs):
        # TipoIva es un Model común (no soft-delete) y Categoria.tipo_iva es on_delete=CASCADE:
        # sin este chequeo, borrar un tipo de IVA borraría de verdad (cascada real de Django, no
        # borrado lógico) todas las categorías que lo usan, y transitivamente sus artículos.
        instance = self.get_object()
        if Categoria.objects.filter(tipo_iva=instance).exists():
            raise DRFValidationError('No se puede eliminar: el tipo de IVA tiene categorías asociadas.')
        return super().destroy(request, *args, **kwargs)


class UnidadMedidaViewSet(viewsets.ModelViewSet):
    queryset = UnidadMedida.objects.all()
    serializer_class = UnidadMedidaSerializer
    permission_classes = (TienePermisoDeModelo,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('nombre', 'abreviatura')

    def destroy(self, request, *args, **kwargs):
        # Igual riesgo que TipoIva: Articulo.unidad_medida es on_delete=CASCADE y UnidadMedida no
        # es soft-delete -> borrar una unidad borraría de verdad todos los artículos que la usan.
        instance = self.get_object()
        if Articulo.objects.filter(unidad_medida=instance).exists():
            raise DRFValidationError('No se puede eliminar: la unidad de medida tiene artículos asociados.')
        return super().destroy(request, *args, **kwargs)


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = (TienePermisoDeModelo,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_fields = ('nodo_padre', 'tipo_iva')
    search_fields = ('nombre',)

    def destroy(self, request, *args, **kwargs):
        # Categoria no es soft-delete: Articulo.categoria y Categoria.nodo_padre son
        # on_delete=CASCADE reales -> borrar una categoría con artículos o subcategorías las
        # borraría de verdad a ellas también (y transitivamente ventas, precios, etc.).
        instance = self.get_object()
        if Articulo.objects.filter(categoria=instance).exists():
            raise DRFValidationError('No se puede eliminar: la categoría tiene artículos asociados.')
        if Categoria.objects.filter(nodo_padre=instance).exists():
            raise DRFValidationError('No se puede eliminar: la categoría tiene subcategorías.')
        return super().destroy(request, *args, **kwargs)


class ListaPrecioViewSet(viewsets.ModelViewSet):
    queryset = ListaPrecio.objects.all()
    serializer_class = ListaPrecioSerializer
    permission_classes = (TienePermisoDeModelo,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('nombre',)

    def destroy(self, request, *args, **kwargs):
        # ListaPrecio no es soft-delete: Cliente.lista_precio y Precio.lista_precio son
        # on_delete=CASCADE reales -> borrar una lista de precios en uso borraría de verdad esos
        # clientes (!) o precios.
        instance = self.get_object()
        if Cliente.objects.filter(lista_precio=instance).exists():
            raise DRFValidationError('No se puede eliminar: la lista de precios está asignada a uno o más clientes.')
        if Precio.objects.filter(lista_precio=instance).exists():
            raise DRFValidationError('No se puede eliminar: la lista de precios tiene precios cargados.')
        return super().destroy(request, *args, **kwargs)


class ArticuloViewSet(viewsets.ModelViewSet):
    # SoftDeleteObject: el manager por defecto ya excluye los borrados
    # (deleted_at no nulo) y `.delete()` hace soft-delete, no borrado físico.
    queryset = Articulo.objects.all()
    serializer_class = ArticuloSerializer
    permission_classes = (TienePermisoDeModelo,)
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
    permission_classes = (TienePermisoDeModelo,)
    filter_backends = (DjangoFilterBackend,)
    # Uso típico del mostrador: GET /api/v1/precio/?articulo=<id>&sucursal=<id>&lista_precio=<id>
    filterset_fields = ('articulo', 'sucursal', 'lista_precio')
