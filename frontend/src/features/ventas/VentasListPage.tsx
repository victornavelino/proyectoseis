import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { ActionIcon, Badge, Button, Container, Group, Paper, Table, Text, TextInput, Title } from '@mantine/core'
import { useDebouncedValue } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import { IconPlus, IconPrinter, IconSearch, IconX } from '@tabler/icons-react'
import { Link, useNavigate } from 'react-router-dom'
import { VENTAS_POR_PAGINA, listarVentas } from '../../api/venta'
import { ApiError } from '../../api/client'
import EstadoVacio from '../../components/EstadoVacio'
import Paginador from '../../components/Paginador'
import type { Venta } from '../../types/venta'
import { formatearMonto } from './dinero'
import { abrirTicketParaImprimir } from './imprimirTicket'

type Accion = 'cobrar' | 'imprimir'

/** Acciones disponibles para una venta: si ya está cobrada o anulada, sólo se puede reimprimir. */
function accionesDisponibles(venta: Venta): Accion[] {
  return !venta.anulado && !venta.cobrada ? ['cobrar', 'imprimir'] : ['imprimir']
}

export default function VentasListPage() {
  const [ventas, setVentas] = useState<Venta[]>([])
  const [total, setTotal] = useState(0)
  const [pagina, setPagina] = useState(1)
  const [busqueda, setBusqueda] = useState('')
  const [busquedaDebounced] = useDebouncedValue(busqueda, 300)
  const [cargando, setCargando] = useState(true)
  const navigate = useNavigate()

  // Navegación por teclado del listado: ↑/↓ elige la venta, ←/→ elige la acción (Cobrar por
  // default) y Enter la ejecuta — pensado para que el cajero cobre sin soltar el teclado.
  const [filaSeleccionada, setFilaSeleccionada] = useState(0)
  const [accion, setAccion] = useState<Accion>('cobrar')
  const contenedorRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setPagina(1)
  }, [busquedaDebounced])

  useEffect(() => {
    setCargando(true)
    listarVentas({ search: busquedaDebounced || undefined, pagina })
      .then((r) => {
        setVentas(r.results)
        setTotal(r.count)
      })
      .catch((err: ApiError) => notifications.show({ title: 'Error', message: err.message, color: 'red' }))
      .finally(() => setCargando(false))
  }, [busquedaDebounced, pagina])

  useEffect(() => {
    setFilaSeleccionada(0)
    setAccion(ventas.length > 0 ? accionesDisponibles(ventas[0])[0] : 'cobrar')
    if (ventas.length === 0) return
    // Si el cajero está tipeando en el buscador no le robamos el foco; en cualquier otro caso
    // (entrar a la página, cambiar de página) el foco va a la primera fila para poder navegar
    // con flechas de entrada.
    if (document.activeElement?.tagName === 'INPUT') return
    contenedorRef.current?.focus()
  }, [ventas])

  const ejecutarAccion = (venta: Venta, accionAEjecutar: Accion) => {
    if (accionAEjecutar === 'cobrar') {
      navigate(`/ventas/${venta.numero_ticket}/cobrar`)
    } else {
      void abrirTicketParaImprimir(venta.numero_ticket)
    }
  }

  const onKeyDownTabla = (e: KeyboardEvent<HTMLDivElement>) => {
    if (ventas.length === 0) return
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault()
      const nuevaFila =
        e.key === 'ArrowDown' ? Math.min(filaSeleccionada + 1, ventas.length - 1) : Math.max(filaSeleccionada - 1, 0)
      setFilaSeleccionada(nuevaFila)
      setAccion(accionesDisponibles(ventas[nuevaFila])[0])
    } else if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
      e.preventDefault()
      const disponibles = accionesDisponibles(ventas[filaSeleccionada])
      const idx = Math.max(disponibles.indexOf(accion), 0)
      const nuevoIdx = Math.min(Math.max(idx + (e.key === 'ArrowRight' ? 1 : -1), 0), disponibles.length - 1)
      setAccion(disponibles[nuevoIdx])
    } else if (e.key === 'Enter') {
      e.preventDefault()
      ejecutarAccion(ventas[filaSeleccionada], accion)
    }
  }

  return (
    <Container size="lg" py="md">
      <Group justify="space-between" mb="md">
        <div>
          <Title order={2}>Ventas</Title>
          <Text c="dimmed" size="sm">
            Historial de ventas y cobros pendientes
          </Text>
        </div>
        <Button component={Link} to="/ventas/nueva" color="red" leftSection={<IconPlus size={16} />}>
          Nueva venta
        </Button>
      </Group>

      <Paper withBorder p="md" mb="md">
        <Group>
          <TextInput
            placeholder="Buscar por nro. de ticket, apellido o DNI del cliente…"
            leftSection={<IconSearch size={16} />}
            value={busqueda}
            onChange={(e) => setBusqueda(e.currentTarget.value)}
            style={{ flex: 1 }}
          />
          {busqueda && (
            <Button variant="subtle" color="gray" leftSection={<IconX size={14} />} onClick={() => setBusqueda('')}>
              Limpiar
            </Button>
          )}
        </Group>
      </Paper>

      <Paper withBorder p="md">
        <Text size="sm" c="dimmed" mb="sm">
          {total} registro{total === 1 ? '' : 's'}
        </Text>

        <div ref={contenedorRef} tabIndex={0} onKeyDown={onKeyDownTabla} style={{ outline: 'none' }}>
          <Table striped highlightOnHover verticalSpacing="sm">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Ticket</Table.Th>
                <Table.Th>Fecha</Table.Th>
                <Table.Th>Cliente</Table.Th>
                <Table.Th>Monto</Table.Th>
                <Table.Th>Estado</Table.Th>
                <Table.Th />
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {ventas.map((venta, i) => {
                const disponibles = accionesDisponibles(venta)
                const seleccionada = i === filaSeleccionada
                return (
                  <Table.Tr
                    key={venta.numero_ticket}
                    onClick={() => {
                      setFilaSeleccionada(i)
                      setAccion(accionesDisponibles(venta)[0])
                    }}
                    style={{
                      cursor: 'pointer',
                      backgroundColor: seleccionada ? 'var(--mantine-color-red-light)' : undefined,
                    }}
                  >
                    <Table.Td>#{venta.numero_ticket}</Table.Td>
                    <Table.Td>{new Date(venta.fecha).toLocaleString('es-AR')}</Table.Td>
                    <Table.Td>{venta.cliente_nombre}</Table.Td>
                    <Table.Td>{formatearMonto(venta.monto)}</Table.Td>
                    <Table.Td>
                      {venta.anulado && <Badge color="gray">Anulada</Badge>}
                      {!venta.anulado && venta.cobrada && <Badge color="green">Cobrada</Badge>}
                      {!venta.anulado && !venta.cobrada && <Badge color="orange">Pendiente de cobro</Badge>}
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs" wrap="nowrap">
                        {disponibles.includes('cobrar') && (
                          <Button
                            component={Link}
                            to={`/ventas/${venta.numero_ticket}/cobrar`}
                            size="xs"
                            variant={seleccionada && accion === 'cobrar' ? 'filled' : 'light'}
                          >
                            Cobrar
                          </Button>
                        )}
                        <ActionIcon
                          variant={seleccionada && accion === 'imprimir' ? 'filled' : 'subtle'}
                          aria-label="Imprimir ticket"
                          onClick={(e) => {
                            e.stopPropagation()
                            void abrirTicketParaImprimir(venta.numero_ticket)
                          }}
                        >
                          <IconPrinter size={16} />
                        </ActionIcon>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                )
              })}
            </Table.Tbody>
          </Table>
        </div>

        {!cargando && ventas.length === 0 && (
          <EstadoVacio
            titulo={busquedaDebounced ? 'Sin resultados' : 'Sin ventas todavía'}
            descripcion={busquedaDebounced ? 'No se encontraron ventas para la búsqueda.' : undefined}
          />
        )}

        {total > VENTAS_POR_PAGINA && (
          <Paginador pagina={pagina} porPagina={VENTAS_POR_PAGINA} total={total} onCambiarPagina={setPagina} />
        )}
      </Paper>
    </Container>
  )
}
