import { useEffect } from 'react'
import { Button, Group, Modal, PasswordInput, Stack, Switch, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { actualizarUsuarioSucursal, crearUsuarioSucursal } from '../../api/usuario'
import { ApiError } from '../../api/client'
import type { UsuarioSucursal } from '../../types/usuario'

interface Props {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
  usuario: UsuarioSucursal | null
}

interface FormValores {
  username: string
  password: string
  first_name: string
  last_name: string
  email: string
  is_active: boolean
}

const VACIO: FormValores = { username: '', password: '', first_name: '', last_name: '', email: '', is_active: true }

export default function UsuarioSucursalFormModal({ opened, onClose, onGuardado, usuario }: Props) {
  const form = useForm<FormValores>({
    initialValues: VACIO,
    validate: {
      username: (v) => (v.trim() ? null : 'Requerido'),
      password: (v) => (!usuario && !v.trim() ? 'Requerido' : null),
    },
  })

  useEffect(() => {
    if (!opened) return
    form.setValues(
      usuario
        ? {
            username: usuario.username,
            password: '',
            first_name: usuario.first_name,
            last_name: usuario.last_name,
            email: usuario.email,
            is_active: usuario.is_active,
          }
        : VACIO,
    )
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, usuario])

  const guardar = form.onSubmit(async (valores) => {
    try {
      if (usuario) {
        const { password: _password, ...datos } = valores
        await actualizarUsuarioSucursal(usuario.id, datos)
      } else {
        await crearUsuarioSucursal(valores)
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
    <Modal opened={opened} onClose={onClose} title={usuario ? 'Editar usuario' : 'Nuevo usuario'}>
      <form onSubmit={guardar}>
        <Stack gap="sm">
          <TextInput
            label="Usuario"
            withAsterisk
            disabled={!!usuario}
            {...form.getInputProps('username')}
          />
          {!usuario && (
            <PasswordInput label="Contraseña" withAsterisk {...form.getInputProps('password')} />
          )}
          <TextInput label="Nombre" {...form.getInputProps('first_name')} />
          <TextInput label="Apellido" {...form.getInputProps('last_name')} />
          <TextInput label="Email" type="email" {...form.getInputProps('email')} />
          {usuario && <Switch label="Activo" {...form.getInputProps('is_active', { type: 'checkbox' })} />}
        </Stack>

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
