import { type ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  ActionIcon,
  AppShell,
  Avatar,
  Burger,
  Group,
  Menu,
  ScrollArea,
  Text,
  TextInput,
  UnstyledButton,
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import {
  IconBell,
  IconBox,
  IconBuildingStore,
  IconCash,
  IconCategory,
  IconChevronDown,
  IconCreditCard,
  IconDiscount2,
  IconGift,
  IconHome2,
  IconId,
  IconListDetails,
  IconLogout,
  IconMapPin,
  IconPercentage,
  IconReceipt2,
  IconRuler,
  IconSearch,
  IconShoppingCart,
  IconTags,
  IconUser,
  IconUsers,
  IconWallet,
  type Icon,
} from '@tabler/icons-react'
import { useAuth } from '../auth/AuthContext'

interface ItemNav {
  to: string
  label: string
  icon: Icon
  seccion: string
}

const NAV: { titulo: string; items: ItemNav[] }[] = [
  { titulo: 'Inicio', items: [{ to: '/', label: 'Dashboard', icon: IconHome2, seccion: 'Inicio' }] },
  {
    titulo: 'Ventas',
    items: [
      { to: '/ventas/nueva', label: 'Nueva venta', icon: IconShoppingCart, seccion: 'Ventas' },
      { to: '/ventas', label: 'Ventas', icon: IconReceipt2, seccion: 'Ventas' },
    ],
  },
  {
    titulo: 'Catálogo',
    items: [
      { to: '/articulos', label: 'Artículos', icon: IconBox, seccion: 'Catálogo' },
      { to: '/articulos/precios', label: 'Precios', icon: IconTags, seccion: 'Catálogo' },
      { to: '/articulos/categorias', label: 'Categorías', icon: IconCategory, seccion: 'Catálogo' },
      { to: '/articulos/listas-precio', label: 'Listas de precio', icon: IconListDetails, seccion: 'Catálogo' },
      { to: '/articulos/unidades-medida', label: 'Unidades de medida', icon: IconRuler, seccion: 'Catálogo' },
      { to: '/articulos/tipos-iva', label: 'Tipos de IVA', icon: IconPercentage, seccion: 'Catálogo' },
    ],
  },
  {
    titulo: 'Clientes',
    items: [
      { to: '/clientes', label: 'Clientes', icon: IconUsers, seccion: 'Clientes' },
      { to: '/clientes/cuentas-corrientes', label: 'Cuentas corrientes', icon: IconWallet, seccion: 'Clientes' },
    ],
  },
  {
    titulo: 'Personal',
    items: [
      { to: '/empleados', label: 'Empleados', icon: IconId, seccion: 'Personal' },
      { to: '/empleados/sucursales', label: 'Sucursales', icon: IconMapPin, seccion: 'Personal' },
    ],
  },
  {
    titulo: 'Promociones',
    items: [
      { to: '/promociones', label: 'Promociones', icon: IconDiscount2, seccion: 'Promociones' },
      { to: '/promociones/descuentos', label: 'Descuentos', icon: IconGift, seccion: 'Promociones' },
    ],
  },
  {
    titulo: 'Caja',
    items: [
      { to: '/caja', label: 'Caja', icon: IconCash, seccion: 'Caja' },
      { to: '/caja/tarjetas', label: 'Tarjetas', icon: IconCreditCard, seccion: 'Caja' },
      { to: '/caja/planes-tarjeta', label: 'Planes de tarjeta', icon: IconListDetails, seccion: 'Caja' },
    ],
  },
]

const TODOS_LOS_ITEMS = NAV.flatMap((grupo) => grupo.items)

export default function AppLayout({ children }: { children: ReactNode }) {
  const [opened, { toggle }] = useDisclosure()
  const { perfil, logout } = useAuth()
  const location = useLocation()

  const itemActual = TODOS_LOS_ITEMS.find((item) => item.to === location.pathname)
    ?? { label: 'Cobro', seccion: 'Ventas' } // /ventas/:id/cobrar no matchea exacto

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{ width: 240, breakpoint: 'sm', collapsed: { mobile: !opened } }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between" wrap="nowrap">
          <Group gap="xs" wrap="nowrap">
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            <div>
              <Text fw={700} size="sm" lh={1.1}>
                Sistema de Gestión
              </Text>
              <Text size="xs" c="dimmed" lh={1.1}>
                Inicio / {itemActual.seccion} / {itemActual.label}
              </Text>
            </div>
          </Group>

          <TextInput
            placeholder="Buscar…"
            leftSection={<IconSearch size={16} />}
            visibleFrom="sm"
            w={280}
            styles={{ input: { backgroundColor: 'var(--mantine-color-gray-0)' } }}
          />

          <Group gap="sm" wrap="nowrap">
            <ActionIcon variant="subtle" color="gray" size="lg" aria-label="Notificaciones">
              <IconBell size={20} />
            </ActionIcon>
            {perfil && (
              <Menu shadow="md" width={200} position="bottom-end">
                <Menu.Target>
                  <UnstyledButton>
                    <Group gap={6}>
                      <Avatar radius="xl" size={32} color="red">
                        <IconUser size={18} />
                      </Avatar>
                      <div style={{ lineHeight: 1.1 }}>
                        <Text size="xs" c="dimmed">
                          Bienvenido,
                        </Text>
                        <Text size="sm" fw={600}>
                          {perfil.first_name || perfil.username}
                        </Text>
                      </div>
                      <IconChevronDown size={14} />
                    </Group>
                  </UnstyledButton>
                </Menu.Target>
                <Menu.Dropdown>
                  <Menu.Label>{perfil.sucursal_nombre ?? 'Sin sucursal'}</Menu.Label>
                  <Menu.Item leftSection={<IconLogout size={16} />} onClick={() => void logout()}>
                    Cerrar sesión
                  </Menu.Item>
                </Menu.Dropdown>
              </Menu>
            )}
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar>
        <AppShell.Section p="md">
          <Group gap="xs" wrap="nowrap">
            <IconBuildingStore size={28} />
            <div style={{ lineHeight: 1.15 }}>
              <Text fw={700} size="sm">
                Carnicería
              </Text>
              <Text fw={700} size="sm" mt={-2}>
                Virgen del Valle
              </Text>
            </div>
          </Group>
        </AppShell.Section>
        <AppShell.Section grow component={ScrollArea} px="sm">
          {NAV.map((grupo) => (
            <div key={grupo.titulo} style={{ marginBottom: 12 }}>
              <Text size="xs" fw={700} c="dimmed" tt="uppercase" px="xs" mb={4}>
                {grupo.titulo}
              </Text>
              {grupo.items.map((item) => {
                const activo = location.pathname === item.to
                const IconItem = item.icon
                return (
                  <UnstyledButton
                    key={item.to}
                    component={Link}
                    to={item.to}
                    p="xs"
                    mb={2}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      width: '100%',
                      borderRadius: 6,
                      backgroundColor: activo ? 'var(--mantine-color-red-light)' : 'transparent',
                      color: activo ? 'var(--mantine-color-red-light-color)' : undefined,
                    }}
                  >
                    <IconItem size={18} />
                    <Text size="sm" fw={activo ? 600 : 400}>
                      {item.label}
                    </Text>
                  </UnstyledButton>
                )
              })}
            </div>
          ))}
        </AppShell.Section>
      </AppShell.Navbar>

      <AppShell.Main bg="gray.0">{children}</AppShell.Main>
    </AppShell>
  )
}
