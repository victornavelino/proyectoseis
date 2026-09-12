import { useEffect, useState } from 'react'
import { ActionIcon, Badge, Button, Group, Modal, NumberInput, Select, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconEdit, IconTrash } from '@tabler/icons-react'
import { actualizarGasto, crearGasto, eliminarGasto, listarGastos, listarTodosLosTiposGasto } from '../../api/caja'
import { ApiError } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import ListaCrud from '../../components/ListaCrud'
import type { Gasto, GastoInput, TipoGasto } from '../../types/caja'
import { formatearMonto } from '../ventas/dinero'

const VACIO: GastoInput = { concepto: '', importe: '', tipo_gasto: null }

function GastoFormModal({
  opened,
  onClose,
  onGuardado,
  gasto,
  tiposGasto,
}: {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
  gasto: Gasto | null
  tiposGasto: TipoGasto[]
}) {
  const form = useForm<GastoInput>({
    initialValues: VACIO,
    validate: {
      concepto: (v) => (v.trim() ? null : 'Ingresá un concepto'),
      tipo_gasto: (v) => (v ? null : 'Elegí un tipo de gasto'),
      importe: (v) => (Number(v) > 0 ? null : 'El importe tiene que ser mayor que cero'),
    },
  })

  useEffect(() => {
    if (opened) {
      form.setValues(gasto ? { concepto: gasto.concepto, importe: gasto.importe, tipo_gasto: gasto.tipo_gasto } : VACIO)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, gasto])

  const guardar = form.onSubmit(async (valores) => {
    try {
      if (gasto) await actualizarGasto(gasto.id, valores)
      else await crearGasto(valores)
      notifications.show({ message: 'Guardado.', color: 'green' })
      onGuardado()
      onClose()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo guardar', message: detalle, color: 'red' })
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title={gasto ? 'Editar gasto' : 'Nuevo gasto'}>
      <form onSubmit={guardar}>
        <TextInput label="Concepto" withAsterisk placeholder="Ej: Papelería" {...form.getInputProps('concepto')} />
        <Select
          label="Tipo de gasto"
          withAsterisk
          mt="sm"
          data={tiposGasto.map((t) => ({ value: String(t.id), label: t.descripcion }))}
          value={form.values.tipo_gasto ? String(form.values.tipo_gasto) : null}
          onChange={(v) => form.setFieldValue('tipo_gasto', v ? Number(v) : null)}
          error={form.errors.tipo_gasto}
        />
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

export default function GastosPage() {
  const { perfil } = useAuth()
  const puedeCargar = !!perfil?.sucursal
  const [modalAbierto, setModalAbierto] = useState(false)
  const [editando, setEditando] = useState<Gasto | null>(null)
  const [recarga, setRecarga] = useState(0)
  const [tiposGasto, setTiposGasto] = useState<TipoGasto[]>([])

  useEffect(() => {
    listarTodosLosTiposGasto()
      .then((r) => setTiposGasto(r.results))
      .catch(() => notifications.show({ message: 'No se pudieron cargar los tipos de gasto.', color: 'red' }))
  }, [])

  const eliminar = async (g: Gasto) => {
    try {
      await eliminarGasto(g.id)
      notifications.show({ message: 'Gasto eliminado.', color: 'green' })
      setRecarga((n) => n + 1)
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo eliminar', message: detalle, color: 'red' })
    }
  }

  return (
    <>
      <ListaCrud<Gasto>
        titulo="Gastos"
        subtitulo="Egresos de caja por gastos varios"
        listar={listarGastos}
        clave={(g) => g.id}
        porPagina={10}
        buscarPlaceholder="Buscar por concepto…"
        puedeCrear={puedeCargar}
        nuevoLabel="Nuevo gasto"
        onNuevo={() => {
          setEditando(null)
          setModalAbierto(true)
        }}
        disparadorRecarga={recarga}
        columnas={[
          { header: 'Concepto', render: (g) => g.concepto },
          { header: 'Tipo', render: (g) => g.tipo_gasto_descripcion ?? '—' },
          { header: 'Importe', render: (g) => formatearMonto(g.importe) },
          { header: 'Fecha', render: (g) => new Date(g.fecha).toLocaleString('es-AR') },
          { header: 'Usuario', render: (g) => g.usuario_username },
          {
            header: 'Estado',
            render: (g) => (
              <Badge color={g.cerrado ? 'gray' : 'green'} variant="light">
                {g.cerrado ? 'Cerrado' : 'Abierto'}
              </Badge>
            ),
          },
        ]}
        accionesHeader={
          puedeCargar
            ? (g) =>
                g.cerrado ? null : (
                  <Group gap={4} wrap="nowrap">
                    <ActionIcon
                      variant="subtle"
                      aria-label="Editar"
                      onClick={() => {
                        setEditando(g)
                        setModalAbierto(true)
                      }}
                    >
                      <IconEdit size={16} />
                    </ActionIcon>
                    <ActionIcon color="red" variant="subtle" aria-label="Eliminar" onClick={() => void eliminar(g)}>
                      <IconTrash size={16} />
                    </ActionIcon>
                  </Group>
                )
            : undefined
        }
      />
      <GastoFormModal
        opened={modalAbierto}
        onClose={() => setModalAbierto(false)}
        onGuardado={() => setRecarga((n) => n + 1)}
        gasto={editando}
        tiposGasto={tiposGasto}
      />
    </>
  )
}
