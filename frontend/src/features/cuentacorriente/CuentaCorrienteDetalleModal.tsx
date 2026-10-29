import { useEffect, useState } from 'react'
import { Badge, Button, Group, Modal, NumberInput, Select, SegmentedControl, Stack, Table, Text, TextInput } from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { listarTodosLosBancos } from '../../api/caja'
import { crearMovimientoCuentaCorriente, listarMovimientosCuentaCorriente, obtenerCuentaCorriente } from '../../api/cuentacorriente'
import { mensajeDeError } from '../../api/client'
import type { Banco } from '../../types/caja'
import type { CuentaCorriente, MedioPagoCC, MovimientoCuentaCorriente, TipoMovimientoCC } from '../../types/cuentacorriente'
import { MEDIOS_PAGO_INFO } from '../ventas/mediosPago'
import { formatearMonto } from '../ventas/dinero'
import { etiquetaSaldo } from './saldo'

const OPCIONES_MEDIO_PAGO: { value: MedioPagoCC; label: string }[] = [
  { value: 'efectivo', label: MEDIOS_PAGO_INFO.efectivo.etiqueta },
  { value: 'transferencia', label: MEDIOS_PAGO_INFO.transferencia.etiqueta },
  { value: 'qr', label: MEDIOS_PAGO_INFO.qr.etiqueta },
]

interface Props {
  opened: boolean
  onClose: () => void
  cuenta: CuentaCorriente | null
  onCambio: () => void
}

export default function CuentaCorrienteDetalleModal({ opened, onClose, cuenta, onCambio }: Props) {
  const [movimientos, setMovimientos] = useState<MovimientoCuentaCorriente[]>([])
  const [cargando, setCargando] = useState(false)
  const [tipo, setTipo] = useState<TipoMovimientoCC>('C')
  const [importe, setImporte] = useState('')
  const [medioPago, setMedioPago] = useState<MedioPagoCC | null>(null)
  const [banco, setBanco] = useState<number | null>(null)
  const [bancos, setBancos] = useState<Banco[]>([])
  const [observaciones, setObservaciones] = useState('')
  const [guardando, setGuardando] = useState(false)
  // Saldo/disponible propios del modal, no el `cuenta` del padre: ese prop queda desactualizado
  // después de registrar un movimiento (el padre no vuelve a pasar un objeto nuevo mientras el
  // modal sigue abierto) -> sin esto, "Disponible" mostraba un valor viejo apenas se cargaba un
  // crédito o débito sin cerrar el modal.
  const [cuentaActual, setCuentaActual] = useState<CuentaCorriente | null>(cuenta)

  const cargar = () => {
    if (!cuenta) return
    setCargando(true)
    listarMovimientosCuentaCorriente(cuenta.id)
      .then((r) => setMovimientos(r.results))
      .catch((err: unknown) => notifications.show({ title: 'Error', message: mensajeDeError(err), color: 'red' }))
      .finally(() => setCargando(false))
  }

  useEffect(() => {
    if (opened && cuenta) {
      cargar()
      // El `cuenta` que pasa el padre es la fila tal como la trajo el último listado -si hubo
      // ventas en cuenta corriente desde entonces (muy probable: el cajero las carga desde la
      // pantalla de venta, no desde acá), ese saldo queda viejo. Se pisa con uno fresco apenas
      // se abre, no sólo después de registrar un movimiento desde este modal.
      setCuentaActual(cuenta)
      obtenerCuentaCorriente(cuenta.id)
        .then(setCuentaActual)
        .catch(() => {
          // si falla, nos quedamos con el `cuenta` del padre (ya seteado arriba) antes que
          // dejar el modal sin nada que mostrar.
        })
      setTipo('C')
      setImporte('')
      setMedioPago(null)
      setBanco(null)
      setObservaciones('')
      if (bancos.length === 0) {
        listarTodosLosBancos()
          .then((r) => setBancos(r.results))
          .catch(() => notifications.show({ message: 'No se pudieron cargar los bancos.', color: 'red' }))
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, cuenta])

  // El medio de pago (y el banco) sólo aplican a un Crédito (ver cuentacorriente.serializers
  // .MovimientoCuentaCorrienteSerializer.validate) -se limpian al pasar a Débito para no mandar
  // un valor que después el backend ignora igual, pero que confundiría si quedara pisado.
  const cambiarTipo = (v: string) => {
    setTipo(v as TipoMovimientoCC)
    if (v === 'D') {
      setMedioPago(null)
      setBanco(null)
    }
  }

  const cambiarMedioPago = (v: string | null) => {
    setMedioPago(v as MedioPagoCC | null)
    if (v !== 'qr' && v !== 'transferencia') setBanco(null)
  }

  // En QR el banco es obligatorio (mismo criterio que al cobrar una venta: hace falta poder
  // identificar el pago); en transferencia queda opcional.
  const faltaBanco = medioPago === 'qr' && !banco

  const agregarMovimiento = async () => {
    if (!cuenta || !importe) return
    if (tipo === 'C' && (!medioPago || faltaBanco)) return
    setGuardando(true)
    try {
      await crearMovimientoCuentaCorriente({
        cuenta: cuenta.id,
        tipo,
        importe,
        medio_pago: tipo === 'C' ? medioPago : null,
        banco: tipo === 'C' ? banco : null,
        observaciones: observaciones || null,
      })
      notifications.show({ message: 'Movimiento registrado.', color: 'green' })
      setImporte('')
      setMedioPago(null)
      setBanco(null)
      setObservaciones('')
      cargar()
      void obtenerCuentaCorriente(cuenta.id).then(setCuentaActual)
      onCambio()
    } catch (err) {
      const detalle = mensajeDeError(err)
      notifications.show({ title: 'No se pudo registrar', message: detalle, color: 'red' })
    } finally {
      setGuardando(false)
    }
  }

  if (!cuenta) return null
  const datos = cuentaActual ?? cuenta
  const etiqueta = etiquetaSaldo(datos.saldo)

  return (
    <Modal opened={opened} onClose={onClose} title={cuenta.cliente_nombre} size="xl">
      <Group justify="space-between" mb="md">
        <Text>
          Saldo: <strong>{formatearMonto(datos.saldo)}</strong>{' '}
          {etiqueta && (
            <Text component="span" c={etiqueta.color} size="sm" fw={600}>
              {etiqueta.texto}
            </Text>
          )}
        </Text>
        <Text c="dimmed" size="sm">
          Tope: {formatearMonto(datos.tope)}
        </Text>
        {/* La cuenta corriente es una línea de crédito hasta `tope` (ver
           cuentacorriente.services.crear_movimiento_cuenta_corriente): esto es cuánto más se le
           puede fiar al cliente antes de que un débito se rechace. */}
        <Text c="dimmed" size="sm">
          Disponible: {formatearMonto(String(Number(datos.tope) - Number(datos.saldo)))}
        </Text>
      </Group>

      <Stack gap="sm" mb="md">
        <SegmentedControl
          value={tipo}
          onChange={cambiarTipo}
          data={[
            { label: 'Pagos del Cliente', value: 'C' },
            { label: 'Consumo (débito)', value: 'D' },
          ]}
        />
        <Group align="flex-end" wrap="wrap">
          <NumberInput placeholder="Importe" decimalScale={2} min={0} value={importe} onChange={(v) => setImporte(String(v))} />
          {tipo === 'C' && (
            <Select
              placeholder="Medio de pago"
              data={OPCIONES_MEDIO_PAGO}
              value={medioPago}
              onChange={cambiarMedioPago}
              w={160}
            />
          )}
          {tipo === 'C' && (medioPago === 'qr' || medioPago === 'transferencia') && (
            <Select
              placeholder={medioPago === 'qr' ? 'Banco (obligatorio)' : 'Banco (opcional)'}
              data={bancos.map((b) => ({ value: String(b.id), label: b.nombre }))}
              value={banco ? String(banco) : null}
              onChange={(v) => setBanco(v ? Number(v) : null)}
              clearable
              w={180}
            />
          )}
          <TextInput placeholder="Observaciones" value={observaciones} onChange={(e) => setObservaciones(e.currentTarget.value)} style={{ flex: 1, minWidth: 180 }} />
          <Button
            loading={guardando}
            disabled={!importe || (tipo === 'C' && (!medioPago || faltaBanco))}
            onClick={() => void agregarMovimiento()}
          >
            Registrar
          </Button>
        </Group>
      </Stack>

      <Table striped verticalSpacing="xs">
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Fecha</Table.Th>
            <Table.Th>Tipo</Table.Th>
            <Table.Th>Importe</Table.Th>
            <Table.Th>Medio de pago</Table.Th>
            <Table.Th>Usuario</Table.Th>
            <Table.Th>Observaciones</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {movimientos.map((m) => (
            <Table.Tr key={m.id}>
              <Table.Td>{new Date(m.fecha).toLocaleDateString('es-AR')}</Table.Td>
              <Table.Td>
                <Badge color={m.tipo === 'C' ? 'green' : 'orange'} variant="light">
                  {m.tipo_display}
                </Badge>
              </Table.Td>
              <Table.Td>{formatearMonto(m.importe)}</Table.Td>
              <Table.Td>
                {m.medio_pago ? (
                  <Group gap={4} wrap="nowrap">
                    <Badge color={MEDIOS_PAGO_INFO[m.medio_pago].color} variant="light">
                      {m.medio_pago_display}
                    </Badge>
                    {m.banco_nombre && (
                      <Text size="xs" c="dimmed">
                        ({m.banco_nombre})
                      </Text>
                    )}
                  </Group>
                ) : (
                  '—'
                )}
              </Table.Td>
              <Table.Td>{m.usuario_username}</Table.Td>
              <Table.Td>{m.observaciones ?? '—'}</Table.Td>
            </Table.Tr>
          ))}
          {!cargando && movimientos.length === 0 && (
            <Table.Tr>
              <Table.Td colSpan={6}>Sin movimientos todavía.</Table.Td>
            </Table.Tr>
          )}
        </Table.Tbody>
      </Table>
    </Modal>
  )
}
