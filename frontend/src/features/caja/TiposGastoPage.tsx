import { useEffect, useState } from 'react'
import { ActionIcon, Button, Group, Modal, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconEdit } from '@tabler/icons-react'
import { actualizarTipoGasto, crearTipoGasto, listarTiposGasto } from '../../api/caja'
import { ApiError } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import ListaCrud from '../../components/ListaCrud'
import type { TipoGasto, TipoGastoInput } from '../../types/caja'

const VACIO: TipoGastoInput = { descripcion: '' }

function TipoGastoFormModal({
  opened,
  onClose,
  onGuardado,
  tipoGasto,
}: {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
  tipoGasto: TipoGasto | null
}) {
  const form = useForm<TipoGastoInput>({ initialValues: VACIO })

  useEffect(() => {
    if (opened) form.setValues(tipoGasto ? { descripcion: tipoGasto.descripcion } : VACIO)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, tipoGasto])

  const guardar = form.onSubmit(async (valores) => {
    try {
      if (tipoGasto) await actualizarTipoGasto(tipoGasto.id, valores)
      else await crearTipoGasto(valores)
      notifications.show({ message: 'Guardado.', color: 'green' })
      onGuardado()
      onClose()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo guardar', message: detalle, color: 'red' })
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title={tipoGasto ? 'Editar tipo de gasto' : 'Nuevo tipo de gasto'}>
      <form onSubmit={guardar}>
        <TextInput label="Descripción" withAsterisk placeholder="Ej: Insumos" {...form.getInputProps('descripcion')} />
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

export default function TiposGastoPage() {
  const { perfil } = useAuth()
  const puedeEditar = perfil?.is_staff ?? false
  const [modalAbierto, setModalAbierto] = useState(false)
  const [editando, setEditando] = useState<TipoGasto | null>(null)
  const [recarga, setRecarga] = useState(0)

  return (
    <>
      <ListaCrud<TipoGasto>
        titulo="Tipos de gasto"
        subtitulo="Usados para clasificar los gastos de caja"
        listar={listarTiposGasto}
        clave={(t) => t.id}
        porPagina={10}
        buscarPlaceholder="Buscar por descripción…"
        puedeCrear={puedeEditar}
        nuevoLabel="Nuevo tipo de gasto"
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
      <TipoGastoFormModal
        opened={modalAbierto}
        onClose={() => setModalAbierto(false)}
        onGuardado={() => setRecarga((n) => n + 1)}
        tipoGasto={editando}
      />
    </>
  )
}
