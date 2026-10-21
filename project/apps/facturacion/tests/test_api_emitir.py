from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils import timezone
from django_afip.models import ConceptType, CurrencyType, DocumentType, PointOfSales, Receipt, ReceiptType, TaxPayer
from rest_framework.test import APIClient

from cliente.models import Cliente
from empleado.models import Empleado, Sucursal
from facturacion.models import ComprobanteVenta
from persona.models import Persona
from venta.models import Venta

Usuario = get_user_model()


@pytest.fixture
def venta(db):
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    usuario = Usuario.objects.create_user(username='cajera', password='x', sucursal=sucursal)
    persona_empleado = Persona.objects.create(nombre='Ana', apellido='Vendedora', documento_identidad='11111111')
    empleado = Empleado.objects.create(persona=persona_empleado, cuil='20111111112')
    persona_cliente = Persona.objects.create(nombre='Juan', apellido='Cliente', documento_identidad='22222222')
    cliente = Cliente.objects.create(persona=persona_cliente, condicion_iva=Cliente.CONSUMIDOR_FINAL)

    ConceptType.objects.create(code=1, description='Productos', valid_from=date(2010, 1, 1))
    DocumentType.objects.create(code=96, description='DNI', valid_from=date(2010, 1, 1))
    CurrencyType.objects.create(code='PES', description='Pesos Argentinos', valid_from=date(2010, 1, 1))
    ReceiptType.objects.create(code=11, description='Factura C', valid_from=date(2010, 1, 1))
    taxpayer = TaxPayer.objects.create(name='Mi Comercio', cuit=20267565393, is_sandboxed=True, active_since=date(2020, 1, 1))
    PointOfSales.objects.create(owner=taxpayer, number=1, issuance_type='CAE')

    return Venta.objects.create(
        empleado=empleado, fecha=timezone.now(), monto=Decimal('1000.00'), descuento=Decimal('0.00'),
        sucursal=sucursal, cliente=cliente, usuario=usuario,
    )


@pytest.mark.django_db
def test_sin_permiso_no_puede_emitir(venta):
    client = APIClient()
    client.force_authenticate(user=venta.usuario)

    response = client.post('/api/v1/comprobanteventa/emitir/', {'venta': venta.pk}, format='json')

    assert response.status_code == 403
    assert not ComprobanteVenta.objects.filter(venta=venta).exists()


@pytest.mark.django_db
def test_con_permiso_emite_y_devuelve_el_comprobante(venta, mocker):
    mocker.patch.object(Receipt, 'validate', return_value=[])
    permiso = Permission.objects.get(content_type__app_label='facturacion', codename='add_comprobanteventa')
    venta.usuario.user_permissions.add(permiso)
    client = APIClient()
    client.force_authenticate(user=venta.usuario)

    response = client.post('/api/v1/comprobanteventa/emitir/', {'venta': venta.pk}, format='json')

    assert response.status_code == 200
    assert response.data['estado'] == ComprobanteVenta.EMITIDO
