import { useEffect, useState } from 'react'
import { Badge, Button, Group, Modal, NumberInput, SegmentedControl, Table, Text, TextInput } from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { crearMovimientoCuentaCorriente, listarMovimientosCuentaCorriente } from '../../api/cuentacorriente'
import { ApiError } from '../../api/client'
import type { CuentaCorriente, MovimientoCuentaCorriente, TipoMovimientoCC } from '../../types/cuentacorriente'
import { formatearMonto } from '../ventas/dinero'

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
  const [observaciones, setObservaciones] = useState('')
  const [guardando, setGuardando] = useState(false)

  const cargar = () => {
    if (!cuenta) return
    setCargando(true)
    listarMovimientosCuentaCorriente(cuenta.id)
      .then((r) => setMovimientos(r.results))
      .catch((err: ApiError) => notifications.show({ title: 'Error', message: err.message, color: 'red' }))
      .finally(() => setCargando(false))
  }

  useEffect(() => {
    if (opened) {
      cargar()
      setTipo('C')
      setImporte('')
      setObservaciones('')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, cuenta])

  const agregarMovimiento = async () => {
    if (!cuenta || !importe) return
    setGuardando(true)
    try {
      await crearMovimientoCuentaCorriente({
        cuenta: cuenta.id,
        tipo,
        importe,
        observaciones: observaciones || null,
      })
      notifications.show({ message: 'Movimiento registrado.', color: 'green' })
      setImporte('')
      setObservaciones('')
      cargar()
      onCambio()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo registrar', message: detalle, color: 'red' })
    } finally {
      setGuardando(false)
    }
  }

  if (!cuenta) return null

  return (
    <Modal opened={opened} onClose={onClose} title={cuenta.cliente_nombre} size="lg">
      <Group justify="space-between" mb="md">
        <Text>
          Saldo: <strong>{formatearMonto(cuenta.saldo)}</strong>
        </Text>
        <Text c="dimmed" size="sm">
          Tope: {formatearMonto(cuenta.tope)}
        </Text>
      </Group>

      <Group align="flex-end" mb="md">
        <SegmentedControl
          value={tipo}
          onChange={(v) => setTipo(v as TipoMovimientoCC)}
          data={[
            { label: 'Pago (crédito)', value: 'C' },
            { label: 'Consumo (débito)', value: 'D' },
          ]}
        />
        <NumberInput placeholder="Importe" decimalScale={2} min={0} value={importe} onChange={(v) => setImporte(String(v))} />
        <TextInput placeholder="Observaciones" value={observaciones} onChange={(e) => setObservaciones(e.currentTarget.value)} style={{ flex: 1 }} />
        <Button loading={guardando} disabled={!importe} onClick={() => void agregarMovimiento()}>
          Registrar
        </Button>
      </Group>

      <Table striped verticalSpacing="xs">
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Fecha</Table.Th>
            <Table.Th>Tipo</Table.Th>
            <Table.Th>Importe</Table.Th>
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
              <Table.Td>{m.usuario_username}</Table.Td>
              <Table.Td>{m.observaciones ?? '—'}</Table.Td>
            </Table.Tr>
          ))}
          {!cargando && movimientos.length === 0 && (
            <Table.Tr>
              <Table.Td colSpan={5}>Sin movimientos todavía.</Table.Td>
            </Table.Tr>
          )}
        </Table.Tbody>
      </Table>
    </Modal>
  )
}
