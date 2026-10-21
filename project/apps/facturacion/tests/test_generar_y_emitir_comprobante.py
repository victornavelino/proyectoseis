from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from django_afip.models import ConceptType, CurrencyType, DocumentType, PointOfSales, Receipt, ReceiptType, TaxPayer

from cliente.models import Cliente
from empleado.models import Empleado, Sucursal
from facturacion.exceptions import ComprobanteYaEmitidoError, SinConfiguracionAfipError
from facturacion.models import ComprobanteVenta
from facturacion.services import generar_y_emitir_comprobante
from persona.models import Persona
from venta.models import Venta

Usuario = get_user_model()


@pytest.fixture
def venta(db):
    """Arma una venta con todo lo que `generar_y_emitir_comprobante` necesita: un cliente con
    documento (se usa como DocumentType 96/DNI del comprobante) y el catálogo mínimo de
    django_afip que normalmente se puebla con `afipmetadata` (acá a mano, sin red)."""
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
        empleado=empleado, fecha=timezone.now(), monto=Decimal('1210.00'), descuento=Decimal('100.00'),
        sucursal=sucursal, cliente=cliente, usuario=usuario,
    )


@pytest.mark.django_db
def test_mapea_los_campos_de_la_venta_al_receipt(venta, mocker):
    mocker.patch.object(Receipt, 'validate', return_value=[])

    comprobante = generar_y_emitir_comprobante(venta)

    assert comprobante.estado == ComprobanteVenta.EMITIDO
    assert comprobante.mensaje_error == ''
    receipt = comprobante.receipt
    assert receipt.document_number == int(venta.cliente.persona.documento_identidad)
    assert receipt.total_amount == Decimal('1110.00')  # monto - descuento
    assert receipt.net_taxed == receipt.total_amount  # Factura C: no discrimina IVA
    assert receipt.net_untaxed == 0
    assert receipt.receipt_type.code == '11'
    assert receipt.concept.code == '1'


@pytest.mark.django_db
def test_validate_con_errores_marca_estado_error_con_mensaje(venta, mocker):
    mocker.patch.object(Receipt, 'validate', return_value=['Error 10015: CUIT no autorizado para emitir'])

    comprobante = generar_y_emitir_comprobante(venta)

    assert comprobante.estado == ComprobanteVenta.ERROR
    assert 'CUIT no autorizado' in comprobante.mensaje_error
    assert comprobante.receipt is not None  # se reutiliza en el reintento, no se pierde


@pytest.mark.django_db
def test_excepcion_de_red_o_auth_no_propaga_y_queda_en_error(venta, mocker):
    mocker.patch.object(Receipt, 'validate', side_effect=ConnectionError('ARCA no responde'))

    comprobante = generar_y_emitir_comprobante(venta)

    assert comprobante.estado == ComprobanteVenta.ERROR
    assert 'ARCA no responde' in comprobante.mensaje_error


@pytest.mark.django_db
def test_no_se_puede_reemitir_un_comprobante_ya_emitido(venta, mocker):
    mocker.patch.object(Receipt, 'validate', return_value=[])
    generar_y_emitir_comprobante(venta)

    with pytest.raises(ComprobanteYaEmitidoError):
        generar_y_emitir_comprobante(venta)


@pytest.mark.django_db
def test_reintento_despues_de_un_error_reutiliza_el_mismo_receipt(venta, mocker):
    mocker.patch.object(Receipt, 'validate', return_value=['Error de ARCA'])
    primer_intento = generar_y_emitir_comprobante(venta)
    receipt_id_original = primer_intento.receipt_id

    mocker.patch.object(Receipt, 'validate', return_value=[])
    segundo_intento = generar_y_emitir_comprobante(venta)

    assert segundo_intento.receipt_id == receipt_id_original
    assert segundo_intento.estado == ComprobanteVenta.EMITIDO
    assert Receipt.objects.count() == 1


@pytest.mark.django_db
def test_sin_punto_de_venta_configurado_levanta_error(venta):
    PointOfSales.objects.all().delete()

    with pytest.raises(SinConfiguracionAfipError):
        generar_y_emitir_comprobante(venta)
