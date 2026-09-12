import { useEffect, useState } from 'react'
import { ActionIcon, Button, Group, Modal, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconEdit } from '@tabler/icons-react'
import { actualizarTipoIngreso, crearTipoIngreso, listarTiposIngreso } from '../../api/caja'
import { ApiError } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import ListaCrud from '../../components/ListaCrud'
import type { TipoIngreso, TipoIngresoInput } from '../../types/caja'

const VACIO: TipoIngresoInput = { descripcion: '' }

function TipoIngresoFormModal({
  opened,
  onClose,
  onGuardado,
  tipoIngreso,
}: {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
  tipoIngreso: TipoIngreso | null
}) {
  const form = useForm<TipoIngresoInput>({ initialValues: VACIO })

  useEffect(() => {
    if (opened) form.setValues(tipoIngreso ? { descripcion: tipoIngreso.descripcion } : VACIO)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, tipoIngreso])

  const guardar = form.onSubmit(async (valores) => {
    try {
      if (tipoIngreso) await actualizarTipoIngreso(tipoIngreso.id, valores)
      else await crearTipoIngreso(valores)
      notifications.show({ message: 'Guardado.', color: 'green' })
      onGuardado()
      onClose()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo guardar', message: detalle, color: 'red' })
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title={tipoIngreso ? 'Editar tipo de ingreso' : 'Nuevo tipo de ingreso'}>
      <form onSubmit={guardar}>
        <TextInput label="Descripción" withAsterisk placeholder="Ej: Alquileres" {...form.getInputProps('descripcion')} />
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

export default function TiposIngresoPage() {
  const { perfil } = useAuth()
  const puedeEditar = perfil?.is_staff ?? false
  const [modalAbierto, setModalAbierto] = useState(false)
  const [editando, setEditando] = useState<TipoIngreso | null>(null)
  const [recarga, setRecarga] = useState(0)

  return (
    <>
      <ListaCrud<TipoIngreso>
        titulo="Tipos de ingreso"
        subtitulo="Usados para clasificar los ingresos varios de caja"
        listar={listarTiposIngreso}
        clave={(t) => t.id}
        porPagina={10}
        buscarPlaceholder="Buscar por descripción…"
        puedeCrear={puedeEditar}
        nuevoLabel="Nuevo tipo de ingreso"
        onNuevo={() => {
          setEditando(null)
          setModalAbierto(true)
        }}
        disparadorRecarga={recarga}
        columnas={[{ header: 'Descripción', render: (t) => t.descripcion }]}
        accionesHeader={
          puedeEditar
            ? (t) => (
                <ActionIcon
                  variant="subtle"
                  aria-label="Editar"
                  onClick={() => {
                    setEditando(t)
                    setModalAbierto(true)
                  }}
                >
                  <IconEdit size={16} />
                </ActionIcon>
              )
            : undefined
        }
      />
      <TipoIngresoFormModal
        opened={modalAbierto}
        onClose={() => setModalAbierto(false)}
        onGuardado={() => setRecarga((n) => n + 1)}
        tipoIngreso={editando}
      />
    </>
  )
}
