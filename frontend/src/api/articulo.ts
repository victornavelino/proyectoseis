import { apiFetch } from './client'
import type { PaginatedResponse } from '../types/api'
import type {
  Articulo,
  ArticuloInput,
  Categoria,
  CategoriaInput,
  ListaPrecio,
  ListaPrecioInput,
  Precio,
  PrecioInput,
  TipoIva,
  TipoIvaInput,
  UnidadMedida,
  UnidadMedidaInput,
} from '../types/articulo'

const POR_PAGINA = 10

export { POR_PAGINA as ARTICULOS_POR_PAGINA }

export function listarArticulos(opciones: { search?: string; pagina?: number } = {}) {
  return apiFetch<PaginatedResponse<Articulo>>('api/v1/articulo/', {
    params: { search: opciones.search, page: opciones.pagina ?? 1, page_size: POR_PAGINA },
  })
}

export function crearArticulo(datos: ArticuloInput) {
  return apiFetch<Articulo>('api/v1/articulo/', { method: 'POST', body: datos })
}

export function actualizarArticulo(id: number, datos: ArticuloInput) {
  return apiFetch<Articulo>(`api/v1/articulo/${id}/`, { method: 'PUT', body: datos })
}

export function eliminarArticulo(id: number) {
  return apiFetch<void>(`api/v1/articulo/${id}/`, { method: 'DELETE' })
}

// --- Tipo de IVA ---
export function listarTiposIva(opciones: { search?: string; pagina?: number } = {}) {
  return apiFetch<PaginatedResponse<TipoIva>>('api/v1/tipoiva/', {
    params: { search: opciones.search, page: opciones.pagina ?? 1, page_size: POR_PAGINA },
  })
}
export function listarTodosLosTiposIva() {
  return apiFetch<PaginatedResponse<TipoIva>>('api/v1/tipoiva/', { params: { page_size: 200 } })
}
export function crearTipoIva(datos: TipoIvaInput) {
  return apiFetch<TipoIva>('api/v1/tipoiva/', { method: 'POST', body: datos })
}
export function actualizarTipoIva(id: number, datos: TipoIvaInput) {
  return apiFetch<TipoIva>(`api/v1/tipoiva/${id}/`, { method: 'PUT', body: datos })
}

// --- Unidad de medida ---
export function listarUnidadesMedidaPag(opciones: { search?: string; pagina?: number } = {}) {
  return apiFetch<PaginatedResponse<UnidadMedida>>('api/v1/unidadmedida/', {
    params: { search: opciones.search, page: opciones.pagina ?? 1, page_size: POR_PAGINA },
  })
}
export function listarUnidadesMedida() {
  return apiFetch<PaginatedResponse<UnidadMedida>>('api/v1/unidadmedida/', { params: { page_size: 200 } })
}
export function crearUnidadMedida(datos: UnidadMedidaInput) {
  return apiFetch<UnidadMedida>('api/v1/unidadmedida/', { method: 'POST', body: datos })
}
export function actualizarUnidadMedida(id: number, datos: UnidadMedidaInput) {
  return apiFetch<UnidadMedida>(`api/v1/unidadmedida/${id}/`, { method: 'PUT', body: datos })
}

// --- Categoría ---
export function listarCategoriasPag(opciones: { search?: string; pagina?: number } = {}) {
  return apiFetch<PaginatedResponse<Categoria>>('api/v1/categoria/', {
    params: { search: opciones.search, page: opciones.pagina ?? 1, page_size: POR_PAGINA },
  })
}
export function listarCategorias() {
  return apiFetch<PaginatedResponse<Categoria>>('api/v1/categoria/', { params: { page_size: 200 } })
}
export function crearCategoria(datos: CategoriaInput) {
  return apiFetch<Categoria>('api/v1/categoria/', { method: 'POST', body: datos })
}
export function actualizarCategoria(id: number, datos: CategoriaInput) {
  return apiFetch<Categoria>(`api/v1/categoria/${id}/`, { method: 'PUT', body: datos })
}

// --- Lista de precios ---
export function listarListasPrecioPag(opciones: { search?: string; pagina?: number } = {}) {
  return apiFetch<PaginatedResponse<ListaPrecio>>('api/v1/listaprecio/', {
    params: { search: opciones.search, page: opciones.pagina ?? 1, page_size: POR_PAGINA },
  })
}
export function crearListaPrecio(datos: ListaPrecioInput) {
  return apiFetch<ListaPrecio>('api/v1/listaprecio/', { method: 'POST', body: datos })
}
export function actualizarListaPrecio(id: number, datos: ListaPrecioInput) {
  return apiFetch<ListaPrecio>(`api/v1/listaprecio/${id}/`, { method: 'PUT', body: datos })
}

// --- Precio ---
export function listarPrecios(opciones: { search?: string; pagina?: number; articulo?: number } = {}) {
  return apiFetch<PaginatedResponse<Precio>>('api/v1/precio/', {
    params: { page: opciones.pagina ?? 1, page_size: POR_PAGINA, articulo: opciones.articulo },
  })
}
export function crearPrecio(datos: PrecioInput) {
  return apiFetch<Precio>('api/v1/precio/', { method: 'POST', body: datos })
}
export function actualizarPrecio(id: number, datos: PrecioInput) {
  return apiFetch<Precio>(`api/v1/precio/${id}/`, { method: 'PUT', body: datos })
}
export function eliminarPrecio(id: number) {
  return apiFetch<void>(`api/v1/precio/${id}/`, { method: 'DELETE' })
}
