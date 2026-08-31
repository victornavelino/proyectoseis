import { apiFetch } from './client'
import type { PaginatedResponse } from '../types/api'
import type {
  Descuento,
  DescuentoInput,
  DiasSemanaInput,
  Promocion,
  PromocionArticulo,
  PromocionArticuloInput,
  PromocionInput,
} from '../types/promocion'

const POR_PAGINA = 10

export function listarPromociones(opciones: { search?: string; pagina?: number } = {}) {
  return apiFetch<PaginatedResponse<Promocion>>('api/v1/promocion/', {
    params: { search: opciones.search, page: opciones.pagina ?? 1, page_size: POR_PAGINA },
  })
}
export function crearPromocion(datos: PromocionInput) {
  return apiFetch<Promocion>('api/v1/promocion/', { method: 'POST', body: datos })
}
export function actualizarPromocion(id: number, datos: PromocionInput) {
  return apiFetch<Promocion>(`api/v1/promocion/${id}/`, { method: 'PUT', body: datos })
}

export function crearDiasSemana(datos: DiasSemanaInput) {
  return apiFetch<{ id: number }>('api/v1/diassemana/', { method: 'POST', body: datos })
}
export function actualizarDiasSemana(id: number, datos: DiasSemanaInput) {
  return apiFetch<{ id: number }>(`api/v1/diassemana/${id}/`, { method: 'PUT', body: datos })
}

export function crearPromocionArticulo(datos: PromocionArticuloInput) {
  return apiFetch<PromocionArticulo>('api/v1/promocionarticulo/', { method: 'POST', body: datos })
}
export function eliminarPromocionArticulo(id: number) {
  return apiFetch<void>(`api/v1/promocionarticulo/${id}/`, { method: 'DELETE' })
}

export function listarDescuentos(opciones: { search?: string; pagina?: number } = {}) {
  return apiFetch<PaginatedResponse<Descuento>>('api/v1/descuento/', {
    params: { search: opciones.search, page: opciones.pagina ?? 1, page_size: POR_PAGINA },
  })
}
export function crearDescuento(datos: DescuentoInput) {
  return apiFetch<Descuento>('api/v1/descuento/', { method: 'POST', body: datos })
}
export function actualizarDescuento(id: number, datos: DescuentoInput) {
  return apiFetch<Descuento>(`api/v1/descuento/${id}/`, { method: 'PUT', body: datos })
}
