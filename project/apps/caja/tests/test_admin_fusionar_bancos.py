from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory

from caja.admin import BancoAdmin
from caja.models import Banco, PagoQr, PagoTransferencia
from empleado.models import Sucursal

Usuario = get_user_model()


def _request_con_mensajes(usuario):
    request = RequestFactory().get('/admin/caja/banco/')
    request.user = usuario
    request.session = {}
    request._messages = FallbackStorage(request)
    return request


@pytest.fixture
def superusuario():
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    return Usuario.objects.create_superuser(username='admin', password='x', sucursal=sucursal)


@pytest.mark.django_db
def test_fusionar_bancos_reasigna_pagos_y_borra_los_duplicados(superusuario):
    canonico = Banco.objects.create(nombre='Mercado Pago')
    duplicado1 = Banco.objects.create(nombre='mercado pago')
    duplicado2 = Banco.objects.create(nombre='MercadoPago')
    pago_transferencia = PagoTransferencia.objects.create(
        importe=Decimal('100'), documento_identidad='11111111', banco=duplicado1,
    )
    pago_qr = PagoQr.objects.create(importe=Decimal('200'), documento_identidad='22222222', banco=duplicado2)

    admin_site = BancoAdmin(Banco, None)
    queryset = Banco.objects.filter(id__in=[canonico.id, duplicado1.id, duplicado2.id])
    admin_site.fusionar_bancos(_request_con_mensajes(superusuario), queryset)

    pago_transferencia.refresh_from_db()
    pago_qr.refresh_from_db()
    assert pago_transferencia.banco_id == canonico.id
    assert pago_qr.banco_id == canonico.id
    assert not Banco.objects.filter(id__in=[duplicado1.id, duplicado2.id]).exists()
    assert Banco.objects.filter(id=canonico.id).exists()


@pytest.mark.django_db
def test_fusionar_bancos_con_uno_solo_no_hace_nada(superusuario):
    banco = Banco.objects.create(nombre='Banco Nación')

    admin_site = BancoAdmin(Banco, None)
    admin_site.fusionar_bancos(_request_con_mensajes(superusuario), Banco.objects.filter(id=banco.id))

    assert Banco.objects.filter(id=banco.id).exists()
