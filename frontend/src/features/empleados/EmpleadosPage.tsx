import { useState } from 'react'
import { ActionIcon, Badge } from '@mantine/core'
import { IconEdit } from '@tabler/icons-react'
import { listarEmpleados } from '../../api/empleado'
import { useAuth } from '../../auth/AuthContext'
import ListaCrud from '../../components/ListaCrud'
import type { Empleado } from '../../types/empleado'
import EmpleadoFormModal from './EmpleadoFormModal'

export default function EmpleadosPage() {
  const { perfil } = useAuth()
  const puedeEditar = perfil?.is_staff ?? false
  const [modalAbierto, setModalAbierto] = useState(false)
  const [editando, setEditando] = useState<Empleado | null>(null)
  const [recarga, setRecarga] = useState(0)

  return (
    <>
      <ListaCrud<Empleado>
        titulo="Empleados"
        subtitulo="Personal que puede atender ventas"
        listar={listarEmpleados}
        clave={(e) => e.id}
        porPagina={10}
        buscarPlaceholder="Buscar por nombre, apellido o CUIL…"
        puedeCrear={puedeEditar}
        nuevoLabel="Nuevo empleado"
        onNuevo={() => {
          setEditando(null)
          setModalAbierto(true)
        }}
        disparadorRecarga={recarga}
        columnas={[
          { header: 'Nombre', render: (e) => e.persona_nombre },
          { header: 'CUIL', render: (e) => e.cuil },
          {
            header: 'Estado',
            render: (e) => (
              <Badge color={e.activo ? 'green' : 'gray'} variant="light">
                {e.activo ? 'Activo' : 'Inactivo'}
              </Badge>
            ),
          },
        ]}
        accionesHeader={
          puedeEditar
            ? (e) => (
                <ActionIcon
                  variant="subtle"
                  aria-label="Editar"
                  onClick={() => {
                    setEditando(e)
                    setModalAbierto(true)
                  }}
                >
                  <IconEdit size={16} />
                </ActionIcon>
              )
            : undefined
        }
      />
      <EmpleadoFormModal
        opened={modalAbierto}
        onClose={() => setModalAbierto(false)}
        onGuardado={() => setRecarga((n) => n + 1)}
        empleado={editando}
      />
    </>
  )
}
