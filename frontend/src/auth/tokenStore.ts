/**
 * Guarda los tokens SOLO en memoria (variable de módulo) — nunca en localStorage ni
 * sessionStorage, para mitigar robo de tokens vía XSS (ver docs/modernizacion/ARQUITECTURA.md
 * § Autenticación). Se pierden al recargar la página o cerrar la pestaña: el usuario tiene que
 * volver a iniciar sesión.
 *
 * Simplificación deliberada respecto al diseño de ARQUITECTURA.md: ahí se proponía el
 * refresh_token en una cookie httpOnly de mismo origen (DEC-009). Eso requiere que el backend
 * envuelva /oauth2/token/ en un endpoint propio que reemita el refresh_token como Set-Cookie en
 * vez de en el body JSON — no está hecho todavía. Por ahora ambos tokens viven acá, en memoria,
 * como cualquier SPA que hable OAuth2 directo contra el Authorization Server. Se puede migrar a
 * la variante con cookie más adelante sin tocar el resto del código (todo el acceso a tokens
 * pasa por este módulo).
 */
interface TokenSet {
  accessToken: string
  refreshToken: string
  expiresAt: number // epoch ms
}

let tokens: TokenSet | null = null

export function setTokens(next: TokenSet): void {
  tokens = next
}

export function getTokens(): TokenSet | null {
  return tokens
}

export function clearTokens(): void {
  tokens = null
}

/** Da un margen de 5s para evitar usar un token que expira mientras viaja la request. */
export function isAccessTokenValid(): boolean {
  return !!tokens && tokens.expiresAt > Date.now() + 5000
}
