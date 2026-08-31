import { apiFetch } from './client'
import type { PaginatedResponse } from '../types/api'
import type { CrearVentaInput, ItemVentaInput, Venta, VentaPrevisualizada } from '../types/venta'

const POR_PAGINA = 10

export { POR_PAGINA as VENTAS_POR_PAGINA }

export function listarVentas(params: { cobrada?: boolean; anulado?: boolean; pagina?: number } = {}) {
  const { pagina, ...resto } = params
  return apiFetch<PaginatedResponse<Venta>>('api/v1/venta/', {
    params: { page_size: POR_PAGINA, page: pagina ?? 1, ...resto },
  })
}

export function obtenerVenta(numeroTicket: number) {
  return apiFetch<Venta>(`api/v1/venta/${numeroTicket}/`)
}

export function previsualizarVenta(cliente: number, articulos: ItemVentaInput[]) {
  return apiFetch<VentaPrevisualizada>('api/v1/venta/previsualizar/', {
    method: 'POST',
    body: { cliente, articulos },
  })
}

export function crearVenta(datos: CrearVentaInput) {
  return apiFetch<Venta>('api/v1/venta/crear/', { method: 'POST', body: datos })
}
