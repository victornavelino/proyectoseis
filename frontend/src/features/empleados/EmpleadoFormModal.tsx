import { useEffect, useState } from 'react'
import { Alert, Button, Group, Modal, Stack, Switch, Text, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { actualizarEmpleado, crearEmpleado } from '../../api/empleado'
import { ApiError } from '../../api/client'
import { buscarPersonaPorDocumento, crearPersona, obtenerPersona } from '../../api/persona'
import type { Empleado } from '../../types/empleado'
import type { Persona } from '../../types/persona'

interface Props {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
  empleado: Empleado | null
}

interface FormValores {
  documento_identidad: string
  nombre: string
  apellido: string
  cuil: string
  activo: boolean
}

const VACIO: FormValores = { documento_identidad: '', nombre: '', apellido: '', cuil: '', activo: true }

/** Mismo patrón que ClienteFormModal: busca la Persona por documento antes de crear una nueva
 * (no duplicar personas por el mismo documento). */
export default function EmpleadoFormModal({ opened, onClose, onGuardado, empleado }: Props) {
  const [personaEncontrada, setPersonaEncontrada] = useState<Persona | null>(null)
  const [buscando, setBuscando] = useState(false)
  const [yaBuscado, setYaBuscado] = useState(false)

  const form = useForm<FormValores>({
    initialValues: VACIO,
    validate: {
      documento_identidad: (v) => (v.trim() ? null : 'Requerido'),
      cuil: (v) => (v.trim() ? null : 'Requerido'),
    },
  })

  useEffect(() => {
    if (!opened) return
    if (empleado) {
      obtenerPersona(empleado.persona)
        .then((persona) => {
          setPersonaEncontrada(persona)
          setYaBuscado(true)
          form.setValues({
            documento_identidad: persona.documento_identidad,
            nombre: persona.nombre,
            apellido: persona.apellido,
            cuil: empleado.cuil,
            activo: empleado.activo,
          })
        })
        .catch(() => notifications.show({ message: 'No se pudo cargar la persona.', color: 'red' }))
    } else {
      form.setValues(VACIO)
      setPersonaEncontrada(null)
      setYaBuscado(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, empleado])

  const buscarPersona = async () => {
    const documento = form.values.documento_identidad.trim()
    if (!documento) {
      form.setFieldError('documento_identidad', 'Ingresá un documento primero')
      return
    }
    setBuscando(true)
    try {
      const personaId = await buscarPersonaPorDocumento(documento)
      if (personaId) {
        const persona = await obtenerPersona(personaId)
        setPersonaEncontrada(persona)
        form.setValues({ ...form.values, nombre: persona.nombre, apellido: persona.apellido })
      } else {
        setPersonaEncontrada(null)
      }
      setYaBuscado(true)
    } catch (err) {
      notifications.show({ title: 'Error al buscar', message: (err as Error).message, color: 'red' })
    } finally {
      setBuscando(false)
    }
  }

  const guardar = form.onSubmit(async (valores) => {
    try {
      let personaId = personaEncontrada?.id
      if (!personaId) {
        const nuevaPersona = await crearPersona({
          nombre: valores.nombre,
          apellido: valores.apellido,
          documento_identidad: valores.documento_identidad,
          fecha_nacimiento: null,
          domicilio: null,
          correo_electronico: null,
          telefonos: [],
        })
        personaId = nuevaPersona.id
      }
      const datos = { persona: personaId, cuil: valores.cuil, fecha_baja: valores.activo ? null : new Date().toISOString().slice(0, 10) }
      if (empleado) await actualizarEmpleado(empleado.id, datos)
      else await crearEmpleado(datos)
      notifications.show({ message: 'Guardado.', color: 'green' })
      onGuardado()
      onClose()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo guardar', message: detalle, color: 'red' })
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title={empleado ? 'Editar empleado' : 'Nuevo empleado'}>
      <form onSubmit={guardar}>
        <Group align="flex-end">
          <TextInput
            label="Documento de identidad"
            withAsterisk
            disabled={!!empleado}
            style={{ flex: 1 }}
            {...form.getInputProps('documento_identidad')}
          />
          {!empleado && (
            <Button variant="light" loading={buscando} type="button" onClick={() => void buscarPersona()}>
              Buscar
            </Button>
          )}
        </Group>

        {!empleado && yaBuscado && personaEncontrada && (
          <Alert color="blue" mt="sm">
            Ya existe una persona con ese documento: <strong>{personaEncontrada.apellido}, {personaEncontrada.nombre}</strong>.
          </Alert>
        )}
        {!empleado && yaBuscado && !personaEncontrada && (
          <Text size="sm" c="dimmed" mt="sm">
            No existe — completá los datos para crearla.
          </Text>
        )}

        {(empleado || (yaBuscado && !personaEncontrada)) && (
          <Stack gap="sm" mt="sm">
            <TextInput label="Nombre" withAsterisk disabled={!!empleado} {...form.getInputProps('nombre')} />
            <TextInput label="Apellido" withAsterisk disabled={!!empleado} {...form.getInputProps('apellido')} />
          </Stack>
        )}

        {(empleado || yaBuscado) && (
          <>
            <TextInput label="CUIL" withAsterisk mt="sm" {...form.getInputProps('cuil')} />
            {empleado && (
              <Switch label="Activo" mt="md" {...form.getInputProps('activo', { type: 'checkbox' })} />
            )}
          </>
        )}

        <Group justify="flex-end" mt="lg">
          <Button variant="default" type="button" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" color="red" disabled={!empleado && !yaBuscado}>
            Guardar
          </Button>
        </Group>
      </form>
    </Modal>
  )
}
