import { useEffect, useRef, useState } from 'react'
import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Container,
  Group,
  NumberInput,
  Paper,
  Select,
  Table,
  Text,
  Title,
} from '@mantine/core'
import { useDebouncedValue } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import { leerPesoBalanza } from '../../api/balanza'
import { listarArticulos } from '../../api/articulo'
import { ApiError } from '../../api/client'
import { listarClientes } from '../../api/cliente'
import { listarEmpleadosActivos } from '../../api/empleado'
import { crearVenta, imprimirTicket, previsualizarVenta } from '../../api/venta'
import BuscadorLista from '../../components/BuscadorLista'
import type { Articulo } from '../../types/articulo'
import type { Cliente } from '../../types/cliente'
import type { Empleado } from '../../types/empleado'
import type { ItemCarrito, VentaPrevisualizada } from '../../types/venta'
import { formatearMonto } from './dinero'
import TicketPreviewModal from './TicketPreviewModal'

function nuevaClave() {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

export default function VentaNuevaPage() {
  const navigate = useNavigate()
  const { perfil } = useAuth()

  const [cliente, setCliente] = useState<Cliente | null>(null)
  const [empleados, setEmpleados] = useState<Empleado[]>([])
  const [empleadoId, setEmpleadoId] = useState<string | null>(null)
  const [carrito, setCarrito] = useState<ItemCarrito[]>([])
  const [previsualizacion, setPrevisualizacion] = useState<VentaPrevisualizada | null>(null)
  const [errorPreview, setErrorPreview] = useState<string | null>(null)
  const [confirmando, setConfirmando] = useState(false)
  const [ticketPreview, setTicketPreview] = useState<{ numeroTicket: number; url: string } | null>(null)
  const empleadoInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    listarEmpleadosActivos()
      .then((r) => setEmpleados(r.results))
      .catch(() => notifications.show({ message: 'No se pudieron cargar los empleados.', color: 'red' }))
  }, [])

  // Preselecciona al vendedor logueado (perfil.empleado, ver usuario.UsuarioSerializer) apenas
  // están disponibles tanto el perfil como la lista de empleados — no pisa una selección manual
  // posterior (el guard de empleadoId===null) ni pasa nada si el usuario no tiene Empleado
  // vinculado o no está en la lista de activos.
  useEffect(() => {
    if (empleadoId !== null || !perfil?.empleado) return
    if (empleados.some((e) => e.id === perfil.empleado)) {
      setEmpleadoId(String(perfil.empleado))
    }
  }, [empleados, perfil, empleadoId])

  const [carritoDebounced] = useDebouncedValue(carrito, 400)

  useEffect(() => {
    const items = carritoDebounced.filter((i) => Number(i.cantidadPeso) > 0)
    if (!cliente || items.length === 0) {
      setPrevisualizacion(null)
      setErrorPreview(null)
      return
    }
    previsualizarVenta(
      cliente.id,
      items.map((i) => ({ articulo: i.articuloId, cantidad_peso: i.cantidadPeso })),
    )
      .then((r) => {
        setPrevisualizacion(r)
        setErrorPreview(null)
      })
      .catch((err: ApiError) => {
        setPrevisualizacion(null)
        setErrorPreview(typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail))
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [carritoDebounced, cliente])

  const agregarArticulo = async (articulo: Articulo) => {
    const clave = nuevaClave()
    setCarrito((actual) => [
      ...actual,
      {
        clave,
        articuloId: articulo.id,
        articuloNombre: articulo.nombre,
        articuloCodigo: articulo.codigo,
        esPorPeso: articulo.es_por_peso,
        cantidadPeso: articulo.es_por_peso ? '' : '1',
      },
    ])
    if (articulo.es_por_peso) {
      try {
        const peso = await leerPesoBalanza()
        setCarrito((actual) => actual.map((i) => (i.clave === clave ? { ...i, cantidadPeso: peso } : i)))
      } catch {
        notifications.show({
          message: 'No se pudo leer la balanza. Ingresá el peso manualmente.',
          color: 'yellow',
        })
      }
    }
  }

  const actualizarCantidad = (clave: string, valor: string) => {
    setCarrito((actual) => actual.map((i) => (i.clave === clave ? { ...i, cantidadPeso: valor } : i)))
  }

  const quitarItem = (clave: string) => {
    setCarrito((actual) => actual.filter((i) => i.clave !== clave))
  }

  const confirmarVenta = async () => {
    if (!cliente || !empleadoId) return
    const items = carrito.filter((i) => Number(i.cantidadPeso) > 0)
    if (items.length === 0) return
    setConfirmando(true)
    try {
      const venta = await crearVenta({
        empleado: Number(empleadoId),
        cliente: cliente.id,
        articulos: items.map((i) => ({ articulo: i.articuloId, cantidad_peso: i.cantidadPeso })),
      })
      notifications.show({ message: `Venta #${venta.numero_ticket} registrada.`, color: 'green' })
      // La venta ya quedó registrada en este punto — si falla sólo el PDF, no bloqueamos el
      // flujo de cobro por eso, vamos directo a /cobrar con un aviso.
      try {
        const blob = await imprimirTicket(venta.numero_ticket)
        setTicketPreview({ numeroTicket: venta.numero_ticket, url: URL.createObjectURL(blob) })
      } catch {
        notifications.show({ message: 'La venta se registró pero no se pudo generar el ticket para imprimir.', color: 'yellow' })
        navigate(`/ventas/${venta.numero_ticket}/cobrar`)
      }
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo registrar la venta', message: detalle, color: 'red' })
    } finally {
      setConfirmando(false)
    }
  }

  const cerrarPreviewYContinuar = () => {
    if (!ticketPreview) return
    URL.revokeObjectURL(ticketPreview.url)
    const numeroTicket = ticketPreview.numeroTicket
    setTicketPreview(null)
    navigate(`/ventas/${numeroTicket}/cobrar`)
  }

  const precioDe = (articuloId: number) => previsualizacion?.articulos.find((a) => a.articulo === articuloId)

  const puedeConfirmar = !!cliente && !!empleadoId && carrito.length > 0 && !errorPreview && !!previsualizacion

  return (
    <Container size="md" py="md">
      <Title order={2}>Nueva venta</Title>
      <Text c="dimmed" size="sm" mb="lg">
        Punto de venta
      </Text>

      <Paper withBorder p="md" mb="md">
        <Group grow align="flex-start">
          <div>
            <Text fw={500} size="sm" mb={4}>
              Cliente
            </Text>
            {cliente ? (
              <Group justify="space-between">
                <Text>
                  {cliente.persona_detalle.apellido}, {cliente.persona_detalle.nombre}
                </Text>
                <Button size="xs" variant="subtle" onClick={() => setCliente(null)}>
                  Cambiar
                </Button>
              </Group>
            ) : (
              <BuscadorLista<Cliente>
                placeholder="Buscar cliente por nombre o documento…"
                buscar={(q) => listarClientes({ search: q }).then((r) => r.results)}
                onSeleccionar={setCliente}
                enfocarSiguienteRef={empleadoInputRef}
                clave={(c) => c.id}
                renderItem={(c) => (
                  <Text size="sm">
                    {c.persona_detalle.apellido}, {c.persona_detalle.nombre} — {c.persona_detalle.documento_identidad}
                  </Text>
                )}
              />
            )}
          </div>

          <Select
            ref={empleadoInputRef}
            label="Empleado que atiende"
            placeholder="Elegir…"
            data={empleados.map((e) => ({ value: String(e.id), label: e.persona_nombre }))}
            value={empleadoId}
            onChange={setEmpleadoId}
          />
        </Group>
      </Paper>

      <Paper withBorder p="md" mb="md">
        <Text fw={500} size="sm" mb={4}>
          Agregar artículo
        </Text>
        <BuscadorLista<Articulo>
          placeholder="Buscar artículo por nombre o código…"
          buscar={(q) => listarArticulos({ search: q }).then((r) => r.results)}
          onSeleccionar={(a) => void agregarArticulo(a)}
          clave={(a) => a.id}
          renderItem={(a) => (
            <Group justify="space-between">
              <Text size="sm">{a.nombre}</Text>
              <Badge variant="light">{a.codigo}</Badge>
            </Group>
          )}
        />
      </Paper>

      <Table striped verticalSpacing="sm" mb="md">
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Artículo</Table.Th>
            <Table.Th>Cantidad / Peso</Table.Th>
            <Table.Th>Subtotal</Table.Th>
            <Table.Th />
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {carrito.map((item) => {
            const precio = precioDe(item.articuloId)
            return (
              <Table.Tr key={item.clave}>
                <Table.Td>{item.articuloNombre}</Table.Td>
                <Table.Td>
                  <NumberInput
                    value={item.cantidadPeso}
                    onChange={(v) => actualizarCantidad(item.clave, String(v))}
                    decimalScale={2}
                    min={0}
                    w={110}
                  />
                </Table.Td>
                <Table.Td>{precio ? formatearMonto(precio.total_articulo) : '—'}</Table.Td>
                <Table.Td>
                  <ActionIcon color="red" variant="subtle" onClick={() => quitarItem(item.clave)} aria-label="Quitar">
                    ✕
                  </ActionIcon>
                </Table.Td>
              </Table.Tr>
            )
          })}
          {carrito.length === 0 && (
            <Table.Tr>
              <Table.Td colSpan={4}>
                <Text c="dimmed">Buscá un artículo para agregarlo.</Text>
              </Table.Td>
            </Table.Tr>
          )}
        </Table.Tbody>
      </Table>

      {errorPreview && (
        <Alert color="red" mb="md">
          {errorPreview}
        </Alert>
      )}

      <Group justify="space-between" align="center">
        <Text size="xl" fw={700}>
          Total: {previsualizacion ? formatearMonto(previsualizacion.monto) : '—'}
        </Text>
        <Button size="lg" color="red" disabled={!puedeConfirmar} loading={confirmando} onClick={() => void confirmarVenta()}>
          Confirmar venta
        </Button>
      </Group>

      <TicketPreviewModal
        opened={!!ticketPreview}
        numeroTicket={ticketPreview?.numeroTicket ?? null}
        url={ticketPreview?.url ?? null}
        onClose={cerrarPreviewYContinuar}
      />
    </Container>
  )
}
