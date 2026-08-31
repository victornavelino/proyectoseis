import { useState } from 'react'
import { ActionIcon, Badge } from '@mantine/core'
import { IconEdit, IconEye } from '@tabler/icons-react'
import { listarCuentasCorrientes } from '../../api/cuentacorriente'
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
