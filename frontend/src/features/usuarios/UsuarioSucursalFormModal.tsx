import { useEffect, useState } from 'react'
import { Alert, Button, Divider, Group, Modal, PasswordInput, Stack, Switch, Text, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { actualizarUsuarioSucursal, crearUsuarioSucursal } from '../../api/usuario'
import { mensajeDeError } from '../../api/client'
import { buscarPersonaPorDocumento, crearPersona, obtenerPersona } from '../../api/persona'
import { actualizarEmpleado, buscarEmpleadoPorPersona, crearEmpleado } from '../../api/empleado'
import type { Empleado } from '../../types/empleado'
import type { Persona } from '../../types/persona'
import type { UsuarioSucursal } from '../../types/usuario'

interface Props {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
  usuario: UsuarioSucursal | null
}

interface FormValores {
  documento_identidad: string
  nombre: string
  apellido: string
  fecha_nacimiento: string
  domicilio: string
  correo_electronico: string
  telefono: string
  cuil: string
  username: string
  password: string
  email: string
  is_active: boolean
}

const VACIO: FormValores = {
  documento_identidad: '',
  nombre: '',
  apellido: '',
  fecha_nacimiento: '',
  domicilio: '',
  correo_electronico: '',
  telefono: '',
  cuil: '',
  username: '',
  password: '',
  email: '',
  is_active: true,
}

/** Da de alta Persona + Empleado + Usuario en una sola pantalla (mismo patrón de "buscar por
 * documento antes de crear" que Cliente/EmpleadoFormModal) — así un encargado de sucursal no
 * necesita pasar por /admin para cargar a alguien nuevo. Lo único que sigue siendo exclusivo
 * del /admin son los permisos: is_staff, grupos y permisos puntuales (ver
 * usuario.serializers.UsuarioSucursalSerializer). */
export default function UsuarioSucursalFormModal({ opened, onClose, onGuardado, usuario }: Props) {
  const editando = usuario !== null
  const tieneEmpleadoVinculado = editando && usuario.empleado_detalle !== null

  const [personaEncontrada, setPersonaEncontrada] = useState<Persona | null>(null)
  const [empleadoEncontrado, setEmpleadoEncontrado] = useState<Empleado | null>(null)
  const [buscando, setBuscando] = useState(false)
  const [yaBuscado, setYaBuscado] = useState(false)
  // Al editar una cuenta que todavía no tiene empleado vinculado, la búsqueda por documento es
  // opcional — este estado la muestra/oculta. Al crear, siempre está visible (no hay nada que
  // mostrar/ocultar).
  const [mostrarBusqueda, setMostrarBusqueda] = useState(!editando)

  const form = useForm<FormValores>({
    initialValues: VACIO,
    validate: {
      username: (v) => (v.trim() ? null : 'Requerido'),
      password: (v) => (!editando && !v.trim() ? 'Requerido' : null),
      documento_identidad: (v) => (mostrarBusqueda && v.trim() === '' ? 'Requerido' : null),
      nombre: (v) => (mostrarBusqueda && !personaEncontrada && !v.trim() ? 'Requerido' : null),
      apellido: (v) => (mostrarBusqueda && !personaEncontrada && !v.trim() ? 'Requerido' : null),
      cuil: (v) => (mostrarBusqueda && !v.trim() ? 'Requerido' : null),
    },
  })

  useEffect(() => {
    if (!opened) return
    setPersonaEncontrada(null)
    setEmpleadoEncontrado(null)
    setYaBuscado(false)
    setMostrarBusqueda(!editando)
    if (usuario) {
      form.setValues({
        ...VACIO,
        username: usuario.username,
        email: usuario.email,
        is_active: usuario.is_active,
        nombre: usuario.first_name,
        apellido: usuario.last_name,
        cuil: usuario.empleado_detalle?.cuil ?? '',
        documento_identidad: usuario.empleado_detalle?.documento_identidad ?? '',
      })
    } else {
      form.setValues(VACIO)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, usuario])

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
        form.setValues({
          ...form.values,
          nombre: persona.nombre,
          apellido: persona.apellido,
          fecha_nacimiento: persona.fecha_nacimiento ?? '',
          domicilio: persona.domicilio ?? '',
          correo_electronico: persona.correo_electronico ?? '',
          email: form.values.email || persona.correo_electronico || '',
        })
        const empleado = await buscarEmpleadoPorPersona(persona.id)
        setEmpleadoEncontrado(empleado)
        if (empleado) form.setFieldValue('cuil', empleado.cuil)
      } else {
        setPersonaEncontrada(null)
        setEmpleadoEncontrado(null)
      }
      setYaBuscado(true)
    } catch (err) {
      notifications.show({ title: 'Error al buscar', message: mensajeDeError(err), color: 'red' })
    } finally {
      setBuscando(false)
    }
  }

  const guardar = form.onSubmit(async (valores) => {
    try {
      let empleadoId: number | null = usuario?.empleado ?? null
      let nombre = valores.nombre
      let apellido = valores.apellido

      if (mostrarBusqueda) {
        let personaId = personaEncontrada?.id
        if (!personaId) {
          const nuevaPersona = await crearPersona({
            nombre: valores.nombre,
            apellido: valores.apellido,
            documento_identidad: valores.documento_identidad,
            fecha_nacimiento: valores.fecha_nacimiento || null,
            domicilio: valores.domicilio || null,
            correo_electronico: valores.correo_electronico || null,
            telefonos: valores.telefono ? [{ tipo: 'celular', numero: valores.telefono }] : [],
          })
          personaId = nuevaPersona.id
        }
        const datosEmpleado = { persona: personaId, cuil: valores.cuil, fecha_baja: null }
        if (empleadoEncontrado) {
          await actualizarEmpleado(empleadoEncontrado.id, datosEmpleado)
          empleadoId = empleadoEncontrado.id
        } else {
          const nuevoEmpleado = await crearEmpleado(datosEmpleado)
          empleadoId = nuevoEmpleado.id
        }
      } else if (tieneEmpleadoVinculado && usuario.empleado_detalle) {
        // Edición sin re-vincular: el nombre/apellido siguen siendo los de la Persona (de sólo
        // lectura acá), no los que pudiera traer el form.
        nombre = usuario.empleado_detalle.nombre
        apellido = usuario.empleado_detalle.apellido
      }

      const datosUsuario = {
        username: valores.username,
        email: valores.email,
        first_name: nombre,
        last_name: apellido,
        is_active: valores.is_active,
        empleado: empleadoId,
      }

      if (editando && usuario) {
        await actualizarUsuarioSucursal(usuario.id, datosUsuario)
      } else {
        await crearUsuarioSucursal({ ...datosUsuario, password: valores.password })
      }
      notifications.show({ message: 'Guardado.', color: 'green' })
      onGuardado()
      onClose()
    } catch (err) {
      const detalle = mensajeDeError(err)
      notifications.show({ title: 'No se pudo guardar', message: detalle, color: 'red' })
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title={editando ? 'Editar usuario' : 'Nuevo usuario'} size="md">
      <form onSubmit={guardar}>
        <Stack gap="sm">
          {tieneEmpleadoVinculado && usuario.empleado_detalle && (
            <Text size="sm">
              <strong>
                {usuario.empleado_detalle.apellido}, {usuario.empleado_detalle.nombre}
              </strong>{' '}
              — Doc. {usuario.empleado_detalle.documento_identidad}
            </Text>
          )}

          {editando && !tieneEmpleadoVinculado && !mostrarBusqueda && (
            <>
              <Alert color="yellow">
                Esta cuenta todavía no tiene un empleado vinculado.{' '}
                <Button variant="subtle" size="compact-sm" onClick={() => setMostrarBusqueda(true)}>
                  Vincular a un empleado
                </Button>
              </Alert>
              <TextInput label="Nombre" withAsterisk {...form.getInputProps('nombre')} />
              <TextInput label="Apellido" withAsterisk {...form.getInputProps('apellido')} />
            </>
          )}

          {mostrarBusqueda && (
            <>
              <Group align="flex-end">
                <TextInput
                  label="Documento de identidad"
                  withAsterisk
                  style={{ flex: 1 }}
                  {...form.getInputProps('documento_identidad')}
                />
                <Button variant="light" loading={buscando} type="button" onClick={() => void buscarPersona()}>
                  Buscar
                </Button>
                {editando && !tieneEmpleadoVinculado && (
                  <Button variant="default" type="button" onClick={() => setMostrarBusqueda(false)}>
                    Cancelar
                  </Button>
                )}
              </Group>

              {yaBuscado && personaEncontrada && (
                <Alert color="blue">
                  Ya existe una persona con ese documento:{' '}
                  <strong>
                    {personaEncontrada.apellido}, {personaEncontrada.nombre}
                  </strong>
                  {empleadoEncontrado ? ' — también tiene un legajo de empleado, se va a reutilizar.' : '.'}
                </Alert>
              )}
              {yaBuscado && !personaEncontrada && (
                <Text size="sm" c="dimmed">
                  No existe ninguna persona con ese documento — completá los datos para crearla.
                </Text>
              )}

              {yaBuscado && !personaEncontrada && (
                <Stack gap="sm">
                  <TextInput label="Nombre" withAsterisk {...form.getInputProps('nombre')} />
                  <TextInput label="Apellido" withAsterisk {...form.getInputProps('apellido')} />
                  <TextInput label="Fecha de nacimiento" type="date" {...form.getInputProps('fecha_nacimiento')} />
                  <TextInput label="Domicilio" {...form.getInputProps('domicilio')} />
                  <TextInput label="Correo electrónico" {...form.getInputProps('correo_electronico')} />
                  <TextInput label="Teléfono" {...form.getInputProps('telefono')} />
                </Stack>
              )}

              {yaBuscado && <TextInput label="CUIL" withAsterisk {...form.getInputProps('cuil')} />}
            </>
          )}

          {tieneEmpleadoVinculado && <TextInput label="CUIL" withAsterisk {...form.getInputProps('cuil')} />}

          <Divider />

          <TextInput label="Usuario" withAsterisk disabled={editando} {...form.getInputProps('username')} />
          {!editando && <PasswordInput label="Contraseña" withAsterisk {...form.getInputProps('password')} />}
          <TextInput label="Email" type="email" {...form.getInputProps('email')} />
          {editando && <Switch label="Activo" {...form.getInputProps('is_active', { type: 'checkbox' })} />}
        </Stack>

        <Group justify="flex-end" mt="lg">
          <Button variant="default" type="button" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" color="red" disabled={mostrarBusqueda && !editando && !yaBuscado}>
            Guardar
          </Button>
        </Group>
      </form>
    </Modal>
  )
}
