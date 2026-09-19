import { useState } from 'react'
import { ActionIcon, Badge } from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconEdit, IconEye, IconTrash } from '@tabler/icons-react'
import { eliminarCuentaCorriente, listarCuentasCorrientes } from '../../api/cuentacorriente'
import { mensajeDeError } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import ListaCrud from '../../components/ListaCrud'
import type { CuentaCorriente } from '../../types/cuentacorriente'
import CuentaCorrienteDetalleModal from './CuentaCorrienteDetalleModal'
import CuentaCorrienteFormModal from './CuentaCorrienteFormModal'
import { formatearMonto } from '../ventas/dinero'

export default function CuentasCorrientesPage() {
  const { perfil } = useAuth()
  const puedeEditar = perfil?.is_staff ?? false
  const [modalFormAbierto, setModalFormAbierto] = useState(false)
  const [modalDetalleAbierto, setModalDetalleAbierto] = useState(false)
  const [seleccionada, setSeleccionada] = useState<CuentaCorriente | null>(null)
  const [recarga, setRecarga] = useState(0)

  const eliminar = async (c: CuentaCorriente) => {
    try {
      await eliminarCuentaCorriente(c.id)
      notifications.show({ message: 'Cuenta corriente eliminada.', color: 'green' })
      setRecarga((n) => n + 1)
    } catch (err) {
      const detalle = mensajeDeError(err)
      notifications.show({ title: 'No se pudo eliminar', message: detalle, color: 'red' })
    }
  }

  return (
    <>
      <ListaCrud<CuentaCorriente>
        titulo="Cuentas corrientes"
        subtitulo="Saldo y movimientos de cuenta corriente por cliente"
        listar={listarCuentasCorrientes}
        clave={(c) => c.id}
        porPagina={10}
        buscarPlaceholder="Buscar por nombre o documento del cliente…"
        puedeCrear={puedeEditar}
        nuevoLabel="Nueva cuenta"
        onNuevo={() => {
          setSeleccionada(null)
          setModalFormAbierto(true)
        }}
        disparadorRecarga={recarga}
        columnas={[
          { header: 'Cliente', render: (c) => c.cliente_nombre },
          { header: 'Saldo', render: (c) => formatearMonto(c.saldo) },
          { header: 'Tope', render: (c) => formatearMonto(c.tope) },
          {
            header: 'Estado',
            render: (c) => (
              <Badge color={c.activa ? 'green' : 'gray'} variant="light">
                {c.activa ? 'Activa' : 'Inactiva'}
              </Badge>
            ),
          },
        ]}
        accionesHeader={(c) => (
          <>
            <ActionIcon
              variant="subtle"
              aria-label="Ver movimientos"
              onClick={() => {
                setSeleccionada(c)
                setModalDetalleAbierto(true)
              }}
            >
              <IconEye size={16} />
            </ActionIcon>
            {puedeEditar && (
              <ActionIcon
                variant="subtle"
                aria-label="Editar"
                onClick={() => {
                  setSeleccionada(c)
                  setModalFormAbierto(true)
                }}
              >
                <IconEdit size={16} />
              </ActionIcon>
            )}
            {puedeEditar && (
              <ActionIcon color="red" variant="subtle" aria-label="Eliminar" onClick={() => void eliminar(c)}>
                <IconTrash size={16} />
              </ActionIcon>
            )}
          </>
        )}
      />
      <CuentaCorrienteFormModal
        opened={modalFormAbierto}
        onClose={() => setModalFormAbierto(false)}
        onGuardado={() => setRecarga((n) => n + 1)}
        cuenta={seleccionada}
      />
      <CuentaCorrienteDetalleModal
        opened={modalDetalleAbierto}
        onClose={() => setModalDetalleAbierto(false)}
        cuenta={seleccionada}
        onCambio={() => setRecarga((n) => n + 1)}
      />
    </>
  )
}
