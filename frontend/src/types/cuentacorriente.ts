export interface CuentaCorriente {
  id: number
  cliente: number
  cliente_nombre: string
  tope: string
  fecha: string
  observaciones: string | null
  activa: boolean
  saldo: string
}
export interface CuentaCorrienteInput {
  cliente: number
  tope: string
  observaciones: string | null
  activa: boolean
}

export type TipoMovimientoCC = 'D' | 'C'

export interface MovimientoCuentaCorriente {
  id: number
  cuenta: number
  cliente_nombre: string
  importe: string
  fecha: string
  tipo: TipoMovimientoCC
  tipo_display: string
  usuario: number
  usuario_username: string
  venta: number | null
  observaciones: string | null
}
export interface MovimientoCuentaCorrienteInput {
  cuenta: number
  importe: string
  tipo: TipoMovimientoCC
  observaciones: string | null
}
