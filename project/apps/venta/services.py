"""Operaciones de negocio transaccionales del dominio venta, para el endpoint DRF nuevo
(venta/api.py). No tocan ni reemplazan el flujo legacy (venta/views.py `guardar_venta`, admin
action `anular_venta`) — conviven (DEC-001) hasta que React reemplace esa pantalla.
"""
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from caja.models import Caja
from venta.exceptions import CajaCerradaError, SinSucursalError, VentaYaAnuladaError, VentaYaCobradaError
from venta.models import Venta, VentaArticulo
from venta.utils import calcular_precio_venta_articulo

CENTAVO = Decimal('0.01')


def _caja_abierta_o_error(sucursal):
    if sucursal is None:
        raise SinSucursalError('El usuario no tiene una sucursal asignada.')
    caja_abierta = Caja.objects.filter(
        sucursal=sucursal, fecha_fin__isnull=True, fecha_inicio__isnull=False
    ).last()
    if not caja_abierta:
        raise CajaCerradaError('La caja de la sucursal está cerrada, no se pueden registrar ventas.')
    return caja_abierta


@transaction.atomic
def crear_venta(*, empleado, cliente, items, usuario):
    """Alta transaccional de una venta y sus artículos.

    `items` es una lista de dicts `{'articulo': Articulo, 'cantidad_peso': Decimal}` — el peso ya
    viene resuelto del frontend (balanza física en el mostrador, PEND-F: sigue siendo el
    navegador el que la lee directo de `http://localhost:4700`, fuera de Django). El PRECIO, en
    cambio, nunca se toma del frontend: se recalcula acá con
    `venta.utils.calcular_precio_venta_articulo`.
    """
    sucursal = usuario.sucursal
    _caja_abierta_o_error(sucursal)

    venta = Venta.objects.create(
        fecha=timezone.now(), monto=Decimal('0'), descuento=Decimal('0'), sucursal=sucursal,
        cliente=cliente, usuario=usuario, empleado=empleado,
    )

    total = Decimal('0')
    for item in items:
        articulo = item['articulo']
        cantidad_peso = item['cantidad_peso']
        precio_lista, precio_final = calcular_precio_venta_articulo(cliente, articulo, sucursal)
        monto_articulo = (precio_final * cantidad_peso).quantize(CENTAVO, rounding=ROUND_HALF_UP)
        VentaArticulo.objects.create(
            total_articulo=monto_articulo,
            cantidad_peso=cantidad_peso,
            precio_promocion=precio_final,
            precio_unitario=precio_lista,
            nombre_articulo=articulo.nombre,
            articulo=articulo,
            codigo_articulo=articulo.codigo,
            venta=venta,
        )
        total += monto_articulo

    venta.monto = total
    venta.save(update_fields=['monto'])
    venta.refresh_from_db()
    return venta


@transaction.atomic
def anular_venta(venta):
    """Anula una venta no cobrada.

    Anular una venta YA cobrada implicaría revertir cobros/cupones de caja o cuenta corriente ya
    generados — qué debe pasar exactamente ahí (¿reversar el movimiento?, ¿generar un egreso
    compensatorio?, ¿no permitirlo?) es una decisión de negocio que ni siquiera el código legacy
    resolvía realmente (el intento de borrado tenía un bug, `.delete` sin paréntesis, que hacía
    que nunca se ejecutara — SISTEMA_ACTUAL.md §15.7). En vez de decidir eso unilateralmente acá,
    este endpoint nuevo sólo cubre el caso simple y frecuente (cancelar antes de cobrar) y deja
    el otro caso pendiente de definición explícita (DECISIONES.md PEND-J).
    """
    if venta.anulado:
        raise VentaYaAnuladaError('La venta ya está anulada.')
    if venta.cobrada:
        raise VentaYaCobradaError(
            'La venta ya fue cobrada; anular una venta cobrada todavía no está soportado por '
            'este endpoint (ver DECISIONES.md PEND-J).'
        )
    venta.anulado = True
    venta.save(update_fields=['anulado'])
    return venta
