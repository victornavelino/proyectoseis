import { useEffect, useState } from 'react'
import { ActionIcon, Badge, Button, Group, Modal, NumberInput, Select, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconEdit, IconTrash } from '@tabler/icons-react'
import { actualizarSueldo, crearSueldo, eliminarSueldo, listarSueldos } from '../../api/caja'
import { ApiError } from '../../api/client'
import { listarEmpleadosActivos } from '../../api/empleado'
import { useAuth } from '../../auth/AuthContext'
import ListaCrud from '../../components/ListaCrud'
import type { Empleado } from '../../types/empleado'
import type { Sueldo, SueldoInput } from '../../types/caja'
import { formatearMonto } from '../ventas/dinero'

const VACIO: SueldoInput = { descripcion: '', importe: '', empleado: null }

function SueldoFormModal({
  opened,
  onClose,
  onGuardado,
  sueldo,
  empleados,
}: {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
  sueldo: Sueldo | null
  empleados: Empleado[]
}) {
  const form = useForm<SueldoInput>({
    initialValues: VACIO,
    validate: {
      descripcion: (v) => (v.trim() ? null : 'Ingresá una descripción'),
      importe: (v) => (Number(v) > 0 ? null : 'El importe tiene que ser mayor que cero'),
    },
  })

  useEffect(() => {
    if (opened) {
      form.setValues(
        sueldo ? { descripcion: sueldo.descripcion, importe: sueldo.importe, empleado: sueldo.empleado } : VACIO,
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, sueldo])

  const guardar = form.onSubmit(async (valores) => {
    try {
      if (sueldo) await actualizarSueldo(sueldo.id, valores)
      else await crearSueldo(valores)
      notifications.show({ message: 'Guardado.', color: 'green' })
      onGuardado()
      onClose()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo guardar', message: detalle, color: 'red' })
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title={sueldo ? 'Editar sueldo' : 'Nuevo sueldo'}>
      <form onSubmit={guardar}>
        <TextInput
          label="Descripción"
          withAsterisk
          placeholder="Ej: Sueldo agosto"
          {...form.getInputProps('descripcion')}
        />
        <Select
          label="Empleado"
          mt="sm"
          clearable
          searchable
          data={empleados.map((e) => ({ value: String(e.id), label: e.persona_nombre }))}
          value={form.values.empleado ? String(form.values.empleado) : null}
          onChange={(v) => form.setFieldValue('empleado', v ? Number(v) : null)}
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

export default function SueldosPage() {
  const { perfil } = useAuth()
  const puedeCargar = !!perfil?.sucursal
  const [modalAbierto, setModalAbierto] = useState(false)
  const [editando, setEditando] = useState<Sueldo | null>(null)
  const [recarga, setRecarga] = useState(0)
  const [empleados, setEmpleados] = useState<Empleado[]>([])

  useEffect(() => {
    listarEmpleadosActivos()
      .then((r) => setEmpleados(r.results))
      .catch(() => notifications.show({ message: 'No se pudieron cargar los empleados.', color: 'red' }))
  }, [])

  const eliminar = async (s: Sueldo) => {
    try {
      await eliminarSueldo(s.id)
      notifications.show({ message: 'Sueldo eliminado.', color: 'green' })
      setRecarga((n) => n + 1)
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo eliminar', message: detalle, color: 'red' })
    }
  }

  return (
    <>
      <ListaCrud<Sueldo>
        titulo="Sueldos"
        subtitulo="Egresos de caja por pago de sueldos"
        listar={listarSueldos}
        clave={(s) => s.id}
        porPagina={10}
        buscarPlaceholder="Buscar por descripción…"
        puedeCrear={puedeCargar}
        nuevoLabel="Nuevo sueldo"
        onNuevo={() => {
          setEditando(null)
          setModalAbierto(true)
        }}
        disparadorRecarga={recarga}
        columnas={[
          { header: 'Descripción', render: (s) => s.descripcion },
          { header: 'Empleado', render: (s) => s.empleado_nombre ?? '—' },
          { header: 'Importe', render: (s) => formatearMonto(s.importe) },
          { header: 'Fecha', render: (s) => new Date(s.fecha).toLocaleString('es-AR') },
          { header: 'Usuario', render: (s) => s.usuario_username },
          {
            header: 'Estado',
            render: (s) => (
              <Badge color={s.cerrado ? 'gray' : 'green'} variant="light">
                {s.cerrado ? 'Cerrado' : 'Abierto'}
              </Badge>
            ),
          },
        ]}
        accionesHeader={
          puedeCargar
            ? (s) =>
                s.cerrado ? null : (
                  <Group gap={4} wrap="nowrap">
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
                    <ActionIcon color="red" variant="subtle" aria-label="Eliminar" onClick={() => void eliminar(s)}>
                      <IconTrash size={16} />
                    </ActionIcon>
                  </Group>
                )
            : undefined
        }
      />
      <SueldoFormModal
        opened={modalAbierto}
        onClose={() => setModalAbierto(false)}
        onGuardado={() => setRecarga((n) => n + 1)}
        sueldo={editando}
        empleados={empleados}
      />
    </>
  )
}
