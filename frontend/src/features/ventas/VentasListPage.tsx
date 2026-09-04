import { useEffect, useState } from 'react'
import { ActionIcon, Badge, Button, Container, Group, Paper, Table, Text, TextInput, Title } from '@mantine/core'
import { useDebouncedValue } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import { IconPlus, IconPrinter, IconSearch, IconX } from '@tabler/icons-react'
import { Link } from 'react-router-dom'
import { VENTAS_POR_PAGINA, listarVentas } from '../../api/venta'
import { ApiError } from '../../api/client'
import EstadoVacio from '../../components/EstadoVacio'
import Paginador from '../../components/Paginador'
import type { Venta } from '../../types/venta'
import { formatearMonto } from './dinero'
import { abrirTicketParaImprimir } from './imprimirTicket'

export default function VentasListPage() {
  const [ventas, setVentas] = useState<Venta[]>([])
  const [total, setTotal] = useState(0)
  const [pagina, setPagina] = useState(1)
  const [busqueda, setBusqueda] = useState('')
  const [busquedaDebounced] = useDebouncedValue(busqueda, 300)
  const [cargando, setCargando] = useState(true)

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
            {ventas.map((venta) => (
              <Table.Tr key={venta.numero_ticket}>
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
                    {!venta.anulado && !venta.cobrada && (
                      <Button component={Link} to={`/ventas/${venta.numero_ticket}/cobrar`} size="xs" variant="light">
                        Cobrar
                      </Button>
                    )}
                    <ActionIcon
                      variant="subtle"
                      aria-label="Imprimir ticket"
                      onClick={() => void abrirTicketParaImprimir(venta.numero_ticket)}
                    >
                      <IconPrinter size={16} />
                    </ActionIcon>
                  </Group>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>

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
