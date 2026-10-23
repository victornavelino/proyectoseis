import { ActionIcon, Group, Text } from '@mantine/core'
import { IconChevronLeft, IconChevronRight } from '@tabler/icons-react'

interface Props {
  pagina: number
  porPagina: number
  total: number
  onCambiarPagina: (pagina: number) => void
}

/** Paginación simple estilo tabla de administración: "Mostrando X–Y de Z" + flechas. La API
 * (util.paginations.LargePagination) es `PageNumberPagination` estándar de DRF — params
 * `page`/`page_size`, respuesta `{count, next, previous, results}`. */
export default function Paginador({ pagina, porPagina, total, onCambiarPagina }: Props) {
  const totalPaginas = Math.max(1, Math.ceil(total / porPagina))
  const desde = total === 0 ? 0 : (pagina - 1) * porPagina + 1
  const hasta = Math.min(pagina * porPagina, total)

  return (
    <Group justify="space-between" mt="sm">
      <Text size="sm" c="dimmed">
        Mostrando {desde}–{hasta} de {total}
      </Text>
      <Group gap="xs">
        <Text size="sm" c="dimmed">
          Página {pagina} de {totalPaginas}
        </Text>
        <ActionIcon
          variant="default"
          disabled={pagina <= 1}
          onClick={() => onCambiarPagina(pagina - 1)}
          aria-label="Página anterior"
        >
          <IconChevronLeft size={16} />
        </ActionIcon>
        <ActionIcon
          variant="default"
          disabled={pagina >= totalPaginas}
          onClick={() => onCambiarPagina(pagina + 1)}
          aria-label="Página siguiente"
        >
          <IconChevronRight size={16} />
        </ActionIcon>
      </Group>
    </Group>
  )
}
