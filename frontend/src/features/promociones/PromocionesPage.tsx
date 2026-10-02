import { useEffect, useState } from 'react'
import { ActionIcon, Badge, Group } from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconEdit, IconTrash } from '@tabler/icons-react'
import { listarTodasLasSucursales } from '../../api/empleado'
import { eliminarPromocion, listarPromociones } from '../../api/promocion'
import { mensajeDeError } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import ListaCrud from '../../components/ListaCrud'
import type { Sucursal } from '../../types/empleado'
import type { Promocion } from '../../types/promocion'
import PromocionFormModal from './PromocionFormModal'

export default function PromocionesPage() {
  const { puedeEscribir, puedeBorrar } = useAuth()
  const puedeEditar = puedeEscribir('promocion.promocion')
  const puedeEliminar = puedeBorrar('promocion.promocion')
  const [modalAbierto, setModalAbierto] = useState(false)
  const [editando, setEditando] = useState<Promocion | null>(null)
  const [recarga, setRecarga] = useState(0)
  const [sucursales, setSucursales] = useState<Sucursal[]>([])

  useEffect(() => {
    listarTodasLasSucursales()
      .then((r) => setSucursales(r.results))
      .catch(() => notifications.show({ message: 'No se pudieron cargar las sucursales.', color: 'red' }))
  }, [])

  const eliminar = async (promocion: Promocion) => {
    try {
      await eliminarPromocion(promocion.id)
      notifications.show({ message: 'Promoción eliminada.', color: 'green' })
      setRecarga((n) => n + 1)
    } catch (err) {
      notifications.show({ title: 'No se pudo eliminar', message: mensajeDeError(err), color: 'red' })
    }
  }

  return (
    <>
      <ListaCrud<Promocion>
        titulo="Promociones"
        subtitulo="Descuentos automáticos por sucursal y días de la semana"
        listar={listarPromociones}
        clave={(p) => p.id}
        porPagina={10}
        buscarPlaceholder="Buscar por nombre…"
        puedeCrear={puedeEditar}
        nuevoLabel="Nueva promoción"
        onNuevo={() => {
          setEditando(null)
          setModalAbierto(true)
        }}
        disparadorRecarga={recarga}
        columnas={[
          { header: 'Nombre', render: (p) => p.nombre },
          { header: 'Sucursal', render: (p) => p.sucursal_nombre ?? '—' },
          { header: 'Prioridad', render: (p) => p.prioridad },
          { header: 'Vigencia', render: (p) => `${p.fecha_inicio} — ${p.fecha_fin}` },
          {
            header: 'Estado',
            render: (p) => (
              <Badge color={p.habilitada ? 'green' : 'gray'} variant="light">
                {p.habilitada ? 'Habilitada' : 'Deshabilitada'}
              </Badge>
            ),
          },
        ]}
        accionesHeader={
          puedeEditar || puedeEliminar
            ? (p) => (
                <Group gap="xs" wrap="nowrap">
                  {puedeEditar && (
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
                  )}
                  {puedeEliminar && (
                    <ActionIcon color="red" variant="subtle" aria-label="Eliminar" onClick={() => void eliminar(p)}>
                      <IconTrash size={16} />
                    </ActionIcon>
                  )}
                </Group>
              )
            : undefined
        }
      />
      <PromocionFormModal
        opened={modalAbierto}
        onClose={() => setModalAbierto(false)}
        onGuardado={() => setRecarga((n) => n + 1)}
        promocion={editando}
        sucursales={sucursales}
      />
    </>
  )
}
