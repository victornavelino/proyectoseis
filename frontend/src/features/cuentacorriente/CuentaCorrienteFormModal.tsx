import { useEffect, useState } from 'react'
import { Button, Group, Modal, NumberInput, Switch, Text, Textarea } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { actualizarCuentaCorriente, crearCuentaCorriente } from '../../api/cuentacorriente'
import { ApiError } from '../../api/client'
import BuscadorLista from '../../components/BuscadorLista'
import { listarClientes } from '../../api/cliente'
import type { Cliente } from '../../types/cliente'
import type { CuentaCorriente } from '../../types/cuentacorriente'

interface Props {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
  cuenta: CuentaCorriente | null
}

interface FormValores {
  tope: string
  observaciones: string
  activa: boolean
}

export default function CuentaCorrienteFormModal({ opened, onClose, onGuardado, cuenta }: Props) {
  const [cliente, setCliente] = useState<Cliente | null>(null)

  const form = useForm<FormValores>({ initialValues: { tope: '100000', observaciones: '', activa: true } })

  useEffect(() => {
    if (opened) {
      setCliente(null)
      form.setValues(
        cuenta
          ? { tope: cuenta.tope, observaciones: cuenta.observaciones ?? '', activa: cuenta.activa }
          : { tope: '100000', observaciones: '', activa: true },
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, cuenta])

  const guardar = form.onSubmit(async (valores) => {
    if (!cuenta && !cliente) {
      notifications.show({ title: 'Falta el cliente', message: 'Elegí un cliente primero.', color: 'red' })
      return
    }
    try {
      const datos = { tope: valores.tope, observaciones: valores.observaciones || null, activa: valores.activa }
      if (cuenta) {
        await actualizarCuentaCorriente(cuenta.id, { ...datos, cliente: cuenta.cliente })
      } else if (cliente) {
        await crearCuentaCorriente({ ...datos, cliente: cliente.id })
      }
      notifications.show({ message: 'Guardado.', color: 'green' })
      onGuardado()
      onClose()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo guardar', message: detalle, color: 'red' })
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title={cuenta ? 'Editar cuenta corriente' : 'Nueva cuenta corriente'}>
      <form onSubmit={guardar}>
        {cuenta ? (
          <Text size="sm" fw={500}>
            {cuenta.cliente_nombre}
          </Text>
        ) : cliente ? (
          <Group justify="space-between">
            <Text size="sm">
              {cliente.persona_detalle.apellido}, {cliente.persona_detalle.nombre}
            </Text>
            <Button size="xs" variant="subtle" type="button" onClick={() => setCliente(null)}>
              Cambiar
            </Button>
          </Group>
        ) : (
          <BuscadorLista<Cliente>
            placeholder="Buscar cliente…"
            buscar={(q) => listarClientes({ search: q }).then((r) => r.results)}
            clave={(c) => c.id}
            onSeleccionar={setCliente}
            renderItem={(c) => (
              <Text size="sm">
                {c.persona_detalle.apellido}, {c.persona_detalle.nombre}
              </Text>
            )}
          />
        )}

        <NumberInput
          label="Tope máximo"
          mt="sm"
          decimalScale={2}
          min={0}
          value={form.values.tope}
          onChange={(v) => form.setFieldValue('tope', String(v))}
        />
        <Textarea label="Observaciones" mt="sm" {...form.getInputProps('observaciones')} />
        {cuenta && (
          <Switch
            label="Activa"
            mt="md"
            checked={form.values.activa}
            onChange={(e) => form.setFieldValue('activa', e.currentTarget.checked)}
          />
        )}

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
