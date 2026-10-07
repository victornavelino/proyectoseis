import { Stack, Text } from '@mantine/core'
import { IconInbox } from '@tabler/icons-react'

export default function EstadoVacio({
  titulo = 'Sin resultados',
  descripcion,
}: {
  titulo?: string
  descripcion?: string
}) {
  return (
    <Stack align="center" py={48} gap={4}>
      <IconInbox size={40} stroke={1.5} color="var(--mantine-color-blue-5)" />
      <Text fw={600}>{titulo}</Text>
      {descripcion && (
        <Text size="sm" c="dimmed">
          {descripcion}
        </Text>
      )}
    </Stack>
  )
}
