import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { apiFetch } from '../api/client'
import type { Perfil } from '../types/usuario'
import { cerrarSesion, iniciarLogin } from './oauthClient'
import { getTokens, isAccessTokenValid } from './tokenStore'

interface AuthContextValue {
  autenticado: boolean
  /** true mientras se resuelve el estado inicial de sesión (evita un parpadeo a "login"). */
  cargando: boolean
  /** Perfil del usuario autenticado (incluye `is_staff`, usado para mostrar/ocultar acciones
   * de escritura en pantallas que el backend restringe a staff — ver util.permissions.
   * IsStaffOrReadOnly en el backend). null hasta que se resuelve el fetch. */
  perfil: Perfil | null
  login: () => Promise<void>
  logout: () => Promise<void>
  /** Llamar después de que AuthCallback complete el intercambio de tokens. */
  refrescarEstado: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [autenticado, setAutenticado] = useState(false)
  const [cargando, setCargando] = useState(true)
  const [perfil, setPerfil] = useState<Perfil | null>(null)

  const refrescarEstado = useCallback(() => {
    setAutenticado(!!getTokens() && isAccessTokenValid())
  }, [])

  useEffect(() => {
    refrescarEstado()
    setCargando(false)
  }, [refrescarEstado])

  useEffect(() => {
    if (!autenticado) {
      setPerfil(null)
      return
    }
    apiFetch<Perfil>('api/v1/usuario/me/')
      .then(setPerfil)
      .catch(() => setPerfil(null))
  }, [autenticado])

  const login = useCallback(async () => {
    await iniciarLogin()
  }, [])

  const logout = useCallback(async () => {
    await cerrarSesion()
    setAutenticado(false)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({ autenticado, cargando, perfil, login, logout, refrescarEstado }),
    [autenticado, cargando, perfil, login, logout, refrescarEstado],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth debe usarse dentro de <AuthProvider>')
  return ctx
}
