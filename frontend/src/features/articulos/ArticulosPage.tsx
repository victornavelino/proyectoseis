import { useEffect, useState } from 'react'
import { ActionIcon, Badge, Button, Container, Group, Paper, Table, Text, TextInput, Title } from '@mantine/core'
import { useDebouncedValue } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import { IconEdit, IconPlus, IconSearch, IconX } from '@tabler/icons-react'
import { ARTICULOS_POR_PAGINA, listarArticulos, listarCategorias, listarUnidadesMedida } from '../../api/articulo'
import { ApiError } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import EstadoVacio from '../../components/EstadoVacio'
import Paginador from '../../components/Paginador'
import type { Articulo, Categoria, UnidadMedida } from '../../types/articulo'
import ArticuloFormModal from './ArticuloFormModal'

export default function ArticulosPage() {
  const { perfil } = useAuth()
  const puedeEditar = perfil?.is_staff ?? false

  const [articulos, setArticulos] = useState<Articulo[]>([])
  const [total, setTotal] = useState(0)
  const [pagina, setPagina] = useState(1)
  const [categorias, setCategorias] = useState<Categoria[]>([])
  const [unidades, setUnidades] = useState<UnidadMedida[]>([])
  const [busqueda, setBusqueda] = useState('')
  const [busquedaDebounced] = useDebouncedValue(busqueda, 300)
  const [cargando, setCargando] = useState(true)
  const [modalAbierto, setModalAbierto] = useState(false)
  const [articuloEditando, setArticuloEditando] = useState<Articulo | null>(null)

  useEffect(() => {
    listarCategorias()
      .then((r) => setCategorias(r.results))
      .catch(() => notifications.show({ message: 'No se pudieron cargar las categorías.', color: 'red' }))
    listarUnidadesMedida()
      .then((r) => setUnidades(r.results))
      .catch(() => notifications.show({ message: 'No se pudieron cargar las unidades.', color: 'red' }))
  }, [])

  useEffect(() => {
    setPagina(1)
  }, [busquedaDebounced])

  const cargarArticulos = () => {
    setCargando(true)
    listarArticulos({ search: busquedaDebounced || undefined, pagina })
      .then((r) => {
        setArticulos(r.results)
        setTotal(r.count)
      })
      .catch((err: ApiError) => notifications.show({ title: 'Error', message: err.message, color: 'red' }))
      .finally(() => setCargando(false))
  }

  useEffect(cargarArticulos, [busquedaDebounced, pagina])

  const abrirNuevo = () => {
    setArticuloEditando(null)
    setModalAbierto(true)
  }

  const abrirEdicion = (articulo: Articulo) => {
    setArticuloEditando(articulo)
    setModalAbierto(true)
  }

  return (
    <Container size="lg" py="md">
      <Group justify="space-between" mb="md">
        <div>
          <Title order={2}>Artículos</Title>
          <Text c="dimmed" size="sm">
            Catálogo de productos de la carnicería
          </Text>
        </div>
        {puedeEditar && (
          <Button color="red" leftSection={<IconPlus size={16} />} onClick={abrirNuevo}>
            Nuevo artículo
          </Button>
        )}
      </Group>

      <Paper withBorder p="md" mb="md">
        <Group>
          <TextInput
            placeholder="Buscar por nombre, código o abreviatura…"
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
              <Table.Th>Código</Table.Th>
              <Table.Th>Nombre</Table.Th>
              <Table.Th>Categoría</Table.Th>
              <Table.Th>Unidad</Table.Th>
              <Table.Th>Por peso</Table.Th>
              {puedeEditar && <Table.Th />}
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {articulos.map((articulo) => (
              <Table.Tr key={articulo.id}>
                <Table.Td>{articulo.codigo}</Table.Td>
                <Table.Td>{articulo.nombre}</Table.Td>
                <Table.Td>{articulo.categoria_nombre}</Table.Td>
                <Table.Td>{articulo.unidad_medida_nombre}</Table.Td>
                <Table.Td>
                  <Badge color={articulo.es_por_peso ? 'blue' : 'gray'} variant="light">
                    {articulo.es_por_peso ? 'Sí' : 'No'}
                  </Badge>
                </Table.Td>
                {puedeEditar && (
                  <Table.Td>
                    <ActionIcon variant="subtle" onClick={() => abrirEdicion(articulo)} aria-label="Editar">
                      <IconEdit size={16} />
                    </ActionIcon>
                  </Table.Td>
                )}
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>

        {!cargando && articulos.length === 0 && (
          <EstadoVacio
            titulo="Sin resultados"
            descripcion={busquedaDebounced ? 'No se encontraron artículos para la búsqueda.' : 'Todavía no hay artículos cargados.'}
          />
        )}

        {total > ARTICULOS_POR_PAGINA && (
          <Paginador pagina={pagina} porPagina={ARTICULOS_POR_PAGINA} total={total} onCambiarPagina={setPagina} />
        )}
      </Paper>

      <ArticuloFormModal
        opened={modalAbierto}
        onClose={() => setModalAbierto(false)}
        onGuardado={cargarArticulos}
        articulo={articuloEditando}
        categorias={categorias}
        unidades={unidades}
      />
    </Container>
  )
}
