import { useEffect, type ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { Center, Loader, Stack, Text, Title } from '@mantine/core'
import { useAuth } from '../auth/AuthContext'

interface Props {
  children: ReactNode
  /** Codename Django (ej. "venta.add_venta") que el usuario necesita para entrar a esta ruta —
   * pensado para pantallas que además de login exigen un permiso puntual, no sólo las que
   * ocultan botones según permiso dentro de la página (ver AuthContext.tienePermiso). Sin esto,
   * alguien sin el permiso igual podía ENTRAR a la pantalla (ej. "Nueva venta") tipeando la URL
   * o por el menú, y recién se enteraba al intentar guardar (403 del backend) — confuso y
   * tarde. */
  requierePermiso?: string
  /** Ruta a la que redirigir en silencio (sin mostrar "Sin acceso") si falta el permiso — para
   * rutas a las que cualquiera puede llegar sin haberlas elegido a propósito, como "/" (todo el
   * mundo cae ahí después de loguearse, sea cual sea su rol). El resto de las rutas protegidas
   * no la necesitan: a esas se llega por el menú o tipeando la URL a propósito, así que tiene
   * sentido avisar en vez de redirigir calladamente. */
  fallbackSiSinAcceso?: string
}

/** Envuelve una ruta que exige sesión; si no hay sesión, dispara el login (redirect a Django). */
export default function ProtectedRoute({ children, requierePermiso, fallbackSiSinAcceso }: Props) {
  const { autenticado, cargando, perfilCargado, login, tienePermiso } = useAuth()

  useEffect(() => {
    if (!cargando && !autenticado) {
      void login()
    }
  }, [cargando, autenticado, login])

  // Mientras `perfil` (y sus `permisos`) todavía no cargó, cualquier `requierePermiso` daría
  // falso negativo (tienePermiso siempre false con perfil null) — esperar evita un "Sin acceso"
  // fantasma que se corrige solo medio segundo después.
  const esperandoPermisos = !!requierePermiso && !perfilCargado

  if (cargando || !autenticado || esperandoPermisos) {
    return (
      <Center h="100vh">
        <Stack align="center">
          <Loader />
          <Text>{autenticado ? 'Cargando…' : 'Redirigiendo al login…'}</Text>
        </Stack>
      </Center>
    )
  }

  if (requierePermiso && !tienePermiso(requierePermiso)) {
    if (fallbackSiSinAcceso) {
      return <Navigate to={fallbackSiSinAcceso} replace />
    }
    return (
      <Center h="100vh">
        <Stack align="center" gap={4}>
          <Title order={3}>Sin acceso</Title>
          <Text c="dimmed">No tenés permiso para entrar a esta pantalla.</Text>
        </Stack>
      </Center>
    )
  }

  return <>{children}</>
}
