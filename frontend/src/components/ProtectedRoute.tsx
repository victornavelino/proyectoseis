import { useEffect, type ReactNode } from 'react'
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
}

/** Envuelve una ruta que exige sesión; si no hay sesión, dispara el login (redirect a Django). */
export default function ProtectedRoute({ children, requierePermiso }: Props) {
  const { autenticado, cargando, login, tienePermiso } = useAuth()

  useEffect(() => {
    if (!cargando && !autenticado) {
      void login()
    }
  }, [cargando, autenticado, login])

  if (cargando || !autenticado) {
    return (
      <Center h="100vh">
        <Stack align="center">
          <Loader />
          <Text>{cargando ? 'Cargando…' : 'Redirigiendo al login…'}</Text>
        </Stack>
      </Center>
    )
  }

  if (requierePermiso && !tienePermiso(requierePermiso)) {
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
