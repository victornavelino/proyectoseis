import { useEffect, useState } from 'react'
import { ActionIcon, Button, Group, Modal, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconEdit } from '@tabler/icons-react'
import { actualizarUnidadMedida, crearUnidadMedida, listarUnidadesMedidaPag } from '../../api/articulo'
import { ApiError } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import ListaCrud from '../../components/ListaCrud'
import type { UnidadMedida, UnidadMedidaInput } from '../../types/articulo'

const VACIO: UnidadMedidaInput = { nombre: '', abreviatura: '' }

function UnidadMedidaFormModal({
  opened,
  onClose,
  onGuardado,
  unidad,
}: {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
  unidad: UnidadMedida | null
}) {
  const form = useForm<UnidadMedidaInput>({ initialValues: VACIO })

  useEffect(() => {
    if (opened) form.setValues(unidad ? { nombre: unidad.nombre, abreviatura: unidad.abreviatura } : VACIO)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, unidad])

  const guardar = form.onSubmit(async (valores) => {
    try {
      if (unidad) await actualizarUnidadMedida(unidad.id, valores)
      else await crearUnidadMedida(valores)
      notifications.show({ message: 'Guardado.', color: 'green' })
      onGuardado()
      onClose()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo guardar', message: detalle, color: 'red' })
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title={unidad ? 'Editar unidad de medida' : 'Nueva unidad de medida'}>
      <form onSubmit={guardar}>
        <TextInput label="Nombre" withAsterisk placeholder="Ej: Kilogramo" {...form.getInputProps('nombre')} />
        <TextInput label="Abreviatura" mt="sm" withAsterisk placeholder="Ej: kg" {...form.getInputProps('abreviatura')} />
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

export default function UnidadesMedidaPage() {
  const { perfil } = useAuth()
  const puedeEditar = perfil?.is_staff ?? false
  const [modalAbierto, setModalAbierto] = useState(false)
  const [editando, setEditando] = useState<UnidadMedida | null>(null)
  const [recarga, setRecarga] = useState(0)

  return (
    <>
      <ListaCrud<UnidadMedida>
        titulo="Unidades de medida"
        subtitulo="Usadas para definir cómo se vende cada artículo"
        listar={listarUnidadesMedidaPag}
        clave={(u) => u.id}
        porPagina={10}
        buscarPlaceholder="Buscar por nombre…"
        puedeCrear={puedeEditar}
        nuevoLabel="Nueva unidad"
        onNuevo={() => {
          setEditando(null)
          setModalAbierto(true)
        }}
        disparadorRecarga={recarga}
        columnas={[
          { header: 'Nombre', render: (u) => u.nombre },
          { header: 'Abreviatura', render: (u) => u.abreviatura },
        ]}
        accionesHeader={
          puedeEditar
            ? (u) => (
                <ActionIcon
                  variant="subtle"
                  aria-label="Editar"
                  onClick={() => {
                    setEditando(u)
                    setModalAbierto(true)
                  }}
                >
                  <IconEdit size={16} />
                </ActionIcon>
              )
            : undefined
        }
      />
      <UnidadMedidaFormModal
        opened={modalAbierto}
        onClose={() => setModalAbierto(false)}
        onGuardado={() => setRecarga((n) => n + 1)}
        unidad={editando}
      />
    </>
  )
}
