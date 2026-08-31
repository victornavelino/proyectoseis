from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from empleado.models import Empleado, Sucursal
from empleado.serializers import EmpleadoSerializer, SucursalSerializer
from util.permissions import IsStaffOrReadOnly


class SucursalViewSet(viewsets.ModelViewSet):
    # Alta/baja de sucursales es una decisión de infraestructura del negocio, no operación de
    # mostrador -> igual criterio que articulo: sólo staff escribe.
    queryset = Sucursal.objects.all()
    serializer_class = SucursalSerializer
    permission_classes = (IsStaffOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('nombre',)


class EmpleadoViewSet(viewsets.ModelViewSet):
    # Alta/baja de empleados es decisión de RR.HH./administración -> sólo staff escribe.
    # Leer (para elegir "quién atiende" en el punto de venta) sí es operación de mostrador
    # normal, como en el legacy venta.views.get_empleados.
    queryset = Empleado.objects.select_related('persona')
    serializer_class = EmpleadoSerializer
    permission_classes = (IsStaffOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_fields = ('fecha_baja',)
    search_fields = ('persona__nombre', 'persona__apellido', 'cuil')
    ordering_fields = ('persona__apellido',)
