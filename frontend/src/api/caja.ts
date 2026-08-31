import { apiFetch } from './client'
import type { PaginatedResponse } from '../types/api'
import type {
  Caja,
  CobrarVentaInput,
  PlanTarjetaDeCredito,
  PlanTarjetaDeCreditoInput,
  ResumenCierreCaja,
  TarjetaDeCredito,
  TarjetaDeCreditoInput,
} from '../types/caja'
import type { Venta } from '../types/venta'

const POR_PAGINA = 10

// --- Tarjetas y planes ---
export function listarTarjetas(opciones: { search?: string; pagina?: number } = {}) {
  return apiFetch<PaginatedResponse<TarjetaDeCredito>>('api/v1/tarjetadecredito/', {
    params: { search: opciones.search, page: opciones.pagina ?? 1, page_size: POR_PAGINA },
  })
}
export function listarTodasLasTarjetas() {
  return apiFetch<PaginatedResponse<TarjetaDeCredito>>('api/v1/tarjetadecredito/', { params: { page_size: 100 } })
}
export function crearTarjeta(datos: TarjetaDeCreditoInput) {
  return apiFetch<TarjetaDeCredito>('api/v1/tarjetadecredito/', { method: 'POST', body: datos })
}
export function actualizarTarjeta(id: number, datos: TarjetaDeCreditoInput) {
  return apiFetch<TarjetaDeCredito>(`api/v1/tarjetadecredito/${id}/`, { method: 'PUT', body: datos })
}

export function listarPlanesTarjetaPag(opciones: { search?: string; pagina?: number } = {}) {
  return apiFetch<PaginatedResponse<PlanTarjetaDeCredito>>('api/v1/plantarjetadecredito/', {
    params: { page: opciones.pagina ?? 1, page_size: POR_PAGINA },
  })
}
export function listarPlanesTarjeta(tarjeta?: number) {
  return apiFetch<PaginatedResponse<PlanTarjetaDeCredito>>('api/v1/plantarjetadecredito/', {
    params: { page_size: 100, tarjeta },
  })
}
export function crearPlanTarjeta(datos: PlanTarjetaDeCreditoInput) {
  return apiFetch<PlanTarjetaDeCredito>('api/v1/plantarjetadecredito/', { method: 'POST', body: datos })
}
export function actualizarPlanTarjeta(id: number, datos: PlanTarjetaDeCreditoInput) {
  return apiFetch<PlanTarjetaDeCredito>(`api/v1/plantarjetadecredito/${id}/`, { method: 'PUT', body: datos })
}

// --- Caja ---
export function listarCajas(opciones: { pagina?: number; sucursal?: number } = {}) {
  return apiFetch<PaginatedResponse<Caja>>('api/v1/caja/', {
    params: { page: opciones.pagina ?? 1, page_size: POR_PAGINA, sucursal: opciones.sucursal },
  })
}
export function cajaAbiertaActual(sucursal: number) {
  return apiFetch<PaginatedResponse<Caja>>('api/v1/caja/', {
    params: { fecha_fin__isnull: true, sucursal, page_size: 1 },
  })
}
export function abrirCaja() {
  return apiFetch<Caja>('api/v1/caja/abrir/', { method: 'POST' })
}
export function cerrarCaja(id: number) {
  return apiFetch<ResumenCierreCaja>(`api/v1/caja/${id}/cerrar/`, { method: 'POST' })
}

export function cobrarVenta(datos: CobrarVentaInput) {
  return apiFetch<Venta>('api/v1/caja/cobrar-venta/', { method: 'POST', body: datos })
}
