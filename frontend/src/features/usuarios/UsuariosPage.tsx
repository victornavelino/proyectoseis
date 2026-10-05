import { useState } from 'react'
import { ActionIcon, Badge, Button, Group, Modal, Text } from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconEdit, IconTrash } from '@tabler/icons-react'
import { eliminarUsuarioSucursal, listarUsuariosSucursal } from '../../api/usuario'
import { mensajeDeError } from '../../api/client'
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
  // Borrado permanente (ver usuario.api.UsuarioSucursalViewSet.destroy) — sin confirmación
  // explícita es un click de más en una fila que elimina la cuenta de verdad, no un soft-delete.
  const [aEliminar, setAEliminar] = useState<UsuarioSucursal | null>(null)
  const [eliminando, setEliminando] = useState(false)

  const confirmarEliminar = async () => {
    if (!aEliminar) return
    setEliminando(true)
    try {
      await eliminarUsuarioSucursal(aEliminar.id)
      notifications.show({ message: 'Usuario eliminado.', color: 'green' })
      setAEliminar(null)
      setRecarga((n) => n + 1)
    } catch (err) {
      notifications.show({ title: 'No se pudo eliminar', message: mensajeDeError(err), color: 'red' })
    } finally {
      setEliminando(false)
    }
  }

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
                <Group gap="xs" wrap="nowrap">
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
                  <ActionIcon color="red" variant="subtle" aria-label="Eliminar" onClick={() => setAEliminar(u)}>
                    <IconTrash size={16} />
                  </ActionIcon>
                </Group>
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
      <Modal opened={aEliminar !== null} onClose={() => setAEliminar(null)} title="Eliminar usuario" centered>
        <Text size="sm">
          ¿Estás seguro de que querés eliminar al usuario <strong>{aEliminar?.username}</strong>? El usuario se
          eliminará permanentemente — esta acción no se puede deshacer.
        </Text>
        <Group justify="flex-end" mt="lg">
          <Button variant="default" onClick={() => setAEliminar(null)} disabled={eliminando}>
            Cancelar
          </Button>
          <Button color="red" loading={eliminando} onClick={() => void confirmarEliminar()}>
            Eliminar
          </Button>
        </Group>
      </Modal>
    </>
  )
}
