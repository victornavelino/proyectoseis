export interface Caja {
  id: number
  sucursal: number
  sucursal_nombre: string
  usuario: number
  usuario_username: string
  fecha_inicio: string
  fecha_fin: string | null
  caja_inicial: string
  caja_final: string
  saldo_actual: string
}

export interface TarjetaDeCredito {
  id: number
  nombre: string
  banco: string | null
}
export type TarjetaDeCreditoInput = Omit<TarjetaDeCredito, 'id'>

export interface PlanTarjetaDeCredito {
  id: number
  tarjeta: number
  tarjeta_nombre: string
  nombre_plan: string
  interes: string
  es_vale: boolean
}
export type PlanTarjetaDeCreditoInput = Omit<PlanTarjetaDeCredito, 'id' | 'tarjeta_nombre'>

export interface PagoEfectivoInput {
  importe: string
}

export interface PagoTarjetaInput {
  plan_tarjeta: number
  numero_tarjeta?: string
  importe: string
  numero_cupon?: string
  lote?: string
  observaciones?: string
}

export interface PagoCuentaCorrienteInput {
  importe: string
  observaciones?: string
}

export interface PagoTransferenciaInput {
  importe: string
  nombre?: string
  apellido?: string
  documento_identidad: string
  banco?: string
  observaciones?: string
}

export interface CobrarVentaInput {
  venta: number
  pagos_efectivo: PagoEfectivoInput[]
  pagos_tarjeta: PagoTarjetaInput[]
  pagos_cuenta_corriente: PagoCuentaCorrienteInput[]
  pagos_transferencia: PagoTransferenciaInput[]
}

export interface ConceptoImporte {
  concepto: string
  importe: string
}

export interface ResumenCierreCaja extends Caja {
  ingresos: ConceptoImporte[]
  total_ingresos: ConceptoImporte
  egresos: ConceptoImporte[]
  total_egresos: ConceptoImporte
  total_cuenta_corriente: ConceptoImporte
}
