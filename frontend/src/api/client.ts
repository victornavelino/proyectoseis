// Cliente HTTP central: todas las llamadas a la API Django pasan por acá — agrega el Bearer
// token (refrescándolo solo si hace falta), arma la URL con querystring, y normaliza errores.
// No hay fetch() sueltos en features/: eso es justamente lo que este módulo evita tener que
// repetir en cada pantalla (especificaciones.md §6: "manejo centralizado de errores HTTP").
import { getTokens, isAccessTokenValid } from '../auth/tokenStore'
import { refrescarTokens } from '../auth/oauthClient'
import { API_BASE_URL } from './config'

export class ApiError extends Error {
  status: number
  /** Cuerpo del error tal cual lo devuelve DRF — JSON plano, ej. {"caja": "..."} (ver
   * docs/modernizacion/API.md). Las pantallas lo usan para mostrar el mensaje por campo. */
  detail: unknown

  constructor(status: number, detail: unknown) {
    super(typeof detail === 'string' ? detail : `Error HTTP ${status}`)
    this.status = status
    this.detail = detail
  }
}

// Evita disparar varios refresh en paralelo si hay varios pedidos simultáneos con el token vencido.
let refrescoEnCurso: Promise<void> | null = null

async function asegurarTokenValido(): Promise<string | null> {
  const tokens = getTokens()
  if (!tokens) return null
  if (isAccessTokenValid()) return tokens.accessToken

  if (!refrescoEnCurso) {
    refrescoEnCurso = refrescarTokens(tokens.refreshToken).finally(() => {
      refrescoEnCurso = null
    })
  }
  await refrescoEnCurso
  return getTokens()?.accessToken ?? null
}

interface ApiFetchOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE'
  body?: unknown
  params?: Record<string, string | number | boolean | undefined>
}

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const url = new URL(path.replace(/^\//, ''), `${API_BASE_URL}/`)
  if (options.params) {
    for (const [key, value] of Object.entries(options.params)) {
      if (value !== undefined) url.searchParams.set(key, String(value))
    }
  }

  const accessToken = await asegurarTokenValido()
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'

  const response = await fetch(url.toString(), {
    method: options.method ?? 'GET',
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  })

  if (response.status === 204) {
    return undefined as T
  }

  const esJson = response.headers.get('Content-Type')?.includes('application/json') ?? false
  const payload = esJson ? await response.json().catch(() => null) : null

  if (!response.ok) {
    throw new ApiError(response.status, payload ?? response.statusText)
  }

  return payload as T
}
