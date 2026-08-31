import { useEffect, useState, type ReactNode } from 'react'
import { Button, Container, Group, Paper, Table, Text, TextInput, Title } from '@mantine/core'
import { useDebouncedValue } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import { IconPlus, IconSearch, IconX } from '@tabler/icons-react'
import { ApiError } from '../api/client'
import type { PaginatedResponse } from '../types/api'
import EstadoVacio from './EstadoVacio'
import Paginador from './Paginador'

export interface Columna<T> {
  header: string
  render: (item: T) => ReactNode
}

interface Props<T> {
  titulo: string
  subtitulo?: string
  listar: (opts: { search?: string; pagina: number }) => Promise<PaginatedResponse<T>>
  columnas: Columna<T>[]
  clave: (item: T) => number | string
  porPagina: number
  buscarPlaceholder?: string
  sinBuscador?: boolean
  puedeCrear?: boolean
  nuevoLabel?: string
  onNuevo?: () => void
  accionesHeader?: (item: T) => ReactNode
  /** Cambiar este número (ej. incrementar un contador) fuerza un refetch — usarlo después de
   * guardar/editar/borrar algo desde un modal externo. */
  disparadorRecarga?: number
}

/** Patrón de listado compartido por todas las pantallas de catálogo/administración: título +
 * subtítulo, tarjeta de filtros (buscador + limpiar), tarjeta de tabla con contador de
 * registros + estado vacío + paginación real (DRF `PageNumberPagination`). Evita repetir este
 * shell en cada dominio — sólo cambian las columnas y el formulario de alta/edición. */
export default function ListaCrud<T>({
  titulo,
  subtitulo,
  listar,
  columnas,
  clave,
  porPagina,
  buscarPlaceholder = 'Buscar…',
  sinBuscador = false,
  puedeCrear = false,
  nuevoLabel = 'Nuevo',
  onNuevo,
  accionesHeader,
  disparadorRecarga = 0,
}: Props<T>) {
  const [items, setItems] = useState<T[]>([])
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
    listar({ search: busquedaDebounced || undefined, pagina })
      .then((r) => {
        setItems(r.results)
        setTotal(r.count)
      })
      .catch((err: ApiError) => notifications.show({ title: 'Error', message: err.message, color: 'red' }))
      .finally(() => setCargando(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [busquedaDebounced, pagina, disparadorRecarga])

  return (
    <Container size="lg" py="md">
      <Group justify="space-between" mb="md">
        <div>
          <Title order={2}>{titulo}</Title>
          {subtitulo && (
            <Text c="dimmed" size="sm">
              {subtitulo}
            </Text>
          )}
        </div>
        {puedeCrear && (
          <Button color="red" leftSection={<IconPlus size={16} />} onClick={onNuevo}>
            {nuevoLabel}
          </Button>
        )}
      </Group>

      {!sinBuscador && (
        <Paper withBorder p="md" mb="md">
          <Group>
            <TextInput
              placeholder={buscarPlaceholder}
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
      )}

      <Paper withBorder p="md">
        <Text size="sm" c="dimmed" mb="sm">
          {total} registro{total === 1 ? '' : 's'}
        </Text>

        <Table striped highlightOnHover verticalSpacing="sm">
          <Table.Thead>
            <Table.Tr>
              {columnas.map((col) => (
                <Table.Th key={col.header}>{col.header}</Table.Th>
              ))}
              {accionesHeader && <Table.Th />}
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {items.map((item) => (
              <Table.Tr key={clave(item)}>
                {columnas.map((col) => (
                  <Table.Td key={col.header}>{col.render(item)}</Table.Td>
                ))}
                {accionesHeader && <Table.Td>{accionesHeader(item)}</Table.Td>}
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>

        {!cargando && items.length === 0 && (
          <EstadoVacio descripcion={busquedaDebounced ? 'No se encontraron resultados para la búsqueda.' : undefined} />
        )}

        {total > porPagina && <Paginador pagina={pagina} porPagina={porPagina} total={total} onCambiarPagina={setPagina} />}
      </Paper>
    </Container>
  )
}
