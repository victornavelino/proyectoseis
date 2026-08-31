import { useEffect, useState } from 'react'
import { ActionIcon, Button, Group, Modal, NumberInput, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconEdit } from '@tabler/icons-react'
import { actualizarTipoIva, crearTipoIva, listarTiposIva } from '../../api/articulo'
import { ApiError } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import ListaCrud from '../../components/ListaCrud'
import type { TipoIva, TipoIvaInput } from '../../types/articulo'

const VACIO: TipoIvaInput = { nombre: '', porcentaje: '' }

function TipoIvaFormModal({
  opened,
  onClose,
  onGuardado,
  tipoIva,
}: {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
  tipoIva: TipoIva | null
}) {
  const form = useForm<TipoIvaInput>({ initialValues: VACIO })

  useEffect(() => {
    if (opened) form.setValues(tipoIva ? { nombre: tipoIva.nombre, porcentaje: tipoIva.porcentaje } : VACIO)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, tipoIva])

  const guardar = form.onSubmit(async (valores) => {
    try {
      if (tipoIva) await actualizarTipoIva(tipoIva.id, valores)
      else await crearTipoIva(valores)
      notifications.show({ message: 'Guardado.', color: 'green' })
      onGuardado()
      onClose()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo guardar', message: detalle, color: 'red' })
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title={tipoIva ? 'Editar tipo de IVA' : 'Nuevo tipo de IVA'}>
      <form onSubmit={guardar}>
        <TextInput label="Nombre" withAsterisk {...form.getInputProps('nombre')} />
        <NumberInput
          label="Porcentaje"
          mt="sm"
          withAsterisk
          suffix="%"
          value={form.values.porcentaje}
          onChange={(v) => form.setFieldValue('porcentaje', String(v))}
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

export default function TiposIvaPage() {
  const { perfil } = useAuth()
  const puedeEditar = perfil?.is_staff ?? false
  const [modalAbierto, setModalAbierto] = useState(false)
  const [editando, setEditando] = useState<TipoIva | null>(null)
  const [recarga, setRecarga] = useState(0)

  return (
    <>
      <ListaCrud<TipoIva>
        titulo="Tipos de IVA"
        subtitulo="Usados para clasificar categorías de artículos"
        listar={listarTiposIva}
        clave={(t) => t.id}
        porPagina={10}
        buscarPlaceholder="Buscar por nombre…"
        puedeCrear={puedeEditar}
        nuevoLabel="Nuevo tipo de IVA"
        onNuevo={() => {
          setEditando(null)
          setModalAbierto(true)
        }}
        disparadorRecarga={recarga}
        columnas={[
          { header: 'Nombre', render: (t) => t.nombre },
          { header: 'Porcentaje', render: (t) => `${t.porcentaje}%` },
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
      <TipoIvaFormModal
        opened={modalAbierto}
        onClose={() => setModalAbierto(false)}
        onGuardado={() => setRecarga((n) => n + 1)}
        tipoIva={editando}
      />
    </>
  )
}
