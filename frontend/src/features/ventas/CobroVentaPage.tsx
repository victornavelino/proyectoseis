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
import {
  IconBuildingBank,
  IconCash,
  IconCreditCard,
  IconPrinter,
  IconTransfer,
  IconTrash,
  IconX,
} from '@tabler/icons-react'
import { useNavigate, useParams } from 'react-router-dom'
import { cobrarVenta, listarPlanesTarjeta } from '../../api/caja'
import { mensajeDeError } from '../../api/client'
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

type Metodo = 'efectivo' | 'tarjeta' | 'cc' | 'transferencia'

function clave() {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

const TARJETA_STAGING_VACIA: Omit<PagoTarjeta, 'clave'> = {
  planTarjetaId: null,
  numeroTarjeta: '',
  importe: '',
  numeroCupon: '',
  lote: '',
}
const TRANSFERENCIA_STAGING_VACIA: Omit<PagoTransferencia, 'clave'> = {
  importe: '',
  documento: '',
  nombre: '',
  apellido: '',
  banco: '',
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

  // Sólo un método de pago "abierto" a la vez (o el modal de Tarjeta) — en vez de mostrar las 4
  // formas de cobro siempre expandidas, el cajero elige una con los botones grandes de arriba
  // (o F1/F2/F3/F6) y sólo ve el formulario de esa.
  const [metodoAbierto, setMetodoAbierto] = useState<Metodo | null>(null)
  const [efectivoImporte, setEfectivoImporte] = useState('')
  // "Paga con" es sólo una calculadora de vuelto para el cajero: nunca se manda al backend.
  const [pagaCon, setPagaCon] = useState('')
  const [tarjetaStaging, setTarjetaStaging] = useState<Omit<PagoTarjeta, 'clave'>>(TARJETA_STAGING_VACIA)
  const [ccImporte, setCcImporte] = useState('')
  const [transferenciaStaging, setTransferenciaStaging] = useState<Omit<PagoTransferencia, 'clave'>>(
    TRANSFERENCIA_STAGING_VACIA,
  )
  const [tarjetaModalAbierto, setTarjetaModalAbierto] = useState(false)
  const efectivoStagingRef = useRef<HTMLInputElement>(null)
  const ccStagingRef = useRef<HTMLInputElement>(null)
  const transferenciaStagingRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!numeroTicket) return
    obtenerVenta(Number(numeroTicket))
      .then(setVenta)
      .catch((err: unknown) => notifications.show({ title: 'Error', message: mensajeDeError(err), color: 'red' }))
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
  const saldoPendiente = totalVenta - totalIngresado
  const cobroCompleto = saldoPendiente <= 0.005
  const coincide = venta ? Math.abs(saldoPendiente) < 0.005 : false
  const hayAlgunPago = efectivo.length + tarjeta.length + cc.length + transferencia.length > 0

  // Abre el formulario del método elegido (o el modal, para Tarjeta) con el importe restante ya
  // cargado — el caso más común es pagar todo con un solo método, así el cajero sólo confirma.
  const abrirMetodo = (metodo: Metodo) => {
    if (cobroCompleto) {
      notifications.show({
        message: 'Ya está cargado el total de la venta. Quitá un pago de la lista para modificarlo.',
        color: 'yellow',
      })
      return
    }
    const sugerido = saldoPendiente.toFixed(2)
    if (metodo === 'tarjeta') {
      setTarjetaStaging((s) => ({ ...s, importe: s.importe || sugerido }))
      setTarjetaModalAbierto(true)
      return
    }
    setMetodoAbierto(metodo)
    if (metodo === 'efectivo') setEfectivoImporte((v) => v || sugerido)
    if (metodo === 'cc') setCcImporte((v) => v || sugerido)
    if (metodo === 'transferencia') setTransferenciaStaging((s) => ({ ...s, importe: s.importe || sugerido }))
  }

  const cerrarPanel = () => {
    setMetodoAbierto(null)
    setEfectivoImporte('')
    setPagaCon('')
    setCcImporte('')
    setTransferenciaStaging(TRANSFERENCIA_STAGING_VACIA)
  }

  // Apenas carga una venta cobrable, se abre directo el panel de Efectivo (el método más común)
  // para no tener que ir a buscarlo con el mouse.
  useEffect(() => {
    if (!cargando && venta && !venta.anulado && !venta.cobrada) {
      setMetodoAbierto('efectivo')
      setEfectivoImporte(String(venta.monto))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cargando, venta?.numero_ticket])

  const aceptarEfectivo = () => {
    if (!(Number(efectivoImporte) > 0)) {
      efectivoStagingRef.current?.focus()
      return
    }
    setEfectivo((a) => [...a, { clave: clave(), importe: efectivoImporte }])
    cerrarPanel()
  }
  const aceptarTarjeta = () => {
    if (!(Number(tarjetaStaging.importe) > 0)) return
    setTarjeta((a) => [...a, { clave: clave(), ...tarjetaStaging }])
    cerrarModalTarjeta()
  }
  const cerrarModalTarjeta = () => {
    setTarjetaModalAbierto(false)
    setTarjetaStaging(TARJETA_STAGING_VACIA)
  }
  const aceptarCc = () => {
    if (!(Number(ccImporte) > 0)) {
      ccStagingRef.current?.focus()
      return
    }
    setCc((a) => [...a, { clave: clave(), importe: ccImporte }])
    cerrarPanel()
  }
  const aceptarTransferencia = () => {
    if (!(Number(transferenciaStaging.importe) > 0)) {
      transferenciaStagingRef.current?.focus()
      return
    }
    setTransferencia((a) => [...a, { clave: clave(), ...transferenciaStaging }])
    cerrarPanel()
  }

  // Vuelto = lo que trae el cliente menos lo que se le está cobrando en esta línea de efectivo.
  const vuelto = pagaCon !== '' ? Number(pagaCon) - Number(efectivoImporte || 0) : null

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
      const detalle = mensajeDeError(err)
      notifications.show({ title: 'No se pudo cobrar', message: detalle, color: 'red' })
    } finally {
      setCobrando(false)
    }
  }

  // Atajos de teclado del cobro: F1/F2/F3/F6 abren el formulario del método correspondiente
  // (igual que tocar su botón) y F4 confirma el cobro — así el cajero no necesita el mouse. Van a
  // nivel de window (no de un input puntual) porque son teclas de función, no imprimibles: no
  // interfieren con lo que se esté tipeando en ese momento.
  useEffect(() => {
    if (cargando || !venta || venta.anulado || venta.cobrada) return
    const onKeyDown = (e: globalThis.KeyboardEvent) => {
      switch (e.key) {
        case 'F1':
          e.preventDefault()
          abrirMetodo('efectivo')
          break
        case 'F2':
          e.preventDefault()
          abrirMetodo('tarjeta')
          break
        case 'F3':
          e.preventDefault()
          abrirMetodo('cc')
          break
        case 'F6':
          e.preventDefault()
          abrirMetodo('transferencia')
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
  }, [cargando, venta, coincide, hayAlgunPago, cobrando, cobroCompleto, saldoPendiente])

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

  // Una sola lista de pagos ya cargados (en vez de una lista aparte por método) para que el
  // cajero vea de un vistazo todo lo que se cobró hasta ahora, y pueda quitar cualquier línea.
  const filasPago = [
    ...efectivo.map((p) => ({
      clave: p.clave,
      tipo: 'Efectivo',
      detalle: '—',
      importe: Number(p.importe),
      quitar: () => setEfectivo((a) => a.filter((x) => x.clave !== p.clave)),
    })),
    ...tarjeta.map((p) => {
      const plan = planes.find((pl) => String(pl.id) === p.planTarjetaId)
      const detalle =
        [plan ? `${plan.tarjeta_nombre} — ${plan.nombre_plan}` : null, p.numeroCupon && `cupón ${p.numeroCupon}`, p.lote && `lote ${p.lote}`]
          .filter(Boolean)
          .join(' · ') || '—'
      return {
        clave: p.clave,
        tipo: 'Tarjeta',
        detalle,
        importe: Number(p.importe),
        quitar: () => setTarjeta((a) => a.filter((x) => x.clave !== p.clave)),
      }
    }),
    ...cc.map((p) => ({
      clave: p.clave,
      tipo: 'Cuenta corriente',
      detalle: '—',
      importe: Number(p.importe),
      quitar: () => setCc((a) => a.filter((x) => x.clave !== p.clave)),
    })),
    ...transferencia.map((p) => ({
      clave: p.clave,
      tipo: 'Transferencia',
      detalle: [`${p.nombre} ${p.apellido}`.trim(), p.documento && `doc ${p.documento}`, p.banco].filter(Boolean).join(' · ') || '—',
      importe: Number(p.importe),
      quitar: () => setTransferencia((a) => a.filter((x) => x.clave !== p.clave)),
    })),
  ]

  const estadoSaldo = !hayAlgunPago
    ? { texto: 'Sin pagos cargados', color: 'gray' }
    : coincide
      ? { texto: 'Cobro completo', color: 'green' }
      : saldoPendiente > 0
        ? { texto: `Falta ${formatearMonto(saldoPendiente)}`, color: 'yellow' }
        : { texto: `Sobra ${formatearMonto(Math.abs(saldoPendiente))}`, color: 'red' }

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
            <Group grow gap="sm">
              <MetodoBoton
                icono={<IconCash size={20} />}
                titulo="Efectivo"
                atajo="F1"
                activo={metodoAbierto === 'efectivo'}
                deshabilitado={cobroCompleto}
                onClick={() => abrirMetodo('efectivo')}
              />
              <MetodoBoton
                icono={<IconCreditCard size={20} />}
                titulo="Tarjeta"
                atajo="F2"
                activo={tarjetaModalAbierto}
                deshabilitado={cobroCompleto}
                onClick={() => abrirMetodo('tarjeta')}
              />
              <MetodoBoton
                icono={<IconBuildingBank size={20} />}
                titulo="Cta. corriente"
                atajo="F3"
                activo={metodoAbierto === 'cc'}
                deshabilitado={cobroCompleto}
                onClick={() => abrirMetodo('cc')}
              />
              <MetodoBoton
                icono={<IconTransfer size={20} />}
                titulo="Transferencia"
                atajo="F6"
                activo={metodoAbierto === 'transferencia'}
                deshabilitado={cobroCompleto}
                onClick={() => abrirMetodo('transferencia')}
              />
            </Group>

            {metodoAbierto === 'efectivo' && (
              <Paper withBorder p="md">
                <Group justify="space-between" mb="xs">
                  <Text fw={600} size="sm">
                    Efectivo
                  </Text>
                  <ActionIcon variant="subtle" color="gray" aria-label="Cerrar" onClick={cerrarPanel}>
                    <IconX size={16} />
                  </ActionIcon>
                </Group>
                <Group grow align="flex-start">
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
                    autoFocus
                  />
                  <NumberInput
                    label="Paga con (para el vuelto)"
                    placeholder="Opcional"
                    value={pagaCon}
                    onChange={(v) => setPagaCon(String(v))}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        aceptarEfectivo()
                      }
                    }}
                    decimalScale={2}
                    min={0}
                  />
                </Group>
                {pagaCon !== '' && vuelto !== null && (
                  <Text mt="xs" size="sm" fw={500} c={vuelto < 0 ? 'red' : 'dimmed'}>
                    {vuelto >= 0 ? `Vuelto: ${formatearMonto(vuelto)}` : `Todavía falta ${formatearMonto(Math.abs(vuelto))}`}
                  </Text>
                )}
                <Group justify="flex-end" mt="sm">
                  <Button variant="subtle" color="gray" onClick={cerrarPanel}>
                    Cancelar
                  </Button>
                  <Button onClick={aceptarEfectivo} disabled={!(Number(efectivoImporte) > 0)}>
                    Agregar
                  </Button>
                </Group>
              </Paper>
            )}

            {metodoAbierto === 'cc' && (
              <Paper withBorder p="md">
                <Group justify="space-between" mb="xs">
                  <Text fw={600} size="sm">
                    Cuenta corriente
                  </Text>
                  <ActionIcon variant="subtle" color="gray" aria-label="Cerrar" onClick={cerrarPanel}>
                    <IconX size={16} />
                  </ActionIcon>
                </Group>
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
                  autoFocus
                />
                <Group justify="flex-end" mt="sm">
                  <Button variant="subtle" color="gray" onClick={cerrarPanel}>
                    Cancelar
                  </Button>
                  <Button onClick={aceptarCc} disabled={!(Number(ccImporte) > 0)}>
                    Agregar
                  </Button>
                </Group>
              </Paper>
            )}

            {metodoAbierto === 'transferencia' && (
              <Paper withBorder p="md">
                <Group justify="space-between" mb="xs">
                  <Text fw={600} size="sm">
                    Transferencia
                  </Text>
                  <ActionIcon variant="subtle" color="gray" aria-label="Cerrar" onClick={cerrarPanel}>
                    <IconX size={16} />
                  </ActionIcon>
                </Group>
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
                    autoFocus
                  />
                  <TextInput
                    label="Documento del titular"
                    value={transferenciaStaging.documento}
                    onChange={(e) => {
                      const documento = e.currentTarget.value
                      setTransferenciaStaging((s) => ({ ...s, documento }))
                    }}
                  />
                </Group>
                <Group grow mt="xs">
                  <TextInput
                    label="Nombre"
                    value={transferenciaStaging.nombre}
                    onChange={(e) => {
                      const nombre = e.currentTarget.value
                      setTransferenciaStaging((s) => ({ ...s, nombre }))
                    }}
                  />
                  <TextInput
                    label="Apellido"
                    value={transferenciaStaging.apellido}
                    onChange={(e) => {
                      const apellido = e.currentTarget.value
                      setTransferenciaStaging((s) => ({ ...s, apellido }))
                    }}
                  />
                  <TextInput
                    label="Banco"
                    value={transferenciaStaging.banco}
                    onChange={(e) => {
                      const banco = e.currentTarget.value
                      setTransferenciaStaging((s) => ({ ...s, banco }))
                    }}
                  />
                </Group>
                <Group justify="flex-end" mt="sm">
                  <Button variant="subtle" color="gray" onClick={cerrarPanel}>
                    Cancelar
                  </Button>
                  <Button onClick={aceptarTransferencia} disabled={!(Number(transferenciaStaging.importe) > 0)}>
                    Agregar
                  </Button>
                </Group>
              </Paper>
            )}

            <div>
              <Text fw={600} size="sm" c="dimmed" mb="xs">
                Pagos cargados
              </Text>
              {filasPago.length === 0 ? (
                <Text size="sm" c="dimmed">
                  Todavía no se cargó ningún pago.
                </Text>
              ) : (
                <Table verticalSpacing="xs">
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>Método</Table.Th>
                      <Table.Th>Detalle</Table.Th>
                      <Table.Th>Importe</Table.Th>
                      <Table.Th />
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {filasPago.map((fila) => (
                      <Table.Tr key={fila.clave}>
                        <Table.Td>{fila.tipo}</Table.Td>
                        <Table.Td>
                          <Text size="sm" c="dimmed">
                            {fila.detalle}
                          </Text>
                        </Table.Td>
                        <Table.Td>{formatearMonto(fila.importe)}</Table.Td>
                        <Table.Td>
                          <ActionIcon color="red" variant="subtle" aria-label="Quitar" onClick={fila.quitar}>
                            <IconTrash size={16} />
                          </ActionIcon>
                        </Table.Td>
                      </Table.Tr>
                    ))}
                  </Table.Tbody>
                </Table>
              )}
            </div>
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

            <Badge fullWidth color={estadoSaldo.color} size="lg" mb="lg">
              {estadoSaldo.texto}
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
              onChange={(e) => {
                const numeroCupon = e.currentTarget.value
                setTarjetaStaging((s) => ({ ...s, numeroCupon }))
              }}
            />
            <TextInput
              label="Lote"
              value={tarjetaStaging.lote}
              onChange={(e) => {
                const lote = e.currentTarget.value
                setTarjetaStaging((s) => ({ ...s, lote }))
              }}
            />
          </Group>
          <Group justify="flex-end" mt="sm">
            <Button variant="subtle" color="gray" onClick={cerrarModalTarjeta}>
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

function MetodoBoton({
  icono,
  titulo,
  atajo,
  activo,
  deshabilitado,
  onClick,
}: {
  icono: ReactNode
  titulo: string
  atajo: string
  activo: boolean
  deshabilitado: boolean
  onClick: () => void
}) {
  return (
    <Button
      variant={activo ? 'filled' : 'light'}
      color={activo ? 'blue' : 'gray'}
      disabled={deshabilitado}
      onClick={onClick}
      styles={{ root: { height: 68, paddingInline: 6 }, label: { whiteSpace: 'normal' } }}
    >
      <Stack gap={4} align="center">
        {icono}
        <Text fw={600} size="xs" ta="center" style={{ lineHeight: 1.15 }}>
          {titulo}
        </Text>
        <Kbd size="xs">{atajo}</Kbd>
      </Stack>
    </Button>
  )
}
