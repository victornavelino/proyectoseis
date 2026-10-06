import { useEffect, useState } from 'react'
import { ActionIcon, Button, Group, Modal, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconEdit, IconTrash } from '@tabler/icons-react'
import { actualizarBanco, crearBanco, eliminarBanco, listarBancos } from '../../api/caja'
import { mensajeDeError } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import ListaCrud from '../../components/ListaCrud'
import type { Banco, BancoInput } from '../../types/caja'

const VACIO: BancoInput = { nombre: '' }

function BancoFormModal({
  opened,
  onClose,
  onGuardado,
  banco,
}: {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
  banco: Banco | null
}) {
  const form = useForm<BancoInput>({ initialValues: VACIO })

  useEffect(() => {
    if (opened) form.setValues(banco ? { nombre: banco.nombre } : VACIO)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, banco])

  const guardar = form.onSubmit(async (valores) => {
    try {
      if (banco) await actualizarBanco(banco.id, valores)
      else await crearBanco(valores)
      notifications.show({ message: 'Guardado.', color: 'green' })
      onGuardado()
      onClose()
    } catch (err) {
      const detalle = mensajeDeError(err)
      notifications.show({ title: 'No se pudo guardar', message: detalle, color: 'red' })
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title={banco ? 'Editar banco' : 'Nuevo banco'}>
      <form onSubmit={guardar}>
        <TextInput label="Nombre" withAsterisk placeholder="Ej: Banco Nación" {...form.getInputProps('nombre')} />
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

export default function BancosPage() {
  const { puedeEscribir, puedeBorrar } = useAuth()
  const puedeEditar = puedeEscribir('caja.banco')
  const puedeEliminar = puedeBorrar('caja.banco')
  const [modalAbierto, setModalAbierto] = useState(false)
  const [editando, setEditando] = useState<Banco | null>(null)
  const [recarga, setRecarga] = useState(0)

  const eliminar = async (banco: Banco) => {
    try {
      await eliminarBanco(banco.id)
      notifications.show({ message: 'Banco eliminado.', color: 'green' })
      setRecarga((n) => n + 1)
    } catch (err) {
      notifications.show({ title: 'No se pudo eliminar', message: mensajeDeError(err), color: 'red' })
    }
  }

  return (
    <>
      <ListaCrud<Banco>
        titulo="Bancos"
        subtitulo="Usados como selector en pagos con transferencia y con QR"
        listar={listarBancos}
        clave={(b) => b.id}
        porPagina={10}
        buscarPlaceholder="Buscar por nombre…"
        puedeCrear={puedeEditar}
        nuevoLabel="Nuevo banco"
        onNuevo={() => {
          setEditando(null)
          setModalAbierto(true)
        }}
        disparadorRecarga={recarga}
        columnas={[{ header: 'Nombre', render: (b) => b.nombre }]}
        accionesHeader={
          puedeEditar || puedeEliminar
            ? (b) => (
                <Group gap="xs" wrap="nowrap">
                  {puedeEditar && (
                    <ActionIcon
                      variant="subtle"
                      aria-label="Editar"
                      onClick={() => {
                        setEditando(b)
                        setModalAbierto(true)
                      }}
                    >
                      <IconEdit size={16} />
                    </ActionIcon>
                  )}
                  {puedeEliminar && (
                    <ActionIcon color="red" variant="subtle" aria-label="Eliminar" onClick={() => void eliminar(b)}>
                      <IconTrash size={16} />
                    </ActionIcon>
                  )}
                </Group>
              )
            : undefined
        }
      />
      <BancoFormModal
        opened={modalAbierto}
        onClose={() => setModalAbierto(false)}
        onGuardado={() => setRecarga((n) => n + 1)}
        banco={editando}
      />
    </>
  )
}
