import { useEffect, useRef, useState } from 'react'
import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Container,
  Divider,
  Group,
  Kbd,
  NumberInput,
  Paper,
  Select,
  Stack,
  Table,
  Text,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { useAuth } from '../../auth/AuthContext'
import { leerPesoBalanza } from '../../api/balanza'
import { listarArticulos } from '../../api/articulo'
import { mensajeDeError } from '../../api/client'
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
  const { perfil } = useAuth()

  const [cliente, setCliente] = useState<Cliente | null>(null)
  const [empleados, setEmpleados] = useState<Empleado[]>([])
  const [empleadoId, setEmpleadoId] = useState<string | null>(null)
  const [carrito, setCarrito] = useState<ItemCarrito[]>([])
  const [previsualizacion, setPrevisualizacion] = useState<VentaPrevisualizada | null>(null)
  const [errorPreview, setErrorPreview] = useState<string | null>(null)
  const [confirmando, setConfirmando] = useState(false)
  const [ticketPreview, setTicketPreview] = useState<{ numeroTicket: number; url: string } | null>(null)
  const [claveAEnfocar, setClaveAEnfocar] = useState<string | null>(null)
  // Clave del ítem que se está pesando en este momento — mientras no sea null, se vuelve a leer
  // la balanza en loop y se pisa su cantidadPeso con cada lectura, para que el campo seguir el
  // peso en tiempo real a medida que se agrega/saca mercadería de la balanza (antes se leía una
  // sola vez al agregar el artículo y quedaba congelado). Se corta en cuanto el usuario toca ese
  // campo a mano, le da Enter, lo deja de enfocar, o se quita el ítem del carrito.
  const [claveEnBalanza, setClaveEnBalanza] = useState<string | null>(null)
  // Mientras se está agregando/sacando mercadería la balanza puede devolver un valor no
  // numérico por un instante (todavía inestable, antes de asentarse) — eso es normal y se
  // resuelve solo en la próxima lectura, 300ms después. Sólo avisamos si falla de forma
  // sostenida (varias lecturas seguidas), para no mostrar un aviso de error cada vez que se
  // toca la balanza.
  const fallosSeguidosRef = useRef(0)
  const errorBalanzaMostradoRef = useRef(false)
  const empleadoInputRef = useRef<HTMLInputElement>(null)
  const articuloInputRef = useRef<HTMLInputElement>(null)
  const cantidadRefs = useRef(new Map<string, HTMLInputElement>())

  const dejarDeLeerBalanza = (clave: string) => {
    setClaveEnBalanza((actual) => (actual === clave ? null : actual))
  }

  const UMBRAL_FALLOS_BALANZA = 5

  useEffect(() => {
    if (!claveEnBalanza) return
    const intervalo = setInterval(() => {
      leerPesoBalanza()
        .then((peso) => {
          fallosSeguidosRef.current = 0
          setCarrito((actual) => actual.map((i) => (i.clave === claveEnBalanza ? { ...i, cantidadPeso: peso } : i)))
        })
        .catch(() => {
          fallosSeguidosRef.current += 1
          if (fallosSeguidosRef.current < UMBRAL_FALLOS_BALANZA || errorBalanzaMostradoRef.current) return
          errorBalanzaMostradoRef.current = true
          notifications.show({
            message: 'No se pudo leer la balanza. Ingresá el peso manualmente.',
            color: 'yellow',
          })
        })
    }, 300)
    return () => clearInterval(intervalo)
  }, [claveEnBalanza])

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

  // Apenas se agrega un artículo, el foco salta a su campo de Cantidad/Peso (ver
  // agregarArticulo) — la fila recién se crea en este render, así que hace falta esperar a que
  // el ref del input exista.
  useEffect(() => {
    if (!claveAEnfocar) return
    const input = cantidadRefs.current.get(claveAEnfocar)
    if (input) {
      input.focus()
      input.select()
    }
    setClaveAEnfocar(null)
  }, [claveAEnfocar])

  // Throttle (no debounce): mientras se está pesando, `carrito` cambia cada 300ms (ver
  // leerPesoBalanza más arriba) — un debounce clásico (esperar a que termine de cambiar)
  // nunca llega a dispararse ahí, así que Precio/Subtotal quedaban congelados hasta soltar la
  // balanza. Con throttle, como mucho una llamada cada RETRASO_MIN_MS, se sigue viendo el
  // precio actualizarse en vivo mientras se pesa, y al soltar la balanza el último peso
  // siempre termina mandándose (el `setTimeout` pendiente).
  const ultimoEnvioPreviewRef = useRef(0)
  const previewPendienteRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (previewPendienteRef.current) {
      clearTimeout(previewPendienteRef.current)
      previewPendienteRef.current = null
    }

    const items = carrito.filter((i) => Number(i.cantidadPeso) > 0)
    if (!cliente || items.length === 0) {
      setPrevisualizacion(null)
      setErrorPreview(null)
      return
    }

    const pedirPreview = () => {
      ultimoEnvioPreviewRef.current = Date.now()
      previsualizarVenta(
        cliente.id,
        items.map((i) => ({ articulo: i.articuloId, cantidad_peso: i.cantidadPeso })),
      )
        .then((r) => {
          setPrevisualizacion(r)
          setErrorPreview(null)
        })
        .catch((err: unknown) => {
          setPrevisualizacion(null)
          setErrorPreview(mensajeDeError(err))
        })
    }

    const RETRASO_MIN_MS = 400
    const transcurrido = Date.now() - ultimoEnvioPreviewRef.current
    if (transcurrido >= RETRASO_MIN_MS) {
      pedirPreview()
    } else {
      previewPendienteRef.current = setTimeout(pedirPreview, RETRASO_MIN_MS - transcurrido)
    }

    return () => {
      if (previewPendienteRef.current) clearTimeout(previewPendienteRef.current)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [carrito, cliente])

  const agregarArticulo = (articulo: Articulo) => {
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
    setClaveAEnfocar(clave)
    if (articulo.es_por_peso) {
      fallosSeguidosRef.current = 0
      errorBalanzaMostradoRef.current = false
      setClaveEnBalanza(clave)
    }
  }

  const actualizarCantidad = (clave: string, valor: string) => {
    setCarrito((actual) => actual.map((i) => (i.clave === clave ? { ...i, cantidadPeso: valor } : i)))
    // El usuario tocó el campo a mano — a partir de acá su valor manda, no lo vuelve a pisar la
    // próxima lectura de la balanza.
    dejarDeLeerBalanza(clave)
  }

  const quitarItem = (clave: string) => {
    setCarrito((actual) => actual.filter((i) => i.clave !== clave))
    dejarDeLeerBalanza(clave)
  }

  // Deja la página lista para la siguiente venta sin pasar por /cobrar: el carnicero solo carga
  // ventas, el cobro lo hace otro operador aparte (desde el listado de Ventas). El empleado que
  // atiende queda tal cual (mismo vendedor para varias ventas seguidas); el buscador de cliente
  // se remonta con autoFocus (ver BuscadorLista) así que el foco vuelve solo ahí.
  const reiniciarParaNuevaVenta = () => {
    setCliente(null)
    setCarrito([])
    setPrevisualizacion(null)
    setErrorPreview(null)
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
      // flujo por eso.
      try {
        const blob = await imprimirTicket(venta.numero_ticket)
        setTicketPreview({ numeroTicket: venta.numero_ticket, url: URL.createObjectURL(blob) })
      } catch {
        notifications.show({ message: 'La venta se registró pero no se pudo generar el ticket para imprimir.', color: 'yellow' })
        reiniciarParaNuevaVenta()
      }
    } catch (err) {
      const detalle = mensajeDeError(err)
      notifications.show({ title: 'No se pudo registrar la venta', message: detalle, color: 'red' })
    } finally {
      setConfirmando(false)
    }
  }

  const cerrarPreviewYContinuar = () => {
    if (!ticketPreview) return
    URL.revokeObjectURL(ticketPreview.url)
    setTicketPreview(null)
    reiniciarParaNuevaVenta()
  }

  const precioDe = (articuloId: number) => previsualizacion?.articulos.find((a) => a.articulo === articuloId)

  const puedeConfirmar = !!cliente && !!empleadoId && carrito.length > 0 && !errorPreview && !!previsualizacion

  // Atajo de teclado F4 = confirmar venta, igual que en el cobro (ver CobroVentaPage) — a nivel
  // de window porque es una tecla de función, no interfiere con lo que se esté tipeando.
  useEffect(() => {
    const onKeyDown = (e: globalThis.KeyboardEvent) => {
      if (e.key !== 'F4') return
      e.preventDefault()
      if (puedeConfirmar && !confirmando) void confirmarVenta()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [puedeConfirmar, confirmando])

  return (
    <Container size="lg" py="md">
      <Title order={2}>Nueva venta</Title>
      <Text c="dimmed" size="sm" mb="lg">
        Punto de venta
      </Text>

      <Group align="flex-start" gap="lg">
        <Stack gap="md" style={{ flex: 1, minWidth: 320 }}>
          <Paper withBorder p="md">
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
                    autoFocus
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

          <Paper withBorder p="md">
            <Text fw={500} size="sm" mb={4}>
              Agregar artículo
            </Text>
            <BuscadorLista<Articulo>
              placeholder="Buscar artículo por nombre o código…"
              buscar={(q) => listarArticulos({ search: q }).then((r) => r.results)}
              onSeleccionar={agregarArticulo}
              inputRef={articuloInputRef}
              clave={(a) => a.id}
              renderItem={(a) => (
                <Group justify="space-between">
                  <Text size="sm">{a.nombre}</Text>
                  <Badge variant="light">{a.codigo}</Badge>
                </Group>
              )}
            />
          </Paper>

          <Paper withBorder p={0}>
            <Table striped verticalSpacing="sm">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Artículo</Table.Th>
                  <Table.Th>Cantidad / Peso</Table.Th>
                  <Table.Th>Precio</Table.Th>
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
                          ref={(el) => {
                            if (el) cantidadRefs.current.set(item.clave, el)
                            else cantidadRefs.current.delete(item.clave)
                          }}
                          value={item.cantidadPeso}
                          onChange={(v) => actualizarCantidad(item.clave, String(v))}
                          onBlur={() => dejarDeLeerBalanza(item.clave)}
                          onKeyDown={(e) => {
                            if (e.key !== 'Enter') return
                            e.preventDefault()
                            dejarDeLeerBalanza(item.clave)
                            articuloInputRef.current?.focus()
                          }}
                          decimalScale={3}
                          min={0}
                          w={110}
                        />
                      </Table.Td>
                      {/* Precio final por unidad (ya con la promoción aplicada si corresponde) —
                         mismo valor que se usa para calcular el Subtotal de al lado, para que la
                         cuenta "precio x cantidad = subtotal" siempre cierre a simple vista. */}
                      <Table.Td>{precio ? formatearMonto(precio.precio_promocion) : '—'}</Table.Td>
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
                    <Table.Td colSpan={5}>
                      <Text c="dimmed">Buscá un artículo para agregarlo.</Text>
                    </Table.Td>
                  </Table.Tr>
                )}
              </Table.Tbody>
            </Table>
          </Paper>

          {errorPreview && <Alert color="red">{errorPreview}</Alert>}
        </Stack>

        {/* Resumen fijo: cliente/empleado/total y el botón de confirmar quedan siempre a la
           vista, sin depender de scrollear pasado el carrito — importante con muchos ítems. */}
        <Paper withBorder p="lg" style={{ width: 300, flexShrink: 0, position: 'sticky', top: 16 }}>
          <Text fw={600} size="sm" c="dimmed" mb="sm">
            Resumen
          </Text>
          <Stack gap={6} mb="md">
            <Group justify="space-between">
              <Text size="sm" c="dimmed">
                Cliente
              </Text>
              <Text size="sm" fw={500} ta="right">
                {cliente ? `${cliente.persona_detalle.apellido}, ${cliente.persona_detalle.nombre}` : '—'}
              </Text>
            </Group>
            <Group justify="space-between">
              <Text size="sm" c="dimmed">
                Artículos
              </Text>
              <Text size="sm" fw={500}>
                {carrito.length}
              </Text>
            </Group>
          </Stack>

          <Divider mb="md" />

          <Text size="sm" c="dimmed">
            Total
          </Text>
          <Text fz={32} fw={800} mb="lg">
            {previsualizacion ? formatearMonto(previsualizacion.monto) : '—'}
          </Text>

          <Group gap="xs" wrap="nowrap" align="stretch">
            <Button
              flex={1}
              size="lg"
              color="red"
              disabled={!puedeConfirmar}
              loading={confirmando}
              onClick={() => void confirmarVenta()}
              onKeyDown={(e) => {
                // Tab desde acá vuelve al buscador de artículo en vez de salir del formulario —
                // es el último campo del flujo de carga, así que cierra el círculo para seguir
                // cargando ítems sin soltar el teclado.
                if (e.key !== 'Tab' || e.shiftKey) return
                e.preventDefault()
                articuloInputRef.current?.focus()
              }}
            >
              Confirmar venta
            </Button>
            <Kbd style={{ alignSelf: 'center' }}>F4</Kbd>
          </Group>
        </Paper>
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
