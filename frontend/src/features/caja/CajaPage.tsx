import { useEffect, useState } from 'react'
import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Container,
  Divider,
  Group,
  Modal,
  NumberInput,
  Paper,
  Table,
  Text,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconEye, IconPrinter } from '@tabler/icons-react'
import {
  abrirCaja,
  cajaAbiertaActual,
  cerrarCaja,
  listarCajas,
  obtenerResumenCaja,
  previsualizarCierre,
} from '../../api/caja'
import { mensajeDeError } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import EstadoVacio from '../../components/EstadoVacio'
import type { Caja, ResumenCierreCaja } from '../../types/caja'
import { formatearMonto } from '../ventas/dinero'
import { abrirResumenCajaParaImprimir } from './imprimirTicketCaja'

export default function CajaPage() {
  const { perfil } = useAuth()
  const [cajaAbierta, setCajaAbierta] = useState<Caja | null>(null)
  const [historial, setHistorial] = useState<Caja[]>([])
  const [cargando, setCargando] = useState(true)
  const [procesando, setProcesando] = useState(false)
  const [resumen, setResumen] = useState<ResumenCierreCaja | null>(null)
  // Sólo se completa mientras `resumen` es una previsualización (fecha_fin todavía null) — el
  // arqueo de caja (conteo físico) que el cajero carga a mano antes de confirmar el cierre.
  const [arqueo, setArqueo] = useState<number | ''>('')

  const cargar = () => {
    if (!perfil?.sucursal) return
    setCargando(true)
    Promise.all([cajaAbiertaActual(perfil.sucursal), listarCajas({ sucursal: perfil.sucursal })])
      .then(([abierta, todas]) => {
        setCajaAbierta(abierta.results[0] ?? null)
        setHistorial(todas.results)
      })
      .catch((err: unknown) => notifications.show({ title: 'Error', message: mensajeDeError(err), color: 'red' }))
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
      const detalle = mensajeDeError(err)
      notifications.show({ title: 'No se pudo abrir la caja', message: detalle, color: 'red' })
    } finally {
      setProcesando(false)
    }
  }

  // Abre el diálogo "Resumen de cierre" en modo previsualización (todavía no cierra la caja):
  // ahí el cajero carga el arqueo de caja y sólo si alcanza confirma el cierre real.
  const handleAbrirCierre = async () => {
    if (!cajaAbierta) return
    setProcesando(true)
    try {
      const r = await previsualizarCierre(cajaAbierta.id)
      setResumen(r)
      setArqueo('')
    } catch (err) {
      const detalle = mensajeDeError(err)
      notifications.show({ title: 'No se pudo previsualizar el cierre', message: detalle, color: 'red' })
    } finally {
      setProcesando(false)
    }
  }

  // Confirma el cierre real (con el arqueo cargado) y, recién ahí, genera el PDF del resumen.
  const handleConfirmarCierre = async () => {
    if (!resumen || arqueo === '') return
    setProcesando(true)
    try {
      const cerrada = await cerrarCaja(resumen.id, String(arqueo))
      notifications.show({ message: 'Caja cerrada.', color: 'green' })
      cargar()
      await abrirResumenCajaParaImprimir(cerrada.id)
      setResumen(null)
    } catch (err) {
      const detalle = mensajeDeError(err)
      notifications.show({ title: 'No se pudo cerrar la caja', message: detalle, color: 'red' })
    } finally {
      setProcesando(false)
    }
  }

  // Reabre el mismo diálogo "Resumen de cierre" para una caja ya cerrada del historial — antes
  // el ícono de la fila abría directo el PDF (imprimirCaja); ahora primero se ve el resumen acá
  // (formato más ordenado) y de ahí, si hace falta, se imprime (ver botón dentro del Modal).
  const handleVerResumen = async (id: number) => {
    try {
      const r = await obtenerResumenCaja(id)
      setResumen(r)
    } catch (err) {
      const detalle = mensajeDeError(err)
      notifications.show({ title: 'No se pudo obtener el resumen', message: detalle, color: 'red' })
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
          <Group justify="space-between" align="flex-end">
            <div>
              <Badge color="green" variant="light" mb={6}>
                Caja abierta
              </Badge>
              <Text size="sm" c="dimmed">
                Desde {new Date(cajaAbierta.fecha_inicio).toLocaleString('es-AR')}
              </Text>
              <Text size="sm" c="dimmed" mt={4}>
                Saldo actual
              </Text>
              <Text fz={32} fw={800}>
                {formatearMonto(cajaAbierta.saldo_actual)}
              </Text>
            </div>
            <Button size="lg" color="red" loading={procesando} onClick={() => void handleAbrirCierre()}>
              Cerrar caja
            </Button>
          </Group>
        ) : (
          <Group justify="space-between" align="center">
            <Text>No hay una caja abierta en esta sucursal.</Text>
            <Button size="lg" color="red" loading={procesando} onClick={() => void handleAbrir()}>
              Abrir caja
            </Button>
          </Group>
        )}
      </Paper>

      <Paper withBorder p={0}>
        <Text size="sm" c="dimmed" p="md" pb={0}>
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
              <Table.Th />
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
                <Table.Td>
                  {c.fecha_fin && (
                    <ActionIcon
                      variant="subtle"
                      aria-label="Ver resumen de cierre"
                      onClick={() => void handleVerResumen(c.id)}
                    >
                      <IconEye size={16} />
                    </ActionIcon>
                  )}
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
        {!cargando && historial.length === 0 && (
          <div style={{ padding: 'var(--mantine-spacing-md)' }}>
            <EstadoVacio titulo="Sin cajas todavía" />
          </div>
        )}
      </Paper>

      <Modal
        opened={!!resumen}
        onClose={() => setResumen(null)}
        title="Resumen de cierre"
        size="md"
        closeOnClickOutside={!procesando}
        withCloseButton={!procesando}
      >
        {resumen && (
          <>
            <Text size="sm" c="dimmed">
              {resumen.sucursal_nombre} · {resumen.fecha_fin ? new Date(resumen.fecha_fin).toLocaleString('es-AR') : '—'}
            </Text>

            <Group align="flex-end" mt={4} mb="md">
              <div>
                <Text size="sm" c="dimmed">
                  Monto calculado
                </Text>
                <Text fz={28} fw={800}>
                  {formatearMonto(resumen.caja_final_calculado)}
                </Text>
              </div>
              {resumen.fecha_fin ? (
                <div>
                  <Text size="sm" c="dimmed">
                    Arqueo de caja
                  </Text>
                  <Text fz={28} fw={800}>
                    {resumen.arqueo ? formatearMonto(resumen.arqueo) : '—'}
                  </Text>
                </div>
              ) : (
                <NumberInput
                  label="Arqueo de caja"
                  description="Total real contado en caja"
                  placeholder="0,00"
                  min={0}
                  decimalScale={2}
                  value={arqueo}
                  onChange={(v) => setArqueo(typeof v === 'number' ? v : '')}
                  disabled={procesando}
                  error={arqueo !== '' && Number(arqueo) < Number(resumen.caja_final_calculado) ? 'Falta efectivo' : null}
                  style={{ flex: 1 }}
                />
              )}
            </Group>

            <Divider my="sm" label="Ingresos" labelPosition="center" />
            {resumen.ingresos.map((i) => (
              <Group justify="space-between" key={i.concepto}>
                <Text size="sm" c="dimmed">
                  {i.concepto}
                </Text>
                <Text size="sm" c="green.8">
                  {formatearMonto(i.importe)}
                </Text>
              </Group>
            ))}
            <Group justify="space-between" fw={600} mt={4}>
              <Text size="sm">{resumen.total_ingresos.concepto}</Text>
              <Text size="sm" c="green.8">
                {formatearMonto(resumen.total_ingresos.importe)}
              </Text>
            </Group>

            <Divider my="sm" label="Egresos" labelPosition="center" />
            {resumen.egresos.map((e) => (
              <Group justify="space-between" key={e.concepto}>
                <Text size="sm" c="dimmed">
                  {e.concepto}
                </Text>
                <Text size="sm" c="red.8">
                  {formatearMonto(e.importe)}
                </Text>
              </Group>
            ))}
            <Group justify="space-between" fw={600} mt={4}>
              <Text size="sm">{resumen.total_egresos.concepto}</Text>
              <Text size="sm" c="red.8">
                {formatearMonto(resumen.total_egresos.importe)}
              </Text>
            </Group>

            <Divider my="sm" />
            <Group justify="space-between" fw={600}>
              <Text size="sm">{resumen.total_cuenta_corriente.concepto}</Text>
              <Text size="sm">{formatearMonto(resumen.total_cuenta_corriente.importe)}</Text>
            </Group>

            <Group justify="flex-end" mt="lg">
              {resumen.fecha_fin ? (
                <>
                  <Button variant="default" onClick={() => setResumen(null)}>
                    Cerrar
                  </Button>
                  <Button
                    color="red"
                    leftSection={<IconPrinter size={16} />}
                    onClick={() => void abrirResumenCajaParaImprimir(resumen.id)}
                  >
                    Imprimir
                  </Button>
                </>
              ) : (
                <>
                  <Button variant="default" onClick={() => setResumen(null)} disabled={procesando}>
                    Cancelar
                  </Button>
                  <Button
                    color="red"
                    loading={procesando}
                    disabled={arqueo === '' || Number(arqueo) < Number(resumen.caja_final_calculado)}
                    onClick={() => void handleConfirmarCierre()}
                  >
                    Cerrar
                  </Button>
                </>
              )}
            </Group>
          </>
        )}
      </Modal>
    </Container>
  )
}
