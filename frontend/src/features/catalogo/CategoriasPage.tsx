import { useEffect, useState } from 'react'
import { ActionIcon, Button, Group, Modal, Select, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconEdit } from '@tabler/icons-react'
import { actualizarCategoria, crearCategoria, listarCategorias, listarCategoriasPag, listarTodosLosTiposIva } from '../../api/articulo'
import { ApiError } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import ListaCrud from '../../components/ListaCrud'
import type { Categoria, CategoriaInput, TipoIva } from '../../types/articulo'

const VACIO: CategoriaInput = { nombre: '', nodo_padre: null, tipo_iva: 0 }

function CategoriaFormModal({
  opened,
  onClose,
  onGuardado,
  categoria,
  tiposIva,
  categorias,
}: {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
  categoria: Categoria | null
  tiposIva: TipoIva[]
  categorias: Categoria[]
}) {
  const form = useForm<CategoriaInput>({
    initialValues: VACIO,
    validate: { tipo_iva: (v) => (v ? null : 'Elegí un tipo de IVA') },
  })

  useEffect(() => {
    if (opened) {
      form.setValues(
        categoria
          ? { nombre: categoria.nombre, nodo_padre: categoria.nodo_padre, tipo_iva: categoria.tipo_iva }
          : VACIO,
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, categoria])

  const guardar = form.onSubmit(async (valores) => {
    try {
      if (categoria) await actualizarCategoria(categoria.id, valores)
      else await crearCategoria(valores)
      notifications.show({ message: 'Guardado.', color: 'green' })
      onGuardado()
      onClose()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo guardar', message: detalle, color: 'red' })
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title={categoria ? 'Editar categoría' : 'Nueva categoría'}>
      <form onSubmit={guardar}>
        <TextInput label="Nombre" withAsterisk placeholder="Ej: Carnes" {...form.getInputProps('nombre')} />
        <Select
          label="Tipo de IVA"
          withAsterisk
          mt="sm"
          data={tiposIva.map((t) => ({ value: String(t.id), label: `${t.nombre} (${t.porcentaje}%)` }))}
          value={form.values.tipo_iva ? String(form.values.tipo_iva) : null}
          onChange={(v) => form.setFieldValue('tipo_iva', v ? Number(v) : 0)}
          error={form.errors.tipo_iva}
        />
        <Select
          label="Categoría padre"
          description="Opcional — para armar subcategorías"
          mt="sm"
          clearable
          data={categorias.filter((c) => c.id !== categoria?.id).map((c) => ({ value: String(c.id), label: c.nombre }))}
          value={form.values.nodo_padre ? String(form.values.nodo_padre) : null}
          onChange={(v) => form.setFieldValue('nodo_padre', v ? Number(v) : null)}
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

export default function CategoriasPage() {
  const { perfil } = useAuth()
  const puedeEditar = perfil?.is_staff ?? false
  const [modalAbierto, setModalAbierto] = useState(false)
  const [editando, setEditando] = useState<Categoria | null>(null)
  const [recarga, setRecarga] = useState(0)
  const [tiposIva, setTiposIva] = useState<TipoIva[]>([])
  const [todasLasCategorias, setTodasLasCategorias] = useState<Categoria[]>([])

  useEffect(() => {
    listarTodosLosTiposIva()
      .then((r) => setTiposIva(r.results))
      .catch(() => notifications.show({ message: 'No se pudieron cargar los tipos de IVA.', color: 'red' }))
  }, [])

  useEffect(() => {
    listarCategorias()
      .then((r) => setTodasLasCategorias(r.results))
      .catch(() => notifications.show({ message: 'No se pudieron cargar las categorías.', color: 'red' }))
  }, [recarga])

  return (
    <>
      <ListaCrud<Categoria>
        titulo="Categorías"
        subtitulo="Clasificación de artículos, con su tipo de IVA"
        listar={listarCategoriasPag}
        clave={(c) => c.id}
        porPagina={10}
        buscarPlaceholder="Buscar por nombre…"
        puedeCrear={puedeEditar}
        nuevoLabel="Nueva categoría"
        onNuevo={() => {
          setEditando(null)
          setModalAbierto(true)
        }}
        disparadorRecarga={recarga}
        columnas={[
          { header: 'Nombre', render: (c) => c.nombre },
          { header: 'Tipo de IVA', render: (c) => c.tipo_iva_nombre },
        ]}
        accionesHeader={
          puedeEditar
            ? (c) => (
                <ActionIcon
                  variant="subtle"
                  aria-label="Editar"
                  onClick={() => {
                    setEditando(c)
                    setModalAbierto(true)
                  }}
                >
                  <IconEdit size={16} />
                </ActionIcon>
              )
            : undefined
        }
      />
      <CategoriaFormModal
        opened={modalAbierto}
        onClose={() => setModalAbierto(false)}
        onGuardado={() => setRecarga((n) => n + 1)}
        categoria={editando}
        tiposIva={tiposIva}
        categorias={todasLasCategorias}
      />
    </>
  )
}
