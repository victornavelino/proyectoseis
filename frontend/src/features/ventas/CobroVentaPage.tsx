import { useEffect, useMemo, useRef, useState, type ReactNode, type RefObject } from 'react'
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
  const [claveAEnfocar, setClaveAEnfocar] = useState<string | null>(null)
  const efectivoAgregarRef = useRef<HTMLButtonElement>(null)
  // Compartido entre las cuatro secciones de pago — las claves salen todas de clave(), así que
  // son únicas sin importar el método.
  const importeRefs = useRef(new Map<string, HTMLInputElement>())

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

  // Apenas carga una venta cobrable, el foco arranca en "+ Agregar" de Efectivo — el método más
  // común, para no tener que ir a buscarlo con el mouse.
  useEffect(() => {
    if (!cargando && venta && !venta.anulado && !venta.cobrada) {
      efectivoAgregarRef.current?.focus()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cargando, venta?.numero_ticket])

  // Al agregar un pago, el foco salta a su campo Importe (la fila recién se crea en este
  // render, así que hace falta esperar a que el ref del input exista).
  useEffect(() => {
    if (!claveAEnfocar) return
    const input = importeRefs.current.get(claveAEnfocar)
    if (input) {
      input.focus()
      input.select()
    }
    setClaveAEnfocar(null)
  }, [claveAEnfocar])

  const registrarImporteRef = (itemClave: string) => (el: HTMLInputElement | null) => {
    if (el) importeRefs.current.set(itemClave, el)
    else importeRefs.current.delete(itemClave)
  }

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
    <Container size="lg" py="md">
      <Group justify="space-between" align="flex-start" mb="lg">
        <div>
          <Title order={2}>Cobrar venta #{venta.numero_ticket}</Title>
          <Text c="dimmed" size="sm">
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

      {venta.anulado && (
        <Alert color="red" mb="md">
          Esta venta está anulada.
        </Alert>
      )}
      {venta.cobrada && !venta.anulado && (
        <Alert color="green" mb="md">
          Esta venta ya fue cobrada.
        </Alert>
      )}

      {!venta.anulado && !venta.cobrada && (
        <Group align="flex-start" gap="lg" mb="lg">
          <Stack gap="md" style={{ flex: 1, minWidth: 320 }}>
            <SeccionPagos
              titulo="Efectivo"
              agregarRef={efectivoAgregarRef}
              onAgregar={() => {
                const nueva = clave()
                setEfectivo((a) => [...a, { clave: nueva, importe: '' }])
                setClaveAEnfocar(nueva)
              }}
            >
              {efectivo.map((p) => (
                <Group key={p.clave}>
                  <NumberInput
                    ref={registrarImporteRef(p.clave)}
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
              onAgregar={() => {
                const nueva = clave()
                setTarjeta((a) => [...a, { clave: nueva, planTarjetaId: null, numeroTarjeta: '', importe: '', numeroCupon: '', lote: '' }])
                setClaveAEnfocar(nueva)
              }}
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
                      ref={registrarImporteRef(p.clave)}
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

            <SeccionPagos
              titulo="Cuenta corriente"
              onAgregar={() => {
                const nueva = clave()
                setCc((a) => [...a, { clave: nueva, importe: '' }])
                setClaveAEnfocar(nueva)
              }}
            >
              {cc.map((p) => (
                <Group key={p.clave}>
                  <NumberInput
                    ref={registrarImporteRef(p.clave)}
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
              onAgregar={() => {
                const nueva = clave()
                setTransferencia((a) => [...a, { clave: nueva, importe: '', documento: '', nombre: '', apellido: '', banco: '' }])
                setClaveAEnfocar(nueva)
              }}
            >
              {transferencia.map((p) => (
                <Paper key={p.clave} withBorder p="sm">
                  <Group grow>
                    <NumberInput
                      ref={registrarImporteRef(p.clave)}
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

          {/* Resumen fijo del cobro: siempre a la vista mientras se cargan varios pagos
             parciales, sin depender de scrollear hasta el final de las secciones. */}
          <Paper withBorder p="lg" style={{ width: 300, flexShrink: 0, position: 'sticky', top: 16 }}>
            <Text fw={600} size="sm" c="dimmed" mb="sm">
              Resumen del cobro
            </Text>

            <Stack gap={6} mb="md">
              <Group justify="space-between">
                <Text size="sm" c="dimmed">
                  A cobrar
                </Text>
                <Text size="sm" fw={500}>
                  {formatearMonto(totalVenta)}
                </Text>
              </Group>
              <Group justify="space-between">
                <Text size="sm" c="dimmed">
                  Ingresado
                </Text>
                <Text size="sm" fw={500}>
                  {formatearMonto(totalIngresado)}
                </Text>
              </Group>
            </Stack>

            <Badge fullWidth color={coincide ? 'green' : 'red'} size="lg" mb="lg">
              {coincide ? 'Coincide' : 'No coincide'}
            </Badge>

            <Button
              fullWidth
              size="lg"
              color="red"
              disabled={!coincide || !hayAlgunPago}
              loading={cobrando}
              onClick={() => void confirmarCobro()}
            >
              Confirmar cobro
            </Button>
          </Paper>
        </Group>
      )}

      <Paper withBorder p={0}>
        <Divider label="Detalle de la venta" labelPosition="center" pt="sm" />
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
      </Paper>
    </Container>
  )
}

function SeccionPagos({
  titulo,
  onAgregar,
  agregarRef,
  children,
}: {
  titulo: string
  onAgregar: () => void
  /** Sólo la usa Efectivo, para que el foco arranque ahí apenas carga la pantalla (ver
   * CobroVentaPage). */
  agregarRef?: RefObject<HTMLButtonElement | null>
  children: ReactNode
}) {
  return (
    <div>
      <Group justify="space-between" mb="xs">
        <Text fw={500}>{titulo}</Text>
        <Button ref={agregarRef} size="xs" variant="light" onClick={onAgregar}>
          + Agregar
        </Button>
      </Group>
      <Stack gap="xs">{children}</Stack>
    </div>
  )
}
