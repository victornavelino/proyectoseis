import { useEffect, useState } from 'react'
import { ActionIcon, Button, Group, Modal, NumberInput, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconEdit } from '@tabler/icons-react'
import { actualizarDescuento, crearDescuento, listarDescuentos } from '../../api/promocion'
import { ApiError } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import ListaCrud from '../../components/ListaCrud'
import type { Descuento, DescuentoInput } from '../../types/promocion'

const VACIO: DescuentoInput = { nombre: '', valor: 0 }

function DescuentoFormModal({
  opened,
  onClose,
  onGuardado,
  descuento,
}: {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
  descuento: Descuento | null
}) {
  const form = useForm<DescuentoInput>({ initialValues: VACIO })

  useEffect(() => {
    if (opened) form.setValues(descuento ? { nombre: descuento.nombre, valor: descuento.valor } : VACIO)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, descuento])

  const guardar = form.onSubmit(async (valores) => {
    try {
      if (descuento) await actualizarDescuento(descuento.id, valores)
      else await crearDescuento(valores)
      notifications.show({ message: 'Guardado.', color: 'green' })
      onGuardado()
      onClose()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo guardar', message: detalle, color: 'red' })
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title={descuento ? 'Editar descuento' : 'Nuevo descuento'}>
      <form onSubmit={guardar}>
        <TextInput
          label="Nombre"
          withAsterisk
          description='Ej: "CUMPLEAÑOS" o "EMPLEADOS" — se aplican por nombre exacto en las ventas'
          {...form.getInputProps('nombre')}
        />
        <NumberInput
          label="Valor"
          withAsterisk
          mt="sm"
          suffix="%"
          min={0}
          max={100}
          value={form.values.valor}
          onChange={(v) => form.setFieldValue('valor', Number(v))}
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

export default function DescuentosPage() {
  const { perfil } = useAuth()
  const puedeEditar = perfil?.is_staff ?? false
  const [modalAbierto, setModalAbierto] = useState(false)
  const [editando, setEditando] = useState<Descuento | null>(null)
  const [recarga, setRecarga] = useState(0)

  return (
    <>
      <ListaCrud<Descuento>
        titulo="Descuentos"
        subtitulo='Descuentos especiales aplicados por nombre exacto (ej. "CUMPLEAÑOS", "EMPLEADOS")'
        listar={listarDescuentos}
        clave={(d) => d.id}
        porPagina={10}
        buscarPlaceholder="Buscar por nombre…"
        puedeCrear={puedeEditar}
        nuevoLabel="Nuevo descuento"
        onNuevo={() => {
          setEditando(null)
          setModalAbierto(true)
        }}
        disparadorRecarga={recarga}
        columnas={[
          { header: 'Nombre', render: (d) => d.nombre },
          { header: 'Valor', render: (d) => `${d.valor}%` },
        ]}
        accionesHeader={
          puedeEditar
            ? (d) => (
                <ActionIcon
                  variant="subtle"
                  aria-label="Editar"
                  onClick={() => {
                    setEditando(d)
                    setModalAbierto(true)
                  }}
                >
                  <IconEdit size={16} />
                </ActionIcon>
              )
            : undefined
        }
      />
      <DescuentoFormModal
        opened={modalAbierto}
        onClose={() => setModalAbierto(false)}
        onGuardado={() => setRecarga((n) => n + 1)}
        descuento={editando}
      />
    </>
  )
}
