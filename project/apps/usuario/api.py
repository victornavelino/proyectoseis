from django.contrib.auth import get_user_model
from rest_framework import filters, permissions, generics, viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from persona.models import Persona
from persona.serializers import PersonaSerializer
from usuario.serializers import (
    RegistroUsuarioSerializer,
    UsuarioSerializer,
    UsuarioSucursalSerializer,
    CambiarClaveSecretaSerializer,
)
from util.permissions import EsEncargadoDeSucursal
from util.serializers import TelefonoSerializer

Usuario = get_user_model()


class RegistroUsuarioAPIView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegistroUsuarioSerializer

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        setattr(self, 'datos_persona', serializer.extraer_datos_persona())
        return serializer

    @staticmethod
    def crear_persona(datos_persona):

        try:
            persona = Persona.objects.get(documento_identidad=datos_persona['documento_identidad'])
        except Persona.DoesNotExist:
            telefonos_data = datos_persona.pop('telefonos', None) or []
            telefono_serializers = [TelefonoSerializer(data=telefono) for telefono in telefonos_data]
            for telefono_serializer in telefono_serializers:
                telefono_serializer.is_valid(raise_exception=True)
            persona_serializer = PersonaSerializer(data=datos_persona)
            persona_serializer.is_valid(raise_exception=True)
            persona_serializer.save()
            persona = persona_serializer.instance
            # Guardamos los teléfonos en persona.
            for telefono_serializer in telefono_serializers:
                if not persona.telefonos.filter(**telefono_serializer.validated_data).exists():
                    telefono_serializer.save(content_object=persona)
        return persona

    def perform_create(self, serializer):
        datos_persona = getattr(self, 'datos_persona')
        persona = self.crear_persona(datos_persona)
        serializer.save(persona=persona)


class UsuarioViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Usuario.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UsuarioSerializer

    def get_object(self, base_method=False):
        user = self.request.user
        if base_method:
            user = super().get_object()
        return user

    @action(
        methods=('patch',),
        detail=False,
        url_path='cambiar-clave-secreta',
        parser_classes=(JSONParser,),
        serializer_class=CambiarClaveSecretaSerializer
    )
    def cambiar_clave_secreta(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_200_OK)


class UsuarioSucursalViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    # Alta de usuarios operativos por el encargado de sucursal — ver util.permissions.
    # EsEncargadoDeSucursal y UsuarioSucursalSerializer para las restricciones de seguridad.
    #
    # Sin destroy() a propósito, mismo criterio que Cliente/Empleado: se desactiva
    # (is_active=False vía PATCH), nunca se borra una cuenta con historial de ventas asociado.
    #
    # `is_staff=False` en el queryset: este endpoint es sólo para las cuentas operativas que el
    # encargado da de alta, no para administrar cuentas de staff (eso sigue siendo /admin).
    serializer_class = UsuarioSucursalSerializer
    permission_classes = (EsEncargadoDeSucursal,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username', 'first_name', 'last_name', 'email')

    def get_queryset(self):
        queryset = Usuario.objects.filter(is_staff=False).order_by('username')
        user = self.request.user
        if user.is_superuser:
            return queryset
        return queryset.filter(sucursal=user.sucursal)
