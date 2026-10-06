import { type ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  ActionIcon,
  AppShell,
  Avatar,
  Burger,
  Group,
  Image,
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
  IconTrendingDown,
  IconTrendingUp,
  IconUser,
  IconUserPlus,
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
  /** Subtítulo opcional dentro del grupo (ej. "Ingresos"/"Egresos" dentro de "Caja") — se
   * muestra sólo cuando cambia respecto al ítem anterior, para agrupar visualmente sin abrir
   * un nuevo `titulo` de sección. */
  subgrupo?: string
  /** Codename Django que hace falta para ver este ítem en el menú (ej. "venta.add_venta" para
   * "Nueva venta") — ver ProtectedRoute.requierePermiso, que además bloquea la ruta en sí. Sin
   * esto el ítem siempre se muestra (igual que hasta ahora). */
  requierePermiso?: string
}

// Un permiso dedicado por sección entera (ver usuario.models.Usuario.Meta.permissions) —
// "puro", sin add_/change_/delete_ de ningún modelo real, así que ningún grupo lo tiene salvo
// que se lo asignen a mano desde /admin. El grupo "Acceso completo (staff)" los recibe todos
// automáticamente (ver usuario.permisos.sincronizar_grupo_acceso_completo); Cajeros/Vendedores
// (o cualquier otro grupo operativo) necesitan que un admin les tilde el que corresponda.
const GATE_DASHBOARD = 'usuario.ver_seccion_dashboard'
const GATE_CATALOGO = 'usuario.ver_seccion_catalogo'
const GATE_PERSONAL = 'usuario.ver_seccion_personal'
const GATE_PROMOCIONES = 'usuario.ver_seccion_promociones'
const GATE_CAJA = 'usuario.ver_seccion_caja'

const NAV: { titulo: string; items: ItemNav[] }[] = [
  {
    titulo: 'Inicio',
    items: [{ to: '/', label: 'Dashboard', icon: IconHome2, seccion: 'Inicio', requierePermiso: GATE_DASHBOARD }],
  },
  {
    titulo: 'Ventas',
    items: [
      {
        to: '/ventas/nueva',
        label: 'Nueva venta',
        icon: IconShoppingCart,
        seccion: 'Ventas',
        requierePermiso: 'venta.add_venta',
      },
      { to: '/ventas', label: 'Ventas', icon: IconReceipt2, seccion: 'Ventas' },
    ],
  },
  {
    titulo: 'Catálogo',
    items: [
      { to: '/articulos', label: 'Artículos', icon: IconBox, seccion: 'Catálogo', requierePermiso: GATE_CATALOGO },
      { to: '/articulos/precios', label: 'Precios', icon: IconTags, seccion: 'Catálogo', requierePermiso: GATE_CATALOGO },
      {
        to: '/articulos/categorias',
        label: 'Categorías',
        icon: IconCategory,
        seccion: 'Catálogo',
        requierePermiso: GATE_CATALOGO,
      },
      {
        to: '/articulos/listas-precio',
        label: 'Listas de precio',
        icon: IconListDetails,
        seccion: 'Catálogo',
        requierePermiso: GATE_CATALOGO,
      },
      {
        to: '/articulos/unidades-medida',
        label: 'Unidades de medida',
        icon: IconRuler,
        seccion: 'Catálogo',
        requierePermiso: GATE_CATALOGO,
      },
      {
        to: '/articulos/tipos-iva',
        label: 'Tipos de IVA',
        icon: IconPercentage,
        seccion: 'Catálogo',
        requierePermiso: GATE_CATALOGO,
      },
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
      { to: '/empleados', label: 'Empleados', icon: IconId, seccion: 'Personal', requierePermiso: GATE_PERSONAL },
      {
        to: '/empleados/sucursales',
        label: 'Sucursales',
        icon: IconMapPin,
        seccion: 'Personal',
        requierePermiso: GATE_PERSONAL,
      },
      {
        to: '/empleados/usuarios',
        label: 'Usuarios',
        icon: IconUserPlus,
        seccion: 'Personal',
        requierePermiso: GATE_PERSONAL,
      },
    ],
  },
  {
    titulo: 'Promociones',
    items: [
      {
        to: '/promociones',
        label: 'Promociones',
        icon: IconDiscount2,
        seccion: 'Promociones',
        requierePermiso: GATE_PROMOCIONES,
      },
      {
        to: '/promociones/descuentos',
        label: 'Descuentos',
        icon: IconGift,
        seccion: 'Promociones',
        requierePermiso: GATE_PROMOCIONES,
      },
    ],
  },
  {
    titulo: 'Caja',
    items: [
      { to: '/caja', label: 'Caja', icon: IconCash, seccion: 'Caja', requierePermiso: GATE_CAJA },
      {
        to: '/caja/ingresos',
        label: 'Ingresos varios',
        icon: IconTrendingUp,
        seccion: 'Caja',
        subgrupo: 'Ingresos',
        requierePermiso: GATE_CAJA,
      },
      {
        to: '/caja/sueldos',
        label: 'Sueldos',
        icon: IconTrendingDown,
        seccion: 'Caja',
        subgrupo: 'Egresos',
        requierePermiso: GATE_CAJA,
      },
      {
        to: '/caja/adelantos',
        label: 'Adelantos',
        icon: IconTrendingDown,
        seccion: 'Caja',
        subgrupo: 'Egresos',
        requierePermiso: GATE_CAJA,
      },
      {
        to: '/caja/retiros-efectivo',
        label: 'Retiros de efectivo',
        icon: IconTrendingDown,
        seccion: 'Caja',
        subgrupo: 'Egresos',
        requierePermiso: GATE_CAJA,
      },
      {
        to: '/caja/gastos',
        label: 'Gastos',
        icon: IconTrendingDown,
        seccion: 'Caja',
        subgrupo: 'Egresos',
        requierePermiso: GATE_CAJA,
      },
      { to: '/caja/tarjetas', label: 'Tarjetas', icon: IconCreditCard, seccion: 'Caja', requierePermiso: GATE_CAJA },
      {
        to: '/caja/planes-tarjeta',
        label: 'Planes de tarjeta',
        icon: IconListDetails,
        seccion: 'Caja',
        requierePermiso: GATE_CAJA,
      },
      {
        to: '/caja/tipos-ingreso',
        label: 'Tipos de ingreso',
        icon: IconTags,
        seccion: 'Caja',
        requierePermiso: GATE_CAJA,
      },
      {
        to: '/caja/tipos-gasto',
        label: 'Tipos de gasto',
        icon: IconTags,
        seccion: 'Caja',
        requierePermiso: GATE_CAJA,
      },
    ],
  },
]

const TODOS_LOS_ITEMS = NAV.flatMap((grupo) => grupo.items)

const NOMBRE_NEGOCIO = import.meta.env.VITE_BUSINESS_NAME || 'Sistema de Gestión'
const LOGO_URL = import.meta.env.VITE_LOGO_URL

export default function AppLayout({ children }: { children: ReactNode }) {
  const [opened, { toggle }] = useDisclosure()
  const { perfil, logout, tienePermiso } = useAuth()
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
            {LOGO_URL && <Image src={LOGO_URL} alt="" h={28} w="auto" fit="contain" />}
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
            {/* Nombre del negocio configurable por variable de entorno (VITE_BUSINESS_NAME, ver
             * frontend/.env.example) — así este sistema se puede reutilizar para otro negocio
             * sin tocar código. */}
            <Text fw={700} size="sm" style={{ lineHeight: 1.15 }}>
              {NOMBRE_NEGOCIO}
            </Text>
          </Group>
        </AppShell.Section>
        <AppShell.Section grow component={ScrollArea} px="sm">
          {NAV.map((grupo) => {
            const items = grupo.items.filter((item) => !item.requierePermiso || tienePermiso(item.requierePermiso))
            if (items.length === 0) return null
            return (
            <div key={grupo.titulo} style={{ marginBottom: 12 }}>
              <Text size="xs" fw={700} c="dimmed" tt="uppercase" px="xs" mb={4}>
                {grupo.titulo}
              </Text>
              {items.map((item, indice) => {
                const activo = location.pathname === item.to
                const IconItem = item.icon
                const mostrarSubgrupo = item.subgrupo && item.subgrupo !== items[indice - 1]?.subgrupo
                return (
                  <div key={item.to}>
                    {mostrarSubgrupo && (
                      <Text fz={10} fw={700} c="dimmed" tt="uppercase" px="xs" mt={6} mb={2}>
                        {item.subgrupo}
                      </Text>
                    )}
                    <UnstyledButton
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
                  </div>
                )
              })}
            </div>
            )
          })}
        </AppShell.Section>
      </AppShell.Navbar>

      <AppShell.Main bg="gray.0">{children}</AppShell.Main>
    </AppShell>
  )
}
