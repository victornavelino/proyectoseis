import { useEffect, useState } from 'react'
import { ActionIcon, Button, Group, Modal, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconEdit } from '@tabler/icons-react'
import { actualizarListaPrecio, crearListaPrecio, listarListasPrecioPag } from '../../api/articulo'
import { ApiError } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import ListaCrud from '../../components/ListaCrud'
import type { ListaPrecio, ListaPrecioInput } from '../../types/articulo'

const VACIO: ListaPrecioInput = { nombre: '' }

function ListaPrecioFormModal({
  opened,
  onClose,
  onGuardado,
  lista,
}: {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
  lista: ListaPrecio | null
}) {
  const form = useForm<ListaPrecioInput>({ initialValues: VACIO })

  useEffect(() => {
    if (opened) form.setValues(lista ? { nombre: lista.nombre } : VACIO)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, lista])

  const guardar = form.onSubmit(async (valores) => {
    try {
      if (lista) await actualizarListaPrecio(lista.id, valores)
      else await crearListaPrecio(valores)
      notifications.show({ message: 'Guardado.', color: 'green' })
      onGuardado()
      onClose()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo guardar', message: detalle, color: 'red' })
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title={lista ? 'Editar lista de precios' : 'Nueva lista de precios'}>
      <form onSubmit={guardar}>
        <TextInput label="Nombre" withAsterisk placeholder="Ej: COMUN" {...form.getInputProps('nombre')} />
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

export default function ListasPrecioPage() {
  const { perfil } = useAuth()
  const puedeEditar = perfil?.is_staff ?? false
  const [modalAbierto, setModalAbierto] = useState(false)
  const [editando, setEditando] = useState<ListaPrecio | null>(null)
  const [recarga, setRecarga] = useState(0)

  return (
    <>
      <ListaCrud<ListaPrecio>
        titulo="Listas de precio"
        subtitulo="Cada cliente usa una lista para calcular sus precios"
        listar={listarListasPrecioPag}
        clave={(l) => l.id}
        porPagina={10}
        buscarPlaceholder="Buscar por nombre…"
        puedeCrear={puedeEditar}
        nuevoLabel="Nueva lista"
        onNuevo={() => {
          setEditando(null)
          setModalAbierto(true)
        }}
        disparadorRecarga={recarga}
        columnas={[{ header: 'Nombre', render: (l) => l.nombre }]}
        accionesHeader={
          puedeEditar
            ? (l) => (
                <ActionIcon
                  variant="subtle"
                  aria-label="Editar"
                  onClick={() => {
                    setEditando(l)
                    setModalAbierto(true)
                  }}
                >
                  <IconEdit size={16} />
                </ActionIcon>
              )
            : undefined
        }
      />
      <ListaPrecioFormModal
        opened={modalAbierto}
        onClose={() => setModalAbierto(false)}
        onGuardado={() => setRecarga((n) => n + 1)}
        lista={editando}
      />
    </>
  )
}
