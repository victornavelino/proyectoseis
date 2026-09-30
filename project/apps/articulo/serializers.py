from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from articulo.models import Articulo, Categoria, ListaPrecio, Precio, TipoIva, UnidadMedida


class TipoIvaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoIva
        fields = ('id', 'nombre', 'porcentaje')


class UnidadMedidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadMedida
        fields = ('id', 'nombre', 'abreviatura')


class CategoriaSerializer(serializers.ModelSerializer):
    tipo_iva_nombre = serializers.CharField(source='tipo_iva.nombre', read_only=True)

    class Meta:
        model = Categoria
        fields = ('id', 'nombre', 'nodo_padre', 'tipo_iva', 'tipo_iva_nombre')


class ListaPrecioSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListaPrecio
        fields = ('id', 'nombre')


class ArticuloSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    unidad_medida_nombre = serializers.CharField(source='unidad_medida.nombre', read_only=True)

    class Meta:
        model = Articulo
        fields = (
            'id',
            'nombre',
            'abreviatura',
            'codigo',
            'categoria',
            'categoria_nombre',
            'unidad_medida',
            'unidad_medida_nombre',
            'es_por_peso',
        )
        # nombre/codigo ya no son unique=True a nivel de campo (ver Articulo.Meta.constraints):
        # la restricción real en la base es condicional (solo entre artículos activos, para que
        # borrar uno libere su nombre/código). DRF arma igual un UniqueValidator a partir de la
        # UniqueConstraint, pero con el mensaje genérico de DRF y sin enterarse de la condición
        # -> se lo pisa acá explícitamente, igual que en CuentaCorrienteSerializer.cliente.
        # `Articulo.objects` (el manager con soft-delete) ya excluye los borrados por su cuenta,
        # así que el queryset da el mismo resultado que la condición de la base.
        extra_kwargs = {
            'nombre': {
                'validators': [
                    UniqueValidator(queryset=Articulo.objects.all(), message='Ya existe un artículo con ese nombre.')
                ]
            },
            'codigo': {
                'validators': [
                    UniqueValidator(
                        queryset=Articulo.objects.all(),
                        message='Ya existe un artículo con ese código de barras.',
                    )
                ]
            },
        }


class PrecioSerializer(serializers.ModelSerializer):
    articulo_nombre = serializers.CharField(source='articulo.nombre', read_only=True)
    articulo_codigo = serializers.CharField(source='articulo.codigo', read_only=True)
    sucursal_nombre = serializers.CharField(source='sucursal.nombre', read_only=True)
    lista_precio_nombre = serializers.CharField(source='lista_precio.nombre', read_only=True)

    class Meta:
        model = Precio
        fields = (
            'id',
            'articulo',
            'articulo_nombre',
            'articulo_codigo',
            'sucursal',
            'sucursal_nombre',
            'lista_precio',
            'lista_precio_nombre',
            'precio',
        )
