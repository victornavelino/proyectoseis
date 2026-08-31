import { useEffect, useState } from 'react'
import { Alert, Button, Divider, Group, Modal, Select, Stack, Text, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { crearCliente, listarListasPrecio } from '../../api/cliente'
import { ApiError } from '../../api/client'
import { buscarPersonaPorDocumento, crearPersona, obtenerPersona } from '../../api/persona'
import type { Cliente, CondicionIva } from '../../types/cliente'
import type { ListaPrecio } from '../../types/articulo'
import type { Persona } from '../../types/persona'

interface Props {
  opened: boolean
  onClose: () => void
  onGuardado: () => void
}

const CONDICIONES_IVA: { value: CondicionIva; label: string }[] = [
  { value: 'cf', label: 'Consumidor final' },
  { value: 'ri', label: 'Responsable inscripto' },
  { value: 'rn', label: 'Responsable no inscripto' },
  { value: 'ex', label: 'Exento' },
  { value: 'mo', label: 'Monotributo' },
]

interface FormValores {
  documento_identidad: string
  nombre: string
  apellido: string
  fecha_nacimiento: string
  domicilio: string
  correo_electronico: string
  telefono: string
  condicion_iva: CondicionIva
  lista_precio: number | null
}

const VALORES_VACIOS: FormValores = {
  documento_identidad: '',
  nombre: '',
  apellido: '',
  fecha_nacimiento: '',
  domicilio: '',
  correo_electronico: '',
  telefono: '',
  condicion_iva: 'cf',
  lista_precio: null,
}

/** Alta de cliente: primero busca si ya existe una Persona con ese documento (reutiliza el
 * mismo patrón que usuario.api.RegistroUsuarioAPIView.crear_persona del backend — no duplicar
 * personas por el mismo documento); si no existe, la crea de cero. */
export default function ClienteFormModal({ opened, onClose, onGuardado }: Props) {
  const [listasPrecio, setListasPrecio] = useState<ListaPrecio[]>([])
  const [personaEncontrada, setPersonaEncontrada] = useState<Persona | null>(null)
  const [buscando, setBuscando] = useState(false)
  const [yaBuscado, setYaBuscado] = useState(false)

  const form = useForm<FormValores>({
    initialValues: VALORES_VACIOS,
    validate: {
      documento_identidad: (v) => (v.trim() ? null : 'Requerido'),
      nombre: (v, valores) => (!personaEncontradaDe(valores) && !v.trim() ? 'Requerido' : null),
      apellido: (v, valores) => (!personaEncontradaDe(valores) && !v.trim() ? 'Requerido' : null),
    },
  })

  // Helper para poder usarlo dentro de `validate` (que no tiene acceso directo al state de arriba
  // por closures de useForm en el momento de declaración) — se resuelve leyendo el ref actual.
  function personaEncontradaDe(_valores: FormValores) {
    return personaEncontrada !== null
  }

  useEffect(() => {
    if (opened) {
      form.setValues(VALORES_VACIOS)
      setPersonaEncontrada(null)
      setYaBuscado(false)
      listarListasPrecio()
        .then((r) => setListasPrecio(r.results))
        .catch(() => notifications.show({ message: 'No se pudieron cargar las listas de precio.', color: 'red' }))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened])

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
        })
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
          fecha_nacimiento: valores.fecha_nacimiento || null,
          domicilio: valores.domicilio || null,
          correo_electronico: valores.correo_electronico || null,
          telefonos: valores.telefono ? [{ tipo: 'celular', numero: valores.telefono }] : [],
        })
        personaId = nuevaPersona.id
      }
      const cliente: Cliente = await crearCliente({
        persona: personaId,
        condicion_iva: valores.condicion_iva,
        lista_precio: valores.lista_precio,
      })
      notifications.show({ message: `Cliente "${cliente.persona_detalle.apellido}, ${cliente.persona_detalle.nombre}" creado.`, color: 'green' })
      onGuardado()
      onClose()
    } catch (err) {
      const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
      notifications.show({ title: 'No se pudo guardar', message: detalle, color: 'red' })
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title="Nuevo cliente" size="md">
      <form onSubmit={guardar}>
        <Group align="flex-end">
          <TextInput
            label="Documento de identidad"
            withAsterisk
            style={{ flex: 1 }}
            {...form.getInputProps('documento_identidad')}
          />
          <Button variant="light" loading={buscando} onClick={() => void buscarPersona()} type="button">
            Buscar
          </Button>
        </Group>

        {yaBuscado && personaEncontrada && (
          <Alert color="blue" mt="sm">
            Ya existe una persona con ese documento: <strong>{personaEncontrada.apellido}, {personaEncontrada.nombre}</strong>.
            Se va a usar esa persona para el cliente nuevo.
          </Alert>
        )}
        {yaBuscado && !personaEncontrada && (
          <Text size="sm" c="dimmed" mt="sm">
            No existe ninguna persona con ese documento — completá los datos para crearla.
          </Text>
        )}

        {yaBuscado && !personaEncontrada && (
          <Stack gap="sm" mt="sm">
            <TextInput label="Nombre" withAsterisk {...form.getInputProps('nombre')} />
            <TextInput label="Apellido" withAsterisk {...form.getInputProps('apellido')} />
            <TextInput label="Fecha de nacimiento" type="date" {...form.getInputProps('fecha_nacimiento')} />
            <TextInput label="Domicilio" {...form.getInputProps('domicilio')} />
            <TextInput label="Correo electrónico" {...form.getInputProps('correo_electronico')} />
            <TextInput label="Teléfono" {...form.getInputProps('telefono')} />
          </Stack>
        )}

        {yaBuscado && (
          <>
            <Divider my="md" />
            <Select
              label="Condición frente al IVA"
              data={CONDICIONES_IVA}
              value={form.values.condicion_iva}
              onChange={(v) => form.setFieldValue('condicion_iva', (v as CondicionIva) ?? 'cf')}
            />
            <Select
              label="Lista de precios"
              mt="sm"
              clearable
              data={listasPrecio.map((l) => ({ value: String(l.id), label: l.nombre }))}
              value={form.values.lista_precio ? String(form.values.lista_precio) : null}
              onChange={(v) => form.setFieldValue('lista_precio', v ? Number(v) : null)}
            />
          </>
        )}

        <Group justify="flex-end" mt="lg">
          <Button variant="default" onClick={onClose} type="button">
            Cancelar
          </Button>
          <Button type="submit" color="red" disabled={!yaBuscado}>
            Guardar
          </Button>
        </Group>
      </form>
    </Modal>
  )
}
