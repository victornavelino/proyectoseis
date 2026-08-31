import { useEffect, useState } from 'react'
import {
  ActionIcon,
  Alert,
  Button,
  Checkbox,
  Divider,
  Group,
  Modal,
  NumberInput,
  Select,
  Stack,
  Switch,
  Table,
  Text,
  Textarea,
  TextInput,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconTrash } from '@tabler/icons-react'
import {
  actualizarDiasSemana,
  actualizarPromocion,
  crearDiasSemana,
  crearPromocion,
  crearPromocionArticulo,
  eliminarPromocionArticulo,
} from '../../api/promocion'
import { listarArticulos } from '../../api/articulo'
import { ApiError } from '../../api/client'
import BuscadorLista from '../../components/BuscadorLista'
import type { Sucursal } from '../../types/empleado'
import type { Articulo } from '../../types/articulo'
import type { Promocion } from '../../types/promocion'
import { formatearMonto } from '../ventas/dinero'

interface Props {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
  promocion: Promocion | null
  sucursales: Sucursal[]
}

interface FormValores {
  nombre: string
  fecha_inicio: string
  fecha_fin: string
  es_por_precio: boolean
  porcentaje_todos: string
  habilitada: boolean
  prioridad: number
  sucursal: number | null
  observaciones: string
  lunes: boolean
  martes: boolean
  miercoles: boolean
  jueves: boolean
  viernes: boolean
  sabado: boolean
  domingo: boolean
}

const VACIO: FormValores = {
  nombre: '',
  fecha_inicio: '',
  fecha_fin: '',
  es_por_precio: false,
  porcentaje_todos: '',
  habilitada: false,
  prioridad: 10,
  sucursal: null,
  observaciones: '',
  lunes: true,
  martes: true,
  miercoles: true,
  jueves: true,
  viernes: true,
  sabado: true,
  domingo: true,
}

const DIAS: { campo: keyof FormValores; label: string }[] = [
  { campo: 'lunes', label: 'Lun' },
  { campo: 'martes', label: 'Mar' },
  { campo: 'miercoles', label: 'Mié' },
  { campo: 'jueves', label: 'Jue' },
  { campo: 'viernes', label: 'Vie' },
  { campo: 'sabado', label: 'Sáb' },
  { campo: 'domingo', label: 'Dom' },
]

export default function PromocionFormModal({ opened, onClose, onGuardado, promocion, sucursales }: Props) {
  const [guardando, setGuardando] = useState(false)

  const form = useForm<FormValores>({
    initialValues: VACIO,
    validate: {
      nombre: (v) => (v.trim() ? null : 'Requerido'),
      fecha_inicio: (v) => (v ? null : 'Requerido'),
      fecha_fin: (v) => (v ? null : 'Requerido'),
      sucursal: (v) => (v ? null : 'Elegí una sucursal'),
      prioridad: (v) => (v >= 1 && v <= 10 ? null : 'Entre 1 y 10'),
      porcentaje_todos: (v, valores) => (!valores.es_por_precio && !v ? 'Requerido si no es por precio' : null),
    },
  })

  useEffect(() => {
    if (opened) {
      if (promocion) {
        const d = promocion.dias_semana_detalle
        form.setValues({
          nombre: promocion.nombre,
          fecha_inicio: promocion.fecha_inicio,
          fecha_fin: promocion.fecha_fin,
          es_por_precio: promocion.es_por_precio,
          porcentaje_todos: promocion.porcentaje_todos ?? '',
          habilitada: promocion.habilitada,
          prioridad: promocion.prioridad,
          sucursal: promocion.sucursal,
          observaciones: promocion.observaciones ?? '',
          lunes: d.lunes,
          martes: d.martes,
          miercoles: d.miercoles,
          jueves: d.jueves,
          viernes: d.viernes,
          sabado: d.sabado,
          domingo: d.domingo,
        })
      } else {
        form.setValues(VACIO)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, promocion])

  const guardar = form.onSubmit(async (valores) => {
    setGuardando(true)
    try {
      const diasPayload = {
        lunes: valores.lunes,
        martes: valores.martes,
        miercoles: valores.miercoles,
        jueves: valores.jueves,
        viernes: valores.viernes,
        sabado: valores.sabado,
        domingo: valores.domingo,
      }
      const diasId = promocion
        ? (await actualizarDiasSemana(promocion.dias_semana_detalle.id, diasPayload)).id
        : (await crearDiasSemana(diasPayload)).id

      const datosPromocion = {
        nombre: valores.nombre,
        fecha_inicio: valores.fecha_inicio,
        fecha_fin: valores.fecha_fin,
        es_por_precio: valores.es_por_precio,
        porcentaje_todos: valores.es_por_precio ? null : valores.porcentaje_todos,
        dias_semana: diasId,
        habilitada: valores.habilitada,
        prioridad: valores.prioridad,
        sucursal: valores.sucursal,
        observaciones: valores.observaciones || null,
      }

      if (promocion) await actualizarPromocion(promocion.id, datosPromocion)
      else await crearPromocion(datosPromocion)

      notifications.show({ message: 'Guardado.', color: 'green' })
      onGuardado()
      onClose()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo guardar', message: detalle, color: 'red' })
    } finally {
      setGuardando(false)
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title={promocion ? 'Editar promoción' : 'Nueva promoción'} size="lg">
      <form onSubmit={guardar}>
        <TextInput label="Nombre" withAsterisk {...form.getInputProps('nombre')} />
        <Group grow mt="sm">
          <TextInput label="Fecha inicio" type="date" withAsterisk {...form.getInputProps('fecha_inicio')} />
          <TextInput label="Fecha fin" type="date" withAsterisk {...form.getInputProps('fecha_fin')} />
        </Group>

        <Text size="sm" fw={500} mt="sm" mb={4}>
          Días de vigencia
        </Text>
        <Group gap="xs">
          {DIAS.map((dia) => (
            <Checkbox
              key={dia.campo}
              label={dia.label}
              checked={form.values[dia.campo] as boolean}
              onChange={(e) => form.setFieldValue(dia.campo, e.currentTarget.checked)}
            />
          ))}
        </Group>

        <Group grow mt="sm">
          <Select
            label="Sucursal"
            withAsterisk
            data={sucursales.map((s) => ({ value: String(s.id), label: s.nombre }))}
            value={form.values.sucursal ? String(form.values.sucursal) : null}
            onChange={(v) => form.setFieldValue('sucursal', v ? Number(v) : null)}
            error={form.errors.sucursal}
          />
          <NumberInput
            label="Prioridad"
            description="1 (más alta) a 10"
            withAsterisk
            min={1}
            max={10}
            value={form.values.prioridad}
            onChange={(v) => form.setFieldValue('prioridad', Number(v))}
            error={form.errors.prioridad}
          />
        </Group>

        <Switch
          label="Por precio fijo (en vez de % sobre todos los artículos)"
          mt="md"
          checked={form.values.es_por_precio}
          onChange={(e) => form.setFieldValue('es_por_precio', e.currentTarget.checked)}
        />

        {!form.values.es_por_precio && (
          <NumberInput
            label="Porcentaje de descuento"
            withAsterisk
            mt="sm"
            suffix="%"
            min={0}
            max={100}
            value={form.values.porcentaje_todos}
            onChange={(v) => form.setFieldValue('porcentaje_todos', String(v))}
            error={form.errors.porcentaje_todos}
          />
        )}

        <Switch
          label="Habilitada"
          mt="md"
          checked={form.values.habilitada}
          onChange={(e) => form.setFieldValue('habilitada', e.currentTarget.checked)}
        />

        <Textarea label="Observaciones" mt="sm" {...form.getInputProps('observaciones')} />

        {form.values.es_por_precio && !promocion && (
          <Alert color="blue" mt="md">
            Guardá la promoción primero; después volvé a abrirla para agregar los artículos con
            precio fijo.
          </Alert>
        )}
        {form.values.es_por_precio && promocion && (
          <ArticulosDePromocion promocionId={promocion.id} articulos={promocion.articulos} onCambio={onGuardado} />
        )}

        <Group justify="flex-end" mt="lg">
          <Button variant="default" type="button" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" color="red" loading={guardando}>
            Guardar
          </Button>
        </Group>
      </form>
    </Modal>
  )
}

function ArticulosDePromocion({
  promocionId,
  articulos,
  onCambio,
}: {
  promocionId: number
  articulos: Promocion['articulos']
  onCambio: () => void
}) {
  const [agregando, setAgregando] = useState(false)
  // Estado local para que la tabla se actualice al instante dentro del modal (el `articulos`
  // que llega por props sólo se refresca cuando se vuelve a abrir el modal, ver
  // PromocionesPage.tsx: `onGuardado` recarga la tabla de fondo, no este prop).
  const [items, setItems] = useState(articulos)

  const agregar = async (articulo: Articulo, valor: string) => {
    try {
      const nuevo = await crearPromocionArticulo({ promocion: promocionId, articulo: articulo.id, valor })
      setItems((actual) => [...actual, nuevo])
      notifications.show({ message: 'Artículo agregado.', color: 'green' })
      onCambio()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo agregar', message: detalle, color: 'red' })
    }
  }

  const quitar = async (id: number) => {
    try {
      await eliminarPromocionArticulo(id)
      setItems((actual) => actual.filter((pa) => pa.id !== id))
      onCambio()
    } catch (err) {
      notifications.show({ title: 'No se pudo quitar', message: (err as Error).message, color: 'red' })
    }
  }

  return (
    <>
      <Divider my="md" label="Artículos con precio fijo" labelPosition="center" />
      <Table verticalSpacing="xs">
        <Table.Tbody>
          {items.map((pa) => (
            <Table.Tr key={pa.id}>
              <Table.Td>
                {pa.articulo_nombre} ({pa.articulo_codigo})
              </Table.Td>
              <Table.Td>{formatearMonto(pa.valor)}</Table.Td>
              <Table.Td>
                <ActionIcon color="red" variant="subtle" onClick={() => void quitar(pa.id)} aria-label="Quitar">
                  <IconTrash size={16} />
                </ActionIcon>
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>

      {agregando ? (
        <NuevoArticuloPromo onAgregar={agregar} onCancelar={() => setAgregando(false)} />
      ) : (
        <Button variant="light" size="xs" mt="xs" onClick={() => setAgregando(true)}>
          + Agregar artículo
        </Button>
      )}
    </>
  )
}

function NuevoArticuloPromo({
  onAgregar,
  onCancelar,
}: {
  onAgregar: (articulo: Articulo, valor: string) => void
  onCancelar: () => void
}) {
  const [articulo, setArticulo] = useState<Articulo | null>(null)
  const [valor, setValor] = useState('')

  return (
    <Stack gap="xs" mt="xs">
      {articulo ? (
        <Group justify="space-between">
          <Text size="sm">{articulo.nombre}</Text>
          <Button size="xs" variant="subtle" onClick={() => setArticulo(null)}>
            Cambiar
          </Button>
        </Group>
      ) : (
        <BuscadorLista<Articulo>
          placeholder="Buscar artículo…"
          buscar={(q) => listarArticulos({ search: q }).then((r) => r.results)}
          clave={(a) => a.id}
          onSeleccionar={setArticulo}
          renderItem={(a) => <Text size="sm">{a.nombre}</Text>}
        />
      )}
      <Group>
        <NumberInput
          placeholder="Precio fijo"
          decimalScale={2}
          min={0}
          value={valor}
          onChange={(v) => setValor(String(v))}
          style={{ flex: 1 }}
        />
        <Button
          size="xs"
          disabled={!articulo || !valor}
          onClick={() => {
            if (articulo) {
              onAgregar(articulo, valor)
              setArticulo(null)
              setValor('')
              onCancelar()
            }
          }}
        >
          Agregar
        </Button>
        <Button size="xs" variant="subtle" color="gray" onClick={onCancelar}>
          Cancelar
        </Button>
      </Group>
    </Stack>
  )
}
