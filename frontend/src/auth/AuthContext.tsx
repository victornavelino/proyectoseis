import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { apiFetch } from '../api/client'
import type { Perfil } from '../types/usuario'
import { cerrarSesion, iniciarLogin } from './oauthClient'
import { getTokens, isAccessTokenValid } from './tokenStore'

interface AuthContextValue {
  autenticado: boolean
  /** true mientras se resuelve el estado inicial de sesión (evita un parpadeo a "login"). */
  cargando: boolean
  /** Perfil del usuario autenticado (incluye `permisos`, usado para mostrar/ocultar acciones
   * de escritura según el permiso Django puntual que el backend exige — ver util.permissions.
   * TienePermisoDeModelo). null hasta que se resuelve el fetch. */
  perfil: Perfil | null
  /** true una vez que se resolvió (éxito o error) el fetch de `perfil` — a diferencia de
   * `cargando` (que sólo cubre si hay o no sesión), esto le permite a ProtectedRoute esperar a
   * tener `perfil.permisos` antes de evaluar `requierePermiso`. Sin esto, justo después del
   * login (perfil todavía null) `tienePermiso` devuelve false para TODO y una ruta protegida
   * muestra "Sin acceso" un instante aunque el usuario sí tenga el permiso, hasta que el fetch
   * resuelve y se vuelve a renderizar. */
  perfilCargado: boolean
  /** ¿Tiene el usuario el permiso Django `codename` (ej. "articulo.delete_articulo")? Primitiva
   * de base — normalmente conviene usar `puedeEscribir`/`puedeBorrar` en su lugar. */
  tienePermiso: (codename: string) => boolean
  /** ¿Puede crear Y editar instancias de `<app_label>.<modelo>` (ej. "articulo.categoria")? El
   * front conjuga alta+edición en un solo botón/flujo, así que exige ambos permisos
   * (add_/change_) a la vez — evita mostrar "Nuevo" a alguien que después el backend rechaza
   * con 403 por no tener add_<modelo>. */
  puedeEscribir: (appModelo: string) => boolean
  /** ¿Puede eliminar instancias de `<app_label>.<modelo>`? */
  puedeBorrar: (appModelo: string) => boolean
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
  const [perfilCargado, setPerfilCargado] = useState(false)

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
      setPerfilCargado(false)
      return
    }
    setPerfilCargado(false)
    apiFetch<Perfil>('api/v1/usuario/me/')
      .then(setPerfil)
      .catch(() => setPerfil(null))
      .finally(() => setPerfilCargado(true))
  }, [autenticado])

  const tienePermiso = useCallback((codename: string) => perfil?.permisos.includes(codename) ?? false, [perfil])

  const puedeEscribir = useCallback(
    (appModelo: string) => {
      const [app, modelo] = appModelo.split('.')
      return tienePermiso(`${app}.add_${modelo}`) && tienePermiso(`${app}.change_${modelo}`)
    },
    [tienePermiso],
  )

  const puedeBorrar = useCallback(
    (appModelo: string) => {
      const [app, modelo] = appModelo.split('.')
      return tienePermiso(`${app}.delete_${modelo}`)
    },
    [tienePermiso],
  )

  const login = useCallback(async () => {
    await iniciarLogin()
  }, [])

  const logout = useCallback(async () => {
    await cerrarSesion()
    setAutenticado(false)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      autenticado,
      cargando,
      perfil,
      perfilCargado,
      tienePermiso,
      puedeEscribir,
      puedeBorrar,
      login,
      logout,
      refrescarEstado,
    }),
    [autenticado, cargando, perfil, perfilCargado, tienePermiso, puedeEscribir, puedeBorrar, login, logout, refrescarEstado],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth debe usarse dentro de <AuthProvider>')
  return ctx
}
