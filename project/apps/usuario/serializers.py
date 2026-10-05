from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import Group
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

Usuario = get_user_model()


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name')


class UsuarioSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)
    sucursal_nombre = serializers.CharField(source='sucursal.nombre', read_only=True, default=None)
    permisos = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_staff',
            'sucursal',
            'sucursal_nombre',
            'empleado',
            'groups',
            'permisos',
        )
        # is_staff/sucursal/empleado de sólo lectura: este endpoint también acepta PATCH del
        # propio usuario autenticado (UsuarioViewSet.get_object() siempre devuelve request.user)
        # — sin esto, cualquier usuario podría auto-otorgarse is_staff, cambiarse de sucursal o
        # vincularse a otro Empleado. `empleado` se expone para que el frontend preseleccione al
        # vendedor logueado en el punto de venta (VentaNuevaPage) — la asignación en sí sigue
        # siendo sólo por /admin.
        read_only_fields = ('is_staff', 'sucursal', 'empleado')

    def get_permisos(self, usuario):
        # get_all_permissions() ya combina permisos individuales + de todos los grupos del
        # usuario, y para is_superuser devuelve automáticamente TODOS los permisos existentes
        # (comportamiento estándar de ModelBackend) — no hace falta un caso especial acá. El
        # frontend usa estos codenames ("app_label.accion_modelo") para mostrar/ocultar botones
        # de alta/edición/borrado sin tener que ser is_staff (ver util.permissions.
        # TienePermisoDeModelo, que exige exactamente estos mismos permisos en el backend).
        return sorted(usuario.get_all_permissions())


class RegistroUsuarioSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=Usuario.objects.all())]
    )

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Usuario
        fields = ('id', 'username', 'password', 'password_2', 'email', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True}
        }

    def extraer_datos_persona(self):
        datos_persona = {}
        if hasattr(self, 'initial_data') and 'persona' in self.initial_data:
            datos_persona = self.initial_data.pop('persona')

        return datos_persona

    def validate(self, attrs):
        if attrs['password'] != attrs['password_2']:
            raise serializers.ValidationError({"password": "Las contraseñas ingresadas no coinciden."})

        return attrs

    def create(self, validated_data):
        usuario = Usuario.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            **{
                'first_name': validated_data['first_name'],
                'last_name': validated_data['last_name'],
                'is_active': True
            }
        )

        return usuario


class UsuarioSucursalSerializer(serializers.ModelSerializer):
    """Alta/gestión de usuarios operativos de una sucursal (ver util.permissions.
    EsEncargadoDeSucursal). Deliberadamente no expone `is_staff`, `is_superuser`, `groups` ni
    `user_permissions`: quien crea desde acá nunca puede otorgarse ni otorgarle a otro más
    privilegio que "cuenta operativa de mi sucursal" — eso sigue siendo exclusivo del /admin.

    `empleado` sí se expone (de lectura/escritura): el frontend arma Persona + Empleado + este
    Usuario en una sola pantalla (ver UsuarioSucursalFormModal), para que dar de alta a alguien
    no requiera pasar por /admin — a diferencia de is_staff/groups, vincular un Empleado no es
    un privilegio de acceso al sistema, es sólo el dato de "quién es" detrás de la cuenta.
    """

    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    sucursal_nombre = serializers.CharField(source='sucursal.nombre', read_only=True, default=None)
    empleado_detalle = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = (
            'id',
            'username',
            'password',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'sucursal',
            'sucursal_nombre',
            'empleado',
            'empleado_detalle',
        )
        read_only_fields = ('sucursal',)
        extra_kwargs = {'empleado': {'required': False, 'allow_null': True}}

    def get_empleado_detalle(self, usuario):
        empleado = usuario.empleado
        if empleado is None:
            return None
        return {
            'persona': empleado.persona_id,
            'nombre': empleado.persona.nombre,
            'apellido': empleado.persona.apellido,
            'documento_identidad': empleado.persona.documento_identidad,
            'cuil': empleado.cuil,
        }

    def validate(self, attrs):
        # La contraseña es obligatoria al crear, pero no se edita desde acá (no hay pantalla de
        # "resetear contraseña de otro usuario" todavía).
        if self.instance is None and not attrs.get('password'):
            raise serializers.ValidationError({'password': 'Este campo es requerido.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('sucursal', None)
        password = validated_data.pop('password')
        request = self.context['request']
        return Usuario.objects.create_user(
            password=password,
            sucursal=request.user.sucursal,
            is_staff=False,
            **validated_data,
        )

    def update(self, instance, validated_data):
        validated_data.pop('password', None)
        validated_data.pop('sucursal', None)
        return super().update(instance, validated_data)


class CambiarClaveSecretaSerializer(serializers.Serializer):
    clave = serializers.CharField(max_length=128, write_only=True, required=True)
    clave_nueva = serializers.CharField(max_length=128, write_only=True, required=True)
    clave_nueva_2 = serializers.CharField(max_length=128, write_only=True, required=True)

    def validate_clave(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña anterior no es válida. ¡Intentalo nuevamente!")
        return value

    def validate(self, data):
        if data['clave_nueva'] != data['clave_nueva_2']:
            raise serializers.ValidationError({'clave_nueva_2': "Los nuevos campos de contraseñas no coinciden"})
        password_validation.validate_password(data['clave_nueva'], self.context['request'].user)
        return data

    def save(self, **kwargs):
        clave = self.validated_data['clave_nueva']
        usuario = self.context['request'].user
        usuario.set_password(clave)
        usuario.save()
        return usuario
