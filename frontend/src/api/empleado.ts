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
