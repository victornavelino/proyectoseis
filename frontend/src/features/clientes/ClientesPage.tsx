import { useEffect, useState } from 'react'
import { Button, Container, Group, Paper, Table, Text, TextInput, Title } from '@mantine/core'
import { useDebouncedValue } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import { IconPlus, IconSearch, IconX } from '@tabler/icons-react'
import { CLIENTES_POR_PAGINA, listarClientes } from '../../api/cliente'
import { ApiError } from '../../api/client'
import EstadoVacio from '../../components/EstadoVacio'
import Paginador from '../../components/Paginador'
import type { Cliente } from '../../types/cliente'
import ClienteFormModal from './ClienteFormModal'

export default function ClientesPage() {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [total, setTotal] = useState(0)
  const [pagina, setPagina] = useState(1)
  const [busqueda, setBusqueda] = useState('')
  const [busquedaDebounced] = useDebouncedValue(busqueda, 300)
  const [cargando, setCargando] = useState(true)
  const [modalAbierto, setModalAbierto] = useState(false)

  useEffect(() => {
    setPagina(1)
  }, [busquedaDebounced])

  const cargarClientes = () => {
    setCargando(true)
    listarClientes({ search: busquedaDebounced || undefined, pagina })
      .then((r) => {
        setClientes(r.results)
        setTotal(r.count)
      })
      .catch((err: ApiError) => notifications.show({ title: 'Error', message: err.message, color: 'red' }))
      .finally(() => setCargando(false))
  }

  useEffect(cargarClientes, [busquedaDebounced, pagina])

  return (
    <Container size="lg" py="md">
      <Group justify="space-between" mb="md">
        <div>
          <Title order={2}>Clientes</Title>
          <Text c="dimmed" size="sm">
            Registro y consulta de clientes
          </Text>
        </div>
        <Button color="red" leftSection={<IconPlus size={16} />} onClick={() => setModalAbierto(true)}>
          Nuevo cliente
        </Button>
      </Group>

      <Paper withBorder p="md" mb="md">
        <Group>
          <TextInput
            placeholder="Buscar por nombre, apellido o documento…"
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
              <Table.Th>Documento</Table.Th>
              <Table.Th>Nombre</Table.Th>
              <Table.Th>Condición IVA</Table.Th>
              <Table.Th>Lista de precios</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {clientes.map((cliente) => (
              <Table.Tr key={cliente.id}>
                <Table.Td>{cliente.persona_detalle.documento_identidad}</Table.Td>
                <Table.Td>
                  {cliente.persona_detalle.apellido}, {cliente.persona_detalle.nombre}
                </Table.Td>
                <Table.Td>{cliente.condicion_iva_display}</Table.Td>
                <Table.Td>{cliente.lista_precio_nombre ?? '—'}</Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>

        {!cargando && clientes.length === 0 && (
          <EstadoVacio
            titulo="Sin resultados"
            descripcion={busquedaDebounced ? 'No se encontraron clientes para la búsqueda.' : 'Todavía no hay clientes cargados.'}
          />
        )}

        {total > CLIENTES_POR_PAGINA && (
          <Paginador pagina={pagina} porPagina={CLIENTES_POR_PAGINA} total={total} onCambiarPagina={setPagina} />
        )}
      </Paper>

      <ClienteFormModal opened={modalAbierto} onClose={() => setModalAbierto(false)} onGuardado={cargarClientes} />
    </Container>
  )
}
