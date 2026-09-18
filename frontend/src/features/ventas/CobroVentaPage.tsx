import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Container,
  Divider,
  Group,
  Kbd,
  Modal,
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
import { IconBuildingBank, IconCash, IconCreditCard, IconPrinter, IconTransfer } from '@tabler/icons-react'
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

  // Campo de carga de cada método de pago: siempre visible y habilitado — el botón "Agregar"
  // (o F1/F2/F3/F6) acepta lo cargado acá y lo suma a la lista de pagos de abajo.
  const [efectivoImporte, setEfectivoImporte] = useState('')
  const [tarjetaStaging, setTarjetaStaging] = useState<Omit<PagoTarjeta, 'clave'>>({
    planTarjetaId: null,
    numeroTarjeta: '',
    importe: '',
    numeroCupon: '',
    lote: '',
  })
  const [ccImporte, setCcImporte] = useState('')
  const [transferenciaStaging, setTransferenciaStaging] = useState<Omit<PagoTransferencia, 'clave'>>({
    importe: '',
    documento: '',
    nombre: '',
    apellido: '',
    banco: '',
  })
  const [tarjetaModalAbierto, setTarjetaModalAbierto] = useState(false)
  const efectivoStagingRef = useRef<HTMLInputElement>(null)
  const ccStagingRef = useRef<HTMLInputElement>(null)
  const transferenciaStagingRef = useRef<HTMLInputElement>(null)

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

  // Apenas carga una venta cobrable, el foco arranca en el campo Importe de Efectivo — el
  // método más común, para no tener que ir a buscarlo con el mouse.
  useEffect(() => {
    if (!cargando && venta && !venta.anulado && !venta.cobrada) {
      efectivoStagingRef.current?.focus()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cargando, venta?.numero_ticket])

  // Acepta lo cargado en el campo de la sección — se usa tanto desde el botón "Agregar" como
  // desde Enter en el campo y los atajos F1/F2/F3/F6 (ver el listener más abajo). Si el importe
  // no es válido todavía, en vez de agregar nada sólo lleva el foco al campo para completarlo.
  const aceptarEfectivo = () => {
    if (!(Number(efectivoImporte) > 0)) {
      efectivoStagingRef.current?.focus()
      return
    }
    setEfectivo((a) => [...a, { clave: clave(), importe: efectivoImporte }])
    setEfectivoImporte('')
    efectivoStagingRef.current?.focus()
  }
  const aceptarTarjeta = () => {
    if (!(Number(tarjetaStaging.importe) > 0)) return
    setTarjeta((a) => [...a, { clave: clave(), ...tarjetaStaging }])
    cerrarModalTarjeta()
  }
  const cerrarModalTarjeta = () => {
    setTarjetaModalAbierto(false)
    setTarjetaStaging({ planTarjetaId: null, numeroTarjeta: '', importe: '', numeroCupon: '', lote: '' })
  }
  const aceptarCc = () => {
    if (!(Number(ccImporte) > 0)) {
      ccStagingRef.current?.focus()
      return
    }
    setCc((a) => [...a, { clave: clave(), importe: ccImporte }])
    setCcImporte('')
    ccStagingRef.current?.focus()
  }
  const aceptarTransferencia = () => {
    if (!(Number(transferenciaStaging.importe) > 0)) {
      transferenciaStagingRef.current?.focus()
      return
    }
    setTransferencia((a) => [...a, { clave: clave(), ...transferenciaStaging }])
    setTransferenciaStaging({ importe: '', documento: '', nombre: '', apellido: '', banco: '' })
    transferenciaStagingRef.current?.focus()
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

  // Atajos de teclado del cobro: F1/F3/F6 aceptan el importe cargado en la sección
  // correspondiente (igual que tocar "Agregar"), F2 abre el modal de Tarjeta, y F4 confirma el
  // cobro — así el cajero no necesita el mouse. Van a nivel de window (no de un input puntual)
  // porque son teclas de función, no imprimibles: no interfieren con lo que se esté tipeando en
  // ese momento.
  useEffect(() => {
    if (cargando || !venta || venta.anulado || venta.cobrada) return
    const onKeyDown = (e: globalThis.KeyboardEvent) => {
      switch (e.key) {
        case 'F1':
          e.preventDefault()
          aceptarEfectivo()
          break
        case 'F2':
          e.preventDefault()
          setTarjetaModalAbierto(true)
          break
        case 'F3':
          e.preventDefault()
          aceptarCc()
          break
        case 'F6':
          e.preventDefault()
          aceptarTransferencia()
          break
        case 'F4':
          e.preventDefault()
          if (coincide && hayAlgunPago && !cobrando) void confirmarCobro()
          break
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cargando, venta, coincide, hayAlgunPago, cobrando])

  if (cargando) return <Container py="md">Cargando…</Container>
  if (!venta) return <Container py="md">No se encontró la venta.</Container>

  const tablaArticulos = (
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
  )

  return (
    <Container size="xl" py="md">
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
          {/* Detalle de artículos a la izquierda, al lado de los tipos de cobro — así el
             cajero ve qué se está cobrando mientras carga los montos. */}
          <Paper withBorder p={0} style={{ width: 420, flexShrink: 0, position: 'sticky', top: 16, maxHeight: 'calc(100vh - 32px)', overflow: 'auto' }}>
            <Divider label="Detalle de la venta" labelPosition="center" pt="sm" />
            {tablaArticulos}
          </Paper>

          <Stack gap="md" style={{ flex: 1, minWidth: 320 }}>
            <SeccionPagos titulo="Efectivo" icono={<IconCash size={18} />} atajo="F1">
              <Group>
                <NumberInput
                  ref={efectivoStagingRef}
                  label="Importe"
                  value={efectivoImporte}
                  onChange={(v) => setEfectivoImporte(String(v))}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      aceptarEfectivo()
                    }
                  }}
                  decimalScale={2}
                  min={0}
                />
                <Button mt={22} onClick={aceptarEfectivo}>
                  Agregar
                </Button>
              </Group>
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

            <SeccionPagos titulo="Tarjeta" icono={<IconCreditCard size={18} />} atajo="F2">
              <Button variant="light" onClick={() => setTarjetaModalAbierto(true)}>
                + Agregar pago con tarjeta
              </Button>
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

            <SeccionPagos titulo="Cuenta corriente" icono={<IconBuildingBank size={18} />} atajo="F3">
              <Group>
                <NumberInput
                  ref={ccStagingRef}
                  label="Importe"
                  value={ccImporte}
                  onChange={(v) => setCcImporte(String(v))}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      aceptarCc()
                    }
                  }}
                  decimalScale={2}
                  min={0}
                />
                <Button mt={22} onClick={aceptarCc}>
                  Agregar
                </Button>
              </Group>
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

            <SeccionPagos titulo="Transferencia" icono={<IconTransfer size={18} />} atajo="F6">
              <Paper withBorder p="sm">
                <Group grow>
                  <NumberInput
                    ref={transferenciaStagingRef}
                    label="Importe"
                    value={transferenciaStaging.importe}
                    onChange={(v) => setTransferenciaStaging((s) => ({ ...s, importe: String(v) }))}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        aceptarTransferencia()
                      }
                    }}
                    decimalScale={2}
                    min={0}
                  />
                  <TextInput
                    label="Documento del titular"
                    value={transferenciaStaging.documento}
                    onChange={(e) => setTransferenciaStaging((s) => ({ ...s, documento: e.currentTarget.value }))}
                  />
                </Group>
                <Button mt="xs" onClick={aceptarTransferencia}>
                  Agregar
                </Button>
              </Paper>
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

            <Group gap="xs" wrap="nowrap" align="stretch">
              <Button
                flex={1}
                size="lg"
                color="red"
                disabled={!coincide || !hayAlgunPago}
                loading={cobrando}
                onClick={() => void confirmarCobro()}
              >
                Confirmar cobro
              </Button>
              <Kbd style={{ alignSelf: 'center' }}>F4</Kbd>
            </Group>
          </Paper>
        </Group>
      )}

      {(venta.anulado || venta.cobrada) && (
        <Paper withBorder p={0}>
          <Divider label="Detalle de la venta" labelPosition="center" pt="sm" />
          {tablaArticulos}
        </Paper>
      )}

      <Modal opened={tarjetaModalAbierto} onClose={cerrarModalTarjeta} title="Agregar pago con tarjeta">
        <Stack gap="sm">
          <Select
            label="Plan"
            data={planes.map((pl) => ({ value: String(pl.id), label: `${pl.tarjeta_nombre} — ${pl.nombre_plan} (${pl.interes}%)` }))}
            value={tarjetaStaging.planTarjetaId}
            onChange={(v) => setTarjetaStaging((s) => ({ ...s, planTarjetaId: v }))}
            data-autofocus
          />
          <NumberInput
            label="Importe"
            value={tarjetaStaging.importe}
            onChange={(v) => setTarjetaStaging((s) => ({ ...s, importe: String(v) }))}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                aceptarTarjeta()
              }
            }}
            decimalScale={2}
            min={0}
          />
          <Group grow>
            <TextInput
              label="Nº cupón"
              value={tarjetaStaging.numeroCupon}
              onChange={(e) => setTarjetaStaging((s) => ({ ...s, numeroCupon: e.currentTarget.value }))}
            />
            <TextInput
              label="Lote"
              value={tarjetaStaging.lote}
              onChange={(e) => setTarjetaStaging((s) => ({ ...s, lote: e.currentTarget.value }))}
            />
          </Group>
          <Group justify="flex-end" mt="sm">
            <Button variant="subtle" onClick={cerrarModalTarjeta}>
              Cancelar
            </Button>
            <Button onClick={aceptarTarjeta} disabled={!(Number(tarjetaStaging.importe) > 0)}>
              Agregar
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  )
}

function SeccionPagos({
  titulo,
  icono,
  atajo,
  children,
}: {
  titulo: string
  /** Ícono del tipo de pago (efectivo, tarjeta, etc.), mostrado junto al título de la sección. */
  icono: ReactNode
  /** Tecla de función que acepta el importe cargado en esta sección (ver el listener en
   * CobroVentaPage) — se muestra junto al título a modo de leyenda guía. */
  atajo: string
  children: ReactNode
}) {
  return (
    <div>
      <Group gap={6} mb="xs">
        {icono}
        <Text fw={500}>{titulo}</Text>
        <Kbd>{atajo}</Kbd>
      </Group>
      <Stack gap="xs">{children}</Stack>
    </div>
  )
}
