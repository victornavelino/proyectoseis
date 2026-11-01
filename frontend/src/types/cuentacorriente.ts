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

// Sólo tiene sentido en un Crédito (con qué pagó el cliente) -ver
// cuentacorriente.models.MovimientoCuentaCorriente.medio_pago.
export type MedioPagoCC = 'efectivo' | 'transferencia' | 'qr' | 'tarjeta'

export interface MovimientoCuentaCorriente {
  id: number
  cuenta: number
  cliente_nombre: string
  importe: string
  fecha: string
  tipo: TipoMovimientoCC
  tipo_display: string
  medio_pago: MedioPagoCC | null
  medio_pago_display: string | null
  banco: number | null
  banco_nombre: string | null
  plan_tarjeta: number | null
  plan_tarjeta_detalle: string | null
  usuario: number
  usuario_username: string
  venta: number | null
  observaciones: string | null
}
export interface MovimientoCuentaCorrienteInput {
  cuenta: number
  importe: string
  tipo: TipoMovimientoCC
  medio_pago: MedioPagoCC | null
  banco: number | null
  plan_tarjeta: number | null
  // Sólo se usan con medio_pago tarjeta: viajan hasta el CuponPagoTarjeta, no son campos
  // persistidos en MovimientoCuentaCorriente (ver cuentacorriente.serializers).
  numero_cupon?: string | null
  lote?: string | null
  observaciones: string | null
}
