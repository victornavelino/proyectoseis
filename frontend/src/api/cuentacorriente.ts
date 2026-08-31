import { apiFetch } from './client'
import type { PaginatedResponse } from '../types/api'
import type {
  CuentaCorriente,
  CuentaCorrienteInput,
  MovimientoCuentaCorriente,
  MovimientoCuentaCorrienteInput,
} from '../types/cuentacorriente'

const POR_PAGINA = 10

export function listarCuentasCorrientes(opciones: { search?: string; pagina?: number } = {}) {
  return apiFetch<PaginatedResponse<CuentaCorriente>>('api/v1/cuentacorriente/', {
    params: { search: opciones.search, page: opciones.pagina ?? 1, page_size: POR_PAGINA },
  })
}
export function obtenerCuentaCorrienteDeCliente(cliente: number) {
  return apiFetch<PaginatedResponse<CuentaCorriente>>('api/v1/cuentacorriente/', {
    params: { cliente, page_size: 1 },
  })
}
export function crearCuentaCorriente(datos: CuentaCorrienteInput) {
  return apiFetch<CuentaCorriente>('api/v1/cuentacorriente/', { method: 'POST', body: datos })
}
export function actualizarCuentaCorriente(id: number, datos: CuentaCorrienteInput) {
  return apiFetch<CuentaCorriente>(`api/v1/cuentacorriente/${id}/`, { method: 'PUT', body: datos })
}

export function listarMovimientosCuentaCorriente(cuenta: number, pagina = 1) {
  return apiFetch<PaginatedResponse<MovimientoCuentaCorriente>>('api/v1/movimientocuentacorriente/', {
    params: { cuenta, page: pagina, page_size: POR_PAGINA },
  })
}
export function crearMovimientoCuentaCorriente(datos: MovimientoCuentaCorrienteInput) {
  return apiFetch<MovimientoCuentaCorriente>('api/v1/movimientocuentacorriente/', { method: 'POST', body: datos })
}
