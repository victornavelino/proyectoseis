import { apiFetch } from './client'
import type { PaginatedResponse } from '../types/api'
import type { UsuarioSucursal, UsuarioSucursalInput } from '../types/usuario'

const POR_PAGINA = 10

export function listarUsuariosSucursal(opciones: { search?: string; pagina?: number } = {}) {
  return apiFetch<PaginatedResponse<UsuarioSucursal>>('api/v1/usuario-sucursal/', {
    params: { search: opciones.search, page: opciones.pagina ?? 1, page_size: POR_PAGINA },
  })
}
export function crearUsuarioSucursal(datos: UsuarioSucursalInput) {
  return apiFetch<UsuarioSucursal>('api/v1/usuario-sucursal/', { method: 'POST', body: datos })
}
export function actualizarUsuarioSucursal(id: number, datos: Omit<UsuarioSucursalInput, 'password'>) {
  return apiFetch<UsuarioSucursal>(`api/v1/usuario-sucursal/${id}/`, { method: 'PATCH', body: datos })
}
/** Sólo permite borrar cuentas sin historial (ver usuario.api.UsuarioSucursalViewSet.destroy) —
 * si tiene ventas/caja/cta. corriente asociados, el backend rechaza con 400; desactivala en vez
 * de borrarla (switch "Activo" en UsuarioSucursalFormModal). */
export function eliminarUsuarioSucursal(id: number) {
  return apiFetch<void>(`api/v1/usuario-sucursal/${id}/`, { method: 'DELETE' })
}
