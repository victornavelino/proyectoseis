import { useEffect, useState } from 'react'
import { ActionIcon, Badge, Button, Group, Modal, NumberInput, Select, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconEdit, IconTrash } from '@tabler/icons-react'
import { actualizarAdelanto, crearAdelanto, eliminarAdelanto, listarAdelantos } from '../../api/caja'
import { ApiError } from '../../api/client'
import { listarEmpleadosActivos } from '../../api/empleado'
import { useAuth } from '../../auth/AuthContext'
import ListaCrud from '../../components/ListaCrud'
import type { Empleado } from '../../types/empleado'
import type { Adelanto, AdelantoInput } from '../../types/caja'
import { formatearMonto } from '../ventas/dinero'

const VACIO: AdelantoInput = { descripcion: '', importe: '', empleado: null }

function AdelantoFormModal({
  opened,
  onClose,
  onGuardado,
  adelanto,
  empleados,
}: {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
  adelanto: Adelanto | null
  empleados: Empleado[]
}) {
  const form = useForm<AdelantoInput>({
    initialValues: VACIO,
    validate: {
      descripcion: (v) => (v.trim() ? null : 'Ingresá una descripción'),
      importe: (v) => (Number(v) > 0 ? null : 'El importe tiene que ser mayor que cero'),
    },
  })

  useEffect(() => {
    if (opened) {
      form.setValues(
        adelanto
          ? { descripcion: adelanto.descripcion, importe: adelanto.importe, empleado: adelanto.empleado }
          : VACIO,
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, adelanto])

  const guardar = form.onSubmit(async (valores) => {
    try {
      if (adelanto) await actualizarAdelanto(adelanto.id, valores)
      else await crearAdelanto(valores)
      notifications.show({ message: 'Guardado.', color: 'green' })
      onGuardado()
      onClose()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo guardar', message: detalle, color: 'red' })
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title={adelanto ? 'Editar adelanto' : 'Nuevo adelanto'}>
      <form onSubmit={guardar}>
        <TextInput
          label="Descripción"
          withAsterisk
          placeholder="Ej: Adelanto de sueldo"
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

export default function AdelantosPage() {
  const { perfil } = useAuth()
  const puedeCargar = !!perfil?.sucursal
  const [modalAbierto, setModalAbierto] = useState(false)
  const [editando, setEditando] = useState<Adelanto | null>(null)
  const [recarga, setRecarga] = useState(0)
  const [empleados, setEmpleados] = useState<Empleado[]>([])

  useEffect(() => {
    listarEmpleadosActivos()
      .then((r) => setEmpleados(r.results))
      .catch(() => notifications.show({ message: 'No se pudieron cargar los empleados.', color: 'red' }))
  }, [])

  const eliminar = async (a: Adelanto) => {
    try {
      await eliminarAdelanto(a.id)
      notifications.show({ message: 'Adelanto eliminado.', color: 'green' })
      setRecarga((n) => n + 1)
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo eliminar', message: detalle, color: 'red' })
    }
  }

  return (
    <>
      <ListaCrud<Adelanto>
        titulo="Adelantos"
        subtitulo="Egresos de caja por adelanto de sueldo"
        listar={listarAdelantos}
        clave={(a) => a.id}
        porPagina={10}
        buscarPlaceholder="Buscar por descripción…"
        puedeCrear={puedeCargar}
        nuevoLabel="Nuevo adelanto"
        onNuevo={() => {
          setEditando(null)
          setModalAbierto(true)
        }}
        disparadorRecarga={recarga}
        columnas={[
          { header: 'Descripción', render: (a) => a.descripcion },
          { header: 'Empleado', render: (a) => a.empleado_nombre ?? '—' },
          { header: 'Importe', render: (a) => formatearMonto(a.importe) },
          { header: 'Fecha', render: (a) => new Date(a.fecha).toLocaleString('es-AR') },
          { header: 'Usuario', render: (a) => a.usuario_username },
          {
            header: 'Estado',
            render: (a) => (
              <Badge color={a.cerrado ? 'gray' : 'green'} variant="light">
                {a.cerrado ? 'Cerrado' : 'Abierto'}
              </Badge>
            ),
          },
        ]}
        accionesHeader={
          puedeCargar
            ? (a) =>
                a.cerrado ? null : (
                  <Group gap={4} wrap="nowrap">
                    <ActionIcon
                      variant="subtle"
                      aria-label="Editar"
                      onClick={() => {
                        setEditando(a)
                        setModalAbierto(true)
                      }}
                    >
                      <IconEdit size={16} />
                    </ActionIcon>
                    <ActionIcon color="red" variant="subtle" aria-label="Eliminar" onClick={() => void eliminar(a)}>
                      <IconTrash size={16} />
                    </ActionIcon>
                  </Group>
                )
            : undefined
        }
      />
      <AdelantoFormModal
        opened={modalAbierto}
        onClose={() => setModalAbierto(false)}
        onGuardado={() => setRecarga((n) => n + 1)}
        adelanto={editando}
        empleados={empleados}
      />
    </>
  )
}
