import { useEffect, useState } from 'react'
import { ActionIcon, Button, Group, Modal, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconEdit } from '@tabler/icons-react'
import { actualizarTarjeta, crearTarjeta, listarTarjetas } from '../../api/caja'
import { ApiError } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import ListaCrud from '../../components/ListaCrud'
import type { TarjetaDeCredito, TarjetaDeCreditoInput } from '../../types/caja'

const VACIO: TarjetaDeCreditoInput = { nombre: '', banco: '' }

function TarjetaFormModal({
  opened,
  onClose,
  onGuardado,
  tarjeta,
}: {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
  tarjeta: TarjetaDeCredito | null
}) {
  const form = useForm<TarjetaDeCreditoInput>({ initialValues: VACIO })

  useEffect(() => {
    if (opened) form.setValues(tarjeta ? { nombre: tarjeta.nombre, banco: tarjeta.banco } : VACIO)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, tarjeta])

  const guardar = form.onSubmit(async (valores) => {
    // `banco` es nullable en el modelo pero no acepta string vacío ("" falla con "Este campo
    // no puede estar en blanco.") — hay que mandar null si el usuario lo dejó sin completar.
    const datos = { ...valores, banco: valores.banco || null }
    try {
      if (tarjeta) await actualizarTarjeta(tarjeta.id, datos)
      else await crearTarjeta(datos)
      notifications.show({ message: 'Guardado.', color: 'green' })
      onGuardado()
      onClose()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo guardar', message: detalle, color: 'red' })
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title={tarjeta ? 'Editar tarjeta' : 'Nueva tarjeta'}>
      <form onSubmit={guardar}>
        <TextInput label="Nombre" withAsterisk placeholder="Ej: Visa" {...form.getInputProps('nombre')} />
        <TextInput label="Banco" mt="sm" {...form.getInputProps('banco')} />
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

export default function TarjetasPage() {
  const { perfil } = useAuth()
  const puedeEditar = perfil?.is_staff ?? false
  const [modalAbierto, setModalAbierto] = useState(false)
  const [editando, setEditando] = useState<TarjetaDeCredito | null>(null)
  const [recarga, setRecarga] = useState(0)

  return (
    <>
      <ListaCrud<TarjetaDeCredito>
        titulo="Tarjetas de crédito"
        listar={listarTarjetas}
        clave={(t) => t.id}
        porPagina={10}
        buscarPlaceholder="Buscar por nombre…"
        puedeCrear={puedeEditar}
        nuevoLabel="Nueva tarjeta"
        onNuevo={() => {
          setEditando(null)
          setModalAbierto(true)
        }}
        disparadorRecarga={recarga}
        columnas={[
          { header: 'Nombre', render: (t) => t.nombre },
          { header: 'Banco', render: (t) => t.banco ?? '—' },
        ]}
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
      <TarjetaFormModal
        opened={modalAbierto}
        onClose={() => setModalAbierto(false)}
        onGuardado={() => setRecarga((n) => n + 1)}
        tarjeta={editando}
      />
    </>
  )
}
