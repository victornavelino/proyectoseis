// Sin barra final — api/client.ts arma las URLs relativas a esto.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

export const OAUTH_CONFIG = {
  clientId: import.meta.env.VITE_OAUTH_CLIENT_ID,
  redirectUri: import.meta.env.VITE_OAUTH_REDIRECT_URI,
  authorizeUrl: `${API_BASE_URL}/oauth2/authorize/`,
  tokenUrl: `${API_BASE_URL}/oauth2/token/`,
  revokeUrl: `${API_BASE_URL}/oauth2/revoke_token/`,
  // Logout "real" de Django (ver project/urls.py) — sin esto, revocar el token no alcanza:
  // oauth2_provider.views.AuthorizationView usa la cookie de sesión de Django (no los tokens
  // OAuth) para saber si hay que pedir credenciales, así que un logout que sólo borra tokens
  // deja al usuario logueado "por sesión" y el próximo login cae directo en la pantalla de
  // autorización (o se reloguea solo) en vez de pedirle usuario/contraseña de nuevo.
  logoutUrl: `${API_BASE_URL}/logout/`,
  // Coincide con OAUTH2_PROVIDER['SCOPES'] del backend (project/settings/base.py).
  scope: 'read write',
}
