from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from articulo.models import Articulo, Categoria, TipoIva, UnidadMedida
from empleado.models import Sucursal
from promocion.models import DiasSemana, Promocion, PromocionArticulo

Usuario = get_user_model()


@pytest.fixture
def promocion():
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    dias_semana = DiasSemana.objects.create(lunes=True)
    promo = Promocion.objects.create(
        nombre='Promo de prueba', fecha_inicio=date.today(), fecha_fin=date.today() + timedelta(days=1),
        es_por_precio=True, porcentaje_todos=None, dias_semana=dias_semana, habilitada=True, prioridad=1,
        sucursal=sucursal,
    )
    tipo_iva = TipoIva.objects.create(nombre='21%', porcentaje=Decimal('21.00'))
    categoria = Categoria.objects.create(nombre='Carnes', tipo_iva=tipo_iva)
    unidad_medida = UnidadMedida.objects.create(nombre='Kilogramo', abreviatura='kg')
    articulo = Articulo.objects.create(
        nombre='Asado', abreviatura='ASADO', codigo='0001', categoria=categoria, unidad_medida=unidad_medida,
    )
    PromocionArticulo.objects.create(promocion=promo, articulo=articulo, valor=Decimal('500.00'))
    return promo


@pytest.fixture
def usuario_staff(promocion):
    usuario = Usuario.objects.create_user(
        username='admin', password='password', sucursal=promocion.sucursal, is_staff=True,
    )
    usuario.groups.add(Group.objects.get(name='Acceso completo (staff)'))
    return usuario


@pytest.mark.django_db
def test_se_puede_eliminar_una_promocion(promocion, usuario_staff):
    client = APIClient()
    client.force_authenticate(user=usuario_staff)

    response = client.delete(f'/api/v1/promocion/{promocion.id}/')

    assert response.status_code == 204
    assert not Promocion.objects.filter(id=promocion.id).exists()
    # Cascada esperada (PromocionArticulo.promocion es on_delete=CASCADE): no es historial de
    # ventas, es sólo la configuración de qué artículos entraban en esta promoción.
    assert not PromocionArticulo.objects.filter(promocion_id=promocion.id).exists()


@pytest.mark.django_db
def test_sin_permiso_no_puede_eliminar_una_promocion(promocion):
    sucursal = promocion.sucursal
    usuario_sin_permiso = Usuario.objects.create_user(username='vendedor', password='password', sucursal=sucursal)
    client = APIClient()
    client.force_authenticate(user=usuario_sin_permiso)

    response = client.delete(f'/api/v1/promocion/{promocion.id}/')

    assert response.status_code == 403
    assert Promocion.objects.filter(id=promocion.id).exists()


@pytest.mark.django_db
def test_superusuario_puede_eliminar_sin_necesitar_el_grupo(promocion):
    # Reproduce el reporte: un superusuario (is_superuser=True) tiene todos los permisos
    # automáticamente (comportamiento estándar de Django), sin depender de ningún grupo.
    sucursal = promocion.sucursal
    superusuario = Usuario.objects.create_user(
        username='dueño', password='password', sucursal=sucursal, is_staff=True, is_superuser=True,
    )
    client = APIClient()
    client.force_authenticate(user=superusuario)

    response = client.delete(f'/api/v1/promocion/{promocion.id}/')

    assert response.status_code == 204
