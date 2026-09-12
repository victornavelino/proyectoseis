import { useEffect, useState } from 'react'
import { ActionIcon, Badge, Button, Group, Modal, NumberInput, Select, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconEdit, IconTrash } from '@tabler/icons-react'
import { actualizarIngreso, crearIngreso, eliminarIngreso, listarIngresos, listarTodosLosTiposIngreso } from '../../api/caja'
import { ApiError } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import ListaCrud from '../../components/ListaCrud'
import type { Ingreso, IngresoInput, TipoIngreso } from '../../types/caja'
import { formatearMonto } from '../ventas/dinero'

const VACIO: IngresoInput = { concepto: '', importe: '', tipo_ingreso: null }

function IngresoFormModal({
  opened,
  onClose,
  onGuardado,
  ingreso,
  tiposIngreso,
}: {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
  ingreso: Ingreso | null
  tiposIngreso: TipoIngreso[]
}) {
  const form = useForm<IngresoInput>({
    initialValues: VACIO,
    validate: {
      concepto: (v) => (v.trim() ? null : 'Ingresá un concepto'),
      tipo_ingreso: (v) => (v ? null : 'Elegí un tipo de ingreso'),
      importe: (v) => (Number(v) > 0 ? null : 'El importe tiene que ser mayor que cero'),
    },
  })

  useEffect(() => {
    if (opened) {
      form.setValues(
        ingreso ? { concepto: ingreso.concepto, importe: ingreso.importe, tipo_ingreso: ingreso.tipo_ingreso } : VACIO,
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, ingreso])

  const guardar = form.onSubmit(async (valores) => {
    try {
      if (ingreso) await actualizarIngreso(ingreso.id, valores)
      else await crearIngreso(valores)
      notifications.show({ message: 'Guardado.', color: 'green' })
      onGuardado()
      onClose()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo guardar', message: detalle, color: 'red' })
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title={ingreso ? 'Editar ingreso' : 'Nuevo ingreso'}>
      <form onSubmit={guardar}>
        <TextInput
          label="Concepto"
          withAsterisk
          placeholder="Ej: Alquiler cobrado"
          {...form.getInputProps('concepto')}
        />
        <Select
          label="Tipo de ingreso"
          withAsterisk
          mt="sm"
          data={tiposIngreso.map((t) => ({ value: String(t.id), label: t.descripcion }))}
          value={form.values.tipo_ingreso ? String(form.values.tipo_ingreso) : null}
          onChange={(v) => form.setFieldValue('tipo_ingreso', v ? Number(v) : null)}
          error={form.errors.tipo_ingreso}
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

export default function IngresosPage() {
  const { perfil } = useAuth()
  const puedeCargar = !!perfil?.sucursal
  const [modalAbierto, setModalAbierto] = useState(false)
  const [editando, setEditando] = useState<Ingreso | null>(null)
  const [recarga, setRecarga] = useState(0)
  const [tiposIngreso, setTiposIngreso] = useState<TipoIngreso[]>([])

  useEffect(() => {
    listarTodosLosTiposIngreso()
      .then((r) => setTiposIngreso(r.results))
      .catch(() => notifications.show({ message: 'No se pudieron cargar los tipos de ingreso.', color: 'red' }))
  }, [])

  const eliminar = async (i: Ingreso) => {
    try {
      await eliminarIngreso(i.id)
      notifications.show({ message: 'Ingreso eliminado.', color: 'green' })
      setRecarga((n) => n + 1)
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo eliminar', message: detalle, color: 'red' })
    }
  }

  return (
    <>
      <ListaCrud<Ingreso>
        titulo="Ingresos varios"
        subtitulo="Ingresos de caja que no son cobro de venta (ej. alquileres, otros cobros)"
        listar={listarIngresos}
        clave={(i) => i.id}
        porPagina={10}
        buscarPlaceholder="Buscar por concepto…"
        puedeCrear={puedeCargar}
        nuevoLabel="Nuevo ingreso"
        onNuevo={() => {
          setEditando(null)
          setModalAbierto(true)
        }}
        disparadorRecarga={recarga}
        columnas={[
          { header: 'Concepto', render: (i) => i.concepto },
          { header: 'Tipo', render: (i) => i.tipo_ingreso_descripcion ?? '—' },
          { header: 'Importe', render: (i) => formatearMonto(i.importe) },
          { header: 'Fecha', render: (i) => new Date(i.fecha).toLocaleString('es-AR') },
          { header: 'Usuario', render: (i) => i.usuario_username },
          {
            header: 'Estado',
            render: (i) => (
              <Badge color={i.cerrado ? 'gray' : 'green'} variant="light">
                {i.cerrado ? 'Cerrado' : 'Abierto'}
              </Badge>
            ),
          },
        ]}
        accionesHeader={
          puedeCargar
            ? (i) =>
                i.cerrado ? null : (
                  <Group gap={4} wrap="nowrap">
                    <ActionIcon
                      variant="subtle"
                      aria-label="Editar"
                      onClick={() => {
                        setEditando(i)
                        setModalAbierto(true)
                      }}
                    >
                      <IconEdit size={16} />
                    </ActionIcon>
                    <ActionIcon color="red" variant="subtle" aria-label="Eliminar" onClick={() => void eliminar(i)}>
                      <IconTrash size={16} />
                    </ActionIcon>
                  </Group>
                )
            : undefined
        }
      />
      <IngresoFormModal
        opened={modalAbierto}
        onClose={() => setModalAbierto(false)}
        onGuardado={() => setRecarga((n) => n + 1)}
        ingreso={editando}
        tiposIngreso={tiposIngreso}
      />
    </>
  )
}
