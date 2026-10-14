from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from caja.admin import MovimientoCajaAdmin
from caja.models import Caja, Ingreso, MovimientoCaja, TipoIngreso
from empleado.models import Sucursal

Usuario = get_user_model()


@pytest.fixture
def sucursal():
    return Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')


@pytest.fixture
def movimiento(sucursal):
    usuario = Usuario.objects.create_user(username='cajera', password='x', sucursal=sucursal)
    caja = Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=Decimal('0'))
    tipo_ingreso = TipoIngreso.objects.create(descripcion='Varios')
    return Ingreso.objects.create(
        usuario=usuario, caja=caja, sucursal=sucursal, tipo='ingreso', importe=Decimal('100'),
        tipo_ingreso=tipo_ingreso, concepto='Prueba',
    )


@pytest.mark.django_db
def test_superusuario_puede_eliminar_desde_movimientos_de_caja(movimiento, sucursal):
    # Antes de este fix, has_delete_permission devolvía False siempre, sin excepción para
    # superusuario (a diferencia de todos los demás ModelAdmin del archivo) — por eso no
    # aparecían las opciones de eliminar en "Movimientos de Caja" ni para el admin.
    superusuario = Usuario.objects.create_superuser(username='admin', password='x', sucursal=sucursal)
    request = RequestFactory().get('/admin/caja/movimientocaja/')
    request.user = superusuario

    admin_site = MovimientoCajaAdmin(MovimientoCaja, None)

    assert admin_site.has_delete_permission(request) is True
    assert admin_site.has_delete_permission(request, obj=movimiento) is True


@pytest.mark.django_db
def test_usuario_comun_no_puede_eliminar_desde_movimientos_de_caja(movimiento, sucursal):
    usuario = Usuario.objects.create_user(username='cajero2', password='x', sucursal=sucursal)
    request = RequestFactory().get('/admin/caja/movimientocaja/')
    request.user = usuario

    admin_site = MovimientoCajaAdmin(MovimientoCaja, None)

    assert admin_site.has_delete_permission(request) is False
    assert admin_site.has_delete_permission(request, obj=movimiento) is False
