import { useEffect, useState } from 'react'
import { ActionIcon, Button, Group, Modal, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconEdit } from '@tabler/icons-react'
import { actualizarSucursal, crearSucursal, listarSucursales } from '../../api/empleado'
import { ApiError } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import ListaCrud from '../../components/ListaCrud'
import type { Sucursal, SucursalInput } from '../../types/empleado'

const VACIO: SucursalInput = { nombre: '', domicilio: '' }

function SucursalFormModal({
  opened,
  onClose,
  onGuardado,
  sucursal,
}: {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
  sucursal: Sucursal | null
}) {
  const form = useForm<SucursalInput>({ initialValues: VACIO })

  useEffect(() => {
    if (opened) form.setValues(sucursal ? { nombre: sucursal.nombre, domicilio: sucursal.domicilio } : VACIO)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, sucursal])

  const guardar = form.onSubmit(async (valores) => {
    try {
      if (sucursal) await actualizarSucursal(sucursal.id, valores)
      else await crearSucursal(valores)
      notifications.show({ message: 'Guardado.', color: 'green' })
      onGuardado()
      onClose()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo guardar', message: detalle, color: 'red' })
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title={sucursal ? 'Editar sucursal' : 'Nueva sucursal'}>
      <form onSubmit={guardar}>
        <TextInput label="Nombre" withAsterisk {...form.getInputProps('nombre')} />
        <TextInput label="Domicilio" mt="sm" withAsterisk {...form.getInputProps('domicilio')} />
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

export default function SucursalesPage() {
  const { perfil } = useAuth()
  const puedeEditar = perfil?.is_staff ?? false
  const [modalAbierto, setModalAbierto] = useState(false)
  const [editando, setEditando] = useState<Sucursal | null>(null)
  const [recarga, setRecarga] = useState(0)

  return (
    <>
      <ListaCrud<Sucursal>
        titulo="Sucursales"
        subtitulo="Puntos de venta de la carnicería"
        listar={listarSucursales}
        clave={(s) => s.id}
        porPagina={10}
        buscarPlaceholder="Buscar por nombre…"
        puedeCrear={puedeEditar}
        nuevoLabel="Nueva sucursal"
        onNuevo={() => {
          setEditando(null)
          setModalAbierto(true)
        }}
        disparadorRecarga={recarga}
        columnas={[
          { header: 'Nombre', render: (s) => s.nombre },
          { header: 'Domicilio', render: (s) => s.domicilio },
        ]}
        accionesHeader={
          puedeEditar
            ? (s) => (
                <ActionIcon
                  variant="subtle"
                  aria-label="Editar"
                  onClick={() => {
                    setEditando(s)
                    setModalAbierto(true)
                  }}
                >
                  <IconEdit size={16} />
                </ActionIcon>
              )
            : undefined
        }
      />
      <SucursalFormModal
        opened={modalAbierto}
        onClose={() => setModalAbierto(false)}
        onGuardado={() => setRecarga((n) => n + 1)}
        sucursal={editando}
      />
    </>
  )
}
