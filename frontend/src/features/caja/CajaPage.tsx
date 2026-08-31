import { useEffect, useState } from 'react'
import { Alert, Button, Container, Divider, Group, Modal, Paper, Table, Text, Title } from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { abrirCaja, cajaAbiertaActual, cerrarCaja, listarCajas } from '../../api/caja'
import { ApiError } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import EstadoVacio from '../../components/EstadoVacio'
import type { Caja, ResumenCierreCaja } from '../../types/caja'
import { formatearMonto } from '../ventas/dinero'

export default function CajaPage() {
  const { perfil } = useAuth()
  const [cajaAbierta, setCajaAbierta] = useState<Caja | null>(null)
  const [historial, setHistorial] = useState<Caja[]>([])
  const [cargando, setCargando] = useState(true)
  const [procesando, setProcesando] = useState(false)
  const [resumen, setResumen] = useState<ResumenCierreCaja | null>(null)

  const cargar = () => {
    if (!perfil?.sucursal) return
    setCargando(true)
    Promise.all([cajaAbiertaActual(perfil.sucursal), listarCajas({ sucursal: perfil.sucursal })])
      .then(([abierta, todas]) => {
        setCajaAbierta(abierta.results[0] ?? null)
        setHistorial(todas.results)
      })
      .catch((err: ApiError) => notifications.show({ title: 'Error', message: err.message, color: 'red' }))
      .finally(() => setCargando(false))
  }

  useEffect(cargar, [perfil?.sucursal])

  const handleAbrir = async () => {
    setProcesando(true)
    try {
      await abrirCaja()
      notifications.show({ message: 'Caja abierta.', color: 'green' })
      cargar()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo abrir la caja', message: detalle, color: 'red' })
    } finally {
      setProcesando(false)
    }
  }

  const handleCerrar = async () => {
    if (!cajaAbierta) return
    setProcesando(true)
    try {
      const r = await cerrarCaja(cajaAbierta.id)
      setResumen(r)
      notifications.show({ message: 'Caja cerrada.', color: 'green' })
      cargar()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo cerrar la caja', message: detalle, color: 'red' })
    } finally {
      setProcesando(false)
    }
  }

  if (!perfil?.sucursal) {
    return (
      <Container size="md" py="md">
        <Alert color="yellow">Tu usuario no tiene una sucursal asignada — no se puede operar la caja.</Alert>
      </Container>
    )
  }

  return (
    <Container size="md" py="md">
      <Title order={2}>Caja</Title>
      <Text c="dimmed" size="sm" mb="lg">
        {perfil.sucursal_nombre}
      </Text>

      <Paper withBorder p="lg" mb="lg">
        {cargando ? (
          <Text>Cargando…</Text>
        ) : cajaAbierta ? (
          <>
            <Group justify="space-between">
              <div>
                <Text fw={600}>Caja abierta</Text>
                <Text size="sm" c="dimmed">
                  Desde {new Date(cajaAbierta.fecha_inicio).toLocaleString('es-AR')}
                </Text>
                <Text mt="xs">Saldo actual: {formatearMonto(cajaAbierta.saldo_actual)}</Text>
              </div>
              <Button color="red" loading={procesando} onClick={() => void handleCerrar()}>
                Cerrar caja
              </Button>
            </Group>
          </>
        ) : (
          <Group justify="space-between">
            <Text>No hay una caja abierta en esta sucursal.</Text>
            <Button color="red" loading={procesando} onClick={() => void handleAbrir()}>
              Abrir caja
            </Button>
          </Group>
        )}
      </Paper>

      <Paper withBorder p="md">
        <Text size="sm" c="dimmed" mb="sm">
          Historial
        </Text>
        <Table striped verticalSpacing="sm">
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Apertura</Table.Th>
              <Table.Th>Cierre</Table.Th>
              <Table.Th>Caja inicial</Table.Th>
              <Table.Th>Caja final</Table.Th>
              <Table.Th>Usuario</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {historial.map((c) => (
              <Table.Tr key={c.id}>
                <Table.Td>{new Date(c.fecha_inicio).toLocaleString('es-AR')}</Table.Td>
                <Table.Td>{c.fecha_fin ? new Date(c.fecha_fin).toLocaleString('es-AR') : '—'}</Table.Td>
                <Table.Td>{formatearMonto(c.caja_inicial)}</Table.Td>
                <Table.Td>{c.fecha_fin ? formatearMonto(c.caja_final) : '—'}</Table.Td>
                <Table.Td>{c.usuario_username}</Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
        {!cargando && historial.length === 0 && <EstadoVacio titulo="Sin cajas todavía" />}
      </Paper>

      <Modal opened={!!resumen} onClose={() => setResumen(null)} title="Resumen de cierre" size="md">
        {resumen && (
          <>
            <Text fw={600}>Caja final: {formatearMonto(resumen.caja_final)}</Text>
            <Divider my="sm" label="Ingresos" labelPosition="center" />
            {resumen.ingresos.map((i) => (
              <Group justify="space-between" key={i.concepto}>
                <Text size="sm">{i.concepto}</Text>
                <Text size="sm">{formatearMonto(i.importe)}</Text>
              </Group>
            ))}
            <Group justify="space-between" fw={600} mt={4}>
              <Text size="sm">{resumen.total_ingresos.concepto}</Text>
              <Text size="sm">{formatearMonto(resumen.total_ingresos.importe)}</Text>
            </Group>
            <Divider my="sm" label="Egresos" labelPosition="center" />
            {resumen.egresos.map((e) => (
              <Group justify="space-between" key={e.concepto}>
                <Text size="sm">{e.concepto}</Text>
                <Text size="sm">{formatearMonto(e.importe)}</Text>
              </Group>
            ))}
            <Group justify="space-between" fw={600} mt={4}>
              <Text size="sm">{resumen.total_egresos.concepto}</Text>
              <Text size="sm">{formatearMonto(resumen.total_egresos.importe)}</Text>
            </Group>
            <Divider my="sm" />
            <Group justify="space-between" fw={600}>
              <Text size="sm">{resumen.total_cuenta_corriente.concepto}</Text>
              <Text size="sm">{formatearMonto(resumen.total_cuenta_corriente.importe)}</Text>
            </Group>
          </>
        )}
      </Modal>
    </Container>
  )
}
