from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import ProtectedError

from caja.models import Caja, CobroVenta, CuponPagoTarjeta, MovimientoCaja, PagoTransferencia
from cliente.models import Cliente
from cuentacorriente.models import CuentaCorriente, MovimientoCuentaCorriente
from venta.models import Venta, VentaArticulo


class Command(BaseCommand):
    help = (
        "Borra datos de prueba (ventas, cobros, cuentas corrientes, caja y/o clientes) para "
        "dejar el sistema limpio antes de arrancar a usarlo en serio. Pensado para instancias "
        "sin ambiente de desarrollo separado, donde las pruebas se hacen sobre la base real "
        "(carnicería/verdulería/pollería) y después hay que resetearla en cada una.\n\n"
        "Por defecto NO borra nada: sólo muestra cuántas filas de cada tabla se borrarían "
        "(dry-run). Agregá --confirmar para ejecutar el borrado de verdad.\n\n"
        "No toca catálogo/configuración (artículos, precios, empleados, usuarios, sucursales, "
        "tarjetas/planes de tarjeta) — sólo los datos operativos de las pruebas."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--ventas', action='store_true',
            help='Ventas, sus artículos y sus cobros (efectivo/tarjeta/transferencia/cta. corriente).',
        )
        parser.add_argument(
            '--cuentas-corrientes', action='store_true', dest='cuentas_corrientes',
            help='Cuentas corrientes de clientes y sus movimientos.',
        )
        parser.add_argument(
            '--caja', action='store_true',
            help='Aperturas/cierres de caja y sus movimientos (ingresos, gastos, sueldos, adelantos, retiros, cobros).',
        )
        parser.add_argument(
            '--clientes', action='store_true',
            help=(
                'TODOS los clientes cargados. No filtra "de prueba" vs. reales — revisá el '
                'conteo del dry-run antes de confirmar. Necesita que ventas y cuentas '
                'corrientes ya estén (o se estén) limpiando en la misma corrida.'
            ),
        )
        parser.add_argument(
            '--todo', action='store_true',
            help='Equivale a --ventas --cuentas-corrientes --caja --clientes.',
        )
        parser.add_argument(
            '--confirmar', action='store_true',
            help='Ejecuta el borrado de verdad. Sin este flag sólo se muestra un resumen (dry-run).',
        )

    def handle(self, *args, **options):
        alcance = {
            'ventas': options['ventas'] or options['todo'],
            'cuentas_corrientes': options['cuentas_corrientes'] or options['todo'],
            'caja': options['caja'] or options['todo'],
            'clientes': options['clientes'] or options['todo'],
        }
        if not any(alcance.values()):
            self.stderr.write(self.style.ERROR(
                'No elegiste ningún alcance. Pasá --ventas, --cuentas-corrientes, --caja, '
                '--clientes, o --todo (--help para el detalle de cada uno).'
            ))
            return

        confirmar = options['confirmar']
        self.stdout.write(self.style.WARNING(
            'MODO SIMULACIÓN (dry-run) — todavía no se borra nada.' if not confirmar
            else 'MODO BORRADO REAL — esto no se puede deshacer.'
        ))

        try:
            if confirmar:
                with transaction.atomic():
                    total = self._ejecutar(alcance, confirmar=True)
            else:
                total = self._ejecutar(alcance, confirmar=False)
        except ProtectedError as exc:
            self.stderr.write(self.style.ERROR(
                f'\nSe abortó todo (no se borró nada, la transacción se revirtió): {exc}\n'
                'Probablemente falta incluir otro alcance en la misma corrida — por ejemplo, '
                '--clientes necesita --ventas y --cuentas-corrientes juntos (o --todo).'
            ))
            return

        if confirmar:
            self.stdout.write(self.style.SUCCESS(f'\nListo. Se borraron {total} filas en total.'))
        else:
            self.stdout.write(self.style.WARNING(
                f'\nDry-run: se borrarían {total} filas en total. '
                'Repetí el comando agregando --confirmar para hacerlo de verdad.'
            ))

    def _ejecutar(self, alcance, confirmar):
        total = 0
        # Orden importante: ventas antes que caja (libera los CobroVenta que protegen a Venta),
        # cuentas corrientes antes que clientes (CuentaCorriente.cliente es PROTECT), y clientes
        # al final de todo.
        if alcance['ventas']:
            total += self._limpiar_ventas(confirmar)
        if alcance['cuentas_corrientes']:
            total += self._limpiar_cuentas_corrientes(confirmar)
        if alcance['caja']:
            total += self._limpiar_caja(confirmar)
        if alcance['clientes']:
            total += self._limpiar_clientes(confirmar)
        return total

    def _contar_y_borrar(self, queryset, etiqueta, confirmar):
        cantidad = queryset.count()
        self.stdout.write(f'  {etiqueta}: {cantidad}')
        if confirmar and cantidad:
            queryset.delete()
        return cantidad

    def _limpiar_ventas(self, confirmar):
        self.stdout.write(self.style.MIGRATE_HEADING('Ventas y cobros'))
        ventas = Venta.objects.all()
        total = 0
        total += self._contar_y_borrar(CuponPagoTarjeta.objects.filter(venta__in=ventas), 'Cupones de tarjeta', confirmar)
        total += self._contar_y_borrar(PagoTransferencia.objects.filter(venta__in=ventas), 'Pagos por transferencia', confirmar)
        total += self._contar_y_borrar(
            MovimientoCuentaCorriente.objects.filter(venta__in=ventas),
            'Movimientos de cta. corriente ligados a una venta', confirmar,
        )
        total += self._contar_y_borrar(CobroVenta.objects.filter(venta__in=ventas), 'Cobros de venta', confirmar)
        total += self._contar_y_borrar(VentaArticulo.objects.filter(venta__in=ventas), 'Artículos de venta', confirmar)
        total += self._contar_y_borrar(ventas, 'Ventas', confirmar)
        return total

    def _limpiar_cuentas_corrientes(self, confirmar):
        self.stdout.write(self.style.MIGRATE_HEADING('Cuentas corrientes'))
        cuentas = CuentaCorriente.objects.all()
        total = 0
        total += self._contar_y_borrar(
            MovimientoCuentaCorriente.objects.filter(cuenta__in=cuentas), 'Movimientos de cta. corriente', confirmar,
        )
        total += self._contar_y_borrar(cuentas, 'Cuentas corrientes', confirmar)
        return total

    def _limpiar_caja(self, confirmar):
        self.stdout.write(self.style.MIGRATE_HEADING('Caja y movimientos'))
        total = 0
        # MovimientoCaja es la tabla base de Sueldo/Adelanto/Ingreso/RetiroEfectivo/Gasto/
        # CobroVenta (herencia multi-tabla) — borrarla de acá cascadea y borra también la fila
        # hija correspondiente en cada una, sin dejar huérfanos.
        total += self._contar_y_borrar(
            MovimientoCaja.objects.all(),
            'Movimientos de caja (ingresos, gastos, sueldos, adelantos, retiros, cobros)', confirmar,
        )
        total += self._contar_y_borrar(Caja.objects.all(), 'Aperturas/cierres de caja', confirmar)
        return total

    def _limpiar_clientes(self, confirmar):
        self.stdout.write(self.style.MIGRATE_HEADING('Clientes'))
        return self._contar_y_borrar(Cliente.objects.all(), 'Clientes (TODOS)', confirmar)
