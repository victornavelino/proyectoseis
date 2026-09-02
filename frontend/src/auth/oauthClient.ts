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

/** Revoca el refresh_token y cierra la sesión de Django subyacente (ver OAUTH_CONFIG.logoutUrl).
 *
 * La revocación es un fetch normal (no depende de cookies). El logout de Django, en cambio, se
 * hace con una navegación real de página completa (`window.location.assign`), NO con
 * `fetch(..., {credentials: 'include'})`: la cookie de sesión usa SameSite=Lax (default de
 * Django), que sólo viaja en navegaciones de nivel superior cross-site, no en un fetch/XHR — en
 * desarrollo front (:5173) y back (:8000) son orígenes distintos, así que un fetch nunca
 * mandaría la cookie y el logout no haría nada del lado de Django (quedaría la sesión viva,
 * que es justamente el bug que esto arregla). `?next=/` hace que LogoutView redirija de vuelta
 * a la SPA en vez de a `/login/` (su destino por defecto, ver next_page en project/urls.py). */
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
      // Si falla la revocación remota (ej. sin conexión), igual seguimos: mejor terminar el
      // logout local y de sesión que dejar al usuario tildado en esta pantalla.
    }
  }
  clearTokens()
  window.location.assign(`${OAUTH_CONFIG.logoutUrl}?next=/`)
}
