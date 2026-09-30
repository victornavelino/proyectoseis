import { useEffect, useState } from 'react'
import { ActionIcon, Group } from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconEdit, IconTrash } from '@tabler/icons-react'
import { eliminarPrecio, listarListasPrecioPag, listarPrecios } from '../../api/articulo'
import { mensajeDeError } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import ListaCrud from '../../components/ListaCrud'
import type { ListaPrecio, Precio } from '../../types/articulo'
import PrecioFormModal from './PrecioFormModal'
import { formatearMonto } from '../ventas/dinero'

export default function PreciosPage() {
  const { perfil } = useAuth()
  const puedeEditar = perfil?.is_staff ?? false
  const [modalAbierto, setModalAbierto] = useState(false)
  const [editando, setEditando] = useState<Precio | null>(null)
  const [recarga, setRecarga] = useState(0)
  const [listasPrecio, setListasPrecio] = useState<ListaPrecio[]>([])

  useEffect(() => {
    listarListasPrecioPag({ pagina: 1 })
      .then((r) => setListasPrecio(r.results))
      .catch(() => notifications.show({ message: 'No se pudieron cargar las listas de precio.', color: 'red' }))
  }, [])

  const eliminar = async (precio: Precio) => {
    try {
      await eliminarPrecio(precio.id)
      notifications.show({ message: 'Precio eliminado.', color: 'green' })
      setRecarga((n) => n + 1)
    } catch (err) {
      notifications.show({ title: 'No se pudo eliminar', message: mensajeDeError(err), color: 'red' })
    }
  }

  return (
    <>
      <ListaCrud<Precio>
        titulo="Precios"
        subtitulo="Precio de cada artículo por sucursal y lista de precios"
        listar={listarPrecios}
        clave={(p) => p.id}
        porPagina={10}
        sinBuscador
        puedeCrear={puedeEditar}
        nuevoLabel="Nuevo precio"
        onNuevo={() => {
          setEditando(null)
          setModalAbierto(true)
        }}
        disparadorRecarga={recarga}
        columnas={[
          { header: 'Artículo', render: (p) => `${p.articulo_nombre} (${p.articulo_codigo})` },
          { header: 'Sucursal', render: (p) => p.sucursal_nombre },
          { header: 'Lista', render: (p) => p.lista_precio_nombre },
          { header: 'Precio', render: (p) => formatearMonto(p.precio) },
        ]}
        accionesHeader={
          puedeEditar
            ? (p) => (
                <Group gap="xs" wrap="nowrap">
                  <ActionIcon
                    variant="subtle"
                    aria-label="Editar"
                    onClick={() => {
                      setEditando(p)
                      setModalAbierto(true)
                    }}
                  >
                    <IconEdit size={16} />
                  </ActionIcon>
                  <ActionIcon color="red" variant="subtle" aria-label="Eliminar" onClick={() => void eliminar(p)}>
                    <IconTrash size={16} />
                  </ActionIcon>
                </Group>
              )
            : undefined
        }
      />
      <PrecioFormModal
        opened={modalAbierto}
        onClose={() => setModalAbierto(false)}
        onGuardado={() => setRecarga((n) => n + 1)}
        precio={editando}
        listasPrecio={listasPrecio}
      />
    </>
  )
}
