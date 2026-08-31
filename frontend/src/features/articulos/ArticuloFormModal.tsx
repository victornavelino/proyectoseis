import { useEffect } from 'react'
import { Button, Group, Modal, Select, Switch, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { actualizarArticulo, crearArticulo } from '../../api/articulo'
import { ApiError } from '../../api/client'
import type { Articulo, ArticuloInput, Categoria, UnidadMedida } from '../../types/articulo'

interface Props {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
  articulo: Articulo | null
  categorias: Categoria[]
  unidades: UnidadMedida[]
}

const VALORES_VACIOS: ArticuloInput = {
  nombre: '',
  abreviatura: '',
  codigo: '',
  categoria: 0,
  unidad_medida: 0,
  es_por_peso: true,
}

export default function ArticuloFormModal({ opened, onClose, onGuardado, articulo, categorias, unidades }: Props) {
  const form = useForm<ArticuloInput>({
    initialValues: VALORES_VACIOS,
    validate: {
      nombre: (v) => (v.trim() ? null : 'Requerido'),
      codigo: (v) => (v.trim() ? null : 'Requerido'),
      categoria: (v) => (v ? null : 'Elegí una categoría'),
      unidad_medida: (v) => (v ? null : 'Elegí una unidad'),
    },
  })

  useEffect(() => {
    if (opened) {
      form.setValues(
        articulo
          ? {
              nombre: articulo.nombre,
              abreviatura: articulo.abreviatura,
              codigo: articulo.codigo,
              categoria: articulo.categoria,
              unidad_medida: articulo.unidad_medida,
              es_por_peso: articulo.es_por_peso,
            }
          : VALORES_VACIOS,
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, articulo])

  const guardar = form.onSubmit(async (valores) => {
    try {
      if (articulo) {
        await actualizarArticulo(articulo.id, valores)
        notifications.show({ message: 'Artículo actualizado.', color: 'green' })
      } else {
        await crearArticulo(valores)
        notifications.show({ message: 'Artículo creado.', color: 'green' })
      }
      onGuardado()
      onClose()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo guardar', message: detalle, color: 'red' })
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title={articulo ? 'Editar artículo' : 'Nuevo artículo'}>
      <form onSubmit={guardar}>
        <TextInput label="Nombre" withAsterisk {...form.getInputProps('nombre')} />
        <TextInput label="Abreviatura" mt="sm" {...form.getInputProps('abreviatura')} />
        <TextInput label="Código de barras" withAsterisk mt="sm" {...form.getInputProps('codigo')} />
        <Select
          label="Categoría"
          withAsterisk
          mt="sm"
          data={categorias.map((c) => ({ value: String(c.id), label: c.nombre }))}
          value={form.values.categoria ? String(form.values.categoria) : null}
          onChange={(v) => form.setFieldValue('categoria', v ? Number(v) : 0)}
          error={form.errors.categoria}
        />
        <Select
          label="Unidad de medida"
          withAsterisk
          mt="sm"
          data={unidades.map((u) => ({ value: String(u.id), label: `${u.nombre} (${u.abreviatura})` }))}
          value={form.values.unidad_medida ? String(form.values.unidad_medida) : null}
          onChange={(v) => form.setFieldValue('unidad_medida', v ? Number(v) : 0)}
          error={form.errors.unidad_medida}
        />
        <Switch label="Se vende por peso" mt="md" {...form.getInputProps('es_por_peso', { type: 'checkbox' })} />
        <Group justify="flex-end" mt="lg">
          <Button variant="default" onClick={onClose} type="button">
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
