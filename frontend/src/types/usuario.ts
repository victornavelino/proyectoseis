export interface Perfil {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  is_staff: boolean
  sucursal: number | null
  sucursal_nombre: string | null
  groups: { id: number; name: string }[]
}

/** Usuario operativo de la propia sucursal del encargado — ver
 * usuario.api.UsuarioSucursalViewSet. Sin is_staff/groups/user_permissions: ese endpoint no los
 * expone, la gestión de permisos avanzados sigue siendo exclusiva del /admin de Django. */
export interface UsuarioSucursal {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  is_active: boolean
  sucursal: number | null
  sucursal_nombre: string | null
}

export interface UsuarioSucursalInput {
  username: string
  email: string
  first_name: string
  last_name: string
  is_active: boolean
  /** Requerida al crear; se omite al editar (no hay reseteo de contraseña de otro usuario todavía). */
  password?: string
}
