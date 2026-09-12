import { useEffect, useState } from 'react'
import { ActionIcon, Badge, Button, Group, Modal, NumberInput, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconEdit, IconTrash } from '@tabler/icons-react'
import { actualizarRetiroEfectivo, crearRetiroEfectivo, eliminarRetiroEfectivo, listarRetirosEfectivo } from '../../api/caja'
import { ApiError } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import ListaCrud from '../../components/ListaCrud'
import type { RetiroEfectivo, RetiroEfectivoInput } from '../../types/caja'
import { formatearMonto } from '../ventas/dinero'

const VACIO: RetiroEfectivoInput = { concepto: '', importe: '' }

function RetiroEfectivoFormModal({
  opened,
  onClose,
  onGuardado,
  retiro,
}: {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
  retiro: RetiroEfectivo | null
}) {
  const form = useForm<RetiroEfectivoInput>({
    initialValues: VACIO,
    validate: {
      concepto: (v) => (v.trim() ? null : 'Ingresá un concepto'),
      importe: (v) => (Number(v) > 0 ? null : 'El importe tiene que ser mayor que cero'),
    },
  })

  useEffect(() => {
    if (opened) form.setValues(retiro ? { concepto: retiro.concepto, importe: retiro.importe } : VACIO)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, retiro])

  const guardar = form.onSubmit(async (valores) => {
    try {
      if (retiro) await actualizarRetiroEfectivo(retiro.id, valores)
      else await crearRetiroEfectivo(valores)
      notifications.show({ message: 'Guardado.', color: 'green' })
      onGuardado()
      onClose()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo guardar', message: detalle, color: 'red' })
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title={retiro ? 'Editar retiro de efectivo' : 'Nuevo retiro de efectivo'}>
      <form onSubmit={guardar}>
        <TextInput label="Concepto" withAsterisk placeholder="Ej: Retiro socio" {...form.getInputProps('concepto')} />
        <NumberInput
          label="Importe"
          withAsterisk
          mt="sm"
          min={0}
          decimalScale={2}
          value={form.values.importe}
          onChange={(v) => form.setFieldValue('importe', String(v))}
          error={form.errors.importe}
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

export default function RetirosEfectivoPage() {
  const { perfil } = useAuth()
  const puedeCargar = !!perfil?.sucursal
  const [modalAbierto, setModalAbierto] = useState(false)
  const [editando, setEditando] = useState<RetiroEfectivo | null>(null)
  const [recarga, setRecarga] = useState(0)

  const eliminar = async (r: RetiroEfectivo) => {
    try {
      await eliminarRetiroEfectivo(r.id)
      notifications.show({ message: 'Retiro eliminado.', color: 'green' })
      setRecarga((n) => n + 1)
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo eliminar', message: detalle, color: 'red' })
    }
  }

  return (
    <>
      <ListaCrud<RetiroEfectivo>
        titulo="Retiros de efectivo"
        subtitulo="Egresos de caja por retiro de efectivo"
        listar={listarRetirosEfectivo}
        clave={(r) => r.id}
        porPagina={10}
        buscarPlaceholder="Buscar por concepto…"
        puedeCrear={puedeCargar}
        nuevoLabel="Nuevo retiro"
        onNuevo={() => {
          setEditando(null)
          setModalAbierto(true)
        }}
        disparadorRecarga={recarga}
        columnas={[
          { header: 'Concepto', render: (r) => r.concepto },
          { header: 'Importe', render: (r) => formatearMonto(r.importe) },
          { header: 'Fecha', render: (r) => new Date(r.fecha).toLocaleString('es-AR') },
          { header: 'Usuario', render: (r) => r.usuario_username },
          {
            header: 'Estado',
            render: (r) => (
              <Badge color={r.cerrado ? 'gray' : 'green'} variant="light">
                {r.cerrado ? 'Cerrado' : 'Abierto'}
              </Badge>
            ),
          },
        ]}
        accionesHeader={
          puedeCargar
            ? (r) =>
                r.cerrado ? null : (
                  <Group gap={4} wrap="nowrap">
                    <ActionIcon
                      variant="subtle"
                      aria-label="Editar"
                      onClick={() => {
                        setEditando(r)
                        setModalAbierto(true)
                      }}
                    >
                      <IconEdit size={16} />
                    </ActionIcon>
                    <ActionIcon color="red" variant="subtle" aria-label="Eliminar" onClick={() => void eliminar(r)}>
                      <IconTrash size={16} />
                    </ActionIcon>
                  </Group>
                )
            : undefined
        }
      />
      <RetiroEfectivoFormModal
        opened={modalAbierto}
        onClose={() => setModalAbierto(false)}
        onGuardado={() => setRecarga((n) => n + 1)}
        retiro={editando}
      />
    </>
  )
}
