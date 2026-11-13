import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Alert, Anchor, Center, Loader, Stack, Text } from '@mantine/core'
import { useAuth } from './AuthContext'
import { completarLogin } from './oauthClient'

/** Pantalla de destino de OAUTH_CONFIG.redirectUri (ruta `/auth/callback`, ver App.tsx). */
export default function AuthCallback() {
  const [searchParams] = useSearchParams()
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const { refrescarEstado } = useAuth()

  useEffect(() => {
    completarLogin(searchParams)
      .then(() => {
        refrescarEstado()
        navigate('/', { replace: true })
      })
      .catch((err: Error) => setError(err.message))
    // Sólo se ejecuta una vez, al montar (el `code` de la URL es de un solo uso).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (error) {
    return (
      <Center h="100vh" p="md">
        <Stack align="center" maw={420}>
          <Alert color="red" title="No se pudo iniciar sesión" w="100%">
            {error}
          </Alert>
          <Anchor href="/">Volver a intentar</Anchor>
        </Stack>
      </Center>
    )
  }

  return (
    <Center h="100vh">
      <Stack align="center">
        <Loader />
        <Text>Iniciando sesión…</Text>
      </Stack>
    </Center>
  )
}
