import { apiFetch, apiFetchBlob } from './client'
import type { PaginatedResponse } from '../types/api'
import type {
  Adelanto,
  AdelantoInput,
  Caja,
  CobrarVentaInput,
  Gasto,
  GastoInput,
  Ingreso,
  IngresoInput,
  PlanTarjetaDeCredito,
  PlanTarjetaDeCreditoInput,
  ResumenCierreCaja,
  RetiroEfectivo,
  RetiroEfectivoInput,
  Sueldo,
  SueldoInput,
  TarjetaDeCredito,
  TarjetaDeCreditoInput,
  TipoGasto,
  TipoGastoInput,
  TipoIngreso,
  TipoIngresoInput,
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

/** Resumen de cierre de caja en PDF (WeasyPrint, ver caja.api.CajaViewSet.imprimir en el backend). */
export function imprimirCaja(id: number) {
  return apiFetchBlob(`api/v1/caja/${id}/imprimir/`)
}

export function cobrarVenta(datos: CobrarVentaInput) {
  return apiFetch<Venta>('api/v1/caja/cobrar-venta/', { method: 'POST', body: datos })
}

// --- Movimientos de caja (Sueldo/Adelanto/Ingreso/RetiroEfectivo/Gasto) ---
// `usuario`/`sucursal`/`caja`/`tipo` los pone el servidor (caja/services.py) — nunca se mandan
// desde acá, ver caja/serializers.py `read_only_fields`.

export function listarSueldos(opciones: { search?: string; pagina: number }) {
  return apiFetch<PaginatedResponse<Sueldo>>('api/v1/sueldo/', {
    params: { search: opciones.search, page: opciones.pagina, page_size: POR_PAGINA },
  })
}
export function crearSueldo(datos: SueldoInput) {
  return apiFetch<Sueldo>('api/v1/sueldo/', { method: 'POST', body: datos })
}
export function actualizarSueldo(id: number, datos: SueldoInput) {
  return apiFetch<Sueldo>(`api/v1/sueldo/${id}/`, { method: 'PATCH', body: datos })
}
export function eliminarSueldo(id: number) {
  return apiFetch<void>(`api/v1/sueldo/${id}/`, { method: 'DELETE' })
}

export function listarAdelantos(opciones: { search?: string; pagina: number }) {
  return apiFetch<PaginatedResponse<Adelanto>>('api/v1/adelanto/', {
    params: { search: opciones.search, page: opciones.pagina, page_size: POR_PAGINA },
  })
}
export function crearAdelanto(datos: AdelantoInput) {
  return apiFetch<Adelanto>('api/v1/adelanto/', { method: 'POST', body: datos })
}
export function actualizarAdelanto(id: number, datos: AdelantoInput) {
  return apiFetch<Adelanto>(`api/v1/adelanto/${id}/`, { method: 'PATCH', body: datos })
}
export function eliminarAdelanto(id: number) {
  return apiFetch<void>(`api/v1/adelanto/${id}/`, { method: 'DELETE' })
}

export function listarIngresos(opciones: { search?: string; pagina: number }) {
  return apiFetch<PaginatedResponse<Ingreso>>('api/v1/ingreso/', {
    params: { search: opciones.search, page: opciones.pagina, page_size: POR_PAGINA },
  })
}
export function crearIngreso(datos: IngresoInput) {
  return apiFetch<Ingreso>('api/v1/ingreso/', { method: 'POST', body: datos })
}
export function actualizarIngreso(id: number, datos: IngresoInput) {
  return apiFetch<Ingreso>(`api/v1/ingreso/${id}/`, { method: 'PATCH', body: datos })
}
export function eliminarIngreso(id: number) {
  return apiFetch<void>(`api/v1/ingreso/${id}/`, { method: 'DELETE' })
}

export function listarRetirosEfectivo(opciones: { search?: string; pagina: number }) {
  return apiFetch<PaginatedResponse<RetiroEfectivo>>('api/v1/retiroefectivo/', {
    params: { search: opciones.search, page: opciones.pagina, page_size: POR_PAGINA },
  })
}
export function crearRetiroEfectivo(datos: RetiroEfectivoInput) {
  return apiFetch<RetiroEfectivo>('api/v1/retiroefectivo/', { method: 'POST', body: datos })
}
export function actualizarRetiroEfectivo(id: number, datos: RetiroEfectivoInput) {
  return apiFetch<RetiroEfectivo>(`api/v1/retiroefectivo/${id}/`, { method: 'PATCH', body: datos })
}
export function eliminarRetiroEfectivo(id: number) {
  return apiFetch<void>(`api/v1/retiroefectivo/${id}/`, { method: 'DELETE' })
}

export function listarGastos(opciones: { search?: string; pagina: number }) {
  return apiFetch<PaginatedResponse<Gasto>>('api/v1/gasto/', {
    params: { search: opciones.search, page: opciones.pagina, page_size: POR_PAGINA },
  })
}
export function crearGasto(datos: GastoInput) {
  return apiFetch<Gasto>('api/v1/gasto/', { method: 'POST', body: datos })
}
export function actualizarGasto(id: number, datos: GastoInput) {
  return apiFetch<Gasto>(`api/v1/gasto/${id}/`, { method: 'PATCH', body: datos })
}
export function eliminarGasto(id: number) {
  return apiFetch<void>(`api/v1/gasto/${id}/`, { method: 'DELETE' })
}

// --- Catálogos de apoyo para Ingreso/Gasto ---

export function listarTiposIngreso(opciones: { search?: string; pagina?: number } = {}) {
  return apiFetch<PaginatedResponse<TipoIngreso>>('api/v1/tipoingreso/', {
    params: { search: opciones.search, page: opciones.pagina ?? 1, page_size: POR_PAGINA },
  })
}
export function listarTodosLosTiposIngreso() {
  return apiFetch<PaginatedResponse<TipoIngreso>>('api/v1/tipoingreso/', { params: { page_size: 100 } })
}
export function crearTipoIngreso(datos: TipoIngresoInput) {
  return apiFetch<TipoIngreso>('api/v1/tipoingreso/', { method: 'POST', body: datos })
}
export function actualizarTipoIngreso(id: number, datos: TipoIngresoInput) {
  return apiFetch<TipoIngreso>(`api/v1/tipoingreso/${id}/`, { method: 'PUT', body: datos })
}

export function listarTiposGasto(opciones: { search?: string; pagina?: number } = {}) {
  return apiFetch<PaginatedResponse<TipoGasto>>('api/v1/tipogasto/', {
    params: { search: opciones.search, page: opciones.pagina ?? 1, page_size: POR_PAGINA },
  })
}
export function listarTodosLosTiposGasto() {
  return apiFetch<PaginatedResponse<TipoGasto>>('api/v1/tipogasto/', { params: { page_size: 100 } })
}
export function crearTipoGasto(datos: TipoGastoInput) {
  return apiFetch<TipoGasto>('api/v1/tipogasto/', { method: 'POST', body: datos })
}
export function actualizarTipoGasto(id: number, datos: TipoGastoInput) {
  return apiFetch<TipoGasto>(`api/v1/tipogasto/${id}/`, { method: 'PUT', body: datos })
}
