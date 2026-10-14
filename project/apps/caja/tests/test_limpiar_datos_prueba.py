from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

from caja.models import (
    Caja,
    CobroVenta,
    CuponPagoTarjeta,
    Gasto,
    MovimientoCaja,
    PagoTransferencia,
    PlanTarjetaDeCredito,
    TarjetaDeCredito,
    TipoGasto,
)
from cliente.models import Cliente
from cuentacorriente.constants import DEBITO
from cuentacorriente.models import CuentaCorriente, MovimientoCuentaCorriente
from empleado.models import Empleado, Sucursal
from persona.models import Persona
from venta.models import Venta, VentaArticulo

Usuario = get_user_model()


@pytest.fixture
def escenario_completo(db):
    """Arma un escenario que toca todas las tablas del comando: una venta con cobro en
    efectivo, un cupón de tarjeta, un pago por transferencia, una cuenta corriente con un
    movimiento ligado a esa misma venta, una caja con un Gasto suelto (sin relación con la
    venta), y un cliente."""
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    usuario = Usuario.objects.create_user(username='cajera', password='x', sucursal=sucursal)
    persona_empleado = Persona.objects.create(nombre='Ana', apellido='Vendedora', documento_identidad='11111111')
    empleado = Empleado.objects.create(persona=persona_empleado, cuil='20111111112')
    persona_cliente = Persona.objects.create(nombre='Juan', apellido='Cliente', documento_identidad='22222222')
    cliente = Cliente.objects.create(persona=persona_cliente, condicion_iva=Cliente.CONSUMIDOR_FINAL)

    venta = Venta.objects.create(
        empleado=empleado, fecha=timezone.now(), monto=Decimal('1000.00'), descuento=Decimal('0.00'),
        sucursal=sucursal, cliente=cliente, usuario=usuario,
    )
    from articulo.models import Articulo, Categoria, TipoIva, UnidadMedida
    tipo_iva = TipoIva.objects.create(nombre='21%', porcentaje=Decimal('21.00'))
    categoria = Categoria.objects.create(nombre='Carnes', tipo_iva=tipo_iva)
    unidad_medida = UnidadMedida.objects.create(nombre='Kilogramo', abreviatura='kg')
    articulo = Articulo.objects.create(
        nombre='Vacío', abreviatura='VACIO', codigo='0001', categoria=categoria, unidad_medida=unidad_medida,
    )
    VentaArticulo.objects.create(
        venta=venta, articulo=articulo, nombre_articulo=articulo.nombre, codigo_articulo=articulo.codigo,
        cantidad_peso=Decimal('1.000'), precio_unitario=Decimal('1000.00'), precio_promocion=Decimal('1000.00'),
        total_articulo=Decimal('1000.00'),
    )

    caja = Caja.objects.create(sucursal=sucursal, usuario=usuario, caja_inicial=Decimal('0'))
    CobroVenta.objects.create(usuario=usuario, caja=caja, sucursal=sucursal, importe=Decimal('400'), venta=venta, tipo='ingreso')

    tarjeta = TarjetaDeCredito.objects.create(nombre='Visa')
    plan = PlanTarjetaDeCredito.objects.create(tarjeta=tarjeta, nombre_plan='1 pago')
    CuponPagoTarjeta.objects.create(
        cliente=cliente, plan_tarjeta=plan, importe=Decimal('300'), importe_con_recargo=Decimal('300'), venta=venta,
    )
    PagoTransferencia.objects.create(importe=Decimal('300'), documento_identidad='22222222', venta=venta)

    cuenta = CuentaCorriente.objects.create(cliente=cliente)
    MovimientoCuentaCorriente.objects.create(cuenta=cuenta, importe=Decimal('0'), tipo=DEBITO, usuario=usuario, venta=venta)

    tipo_gasto = TipoGasto.objects.create(descripcion='Alquiler')
    Gasto.objects.create(
        usuario=usuario, caja=caja, sucursal=sucursal, tipo='egreso', importe=Decimal('500'),
        tipo_gasto=tipo_gasto, concepto='Alquiler',
    )

    return {
        'sucursal': sucursal, 'usuario': usuario, 'cliente': cliente, 'venta': venta, 'caja': caja,
        'tarjeta': tarjeta, 'plan': plan,
    }


def _conteos():
    return {
        'ventas': Venta.objects.count(),
        'venta_articulos': VentaArticulo.objects.count(),
        'cobros': CobroVenta.objects.count(),
        'cupones': CuponPagoTarjeta.objects.count(),
        'transferencias': PagoTransferencia.objects.count(),
        'mov_cc': MovimientoCuentaCorriente.objects.count(),
        'cuentas_cc': CuentaCorriente.objects.count(),
        'mov_caja': MovimientoCaja.objects.count(),
        'cajas': Caja.objects.count(),
        'clientes': Cliente.objects.count(),
        'gastos': Gasto.objects.count(),
    }


@pytest.mark.django_db
def test_dry_run_no_borra_nada(escenario_completo):
    antes = _conteos()
    call_command('limpiar_datos_prueba', '--todo')
    assert _conteos() == antes


@pytest.mark.django_db
def test_ventas_borra_venta_y_todo_lo_que_cuelga_de_ella(escenario_completo):
    call_command('limpiar_datos_prueba', '--ventas', '--confirmar')
    conteos = _conteos()
    assert conteos['ventas'] == 0
    assert conteos['venta_articulos'] == 0
    assert conteos['cobros'] == 0
    assert conteos['cupones'] == 0
    assert conteos['transferencias'] == 0
    assert conteos['mov_cc'] == 0  # el movimiento estaba ligado a la venta
    # lo que NO pidió --ventas sigue intacto:
    assert conteos['cuentas_cc'] == 1
    assert conteos['cajas'] == 1
    assert conteos['gastos'] == 1
    assert conteos['clientes'] == 1


@pytest.mark.django_db
def test_cuentas_corrientes_solo_borra_cuentas_y_sus_movimientos(escenario_completo):
    call_command('limpiar_datos_prueba', '--cuentas-corrientes', '--confirmar')
    conteos = _conteos()
    assert conteos['cuentas_cc'] == 0
    assert conteos['mov_cc'] == 0
    # las ventas y todo lo demás siguen intactas
    assert conteos['ventas'] == 1
    assert conteos['cobros'] == 1


@pytest.mark.django_db
def test_caja_cascadea_a_cobroventa_y_gasto_sin_romper(escenario_completo):
    call_command('limpiar_datos_prueba', '--caja', '--confirmar')
    conteos = _conteos()
    assert conteos['mov_caja'] == 0
    assert conteos['cobros'] == 0  # CobroVenta es MovimientoCaja, cascadea
    assert conteos['gastos'] == 0  # Gasto también
    assert conteos['cajas'] == 0
    # la venta en sí no se toca (sólo su registro de cobro en caja)
    assert conteos['ventas'] == 1


@pytest.mark.django_db
def test_clientes_solo_falla_protegido_si_faltan_los_otros_alcances(escenario_completo):
    antes = _conteos()
    call_command('limpiar_datos_prueba', '--clientes', '--confirmar')
    # ProtectedError atrapado adentro del comando -> no debe propagar, y no debe borrar nada
    # (transacción revertida completa).
    assert _conteos() == antes


@pytest.mark.django_db
def test_todo_limpia_absolutamente_todo_sin_errores(escenario_completo):
    call_command('limpiar_datos_prueba', '--todo', '--confirmar')
    conteos = _conteos()
    assert all(valor == 0 for valor in conteos.values())


@pytest.mark.django_db
def test_todo_no_toca_catalogo_de_tarjetas(escenario_completo):
    call_command('limpiar_datos_prueba', '--todo', '--confirmar')
    assert TarjetaDeCredito.objects.count() == 1
    assert PlanTarjetaDeCredito.objects.count() == 1
