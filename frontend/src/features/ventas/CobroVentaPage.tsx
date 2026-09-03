import { useEffect, useMemo, useState, type ReactNode } from 'react'
import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Container,
  Divider,
  Group,
  NumberInput,
  Paper,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconPrinter } from '@tabler/icons-react'
import { useNavigate, useParams } from 'react-router-dom'
import { cobrarVenta, listarPlanesTarjeta } from '../../api/caja'
import { ApiError } from '../../api/client'
import { obtenerVenta } from '../../api/venta'
import type { PlanTarjetaDeCredito } from '../../types/caja'
import type { Venta } from '../../types/venta'
import { formatearMonto } from './dinero'
import { abrirTicketParaImprimir } from './imprimirTicket'

interface PagoEfectivo {
  clave: string
  importe: string
}
interface PagoTarjeta {
  clave: string
  planTarjetaId: string | null
  numeroTarjeta: string
  importe: string
  numeroCupon: string
  lote: string
}
interface PagoCC {
  clave: string
  importe: string
}
interface PagoTransferencia {
  clave: string
  importe: string
  documento: string
  nombre: string
  apellido: string
  banco: string
}

function clave() {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

export default function CobroVentaPage() {
  const { numeroTicket } = useParams<{ numeroTicket: string }>()
  const navigate = useNavigate()

  const [venta, setVenta] = useState<Venta | null>(null)
  const [planes, setPlanes] = useState<PlanTarjetaDeCredito[]>([])
  const [cargando, setCargando] = useState(true)
  const [cobrando, setCobrando] = useState(false)

  const [efectivo, setEfectivo] = useState<PagoEfectivo[]>([])
  const [tarjeta, setTarjeta] = useState<PagoTarjeta[]>([])
  const [cc, setCc] = useState<PagoCC[]>([])
  const [transferencia, setTransferencia] = useState<PagoTransferencia[]>([])

  useEffect(() => {
    if (!numeroTicket) return
    obtenerVenta(Number(numeroTicket))
      .then(setVenta)
      .catch((err: ApiError) => notifications.show({ title: 'Error', message: err.message, color: 'red' }))
      .finally(() => setCargando(false))
    listarPlanesTarjeta()
      .then((r) => setPlanes(r.results))
      .catch(() => notifications.show({ message: 'No se pudieron cargar los planes de tarjeta.', color: 'red' }))
  }, [numeroTicket])

  const totalIngresado = useMemo(() => {
    const suma = (lista: { importe: string }[]) => lista.reduce((acc, p) => acc + (Number(p.importe) || 0), 0)
    return suma(efectivo) + suma(tarjeta) + suma(cc) + suma(transferencia)
  }, [efectivo, tarjeta, cc, transferencia])

  const totalVenta = venta ? Number(venta.monto) : 0
  const coincide = venta ? Math.abs(totalIngresado - totalVenta) < 0.005 : false
  const hayAlgunPago = efectivo.length + tarjeta.length + cc.length + transferencia.length > 0

  const confirmarCobro = async () => {
    if (!venta || !coincide) return
    setCobrando(true)
    try {
      const actualizada = await cobrarVenta({
        venta: venta.numero_ticket,
        pagos_efectivo: efectivo.map((p) => ({ importe: p.importe })),
        pagos_tarjeta: tarjeta.map((p) => ({
          plan_tarjeta: Number(p.planTarjetaId),
          numero_tarjeta: p.numeroTarjeta || undefined,
          importe: p.importe,
          numero_cupon: p.numeroCupon || undefined,
          lote: p.lote || undefined,
        })),
        pagos_cuenta_corriente: cc.map((p) => ({ importe: p.importe })),
        pagos_transferencia: transferencia.map((p) => ({
          importe: p.importe,
          documento_identidad: p.documento,
          nombre: p.nombre || undefined,
          apellido: p.apellido || undefined,
          banco: p.banco || undefined,
        })),
      })
      notifications.show({ message: `Venta #${actualizada.numero_ticket} cobrada.`, color: 'green' })
      navigate('/ventas')
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo cobrar', message: detalle, color: 'red' })
    } finally {
      setCobrando(false)
    }
  }

  if (cargando) return <Container py="md">Cargando…</Container>
  if (!venta) return <Container py="md">No se encontró la venta.</Container>

  return (
    <Container size="md" py="md">
      <Group justify="space-between" align="flex-start">
        <div>
          <Title order={2}>Cobrar venta #{venta.numero_ticket}</Title>
          <Text c="dimmed" size="sm" mb="lg">
            {venta.cliente_nombre} — Total {formatearMonto(venta.monto)}
          </Text>
        </div>
        <ActionIcon
          variant="subtle"
          size="lg"
          aria-label="Imprimir ticket"
          onClick={() => void abrirTicketParaImprimir(venta.numero_ticket)}
        >
          <IconPrinter size={20} />
        </ActionIcon>
      </Group>

      {venta.anulado && <Alert color="red">Esta venta está anulada.</Alert>}
      {venta.cobrada && !venta.anulado && <Alert color="green">Esta venta ya fue cobrada.</Alert>}

      {!venta.anulado && !venta.cobrada && (
        <>
          <Stack gap="md">
            <SeccionPagos
              titulo="Efectivo"
              onAgregar={() => setEfectivo((a) => [...a, { clave: clave(), importe: '' }])}
            >
              {efectivo.map((p) => (
                <Group key={p.clave}>
                  <NumberInput
                    label="Importe"
                    value={p.importe}
                    onChange={(v) => setEfectivo((a) => a.map((x) => (x.clave === p.clave ? { ...x, importe: String(v) } : x)))}
                    decimalScale={2}
                    min={0}
                  />
                  <Button variant="subtle" color="red" mt={22} onClick={() => setEfectivo((a) => a.filter((x) => x.clave !== p.clave))}>
                    Quitar
                  </Button>
                </Group>
              ))}
            </SeccionPagos>

            <SeccionPagos
              titulo="Tarjeta"
              onAgregar={() =>
                setTarjeta((a) => [...a, { clave: clave(), planTarjetaId: null, numeroTarjeta: '', importe: '', numeroCupon: '', lote: '' }])
              }
            >
              {tarjeta.map((p) => (
                <Paper key={p.clave} withBorder p="sm">
                  <Group grow>
                    <Select
                      label="Plan"
                      data={planes.map((pl) => ({ value: String(pl.id), label: `${pl.tarjeta_nombre} — ${pl.nombre_plan} (${pl.interes}%)` }))}
                      value={p.planTarjetaId}
                      onChange={(v) => setTarjeta((a) => a.map((x) => (x.clave === p.clave ? { ...x, planTarjetaId: v } : x)))}
                    />
                    <NumberInput
                      label="Importe"
                      value={p.importe}
                      onChange={(v) => setTarjeta((a) => a.map((x) => (x.clave === p.clave ? { ...x, importe: String(v) } : x)))}
                      decimalScale={2}
                      min={0}
                    />
                  </Group>
                  <Group grow mt="xs">
                    <TextInput
                      label="Nº cupón"
                      value={p.numeroCupon}
                      onChange={(e) => setTarjeta((a) => a.map((x) => (x.clave === p.clave ? { ...x, numeroCupon: e.currentTarget.value } : x)))}
                    />
                    <TextInput
                      label="Lote"
                      value={p.lote}
                      onChange={(e) => setTarjeta((a) => a.map((x) => (x.clave === p.clave ? { ...x, lote: e.currentTarget.value } : x)))}
                    />
                  </Group>
                  <Button variant="subtle" color="red" size="xs" mt="xs" onClick={() => setTarjeta((a) => a.filter((x) => x.clave !== p.clave))}>
                    Quitar
                  </Button>
                </Paper>
              ))}
            </SeccionPagos>

            <SeccionPagos titulo="Cuenta corriente" onAgregar={() => setCc((a) => [...a, { clave: clave(), importe: '' }])}>
              {cc.map((p) => (
                <Group key={p.clave}>
                  <NumberInput
                    label="Importe"
                    value={p.importe}
                    onChange={(v) => setCc((a) => a.map((x) => (x.clave === p.clave ? { ...x, importe: String(v) } : x)))}
                    decimalScale={2}
                    min={0}
                  />
                  <Button variant="subtle" color="red" mt={22} onClick={() => setCc((a) => a.filter((x) => x.clave !== p.clave))}>
                    Quitar
                  </Button>
                </Group>
              ))}
            </SeccionPagos>

            <SeccionPagos
              titulo="Transferencia"
              onAgregar={() =>
                setTransferencia((a) => [...a, { clave: clave(), importe: '', documento: '', nombre: '', apellido: '', banco: '' }])
              }
            >
              {transferencia.map((p) => (
                <Paper key={p.clave} withBorder p="sm">
                  <Group grow>
                    <NumberInput
                      label="Importe"
                      value={p.importe}
                      onChange={(v) => setTransferencia((a) => a.map((x) => (x.clave === p.clave ? { ...x, importe: String(v) } : x)))}
                      decimalScale={2}
                      min={0}
                    />
                    <TextInput
                      label="Documento del titular"
                      value={p.documento}
                      onChange={(e) => setTransferencia((a) => a.map((x) => (x.clave === p.clave ? { ...x, documento: e.currentTarget.value } : x)))}
                    />
                  </Group>
                  <Button variant="subtle" color="red" size="xs" mt="xs" onClick={() => setTransferencia((a) => a.filter((x) => x.clave !== p.clave))}>
                    Quitar
                  </Button>
                </Paper>
              ))}
            </SeccionPagos>
          </Stack>

          <Divider my="md" />

          <Group justify="space-between">
            <Text>
              Ingresado: <strong>{formatearMonto(totalIngresado)}</strong> / A cobrar:{' '}
              <strong>{formatearMonto(totalVenta)}</strong>
            </Text>
            <Badge color={coincide ? 'green' : 'red'}>{coincide ? 'Coincide' : 'No coincide'}</Badge>
          </Group>

          <Group justify="flex-end" mt="md">
            <Button
              size="lg"
              color="red"
              disabled={!coincide || !hayAlgunPago}
              loading={cobrando}
              onClick={() => void confirmarCobro()}
            >
              Confirmar cobro
            </Button>
          </Group>
        </>
      )}

      <Divider my="lg" label="Detalle de la venta" labelPosition="center" />
      <Table striped verticalSpacing="xs">
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Artículo</Table.Th>
            <Table.Th>Cantidad</Table.Th>
            <Table.Th>Subtotal</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {venta.articulos.map((a) => (
            <Table.Tr key={a.id}>
              <Table.Td>{a.nombre_articulo}</Table.Td>
              <Table.Td>{a.cantidad_peso}</Table.Td>
              <Table.Td>{formatearMonto(a.total_articulo)}</Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Container>
  )
}

function SeccionPagos({
  titulo,
  onAgregar,
  children,
}: {
  titulo: string
  onAgregar: () => void
  children: ReactNode
}) {
  return (
    <div>
      <Group justify="space-between" mb="xs">
        <Text fw={500}>{titulo}</Text>
        <Button size="xs" variant="light" onClick={onAgregar}>
          + Agregar
        </Button>
      </Group>
      <Stack gap="xs">{children}</Stack>
    </div>
  )
}
