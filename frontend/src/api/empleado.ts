import { apiFetch } from './client'
import type { PaginatedResponse } from '../types/api'
import type { Empleado, EmpleadoInput, Sucursal, SucursalInput } from '../types/empleado'

const POR_PAGINA = 10

export function listarEmpleadosActivos(search?: string) {
  return apiFetch<PaginatedResponse<Empleado>>('api/v1/empleado/', {
    params: { search, page_size: 100, fecha_baja__isnull: true },
  })
}

export function listarEmpleados(opciones: { search?: string; pagina?: number } = {}) {
  return apiFetch<PaginatedResponse<Empleado>>('api/v1/empleado/', {
    params: { search: opciones.search, page: opciones.pagina ?? 1, page_size: POR_PAGINA },
  })
}
export function crearEmpleado(datos: EmpleadoInput) {
  return apiFetch<Empleado>('api/v1/empleado/', { method: 'POST', body: datos })
}
export function actualizarEmpleado(id: number, datos: EmpleadoInput) {
  return apiFetch<Empleado>(`api/v1/empleado/${id}/`, { method: 'PUT', body: datos })
}

/** Empleado ya existente para esa persona, o null — mismo criterio que
 * persona.buscarPersonaPorDocumento: no duplicar (una persona no debería tener dos legajos de
 * empleado). Usado por UsuarioSucursalFormModal al dar de alta un usuario para una persona que
 * ya existe. */
export async function buscarEmpleadoPorPersona(personaId: number): Promise<Empleado | null> {
  const data = await apiFetch<PaginatedResponse<Empleado>>('api/v1/empleado/', {
    params: { persona: personaId, page_size: 1 },
  })
  return data.results[0] ?? null
}

export function listarSucursales(opciones: { search?: string; pagina?: number } = {}) {
  return apiFetch<PaginatedResponse<Sucursal>>('api/v1/sucursal/', {
    params: { search: opciones.search, page: opciones.pagina ?? 1, page_size: POR_PAGINA },
  })
}
export function listarTodasLasSucursales() {
  return apiFetch<PaginatedResponse<Sucursal>>('api/v1/sucursal/', { params: { page_size: 200 } })
}
export function crearSucursal(datos: SucursalInput) {
  return apiFetch<Sucursal>('api/v1/sucursal/', { method: 'POST', body: datos })
}
export function actualizarSucursal(id: number, datos: SucursalInput) {
  return apiFetch<Sucursal>(`api/v1/sucursal/${id}/`, { method: 'PUT', body: datos })
}
