from rest_framework import serializers

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
