import { Container, Paper, SimpleGrid, Text, Title } from '@mantine/core'
import { IconBox, IconReceipt2, IconShoppingCart, IconUsers, type Icon } from '@tabler/icons-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'

const ACCESOS: { to: string; label: string; descripcion: string; icon: Icon }[] = [
  { to: '/ventas/nueva', label: 'Nueva venta', descripcion: 'Punto de venta', icon: IconShoppingCart },
  { to: '/ventas', label: 'Ventas', descripcion: 'Historial y cobros pendientes', icon: IconReceipt2 },
  { to: '/articulos', label: 'Artículos', descripcion: 'Catálogo de productos', icon: IconBox },
  { to: '/clientes', label: 'Clientes', descripcion: 'Registro de clientes', icon: IconUsers },
]

export default function InicioPage() {
  const { perfil } = useAuth()

  return (
    <Container size="lg" py="md">
      <Title order={2}>Hola, {perfil?.first_name || perfil?.username}</Title>
      <Text c="dimmed" size="sm" mb="xl">
        {perfil?.sucursal_nombre ?? 'Sin sucursal asignada'}
      </Text>

      <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }}>
        {ACCESOS.map((acceso) => {
          const IconAcceso = acceso.icon
          return (
            <Paper
              key={acceso.to}
              withBorder
              component={Link}
              to={acceso.to}
              p="lg"
              style={{ textDecoration: 'none', color: 'inherit' }}
            >
              <IconAcceso size={28} color="var(--mantine-color-red-6)" />
              <Text fw={600} mt="sm">
                {acceso.label}
              </Text>
              <Text size="xs" c="dimmed">
                {acceso.descripcion}
              </Text>
            </Paper>
          )
        })}
      </SimpleGrid>
    </Container>
  )
}
