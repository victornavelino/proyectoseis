import { apiFetch } from './client'
import type { PaginatedResponse } from '../types/api'
import type { Cliente, ClienteInput } from '../types/cliente'
import type { ListaPrecio } from '../types/articulo'

const POR_PAGINA = 10

export { POR_PAGINA as CLIENTES_POR_PAGINA }

export function listarClientes(opciones: { search?: string; pagina?: number } = {}) {
  return apiFetch<PaginatedResponse<Cliente>>('api/v1/cliente/', {
    params: { search: opciones.search, page: opciones.pagina ?? 1, page_size: POR_PAGINA },
  })
}

export function crearCliente(datos: ClienteInput) {
  return apiFetch<Cliente>('api/v1/cliente/', { method: 'POST', body: datos })
}

export function actualizarCliente(id: number, datos: Partial<ClienteInput>) {
  return apiFetch<Cliente>(`api/v1/cliente/${id}/`, { method: 'PATCH', body: datos })
}

export function listarListasPrecio() {
  return apiFetch<PaginatedResponse<ListaPrecio>>('api/v1/listaprecio/', { params: { page_size: 200 } })
}
