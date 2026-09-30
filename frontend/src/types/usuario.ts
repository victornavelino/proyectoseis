export interface Perfil {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  is_staff: boolean
  sucursal: number | null
  sucursal_nombre: string | null
  /** Empleado vinculado a este usuario (asignado por /admin) — VentaNuevaPage lo usa para
   * preseleccionar al vendedor logueado. null si el usuario no tiene un Empleado asociado. */
  empleado: number | null
  groups: { id: number; name: string }[]
  /** Codenames "app_label.accion_modelo" (ej. "articulo.delete_articulo") de TODOS los permisos
   * Django del usuario — individuales + de sus grupos, superusuario ya resuelto a "todos" (ver
   * usuario.serializers.UsuarioSerializer.get_permisos). Usar junto con useAuth().tienePermiso
   * en vez de comparar contra `is_staff` para decidir qué botones de alta/edición/borrado
   * mostrar — ver util.permissions.TienePermisoDeModelo en el backend, que exige exactamente
   * estos mismos permisos. */
  permisos: string[]
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
