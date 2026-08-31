import { useEffect, useState } from 'react'
import { ActionIcon, Button, Group, Modal, NumberInput, Select, Switch, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconEdit } from '@tabler/icons-react'
import { actualizarPlanTarjeta, crearPlanTarjeta, listarPlanesTarjetaPag, listarTodasLasTarjetas } from '../../api/caja'
import { ApiError } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import ListaCrud from '../../components/ListaCrud'
import type { PlanTarjetaDeCredito, PlanTarjetaDeCreditoInput, TarjetaDeCredito } from '../../types/caja'

const VACIO: PlanTarjetaDeCreditoInput = { tarjeta: 0, nombre_plan: '', interes: '0', es_vale: false }

function PlanFormModal({
  opened,
  onClose,
  onGuardado,
  plan,
  tarjetas,
}: {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
  plan: PlanTarjetaDeCredito | null
  tarjetas: TarjetaDeCredito[]
}) {
  const form = useForm<PlanTarjetaDeCreditoInput>({
    initialValues: VACIO,
    validate: { tarjeta: (v) => (v ? null : 'Elegí una tarjeta') },
  })

  useEffect(() => {
    if (opened) {
      form.setValues(
        plan ? { tarjeta: plan.tarjeta, nombre_plan: plan.nombre_plan, interes: plan.interes, es_vale: plan.es_vale } : VACIO,
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, plan])

  const guardar = form.onSubmit(async (valores) => {
    try {
      if (plan) await actualizarPlanTarjeta(plan.id, valores)
      else await crearPlanTarjeta(valores)
      notifications.show({ message: 'Guardado.', color: 'green' })
      onGuardado()
      onClose()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo guardar', message: detalle, color: 'red' })
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title={plan ? 'Editar plan' : 'Nuevo plan de tarjeta'}>
      <form onSubmit={guardar}>
        <Select
          label="Tarjeta"
          withAsterisk
          data={tarjetas.map((t) => ({ value: String(t.id), label: t.nombre }))}
          value={form.values.tarjeta ? String(form.values.tarjeta) : null}
          onChange={(v) => form.setFieldValue('tarjeta', v ? Number(v) : 0)}
          error={form.errors.tarjeta}
        />
        <TextInput label="Nombre del plan" withAsterisk mt="sm" placeholder="Ej: 3 pagos sin interés" {...form.getInputProps('nombre_plan')} />
        <NumberInput
          label="Interés"
          mt="sm"
          suffix="%"
          min={0}
          value={form.values.interes}
          onChange={(v) => form.setFieldValue('interes', String(v))}
        />
        <Switch
          label="Es vale (sin recargo real, sólo registro)"
          mt="md"
          checked={form.values.es_vale}
          onChange={(e) => form.setFieldValue('es_vale', e.currentTarget.checked)}
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

export default function PlanesTarjetaPage() {
  const { perfil } = useAuth()
  const puedeEditar = perfil?.is_staff ?? false
  const [modalAbierto, setModalAbierto] = useState(false)
  const [editando, setEditando] = useState<PlanTarjetaDeCredito | null>(null)
  const [recarga, setRecarga] = useState(0)
  const [tarjetas, setTarjetas] = useState<TarjetaDeCredito[]>([])

  useEffect(() => {
    listarTodasLasTarjetas()
      .then((r) => setTarjetas(r.results))
      .catch(() => notifications.show({ message: 'No se pudieron cargar las tarjetas.', color: 'red' }))
  }, [recarga])

  return (
    <>
      <ListaCrud<PlanTarjetaDeCredito>
        titulo="Planes de tarjeta"
        subtitulo="Planes de pago disponibles por tarjeta, con su interés"
        listar={listarPlanesTarjetaPag}
        clave={(p) => p.id}
        porPagina={10}
        sinBuscador
        puedeCrear={puedeEditar}
        nuevoLabel="Nuevo plan"
        onNuevo={() => {
          setEditando(null)
          setModalAbierto(true)
        }}
        disparadorRecarga={recarga}
        columnas={[
          { header: 'Tarjeta', render: (p) => p.tarjeta_nombre },
          { header: 'Plan', render: (p) => p.nombre_plan },
          { header: 'Interés', render: (p) => `${p.interes}%` },
        ]}
        accionesHeader={
          puedeEditar
            ? (p) => (
                <ActionIcon
                  variant="subtle"
                  aria-label="Editar"
                  onClick={() => {
                    setEditando(p)
                    setModalAbierto(true)
                  }}
                >
                  <IconEdit size={16} />
                </ActionIcon>
              )
            : undefined
        }
      />
      <PlanFormModal
        opened={modalAbierto}
        onClose={() => setModalAbierto(false)}
        onGuardado={() => setRecarga((n) => n + 1)}
        plan={editando}
        tarjetas={tarjetas}
      />
    </>
  )
}
