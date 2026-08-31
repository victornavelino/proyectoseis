import { useEffect, type ReactNode } from 'react'
import { Center, Loader, Stack, Text } from '@mantine/core'
import { useAuth } from '../auth/AuthContext'

/** Envuelve una ruta que exige sesión; si no hay sesión, dispara el login (redirect a Django). */
export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const { autenticado, cargando, login } = useAuth()

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

  return <>{children}</>
}
