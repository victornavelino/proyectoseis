// Cliente OAuth2 Authorization Code + PKCE contra django-oauth-toolkit (ver
// docs/modernizacion/API.md § OAuth2 en la raíz del repo para el detalle del flujo verificado
// del lado del backend).
import { OAUTH_CONFIG } from '../api/config'
import { generarParPkce, generarState } from './pkce'
import { clearTokens, getTokens, setTokens } from './tokenStore'

const VERIFIER_KEY = 'oauth_code_verifier'
const STATE_KEY = 'oauth_state'

interface TokenResponse {
  access_token: string
  refresh_token: string
  expires_in: number
  token_type: string
  scope: string
}

interface TokenErrorResponse {
  error: string
  error_description?: string
}

/** Redirige el navegador a la pantalla de login/autorización de Django. */
export async function iniciarLogin(): Promise<void> {
  const { codeVerifier, codeChallenge } = await generarParPkce()
  const state = generarState()

  // sessionStorage acá está bien: no es un token, es sólo el ida-y-vuelta del redirect. Se
  // pierde si se cierra la pestaña antes de volver del login, que es el comportamiento correcto
  // (no queda un verifier viejo dando vueltas).
  sessionStorage.setItem(VERIFIER_KEY, codeVerifier)
  sessionStorage.setItem(STATE_KEY, state)

  const params = new URLSearchParams({
    response_type: 'code',
    client_id: OAUTH_CONFIG.clientId,
    redirect_uri: OAUTH_CONFIG.redirectUri,
    scope: OAUTH_CONFIG.scope,
    state,
    code_challenge: codeChallenge,
    code_challenge_method: 'S256',
  })

  window.location.assign(`${OAUTH_CONFIG.authorizeUrl}?${params.toString()}`)
}

/** Se llama desde la pantalla de callback (`/auth/callback`) con los query params recibidos. */
export async function completarLogin(searchParams: URLSearchParams): Promise<void> {
  const error = searchParams.get('error')
  if (error) {
    sessionStorage.removeItem(VERIFIER_KEY)
    sessionStorage.removeItem(STATE_KEY)
    throw new Error(searchParams.get('error_description') ?? error)
  }

  const code = searchParams.get('code')
  const state = searchParams.get('state')
  const expectedState = sessionStorage.getItem(STATE_KEY)
  const codeVerifier = sessionStorage.getItem(VERIFIER_KEY)

  sessionStorage.removeItem(VERIFIER_KEY)
  sessionStorage.removeItem(STATE_KEY)

  if (!code || !state || !codeVerifier || state !== expectedState) {
    throw new Error('Respuesta de autorización inválida: falta el código o no coincide el state.')
  }

  await intercambiarPorTokens(
    new URLSearchParams({
      grant_type: 'authorization_code',
      code,
      redirect_uri: OAUTH_CONFIG.redirectUri,
      client_id: OAUTH_CONFIG.clientId,
      code_verifier: codeVerifier,
    }),
  )
}

export async function refrescarTokens(refreshToken: string): Promise<void> {
  await intercambiarPorTokens(
    new URLSearchParams({
      grant_type: 'refresh_token',
      refresh_token: refreshToken,
      client_id: OAUTH_CONFIG.clientId,
    }),
  )
}

async function intercambiarPorTokens(body: URLSearchParams): Promise<void> {
  const response = await fetch(OAUTH_CONFIG.tokenUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  })

  if (!response.ok) {
    clearTokens()
    const detalle = (await response.json().catch(() => null)) as TokenErrorResponse | null
    throw new Error(detalle?.error_description ?? detalle?.error ?? 'No se pudo obtener el token.')
  }

  const data = (await response.json()) as TokenResponse
  setTokens({
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
    expiresAt: Date.now() + data.expires_in * 1000,
  })
}

/** Revoca el refresh_token en el backend (si hay sesión) y limpia el estado local. */
export async function cerrarSesion(): Promise<void> {
  const tokens = getTokens()
  if (tokens) {
    try {
      await fetch(OAUTH_CONFIG.revokeUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ token: tokens.refreshToken, client_id: OAUTH_CONFIG.clientId }),
      })
    } catch {
      // Si falla la revocación remota (ej. sin conexión), igual limpiamos la sesión local: el
      // usuario ve el efecto de "cerrar sesión" de inmediato.
    }
  }
  clearTokens()
}
