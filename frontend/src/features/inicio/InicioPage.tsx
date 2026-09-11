import { useEffect, useState } from 'react'
import { Alert, Badge, Container, Divider, Grid, Group, Paper, SimpleGrid, Skeleton, Text, Title } from '@mantine/core'
import { BarChart, DonutChart, LineChart } from '@mantine/charts'
import { IconBox, IconReceipt2, IconShoppingCart, IconUsers, type Icon } from '@tabler/icons-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import { ApiError } from '../../api/client'
import { obtenerResumenDashboard } from '../../api/venta'
import type { ResumenDashboard } from '../../types/venta'
import { formatearMonto } from '../ventas/dinero'

const ACCESOS: { to: string; label: string; descripcion: string; icon: Icon }[] = [
  { to: '/ventas/nueva', label: 'Nueva venta', descripcion: 'Punto de venta', icon: IconShoppingCart },
  { to: '/ventas', label: 'Ventas', descripcion: 'Historial y cobros pendientes', icon: IconReceipt2 },
  { to: '/articulos', label: 'Artículos', descripcion: 'Catálogo de productos', icon: IconBox },
  { to: '/clientes', label: 'Clientes', descripcion: 'Registro de clientes', icon: IconUsers },
]

// Un color fijo por medio de pago (nunca reasignado según el monto) para que la torta de "Medios
// de pago" siempre pinte igual cada medio — ver dataviz skill: "color follows the entity, never
// its rank". Paleta categórica validada (CVD-safe) con scripts/validate_palette.js del skill.
const MEDIOS_PAGO_INFO: Record<ResumenDashboard['medios_pago'][number]['medio'], { etiqueta: string; color: string }> = {
  efectivo: { etiqueta: 'Efectivo', color: 'blue.6' },
  tarjeta: { etiqueta: 'Tarjeta', color: 'teal.6' },
  cuenta_corriente: { etiqueta: 'Cuenta corriente', color: 'orange.7' },
  transferencia: { etiqueta: 'Transferencia', color: 'grape.6' },
}

/** "2026-08-29" -> "29/08", para no saturar el eje X del gráfico de evolución. */
function formatearFechaCorta(fechaIso: string) {
  const [, mes, dia] = fechaIso.split('-')
  return `${dia}/${mes}`
}

export default function InicioPage() {
  const { perfil } = useAuth()
  const [resumen, setResumen] = useState<ResumenDashboard | null>(null)
  const [cargandoResumen, setCargandoResumen] = useState(true)
  const [errorResumen, setErrorResumen] = useState<string | null>(null)

  useEffect(() => {
    obtenerResumenDashboard()
      .then(setResumen)
      .catch((err: unknown) => {
        const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
        setErrorResumen(detalle)
      })
      .finally(() => setCargandoResumen(false))
  }, [])

  const datosVentasPorDia = (resumen?.ventas_por_dia ?? []).map((f) => ({
    fecha: formatearFechaCorta(f.fecha),
    Ventas: Number(f.total),
  }))
  const hayVentasEnElPeriodo = datosVentasPorDia.some((f) => f.Ventas > 0)

  const datosTopArticulos = (resumen?.top_articulos ?? []).map((a) => ({
    nombre: a.nombre,
    Vendido: Number(a.total),
  }))

  const datosMediosPago = (resumen?.medios_pago ?? [])
    .filter((m) => Number(m.total) > 0)
    .map((m) => ({
      name: MEDIOS_PAGO_INFO[m.medio].etiqueta,
      value: Number(m.total),
      color: MEDIOS_PAGO_INFO[m.medio].color,
    }))

  return (
    <Container size="lg" py="md">
      <Title order={2}>Hola, {perfil?.first_name || perfil?.username}</Title>
      <Text c="dimmed" size="sm" mb="xl">
        {perfil?.sucursal_nombre ?? 'Sin sucursal asignada'}
      </Text>

      <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }} mb="xl">
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

      <Divider label="Resumen" labelPosition="left" mb="md" />

      {errorResumen && (
        <Alert color="red" mb="md" title="No se pudo cargar el resumen">
          {errorResumen}
        </Alert>
      )}

      <SimpleGrid cols={{ base: 1, sm: 3 }} mb="lg">
        <Paper withBorder p="md">
          <Text size="sm" c="dimmed">
            Ventas de hoy
          </Text>
          {cargandoResumen ? (
            <Skeleton h={32} mt={6} />
          ) : (
            <>
              <Text fz={28} fw={800}>
                {formatearMonto(resumen?.hoy.total ?? '0')}
              </Text>
              <Text size="xs" c="dimmed">
                {resumen?.hoy.cantidad_tickets ?? 0} ticket(s)
              </Text>
            </>
          )}
        </Paper>

        <Paper withBorder p="md">
          <Text size="sm" c="dimmed">
            Ticket promedio (hoy)
          </Text>
          {cargandoResumen ? <Skeleton h={32} mt={6} /> : <Text fz={28} fw={800}>{formatearMonto(resumen?.hoy.ticket_promedio ?? '0')}</Text>}
        </Paper>

        <Paper withBorder p="md">
          <Text size="sm" c="dimmed">
            Caja
          </Text>
          {cargandoResumen ? (
            <Skeleton h={32} mt={6} />
          ) : resumen?.caja.abierta ? (
            <Group gap="xs" align="baseline">
              <Text fz={28} fw={800}>
                {formatearMonto(resumen.caja.saldo)}
              </Text>
              <Badge color="green" variant="light">
                Abierta
              </Badge>
            </Group>
          ) : (
            <Group mt={6}>
              <Badge color="gray" variant="light" size="lg">
                Cerrada
              </Badge>
            </Group>
          )}
        </Paper>
      </SimpleGrid>

      <Grid>
        <Grid.Col span={{ base: 12, md: 7 }}>
          <Paper withBorder p="md" h="100%">
            <Text fw={600} size="sm" mb="sm">
              Ventas de los últimos {resumen?.ventas_por_dia.length ?? 14} días
            </Text>
            {cargandoResumen ? (
              <Skeleton h={220} />
            ) : !hayVentasEnElPeriodo ? (
              <Text c="dimmed" size="sm" py="xl" ta="center">
                Todavía no hay ventas registradas en este período.
              </Text>
            ) : (
              <LineChart
                h={220}
                data={datosVentasPorDia}
                dataKey="fecha"
                series={[{ name: 'Ventas', color: 'red.6' }]}
                curveType="linear"
                withDots={datosVentasPorDia.length <= 31}
                valueFormatter={(v) => formatearMonto(v)}
              />
            )}
          </Paper>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 5 }}>
          <Paper withBorder p="md" h="100%">
            <Text fw={600} size="sm" mb="sm">
              Medios de pago
            </Text>
            {cargandoResumen ? (
              <Skeleton h={220} />
            ) : datosMediosPago.length === 0 ? (
              <Text c="dimmed" size="sm" py="xl" ta="center">
                Todavía no hay cobros registrados en este período.
              </Text>
            ) : (
              <DonutChart
                h={220}
                data={datosMediosPago}
                withLabels
                withLegend
                labelsType="percent"
                valueFormatter={(v) => formatearMonto(v)}
              />
            )}
          </Paper>
        </Grid.Col>

        <Grid.Col span={12}>
          <Paper withBorder p="md">
            <Text fw={600} size="sm" mb="sm">
              Cortes más vendidos
            </Text>
            {cargandoResumen ? (
              <Skeleton h={260} />
            ) : datosTopArticulos.length === 0 ? (
              <Text c="dimmed" size="sm" py="xl" ta="center">
                Todavía no hay artículos vendidos en este período.
              </Text>
            ) : (
              <BarChart
                h={Math.max(180, datosTopArticulos.length * 36)}
                data={datosTopArticulos}
                dataKey="nombre"
                series={[{ name: 'Vendido', color: 'red.6' }]}
                orientation="vertical"
                valueFormatter={(v) => formatearMonto(v)}
              />
            )}
          </Paper>
        </Grid.Col>
      </Grid>
    </Container>
  )
}
