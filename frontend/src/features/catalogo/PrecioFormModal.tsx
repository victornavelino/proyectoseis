import { useEffect, useState } from 'react'
import { Button, Group, Modal, NumberInput, Select, Text } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { actualizarPrecio, crearPrecio, listarArticulos } from '../../api/articulo'
import { listarTodasLasSucursales } from '../../api/empleado'
import { ApiError } from '../../api/client'
import BuscadorLista from '../../components/BuscadorLista'
import type { Articulo, ListaPrecio, Precio, PrecioInput } from '../../types/articulo'
import type { Sucursal } from '../../types/empleado'

interface Props {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
  precio: Precio | null
  listasPrecio: ListaPrecio[]
}

export default function PrecioFormModal({ opened, onClose, onGuardado, precio, listasPrecio }: Props) {
  const [sucursales, setSucursales] = useState<Sucursal[]>([])
  const [articuloElegido, setArticuloElegido] = useState<{ id: number; nombre: string; codigo: string } | null>(null)

  const form = useForm<PrecioInput>({
    initialValues: { articulo: 0, sucursal: 0, lista_precio: 0, precio: '' },
    validate: {
      sucursal: (v) => (v ? null : 'Elegí una sucursal'),
      lista_precio: (v) => (v ? null : 'Elegí una lista'),
      precio: (v) => (Number(v) > 0 ? null : 'Ingresá un precio válido'),
    },
  })

  useEffect(() => {
    if (opened) {
      listarTodasLasSucursales()
        .then((r) => setSucursales(r.results))
        .catch(() => notifications.show({ message: 'No se pudieron cargar las sucursales.', color: 'red' }))
      if (precio) {
        form.setValues({
          articulo: precio.articulo,
          sucursal: precio.sucursal,
          lista_precio: precio.lista_precio,
          precio: precio.precio,
        })
        setArticuloElegido({ id: precio.articulo, nombre: precio.articulo_nombre, codigo: precio.articulo_codigo })
      } else {
        form.setValues({ articulo: 0, sucursal: 0, lista_precio: 0, precio: '' })
        setArticuloElegido(null)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, precio])

  const guardar = form.onSubmit(async (valores) => {
    if (!valores.articulo) {
      notifications.show({ title: 'Falta el artículo', message: 'Elegí un artículo primero.', color: 'red' })
      return
    }
    try {
      if (precio) await actualizarPrecio(precio.id, valores)
      else await crearPrecio(valores)
      notifications.show({ message: 'Guardado.', color: 'green' })
      onGuardado()
      onClose()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo guardar', message: detalle, color: 'red' })
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title={precio ? 'Editar precio' : 'Nuevo precio'}>
      <form onSubmit={guardar}>
        <Text size="sm" fw={500} mb={4}>
          Artículo
        </Text>
        {precio ? (
          <Text size="sm">
            {precio.articulo_nombre} ({precio.articulo_codigo})
          </Text>
        ) : articuloElegido ? (
          <Group justify="space-between">
            <Text size="sm">
              {articuloElegido.nombre} ({articuloElegido.codigo})
            </Text>
            <Button
              size="xs"
              variant="subtle"
              type="button"
              onClick={() => {
                setArticuloElegido(null)
                form.setFieldValue('articulo', 0)
              }}
            >
              Cambiar
            </Button>
          </Group>
        ) : (
          <BuscadorLista<Articulo>
            placeholder="Buscar artículo…"
            buscar={(q) => listarArticulos({ search: q }).then((r) => r.results)}
            clave={(a) => a.id}
            onSeleccionar={(a) => {
              setArticuloElegido({ id: a.id, nombre: a.nombre, codigo: a.codigo })
              form.setFieldValue('articulo', a.id)
            }}
            renderItem={(a) => (
              <Text size="sm">
                {a.nombre} ({a.codigo})
              </Text>
            )}
          />
        )}

        <Select
          label="Sucursal"
          withAsterisk
          mt="sm"
          data={sucursales.map((s) => ({ value: String(s.id), label: s.nombre }))}
          value={form.values.sucursal ? String(form.values.sucursal) : null}
          onChange={(v) => form.setFieldValue('sucursal', v ? Number(v) : 0)}
          error={form.errors.sucursal}
        />
        <Select
          label="Lista de precios"
          withAsterisk
          mt="sm"
          data={listasPrecio.map((l) => ({ value: String(l.id), label: l.nombre }))}
          value={form.values.lista_precio ? String(form.values.lista_precio) : null}
          onChange={(v) => form.setFieldValue('lista_precio', v ? Number(v) : 0)}
          error={form.errors.lista_precio}
        />
        <NumberInput
          label="Precio"
          withAsterisk
          mt="sm"
          decimalScale={2}
          min={0}
          value={form.values.precio}
          onChange={(v) => form.setFieldValue('precio', String(v))}
          error={form.errors.precio}
        />

        <Group justify="flex-end" mt="lg">
          <Button variant="default" type="button" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" color="red">
            Guardar
          </Button>
        </Group>
      </form>
    </Modal>
  )
}
