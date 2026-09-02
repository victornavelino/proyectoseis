import { useState } from 'react'
import { ActionIcon, Badge } from '@mantine/core'
import { IconEdit } from '@tabler/icons-react'
import { listarUsuariosSucursal } from '../../api/usuario'
import { useAuth } from '../../auth/AuthContext'
import ListaCrud from '../../components/ListaCrud'
import type { UsuarioSucursal } from '../../types/usuario'
import UsuarioSucursalFormModal from './UsuarioSucursalFormModal'

/** Alta de usuarios operativos (cajeros, etc.) de la propia sucursal — el backend
 * (UsuarioSucursalViewSet) sólo lista/permite crear usuarios de la sucursal del encargado
 * logueado, así que acá no hace falta elegir ni mostrar la sucursal. */
export default function UsuariosPage() {
  const { perfil } = useAuth()
  const puedeEditar = perfil?.is_staff ?? false
  const [modalAbierto, setModalAbierto] = useState(false)
  const [editando, setEditando] = useState<UsuarioSucursal | null>(null)
  const [recarga, setRecarga] = useState(0)

  return (
    <>
      <ListaCrud<UsuarioSucursal>
        titulo="Usuarios"
        subtitulo="Cuentas para operar el sistema en esta sucursal"
        listar={listarUsuariosSucursal}
        clave={(u) => u.id}
        porPagina={10}
        buscarPlaceholder="Buscar por usuario, nombre o email…"
        puedeCrear={puedeEditar}
        nuevoLabel="Nuevo usuario"
        onNuevo={() => {
          setEditando(null)
          setModalAbierto(true)
        }}
        disparadorRecarga={recarga}
        columnas={[
          { header: 'Usuario', render: (u) => u.username },
          { header: 'Nombre', render: (u) => `${u.first_name} ${u.last_name}`.trim() },
          { header: 'Email', render: (u) => u.email },
          {
            header: 'Estado',
            render: (u) => (
              <Badge color={u.is_active ? 'green' : 'gray'} variant="light">
                {u.is_active ? 'Activo' : 'Inactivo'}
              </Badge>
            ),
          },
        ]}
        accionesHeader={
          puedeEditar
            ? (u) => (
                <ActionIcon
                  variant="subtle"
                  aria-label="Editar"
                  onClick={() => {
                    setEditando(u)
                    setModalAbierto(true)
                  }}
                >
                  <IconEdit size={16} />
                </ActionIcon>
              )
            : undefined
        }
      />
      <UsuarioSucursalFormModal
        opened={modalAbierto}
        onClose={() => setModalAbierto(false)}
        onGuardado={() => setRecarga((n) => n + 1)}
        usuario={editando}
      />
    </>
  )
}
